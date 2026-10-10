#!/usr/bin/env python3
"""Audition short recognized notes while preserving the accepted note list.

Rechecks Basic Pitch with a shorter minimum duration, uses CQT pitch support,
rejects adjacent-pitch ambiguity and refuses to crowd existing tracker voices.
This does not repair vibrato contours or merge sustained-note fragments.
"""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
from arrange_tracker import role_map


def note_rows(note,step):
    first=max(0,math.floor(note[0]/step+.5))
    last=max(first+1,math.floor(note[1]/step+.5))
    return range(first,last)


def choose_additions(base,evidence,bpm=92):
    step=7.5/bpm
    occupancy=collections.Counter(row for note in base for row in note_rows(note,step))
    accepted=[]
    reviewed=[]
    for entry in sorted(evidence,key=lambda e:(-e['note'][3],e['note'][0],e['note'][2])):
        n=entry['note']
        duration=n[1]-n[0]
        reason='accepted short-note candidate'
        same=[o for o in base+accepted if o[2]==n[2] and min(o[1],n[1])>max(o[0],n[0])]
        neighbor=[o for o in base+accepted if abs(o[2]-n[2])==1 and
                  max(0,min(o[1],n[1])-max(o[0],n[0]))>duration*.5]
        if same:
            reason='already covered by accepted pitch'
        elif not .05<=duration<=.128:
            reason='outside short-note scope'
        elif n[3]<.4 or entry['onset_probability']<.5:
            reason='weak note or attack evidence'
        elif entry['pitch_ratio']<1.25:
            reason='weak isolated pitch evidence'
        elif neighbor:
            reason='adjacent pitch ambiguity; possible vibrato'
        elif any(occupancy[row]>=7 for row in note_rows(n,step)):
            reason='would crowd accepted seven pitched voices'
        else:
            accepted.append(n)
            occupancy.update(note_rows(n,step))
        reviewed.append(dict(entry,decision=reason))
    return sorted(accepted,key=lambda n:(n[0],n[2])),reviewed


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--bpm',type=int,default=92)
    p.add_argument('--duration',type=float,default=24)
    a=p.parse_args()
    if not 32<=a.bpm<=255 or not 0<a.duration<=120:
        p.error('invalid BPM/duration')
    base=json.loads(a.notes.read_text())
    arrangement=json.loads(a.arrangement.read_text())
    base_sha=hashlib.sha256(a.notes.read_bytes()).hexdigest()
    if arrangement['notes_sha256']!=base_sha:
        p.error('arrangement belongs to a different note file')
    if arrangement['source_sha256']!=hashlib.sha256(a.audio.read_bytes()).hexdigest():
        p.error('audio differs from the accepted source')
    import librosa
    import numpy as np
    from basic_pitch.note_creation import model_frames_to_time
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    a.out.mkdir(parents=True,exist_ok=True)
    import soundfile as sf
    from basic_pitch.inference import predict
    sf.write(a.out/'excerpt.wav',y,sr)
    outputs,_,events=predict(a.out/'excerpt.wav',minimum_note_length=60)
    candidates=[[float(n[0]),float(n[1]),int(n[2]),float(n[3])] for n in events]
    (a.out/'short-note-candidates.json').write_text(json.dumps(candidates,indent=2)+'\n')
    np.savez_compressed(a.out/'model-output.npz',**outputs)
    times=model_frames_to_time(len(outputs['onset']))
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=256,fmin=librosa.midi_to_hz(24),n_bins=72))
    evidence=[]
    for n in candidates:
        begin=max(0,int(np.searchsorted(times,n[0]-.025)))
        end=min(len(times),int(np.searchsorted(times,n[0]+.04))+1)
        pitch=n[2]-21
        onset=float(np.max(outputs['onset'][begin:end,pitch])) if begin<end and 0<=pitch<88 else 0
        first=max(0,round(n[0]*sr/256));last=min(cqt.shape[1],max(first+1,round(n[1]*sr/256)))
        index=n[2]-24
        ratio=0
        if 1<=index<71 and first<last:
            strength=float(np.mean(cqt[index,first:last]))
            neighbor=max(float(np.mean(cqt[index-1,first:last])),float(np.mean(cqt[index+1,first:last])))
            ratio=strength/max(1e-12,neighbor)
        evidence.append(dict(note=n,onset_probability=onset,pitch_ratio=ratio))
    additions,reviewed=choose_additions(base,evidence,a.bpm)
    updated=base+additions
    note_file=a.out/'notes.json'
    note_file.write_text(json.dumps(updated,indent=2)+'\n')
    arrangement['roles']+=role_map(additions)
    arrangement['notes_sha256']=hashlib.sha256(note_file.read_bytes()).hexdigest()
    arrangement['note_recovery']=dict(base_notes_sha256=base_sha,
                                     added_notes=additions,minimum_candidate_ms=60,
                                     method='short-note recheck + attack/CQT/ambiguity/capacity gates',
                                     limitations='Candidate additions need audition; original events preserved; no vibrato effects or sustained-gap merging')
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    report=dict(original_notes=len(base),candidate_notes=len(candidates),added_notes=len(additions),
                decisions=dict(collections.Counter(e['decision'] for e in reviewed)),review=reviewed)
    (a.out/'recovery-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='review'},indent=2))


if __name__=='__main__':
    main()
