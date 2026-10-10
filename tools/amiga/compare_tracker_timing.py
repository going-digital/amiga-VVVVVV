#!/usr/bin/env python3
"""Make a finer-row editing comparison without changing recognized notes.

Accepted drum tick times are retained. Existing vibrato is re-calibrated for
speed 3 at the doubled editing BPM using independently rendered pitch traces.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def finer_arrangement(arrangement,bpm=92):
    if not 32<=bpm<=127:raise ValueError('doubled editing BPM must fit MOD tempo')
    if arrangement.get('tick_multiplier',1)!=2:
        raise ValueError('comparison requires the accepted doubled tick clock')
    if arrangement['percussion'].get('timing')!='ticks':
        raise ValueError('comparison requires accepted tick-timed percussion')
    result=copy.deepcopy(arrangement)
    step=7.5/bpm
    result['tick_multiplier']=1
    for hit in result['percussion']['hits']:
        # Preserve baseline EDx rounding rather than resnapping original times
        # onto the now twice-as-fine tick grid.
        hit['time']=max(0,math.floor(hit['time']/(step/3)+.5))*(step/3)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--library',type=Path,required=True)
    p.add_argument('--bpm',type=int,default=92)
    a=p.parse_args()
    baseline=json.loads(a.arrangement.read_text())
    try:arrangement=finer_arrangement(baseline,a.bpm)
    except ValueError as error:p.error(str(error))
    a.out.mkdir(parents=True,exist_ok=True)
    from detect_vibrato import calibrate
    review=[]
    fits={entry['note_index']:entry for entry in baseline.get('vibrato_detection',{}).get('review',[]) if entry['accepted']}
    for index,effect in enumerate(arrangement.get('vibrato',[])):
        if effect is None:continue
        if index not in fits:p.error('existing vibrato lacks source fit for independent re-calibration')
        target=fits[index]
        selected,calibration=calibrate(a.library,a.out,target['pitch'],arrangement['roles'][index],target['fundamental'],bpm=a.bpm*2,tick_multiplier=1)
        actual=calibration['chosen'];source=target['fundamental']
        if actual['score']<.6 or abs(actual['rate']-source['rate'])>.5 or not .5<=actual['depth_cents']/source['depth_cents']<=1.5:
            p.error('finer-grid vibrato calibration outside tolerance')
        arrangement['vibrato'][index]=selected
        review.append(dict(note_index=index,effect=selected,calibration=calibration))
    arrangement['timing_comparison']=dict(baseline_arrangement_sha256=hashlib.sha256(a.arrangement.read_bytes()).hexdigest(),
        baseline_editing_bpm=a.bpm,editing_bpm=a.bpm*2,baseline_speed=6,replay_speed=3,
        calibration_library_sha256=hashlib.sha256(a.library.read_bytes()).hexdigest(),vibrato_review=review,
        limitations='Timing audition only; note list unchanged; attacks/releases re-quantized; accepted drum tick times preserved; source vibrato phase still approximate')
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(arrangement['timing_comparison'],indent=2))


if __name__=='__main__':main()
