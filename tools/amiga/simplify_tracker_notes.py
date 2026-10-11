#!/usr/bin/env python3
"""Merge weak adjacent same-pitch segmentation and use fixed instrument levels.

Source attack evidence protects rhythmic repeats; existing calibrated vibrato
is never merged. Outputs a separate audition and preserves original metadata.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
from recover_short_notes import note_rows


def merge_fragments(notes,roles,vibrato,evidence,bpm=92):
    if len(roles)!=len(notes) or len(vibrato)!=len(notes) or not 32<=bpm<=255:raise ValueError('invalid roles/effects/grid')
    updated=copy.deepcopy(notes);parent=list(range(len(notes)));removed=set();review=[];step=7.5/bpm
    for entry in sorted(evidence,key=lambda e:notes[e['following']][0]):
        first,following=entry['first'],entry['following'];root=parent[first]
        a,b=updated[root],updated[following];gap=b[0]-a[1]
        reason='merged weak same-pitch fragment'
        if following in removed:
            reason='fragment already consumed'
        elif a[2]!=b[2] or roles[root]!=roles[following] or not -.001<=gap<=.025:
            reason='different pitch/role or noncontiguous notes'
        elif vibrato[root] is not None or vibrato[following] is not None:
            reason='preserve calibrated vibrato'
        elif entry['onset_probability']>=.65 or max(entry['harmonic_rises'])>=1.5:
            reason='preserve supported repeated attack'
        else:
            old_rows=set(note_rows(a,step))|set(note_rows(b,step))
            if set(note_rows([a[0],b[1],a[2],a[3]],step))-old_rows:
                reason='would fill an additional tracker row'
            else:
                a[1]=b[1];removed.add(following);parent[following]=root
        review.append(dict(entry,decision=reason,parent_original_index=root))
    retained=[i for i in range(len(notes)) if i not in removed]
    return [updated[i] for i in retained],retained,review


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--candidate-dir',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.out.exists():p.error('choose a new output directory; do not overwrite tracker edits')
    notes_path=a.baseline/'notes.json';notes=json.loads(notes_path.read_text());arr=json.loads((a.baseline/'arrangement.json').read_text());cached=json.loads((a.candidate_dir/'arrangement.json').read_text())
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    if arr['source_sha256']!=digest(a.audio) or arr['notes_sha256']!=digest(notes_path) or cached['source_sha256']!=arr['source_sha256']:p.error('source/baseline/candidate mismatch')
    import librosa
    import numpy as np
    from basic_pitch.note_creation import model_frames_to_time
    model_path=a.candidate_dir/'model-output.npz';model=np.load(model_path);times=model_frames_to_time(len(model['note']))
    y,sr=librosa.load(a.audio,sr=22050,duration=24)
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=128,fmin=librosa.midi_to_hz(24),n_bins=288,bins_per_octave=36));ct=np.arange(cqt.shape[1])*128/sr
    groups=collections.defaultdict(list);evidence=[]
    for index,note in enumerate(notes):groups[(note[2],arr['roles'][index])].append(index)
    for (pitch,role),indices in groups.items():
        indices.sort(key=lambda i:notes[i][0])
        for first,following in zip(indices,indices[1:]):
            time=notes[following][0];gap=time-notes[first][1]
            if not -.001<=gap<=.025:continue
            frames=(times>=time-.025)&(times<time+.025)
            before=(ct>=time-.045)&(ct<time-.01);after=(ct>=time)&(ct<time+.04)
            if not frames.any() or not before.any() or not after.any():continue
            rises=[]
            for harmonic in (1,2,3):
                band=round((pitch-24+12*np.log2(harmonic))*3)
                energy=cqt[max(0,band-1):band+2].max(axis=0)
                rises.append(float(energy[after].mean()/max(1e-9,energy[before].mean())))
            evidence.append(dict(first=first,following=following,time=time,pitch=pitch,gap=gap,onset_probability=float(model['onset'][frames,pitch-21].max()),harmonic_rises=rises))
    updated,retained,review=merge_fragments(notes,arr['roles'],arr['vibrato'],evidence)
    result={key:copy.deepcopy(arr[key]) for key in ('source_sha256','percussion','role_levels','tick_multiplier')}
    result.update(roles=[arr['roles'][i] for i in retained],vibrato=[arr['vibrato'][i] for i in retained],waveform_profile='pulse-triangle',fixed_volume=32)
    # Operational calibration indices follow the retained score. All historical
    # recovery/role reviews stay in a separate, byte-identical baseline file.
    mapping={old:new for new,old in enumerate(retained)}
    if 'vibrato_detection' in arr:
        result['vibrato_detection']=copy.deepcopy(arr['vibrato_detection'])
        result['vibrato_detection']['review']=[dict(e,original_note_index=e['note_index'],note_index=mapping[e['note_index']]) for e in arr['vibrato_detection']['review'] if e['note_index'] in mapping]
    a.out.mkdir(parents=True);out_notes=a.out/'notes.json';out_notes.write_text(json.dumps(updated,indent=2)+'\n');result['notes_sha256']=digest(out_notes)
    result['note_simplification']=dict(base_notes_sha256=digest(notes_path),baseline_arrangement_sha256=digest(a.baseline/'arrangement.json'),model_output_sha256=digest(model_path),retained_original_indices=retained,review=review,
        limitations='Conservative same-pitch segmentation merge needs audition; fixed levels replace recognition-confidence dynamics; calibrated vibrato protected; no additional active tracker rows or new pitches')
    (a.out/'baseline-arrangement.json').write_bytes((a.baseline/'arrangement.json').read_bytes())
    (a.out/'arrangement.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(original_notes=len(notes),notes=len(updated),decisions=dict(collections.Counter(e['decision'] for e in review))),indent=2))


if __name__=='__main__':main()
