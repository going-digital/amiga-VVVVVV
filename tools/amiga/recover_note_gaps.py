#!/usr/bin/env python3
"""Audition supported short same-pitch gaps without removing any attacks.

Extends note releases only. This is not vibrato-effect transcription and does
not establish whether the source articulation was intended to be staccato.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
from recover_short_notes import note_rows


def extend_gaps(notes,evidence,bpm=92):
    result=copy.deepcopy(notes)
    occupancy=collections.Counter(row for note in notes for row in note_rows(note,7.5/bpm))
    review=[]
    for entry in sorted(evidence,key=lambda e:(-e['note_mean'],e['first'])):
        first,following=entry['first'],entry['following']
        a,b=result[first],result[following]
        gap=b[0]-a[1]
        extra=set(note_rows([a[0],b[0],a[2],a[3]],7.5/bpm))-set(note_rows(a,7.5/bpm))
        reason='supported release extension'
        if a[2]!=b[2] or not .02<gap<=.2:
            reason='outside same-pitch short-gap scope'
        elif entry['note_mean']<.2 or entry['note_min']<.12 or entry['contour_mean']<.18 or entry['contour_min']<.14:
            reason='weak continuous model evidence'
        elif entry['pitch_ratio']<1.4:
            reason='weak isolated source pitch'
        elif entry['internal_onset']>=.5:
            reason='possible unrecognized attack inside gap'
        elif not extra:
            reason='no tracker-row gap to repair'
        elif any(occupancy[row]>=7 for row in extra):
            reason='would crowd accepted pitched voices'
        else:
            a[1]=b[0]
            occupancy.update(extra)
        review.append(dict(entry,old_end=notes[first][1],new_end=a[1],decision=reason))
    return result,review


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    p.add_argument('--bpm',type=int,default=92)
    a=p.parse_args()
    if not 0<a.duration<=120 or not 32<=a.bpm<=255:
        p.error('invalid duration/BPM')
    notes=json.loads(a.notes.read_text());arrangement=json.loads(a.arrangement.read_text())
    base_sha=hashlib.sha256(a.notes.read_bytes()).hexdigest()
    if arrangement['notes_sha256']!=base_sha or arrangement['source_sha256']!=hashlib.sha256(a.audio.read_bytes()).hexdigest():
        p.error('source or accepted notes differ from arrangement')
    import librosa
    import numpy as np
    import soundfile as sf
    from basic_pitch.inference import predict
    from basic_pitch.note_creation import model_frames_to_time,midi_pitch_to_contour_bin
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    a.out.mkdir(parents=True,exist_ok=True)
    sf.write(a.out/'excerpt.wav',y,sr)
    model,_,_=predict(a.out/'excerpt.wav',minimum_note_length=60)
    np.savez_compressed(a.out/'model-output.npz',**model)
    times=model_frames_to_time(len(model['note']))
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=256,fmin=librosa.midi_to_hz(24),n_bins=72))
    cqt_times=np.arange(cqt.shape[1])*256/sr
    groups=collections.defaultdict(list)
    for i,n in enumerate(notes):groups[n[2]].append(i)
    evidence=[]
    for pitch,indices in groups.items():
        indices.sort(key=lambda i:notes[i][0])
        for first,following in zip(indices,indices[1:]):
            start,end=notes[first][1],notes[following][0]
            if not .02<end-start<=.2:continue
            frames=(times>=start)&(times<end)
            cqframes=(cqt_times>=start)&(cqt_times<end)
            index=pitch-24
            if not frames.any() or not cqframes.any() or not 1<=index<71:continue
            note=model['note'][frames,pitch-21]
            center=int(round(float(midi_pitch_to_contour_bin(pitch))))
            contour=model['contour'][frames,max(0,center-1):min(264,center+2)].max(axis=1)
            interior=(times>=start+.025)&(times<end-.025)
            onset=float(model['onset'][interior,pitch-21].max()) if interior.any() else 0
            ratio=float(cqt[index,cqframes].mean()/max(1e-12,cqt[index-1,cqframes].mean(),cqt[index+1,cqframes].mean()))
            evidence.append(dict(first=first,following=following,pitch=pitch,gap_seconds=end-start,
                                 note_mean=float(note.mean()),note_min=float(note.min()),
                                 contour_mean=float(contour.mean()),contour_min=float(contour.min()),
                                 pitch_ratio=ratio,internal_onset=onset))
    updated,review=extend_gaps(notes,evidence,a.bpm)
    output=a.out/'notes.json';output.write_text(json.dumps(updated,indent=2)+'\n')
    arrangement['notes_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
    arrangement['gap_recovery']=dict(base_notes_sha256=base_sha,review=review,
                                    limitations='Release extensions need audition; starts/pitches/strengths and all following attacks retained; no vibrato effects')
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(dict(decisions=dict(collections.Counter(e['decision'] for e in review)),
                         extensions=[e for e in review if e['decision']=='supported release extension']),indent=2))


if __name__=='__main__':main()
