#!/usr/bin/env python3
"""Recover strong same-pitch attacks hidden inside accepted held notes."""
import argparse
import collections
import copy
import hashlib
import json
import math
from pathlib import Path
from recover_short_notes import note_rows


def split_attacks(notes,evidence,vibrato=None,bpm=92):
    updated=copy.deepcopy(notes);tails=[];parents=[];review=[];cuts=collections.defaultdict(dict)
    step=7.5/bpm
    for entry in sorted(evidence,key=lambda e:(-e['onset_probability'],e['time'])):
        index,time=entry['note_index'],entry['time'];note=notes[index]
        first,last=note_rows(note,step).start,note_rows(note,step).stop
        row=math.floor(time/step+.5)
        reason='accepted same-pitch retrigger'
        if not note[0]+.07<time<note[1]-.07 or not first<row<last:
            reason='outside interior tracker rows'
        elif vibrato and vibrato[index] is not None:
            reason='preserve accepted vibrato articulation'
        elif entry['onset_probability']<.7 or entry['note_probability']<.3:
            reason='weak model attack'
        elif entry['fundamental_rise']<2 or entry['harmonic_rise']<1.5 or entry['pitch_ratio']<1.3:
            reason='weak isolated harmonic attack'
        elif any(i!=index and o[2]==note[2] and abs(o[0]-time)<.04 for i,o in enumerate(notes)):
            reason='same-pitch attack already recognized'
        elif row in cuts[index] or any(abs(time-other)<.07 for other in cuts[index].values()):
            reason='duplicate row or closely spaced attack'
        else:cuts[index][row]=time
        review.append(dict(entry,decision=reason))
    for index,rows in sorted(cuts.items()):
        times=sorted(rows.values());original=notes[index]
        updated[index][1]=times[0]
        for start,end in zip(times,times[1:]+[original[1]]):
            tails.append([start,end,original[2],original[3]]);parents.append(index)
    return updated+tails,parents,review


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--bpm',type=int,default=92)
    p.add_argument('--duration',type=float,default=24)
    a=p.parse_args()
    if not 32<=a.bpm<=255 or not 0<a.duration<=120:p.error('invalid BPM/duration')
    notes=json.loads(a.notes.read_text());arrangement=json.loads(a.arrangement.read_text())
    base_sha=hashlib.sha256(a.notes.read_bytes()).hexdigest()
    if arrangement['notes_sha256']!=base_sha or arrangement['source_sha256']!=hashlib.sha256(a.audio.read_bytes()).hexdigest():
        p.error('source/notes differ from accepted arrangement')
    import librosa
    import numpy as np
    import soundfile as sf
    from scipy.signal import find_peaks
    from basic_pitch.inference import predict
    from basic_pitch.note_creation import model_frames_to_time
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    a.out.mkdir(parents=True,exist_ok=True);sf.write(a.out/'excerpt.wav',y,sr)
    model,_,_=predict(a.out/'excerpt.wav',minimum_note_length=35,onset_threshold=.4,frame_threshold=.25)
    np.savez_compressed(a.out/'model-output.npz',**model)
    times=model_frames_to_time(len(model['note']))
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=128,fmin=librosa.midi_to_hz(24),n_bins=84))
    ct=np.arange(cqt.shape[1])*128/sr;evidence=[]
    for index,note in enumerate(notes):
        start,end,pitch,_=note
        if end-start<.14 or not 25<=pitch<=94:continue
        for frame in find_peaks(model['onset'][:,pitch-21],height=.4,prominence=.15,distance=6)[0]:
            time=float(times[frame])
            if not start+.07<time<min(end-.07,len(y)/sr-.04):continue
            before=(ct>=time-.045)&(ct<time-.01);after=(ct>=time)&(ct<time+.04)
            if not before.any() or not after.any():continue
            fundamental=pitch-24;harmonic=fundamental+12
            rise=lambda band:float(cqt[band,after].mean()/max(1e-9,cqt[band,before].mean()))
            ratio=float(cqt[fundamental,after].mean()/max(1e-9,cqt[fundamental-1,after].mean(),cqt[fundamental+1,after].mean()))
            evidence.append(dict(note_index=index,time=time,onset_probability=float(model['onset'][frame,pitch-21]),
                                 note_probability=float(model['note'][frame,pitch-21]),
                                 fundamental_rise=rise(fundamental),harmonic_rise=rise(harmonic),pitch_ratio=ratio))
    updated,parents,review=split_attacks(notes,evidence,arrangement.get('vibrato'),a.bpm)
    output=a.out/'notes.json';output.write_text(json.dumps(updated,indent=2)+'\n')
    roles=arrangement['roles'];arrangement['roles']=roles+[roles[i] for i in parents]
    if 'vibrato' in arrangement:arrangement['vibrato']+=[None]*len(parents)
    arrangement['notes_sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
    arrangement['retrigger_recovery']=dict(base_notes_sha256=base_sha,tail_parent_indices=parents,review=review,
        limitations='Same-pitch attacks inferred from model and harmonic rises; articulation needs audition; existing pitch/strength/coverage preserved; vibrato notes excluded')
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(dict(retriggers=len(parents),decisions=dict(collections.Counter(e['decision'] for e in review)),
                         accepted=[e for e in review if e['decision']=='accepted same-pitch retrigger']),indent=2))


if __name__=='__main__':main()
