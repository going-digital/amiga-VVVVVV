#!/usr/bin/env python3
"""Audition existing lower-register notes with the lead instrument.

Explicit time/pitch requests test a role hypothesis, not automatic instrument
recognition. Note pitches, timings and recognition confidences stay unchanged.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def lead_role_audition(notes, arrangement, requests, tolerance=.035):
    if not 0<tolerance<=.1:raise ValueError('invalid onset matching tolerance')
    if len(arrangement['roles'])!=len(notes):raise ValueError('role count differs from notes')
    result=copy.deepcopy(arrangement);changes=[];selected=set()
    for time,pitch in requests:
        if not math.isfinite(time) or not 0<=time<=24 or not 48<=pitch<67:
            raise ValueError('request must identify a lower-register pitched note')
        matches=[i for i,n in enumerate(notes) if n[2]==pitch and abs(n[0]-time)<=tolerance]
        if len(matches)!=1:raise ValueError('request must match exactly one existing note')
        index=matches[0]
        if index in selected:raise ValueError('duplicate note request')
        if result['roles'][index]!='harmony':raise ValueError('requested note must currently use harmony')
        if result.get('vibrato',[None]*len(notes))[index] is not None:
            raise ValueError('role change requires fresh vibrato calibration')
        selected.add(index);result['roles'][index]='lead'
        strength=notes[index][3];levels=result['role_levels']
        changes.append(dict(note_index=index,time=notes[index][0],pitch=pitch,
            old_role='harmony',role='lead',
            old_volume=min(48,round(strength*48*levels['harmony'])),
            volume=min(48,round(strength*48*levels['lead']))))
    return result,changes


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--lead-note',action='append',required=True,metavar='SECONDS:MIDI')
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();notes=json.loads(a.notes.read_text());arrangement=json.loads(a.arrangement.read_text())
    if arrangement['notes_sha256']!=hashlib.sha256(a.notes.read_bytes()).hexdigest():p.error('notes differ from arrangement')
    try:
        requests=[]
        for value in a.lead_note:
            time,pitch=value.split(':');requests.append((float(time),int(pitch)))
        result,changes=lead_role_audition(notes,arrangement,requests)
    except ValueError as error:p.error(str(error))
    result['lead_role_audition']=dict(baseline_arrangement_sha256=hashlib.sha256(a.arrangement.read_bytes()).hexdigest(),changes=changes,
        limitations='Explicit lower-register role hypothesis for audition, not recovered notes or confirmed instrument identity; brighter sample and existing lead gain both change; no pitch/timing/percussion edits')
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'notes.json').write_bytes(a.notes.read_bytes())
    (a.out/'arrangement.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['lead_role_audition'],indent=2))


if __name__=='__main__':main()
