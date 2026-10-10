#!/usr/bin/env python3
"""Recover fast pitched attacks supported by source evidence and nearby runs.

These are candidate arpeggio/run notes, not inferred MOD arpeggio effects.
Retains accepted events and reserves the eighth channel for percussion.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
from arrange_tracker import role_map
from recover_short_notes import note_rows


def choose_fast(notes,evidence,bpm=92):
    occupancy=collections.Counter(row for n in notes for row in note_rows(n,7.5/bpm))
    accepted=[];review=[]
    for e in sorted(evidence,key=lambda e:(-e['note'][3],e['note'][0],e['note'][2])):
        n=e['note'];start,end,pitch,strength=n
        reason='accepted fast pitched attack'
        current=notes+accepted
        overlap=lambda o:max(0,min(o[1],end)-max(o[0],start))
        # Supporting attacks come from the accepted baseline, not other new
        # candidates. Distinct pitches/times prevent a chord or vibrato fragment
        # from supplying its own evidence for a fast run.
        support=[o for o in notes if .025<=abs(o[0]-start)<=.22 and
                 .035<=o[1]-o[0]<=.25 and 2<=abs(o[2]-pitch)<=12 and overlap(o)<=.025]
        preceding=[o for o in support if o[0]<start]
        following=[o for o in support if o[0]>start]
        run=any(a[2]!=b[2] and b[0]-a[0]<=.32 for a in preceding for b in following)
        rows=list(note_rows(n,7.5/bpm))
        if any(o[2]==pitch and overlap(o)>0 for o in current):
            reason='already covered by accepted pitch'
        elif not .035<=end-start<=.128:
            reason='outside fast-note scope'
        elif strength<.3 or e['onset_probability']<.45 or e['contour_mean']<.18:
            reason='weak pitched attack evidence'
        elif e['pitch_ratio']<1.4:
            reason='weak isolated source pitch'
        elif any(abs(o[2]-pitch)==1 and overlap(o)>(end-start)*.5 for o in current):
            reason='adjacent pitch ambiguity'
        elif not run:
            reason='no accepted surrounding fast run'
        elif any(occupancy[row]>=7 for row in rows):
            reason='would crowd accepted pitched voices'
        else:
            accepted.append(n);occupancy.update(rows)
        review.append(dict(e,decision=reason))
    return sorted(accepted,key=lambda n:(n[0],n[2])),review


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    p.add_argument('--bpm',type=int,default=92)
    a=p.parse_args()
    if not 0<a.duration<=120 or not 32<=a.bpm<=255:p.error('invalid duration/BPM')
    notes=json.loads(a.notes.read_text());arrangement=json.loads(a.arrangement.read_text())
    base_sha=hashlib.sha256(a.notes.read_bytes()).hexdigest()
    if arrangement['notes_sha256']!=base_sha or arrangement['source_sha256']!=hashlib.sha256(a.audio.read_bytes()).hexdigest():
        p.error('source/notes differ from accepted arrangement')
    import librosa
    import numpy as np
    import soundfile as sf
    from basic_pitch.inference import predict
    from basic_pitch.note_creation import model_frames_to_time,midi_pitch_to_contour_bin
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    a.out.mkdir(parents=True,exist_ok=True);sf.write(a.out/'excerpt.wav',y,sr)
    model,_,events=predict(a.out/'excerpt.wav',minimum_note_length=35,onset_threshold=.4,frame_threshold=.25)
    np.savez_compressed(a.out/'model-output.npz',**model)
    times=model_frames_to_time(len(model['note']))
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=256,fmin=librosa.midi_to_hz(24),n_bins=72))
    ct=np.arange(cqt.shape[1])*256/sr
    evidence=[]
    for event in events:
        start,end,pitch,strength=float(event[0]),float(event[1]),int(event[2]),float(event[3])
        if end>len(y)/sr:continue
        frames=(times>=start)&(times<end)
        attacks=(times>=start-.025)&(times<=start+.04)
        cqframes=(ct>=start)&(ct<end);index=pitch-24
        if not frames.any() or not attacks.any() or not cqframes.any() or not 1<=index<71:continue
        center=int(round(float(midi_pitch_to_contour_bin(pitch))))
        contour=model['contour'][frames,max(0,center-1):min(264,center+2)].max(axis=1)
        ratio=float(cqt[index,cqframes].mean()/max(1e-12,cqt[index-1,cqframes].mean(),cqt[index+1,cqframes].mean()))
        evidence.append(dict(note=[start,end,pitch,strength],contour_mean=float(contour.mean()),
                             onset_probability=float(model['onset'][attacks,pitch-21].max()),pitch_ratio=ratio))
    additions,review=choose_fast(notes,evidence,a.bpm)
    output=a.out/'notes.json';output.write_text(json.dumps(notes+additions,indent=2)+'\n')
    arrangement['notes_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
    arrangement['roles']+=role_map(additions)
    arrangement['fast_note_recovery']=dict(base_notes_sha256=base_sha,added_notes=additions,review=review,
                                           limitations='Candidate fast runs need audition; accepted notes unchanged; original row grid; no MOD arpeggio/vibrato effects')
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(dict(added_notes=additions,decisions=dict(collections.Counter(e['decision'] for e in review))),indent=2))


if __name__=='__main__':main()
