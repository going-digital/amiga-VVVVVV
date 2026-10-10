#!/usr/bin/env python3
"""Compare source and independently rendered role-audition harmonic profiles.

Mixed-source ratios are diagnostic: shared harmonics can contain other voices.
They do not establish instrument identity or prove a missing independent note.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def profiles(path,notes,changes):
    import librosa
    import numpy as np
    y,sr=librosa.load(path,sr=22050)
    cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=128,fmin=librosa.midi_to_hz(24),n_bins=252,bins_per_octave=36))
    times=np.arange(cqt.shape[1])*128/sr;result=[]
    for change in changes:
        start,end,pitch,_=notes[change['note_index']]
        frames=(times>start+.02)&(times<min(end-.01,start+.13))
        if not frames.any():raise ValueError('note too short for harmonic comparison')
        amplitudes=[]
        for harmonic in (1,2,3):
            index=round((pitch-24+12*np.log2(harmonic))*3)
            amplitudes.append(float(cqt[index-1:index+2,frames].max(axis=0).mean()))
        if amplitudes[0]<1e-9:raise ValueError('no measurable fundamental')
        result.append([v/amplitudes[0] for v in amplitudes])
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path)
    p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--audition',type=Path,required=True)
    a=p.parse_args()
    arrangement=json.loads((a.audition/'arrangement.json').read_text());metadata=arrangement['lead_role_audition']
    if sha(a.baseline/'arrangement.json')!=metadata['baseline_arrangement_sha256'] or sha(a.source)!=arrangement['source_sha256']:p.error('source or baseline differs from audition')
    if sha(a.baseline/'notes.json')!=sha(a.audition/'notes.json') or sha(a.audition/'notes.json')!=arrangement['notes_sha256']:p.error('audition note list changed')
    replay={}
    for name,path in [('baseline',a.baseline),('audition',a.audition)]:
        replay[name]=json.loads((path/'arranged-eight.render.json').read_text())
        if replay[name]['module_sha256']!=sha(path/'arranged-eight.mod'):p.error('render metadata belongs to another module')
    if replay['baseline']['library_sha256']!=replay['audition']['library_sha256']:p.error('renders use different replay libraries')
    notes=json.loads((a.audition/'notes.json').read_text());changes=metadata['changes']
    try:
        measured={name:profiles(path,notes,changes) for name,path in [('source',a.source),('baseline',a.baseline/'arranged-eight.wav'),('audition',a.audition/'arranged-eight.wav')]}
    except ValueError as error:p.error(str(error))
    review=[]
    for index,change in enumerate(changes):
        ratios={name:rows[index] for name,rows in measured.items()}
        errors={name:[abs(ratios[name][h]-ratios['source'][h]) for h in (1,2)] for name in ('baseline','audition')}
        review.append(dict(change,ratios=ratios,absolute_ratio_errors=errors))
    report=dict(source_sha256=sha(a.source),notes_sha256=arrangement['notes_sha256'],replay=replay,
        render_audio_sha256={name:sha(path/'arranged-eight.wav') for name,path in [('baseline',a.baseline),('audition',a.audition)]},
        measurement=dict(sample_rate=22050,hop=128,bins_per_semitone=3,harmonics=[1,2,3],window_start_offset=.02,window_end_offset=-.01,maximum_window_end_offset=.13),review=review,
        limitations='Mixed-source harmonic magnitudes normalized to each fundamental; shared harmonics, phase interference, quantization and leakage can affect ratios; role audition changes both timbre and volume; no instrument-identity inference')
    (a.audition/'harmonic-comparison.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(review,indent=2))


if __name__=='__main__':main()
