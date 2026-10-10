#!/usr/bin/env python3
"""Add conservative, evidence-backed pickups to an accepted repeating groove.

Anchors, bar phase and samples remain unchanged. Recurring kick syncopations
are admitted only in observed bars; snare pickups only at observed phrase ends.
"""
import argparse
import copy
import json
import math
from pathlib import Path


def add_variations(percussion,duration,min_bars=3,phrase_bars=4):
    if not 0<duration<=120 or min_bars<2 or phrase_bars<2:
        raise ValueError('invalid duration/support/phrase length')
    result=copy.deepcopy(percussion)
    base=percussion.get('base_groove_hits',percussion['hits'])
    result['hits']=copy.deepcopy(base)
    template=percussion['bar_template']
    period,phase,bins=template['seconds'],template['phase'],template['bins']
    step=period/bins
    anchors={(h['bar'],h['position']) for h in base}
    anchor_positions={e['position'] for e in template['events']}
    support={}
    rejected_alignment=0
    for hit in percussion['unregularized_hits']:
        index=math.floor((hit['time']-phase)/step+.5)
        if index<0:
            continue
        aligned=phase+index*step
        # Loose recognition timestamps need to agree with the approved grid.
        if abs(hit['time']-aligned)>step*.3:
            rejected_alignment+=1
            continue
        bar,position=divmod(index,bins)
        key=(hit['sample'],position)
        previous=support.setdefault(key,{}).get(bar)
        if previous is None or hit['strength']>previous['strength']:
            support[key][bar]=hit
    choices=[]
    for (sample,position),bars in support.items():
        kind=percussion['samples'][sample]['name'].split()[0]
        if position in anchor_positions or len(bars)<min_bars:
            continue
        if kind=='kick' and position%2==0:
            mode='observed kick syncopation'
        elif kind=='snare' and position>=bins*3//4:
            mode='observed phrase-end snare pickup'
        else:
            continue
        choices.append(dict(sample=sample,position=position,supporting_bars=sorted(bars),
                            mode=mode,bars=bars))
    extras=[]
    used_bars=set()
    # One extra per bar. Phrase-end pickups take priority at phrase boundaries;
    # otherwise stronger recurrence wins. Never remove/move an anchor.
    for bar in range(math.ceil((duration-phase)/period)):
        available=[choice for choice in choices if bar in choice['bars'] and
                   ('kick' in choice['mode'] or bar%phrase_bars==phrase_bars-1)]
        available.sort(key=lambda c:('snare' not in c['mode'],-len(c['bars']),-c['position']))
        for choice in available:
            position=choice['position']
            time=phase+(bar+position/bins)*period
            if not 0<=time<duration or (bar,position) in anchors or bar in used_bars:
                continue
            # Keep the accepted constant gain for EDx instrument-header playback.
            original=choice['bars'][bar]
            extra=dict(time=time,sample=choice['sample'],strength=original['strength'],
                       bar=bar,position=position,variation=choice['mode'],
                       detected_time=original['time'])
            extras.append(extra)
            used_bars.add(bar)
            break
    result['base_groove_hits']=copy.deepcopy(base)
    result['hits']=sorted(result['hits']+extras,key=lambda h:h['time'])
    result['variations']=dict(min_support_bars=min_bars,phrase_bars=phrase_bars,
                              max_extras_per_bar=1,alignment_tolerance_seconds=step*.3,
                              rejected_alignment=rejected_alignment,added_hits=extras,
                              candidates=[{k:v for k,v in c.items() if k!='bars'} for c in choices],
                              limitations='Conservative hypotheses; no new drum identities; source hit labels may be wrong; assumed phrase length; not an exact rhythm transcription')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    p.add_argument('--min-bars',type=int,default=3)
    p.add_argument('--phrase-bars',type=int,default=4)
    a=p.parse_args()
    arrangement=json.loads(a.arrangement.read_text())
    arrangement['percussion']=add_variations(arrangement['percussion'],a.duration,a.min_bars,a.phrase_bars)
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(arrangement['percussion']['variations'],indent=2))


if __name__=='__main__':
    main()
