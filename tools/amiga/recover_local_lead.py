#!/usr/bin/env python3
"""Refine reported lead gaps with narrow-band harmonic and stable-pitch evidence.

Uses an existing model candidate review; does not invent notes from timestamps.
Octave ambiguities remain excluded. Outputs an audition, not a recovered score.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
from recover_short_notes import note_rows


def refine_lead(notes, evidence, bpm=92):
    updated=copy.deepcopy(notes);added=[];changes=[];review=[];step=7.5/bpm
    for entry in sorted(evidence,key=lambda e:(-e['note'][3],e['note'][0])):
        start,end,pitch,strength=entry['note'];current=updated+added
        reason='accepted local lead attack'
        following=[i for i,n in enumerate(updated) if n[2]==pitch and 0<=n[0]-end<=.025 and 0<n[0]-start<=.06]
        merge=following[0] if len(following)==1 else None
        bands=entry['bands'];fundamental=bands[0]
        upper=[b for b in bands[1:] if b['rise']>=2 and b['isolation']>=2 and b['stable'] and abs(b['median_cents']-fundamental['median_cents'])<=20]
        overlap=lambda n:max(0,min(n[1],end)-max(n[0],start))
        if not 67<=pitch<=84 or not .035<=end-start<=.35:
            reason='outside local lead scope'
        elif strength<.3 or entry['onset_probability']<.5 or entry['contour_mean']<.18:
            reason='weak model evidence'
        elif fundamental['rise']<2 or fundamental['isolation']<2 or not fundamental['stable'] or not upper:
            reason='weak isolated stable harmonic attack'
        elif any(n[2]==pitch and overlap(n)>0 for n in current):
            reason='already covered by accepted pitch'
        # Moving an already accepted contiguous attack adds no upper voice.
        # New pitches still require exclusion of simultaneous lower overtones.
        elif merge is None and any(pitch-n[2] in (12,19,24) and abs(n[0]-start)<=.04 for n in current):
            reason='possible overtone of simultaneous lower attack'
        elif merge is None and any(abs(n[2]-pitch)==1 and overlap(n)>(end-start)*.5 for n in current):
            reason='adjacent pitch ambiguity'
        else:
            candidate=([start,updated[merge][1],pitch,updated[merge][3]] if merge is not None else entry['note'])
            other=[n for i,n in enumerate(updated) if i!=merge]+added
            rows=set(note_rows(candidate,step))
            occupancy=collections.Counter(row for n in other for row in note_rows(n,step))
            if any(n[2]==pitch and rows.intersection(note_rows(n,step)) for n in other):
                reason='same-pitch collision after tracker quantization'
            elif any(occupancy[row]>=7 for row in rows):
                reason='would crowd accepted pitched voices'
            elif merge is not None:
                old_start=updated[merge][0];updated[merge][0]=start
                reason='advance accepted same-pitch attack'
                changes.append(dict(note_index=merge,old_start=old_start,start=start,pitch=pitch))
            else:added.append(copy.deepcopy(entry['note']))
        review.append(dict(entry,prior_decision=entry.get('decision'),decision=reason))
    return updated+added,changes,review


def measure_candidates(audio, candidates):
    import librosa
    import numpy as np
    from detect_vibrato import pitch_trace
    y,sr=librosa.load(audio,sr=22050,duration=24)
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=128,fmin=librosa.midi_to_hz(24),n_bins=288,bins_per_octave=36))
    times=np.arange(cqt.shape[1])*128/sr
    spectrum=np.abs(librosa.stft(y,n_fft=2048,hop_length=64))
    trace_times=np.arange(spectrum.shape[1])*64/sr
    result=[]
    for entry in candidates:
        start,end,pitch,_=entry['note']
        before=(times>=start-.045)&(times<start-.01)
        after=(times>=start)&(times<min(end,start+.065))
        indices=np.where((trace_times>=start+.01)&(trace_times<end-.005))[0]
        if not before.any() or not after.any() or len(indices)<5:continue
        bands=[]
        for harmonic in (1,2,3):
            index=round((pitch-24+12*np.log2(harmonic))*3)
            band=cqt[index-1:index+2].max(axis=0)
            trace=pitch_trace(spectrum,sr,2048,indices,librosa.midi_to_hz(pitch)*harmonic)
            bands.append(dict(harmonic=harmonic,
                rise=float(band[after].mean()/max(1e-9,band[before].mean())),
                isolation=float(band[after].mean()/max(1e-9,cqt[index-3,after].mean(),cqt[index+3,after].mean())),
                median_cents=float(np.median(trace)),p90_absolute_cents=float(np.percentile(np.abs(trace),90)),
                stable=bool(np.percentile(np.abs(trace),90)<=40 and np.ptp(trace)<=40)))
        result.append(dict(entry,bands=bands))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--candidate-arrangement',type=Path,required=True)
    p.add_argument('--times',type=float,nargs='+',required=True)
    p.add_argument('--radius',type=float,default=.6)
    p.add_argument('--bpm',type=int,default=92)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if not 32<=a.bpm<=255 or not 0<a.radius<=2 or any(not 0<=t<=24 for t in a.times):p.error('invalid timing window')
    notes=json.loads(a.notes.read_text());arr=json.loads(a.arrangement.read_text());cached=json.loads(a.candidate_arrangement.read_text())
    source_sha=hashlib.sha256(a.audio.read_bytes()).hexdigest();base_sha=hashlib.sha256(a.notes.read_bytes()).hexdigest()
    if arr['notes_sha256']!=base_sha or arr['source_sha256']!=source_sha or cached['source_sha256']!=source_sha or cached['source_note_recovery']['base_notes_sha256']!=base_sha:p.error('source or candidate baseline mismatch')
    candidates=[e for e in cached['source_note_recovery']['review'] if 67<=e['note'][2]<=84 and e['decision']!='already covered by accepted pitch' and min(abs(e['note'][0]-t) for t in a.times)<=a.radius]
    evidence=measure_candidates(a.audio,candidates)
    updated,changes,review=refine_lead(notes,evidence,a.bpm)
    a.out.mkdir(parents=True,exist_ok=True);path=a.out/'notes.json';path.write_text(json.dumps(updated,indent=2)+'\n')
    added=updated[len(notes):];arr['roles']+=['lead']*len(added)
    if 'vibrato' in arr:arr['vibrato']+=[None]*len(added)
    arr['notes_sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    arr['local_lead_recovery']=dict(base_notes_sha256=base_sha,candidate_arrangement_sha256=hashlib.sha256(a.candidate_arrangement.read_bytes()).hexdigest(),reported_times=a.times,radius=a.radius,attack_advances=changes,added_notes=added,review=review,
        limitations='Localized source-supported audition; harmonic coincidence remains excluded; stable pitch is not instrument identity; no new vibrato or percussion')
    (a.out/'arrangement.json').write_text(json.dumps(arr,indent=2)+'\n')
    print(json.dumps(dict(attack_advances=changes,added_notes=added,decisions=dict(collections.Counter(e['decision'] for e in review))),indent=2))


if __name__=='__main__':main()
