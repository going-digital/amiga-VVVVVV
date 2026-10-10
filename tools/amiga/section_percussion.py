#!/usr/bin/env python3
"""Restore observed percussion positions recurring within a bounded section.

Preserves the accepted groove and sparse pickups. No new timbres, unobserved
hits, late-bar fills or missing-hit interpolation are introduced.
"""
import argparse
import copy
import json
import math
from pathlib import Path


def refine_sections(percussion,duration=24,min_bars=4,min_density=.75):
    if not 0<duration<=120 or min_bars<4 or not 0<min_density<=1:
        raise ValueError('invalid duration/support/density')
    result=copy.deepcopy(percussion)
    base=percussion.get('section_base_hits',percussion['hits'])
    result['hits']=copy.deepcopy(base)
    template=percussion['bar_template']
    period,phase,bins=template['seconds'],template['phase'],template['bins']
    step=period/bins
    support={}
    for hit in percussion['unregularized_hits']:
        index=math.floor((hit['time']-phase)/step+.5)
        if index<0 or abs(hit['time']-(phase+index*step))>step*.3:
            continue
        bar,position=divmod(index,bins)
        # Late-bar material remains under the accepted phrase/pickup rules.
        if position>=bins*3//4:
            continue
        bars=support.setdefault((hit['sample'],position),{})
        if bar not in bars or hit['strength']>bars[bar]['strength']:
            bars[bar]=hit
    candidates=[]
    for (sample,position),bars in support.items():
        ordered=sorted(bars)
        if len(ordered)<min_bars:
            continue
        span=ordered[-1]-ordered[0]+1
        density=len(ordered)/span
        if density<min_density:
            continue
        candidates.append(dict(sample=sample,position=position,first_bar=ordered[0],
                               last_bar=ordered[-1],supporting_bars=ordered,density=density))
    # At most one addition in a bar, preferring the most consistently observed
    # position. Existing events win any collision regardless of drum identity.
    occupied={(h['bar'],h['position']) for h in base}
    used=set();extras=[]
    for candidate in sorted(candidates,key=lambda c:(-len(c['supporting_bars']),-c['density'],c['sample'],c['position'])):
        sample,position=candidate['sample'],candidate['position']
        for bar in candidate['supporting_bars']:
            time=phase+(bar+position/bins)*period
            if not 0<=time<duration or (bar,position) in occupied or bar in used:
                continue
            original=support[(sample,position)][bar]
            extras.append(dict(time=time,sample=sample,strength=original['strength'],
                               bar=bar,position=position,detected_time=original['time'],
                               variation='observed section recurrence'))
            occupied.add((bar,position));used.add(bar)
    result['section_base_hits']=copy.deepcopy(base)
    result['hits']=sorted(result['hits']+extras,key=lambda h:h['time'])
    result['section_refinement']=dict(min_support_bars=min_bars,min_density=min_density,
                                      candidates=candidates,added_hits=extras,
                                      alignment_tolerance_seconds=step*.3,
                                      limitations='Detector labels remain hypotheses; section bounds follow observations; no missing-hit interpolation, new instruments or late-bar fills')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    a=p.parse_args()
    arrangement=json.loads(a.arrangement.read_text())
    try:
        arrangement['percussion']=refine_sections(arrangement['percussion'],a.duration)
    except ValueError as error:
        p.error(str(error))
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(arrangement['percussion']['section_refinement'],indent=2))


if __name__=='__main__':
    main()
