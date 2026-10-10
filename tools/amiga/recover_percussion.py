#!/usr/bin/env python3
"""Recheck masked attacks, restoring only observed, established drum positions."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def add_recovered(percussion,observations,duration=24,min_bars=4):
    if not 0<duration<=120 or min_bars<2:
        raise ValueError('invalid duration/support')
    result=copy.deepcopy(percussion)
    base=percussion.get('recovery_base_hits',percussion['hits'])
    result['hits']=copy.deepcopy(base)
    template=percussion['bar_template']
    period,phase,bins=template['seconds'],template['phase'],template['bins']
    step=period/bins
    kinds={s['name'].split()[0]:i for i,s in enumerate(percussion['samples'])}
    established={}
    for hit in base:
        established.setdefault((hit['sample'],hit['position']),set()).add(hit['bar'])
    occupied={(h['bar'],h['position']) for h in base}
    extras=[];review=[];used=set()
    for observation in sorted(observations,key=lambda o:(-o['strength'],o['time'])):
        entry=copy.deepcopy(observation)
        index=math.floor((entry['time']-phase)/step+.5)
        bar,position=divmod(index,bins)
        time=phase+index*step
        sample=kinds.get(entry['kind'])
        reason='recovered established position'
        if sample is None:
            reason='no accepted instrument for this classification'
        elif entry['raw_kind'] is not None and entry['raw_kind']!=entry['kind']:
            reason='conflicting full-mix classification'
        elif abs(entry['time']-time)>step*.3 or not 0<=time<duration:
            reason='outside accepted grid/duration'
        elif len(established.get((sample,position),()))<min_bars:
            reason='position not established in accepted arrangement'
        elif (bar,position) in occupied:
            reason='existing event preserved'
        elif bar in used:
            reason='one recovered hit per bar'
        else:
            extras.append(dict(time=time,sample=sample,strength=entry['strength'],
                               bar=bar,position=position,detected_time=entry['time'],
                               variation='masked attack at established position'))
            occupied.add((bar,position));used.add(bar)
        entry['decision']=reason;review.append(entry)
    result['recovery_base_hits']=copy.deepcopy(base)
    result['hits']=sorted(result['hits']+extras,key=lambda h:h['time'])
    result['attack_recovery']=dict(min_support_bars=min_bars,added_hits=extras,review=review,
                                   limitations='Masked-attack labels are hypotheses; only existing instrument/position combinations; no unobserved hits or new timbres')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    a=p.parse_args()
    if not 0<a.duration<=120:
        p.error('invalid duration')
    arrangement=json.loads(a.arrangement.read_text())
    candidates=json.loads(a.candidates.read_text())
    digest=hashlib.sha256(a.audio.read_bytes()).hexdigest()
    if any(doc.get('percussion_source_sha256')!=digest for doc in (arrangement,candidates)):
        p.error('source recording differs from arrangement/candidates')
    import librosa
    from recognize_percussion import transient_signal
    from reconstruct_drums import measure_attack,classify,classify_masked
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    clean,_,_,_=transient_signal(y,sr)
    observations=[]
    for hit in candidates['percussion']['hits']:
        start=max(0,round(hit['time']*sr));end=start+round(.24*sr)
        if len(y[start:end])<round(.18*sr):
            continue
        metrics=measure_attack(clean[start:end],sr)
        raw_metrics=measure_attack(y[start:end],sr)
        kind,reason=classify_masked(raw_metrics,metrics)
        raw_kind,_=classify(raw_metrics)
        observations.append(dict(time=hit['time'],strength=hit['strength'],kind=kind,
                                 raw_kind=raw_kind,metrics=metrics,raw_metrics=raw_metrics,reason=reason))
    arrangement['percussion']=add_recovered(arrangement['percussion'],observations,min(a.duration,len(y)/sr))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(arrangement['percussion']['attack_recovery']['added_hits'],indent=2))


if __name__=='__main__':
    main()
