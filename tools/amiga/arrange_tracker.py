#!/usr/bin/env python3
"""Build an editable role/timbre audition from cached detected notes and audio.

Roles are pitch-range guesses, not instrument recognition. HPSS transients may
contain melodic attacks; drum labels and selection require audition/correction.
"""
import argparse
import hashlib
import json
from pathlib import Path
from transcribe_tracker import working_module


def role_map(notes, bass_limit=48, lead_limit=67):
    if bass_limit >= lead_limit:
        raise ValueError('bass boundary must be below lead boundary')
    return ['bass' if n[2] < bass_limit else 'lead' if n[2] >= lead_limit else 'harmony'
            for n in notes]


def extract_percussion(audio, duration):
    import librosa
    import numpy as np
    from scipy.signal import resample_poly
    y, sr = librosa.load(audio, sr=22050, duration=duration)
    _, percussive = librosa.effects.hpss(y, margin=(2,4))
    envelope = librosa.onset.onset_strength(y=percussive, sr=sr, hop_length=256)
    frames = librosa.onset.onset_detect(onset_envelope=envelope, sr=sr,
                                      hop_length=256, backtrack=False)
    candidates = []
    for frame in frames:
        onset = int(frame)*256
        start = max(0, onset-round(.008*sr))
        clip = percussive[start:min(len(y),start+round(.16*sr))]
        if len(clip) < 128:
            continue
        energy = float(np.sqrt(np.mean(clip**2)))
        if energy < .002:
            continue
        spectrum = np.abs(np.fft.rfft(clip*np.hanning(len(clip))))
        freq = np.fft.rfftfreq(len(clip),1/sr)
        centroid = float(np.sum(spectrum*freq)/max(1e-12,np.sum(spectrum)))
        name = 'low transient' if centroid < 1500 else 'mid transient' if centroid < 4500 else 'high transient'
        candidates.append(dict(time=onset/sr, name=name, energy=energy, clip=clip))
    samples = []
    names = sorted(set(hit['name'] for hit in candidates))
    for name in names:
        exemplar = max((hit for hit in candidates if hit['name']==name), key=lambda hit:hit['energy'])
        clip = resample_poly(exemplar['clip'],1,2)
        clip *= np.minimum(np.arange(len(clip))/32,1)
        clip *= np.minimum(np.arange(len(clip))[::-1]/128,1)
        clip /= max(1e-12,float(np.max(np.abs(clip))))
        pcm = np.clip(np.rint(clip*100),-127,127).astype(np.int8)
        pcm = pcm[:len(pcm)//2*2]
        pcm[:2] = 0  # conventional MOD no-loop restart area
        samples.append(dict(name=name, pcm=list(pcm.astype(np.uint8).tolist()),
                            source_time=exemplar['time'], sample_rate=11025))
    maximum = max((hit['energy'] for hit in candidates),default=1)
    hits = [dict(time=hit['time'], sample=names.index(hit['name']),
                 strength=min(1, max(.2,hit['energy']/maximum))) for hit in candidates]
    return dict(samples=samples,hits=hits), percussive, sr


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--bpm',type=int,default=92)
    p.add_argument('--duration',type=float,default=24)
    p.add_argument('--bass-limit',type=int,default=48)
    p.add_argument('--lead-limit',type=int,default=67)
    p.add_argument('--arrangement',type=Path,help='Reuse/edit saved role assignments and transient samples/hits')
    args = p.parse_args()
    notes = json.loads(args.notes.read_text())
    args.out.mkdir(parents=True,exist_ok=True)
    notes_digest = hashlib.sha256(args.notes.read_bytes()).hexdigest()
    if args.arrangement:
        arrangement = json.loads(args.arrangement.read_text())
        if arrangement['notes_sha256'] != notes_digest:
            p.error('arrangement belongs to a different detected-note file')
    else:
        drums, percussive, sr = extract_percussion(args.audio,args.duration)
        import soundfile as sf
        sf.write(args.out/'percussive-source.wav',percussive,sr)
        arrangement = dict(notes_sha256=notes_digest,
                           source_sha256=hashlib.sha256(args.audio.read_bytes()).hexdigest(),
                           roles=role_map(notes,args.bass_limit,args.lead_limit),
                           role_levels=dict(bass=1,lead=1.2,harmony=.5),percussion=drums,
                           limitations='Provisional pitch-range roles and HPSS transient guesses; no vibrato repair; source transient samples may retain melodic attacks.')
    arrangement.setdefault('role_levels',dict(bass=1,lead=1.2,harmony=.5))
    data, report = working_module(notes,args.bpm,args.duration,roles=arrangement['roles'],
                                  percussion=arrangement['percussion'],role_levels=arrangement.get('role_levels'),vibrato=arrangement.get('vibrato'),tick_multiplier=arrangement.get('tick_multiplier',1))
    (args.out/'arranged-eight.mod').write_bytes(data)
    (args.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    # Separate pitched stems use the same MOD player/tuning as the arrangement.
    for role in ('bass','lead','harmony'):
        subset = [note for note,r in zip(notes,arrangement['roles']) if r==role]
        effects = [v for v,r in zip(arrangement.get('vibrato',[None]*len(notes)),arrangement['roles']) if r==role]
        stem, _ = working_module(subset,args.bpm,args.duration,roles=[role]*len(subset),role_levels=arrangement.get('role_levels'),vibrato=effects,tick_multiplier=arrangement.get('tick_multiplier',1))
        (args.out/(role+'.mod')).write_bytes(stem)
    drum, _ = working_module([],args.bpm,args.duration,roles=[],percussion=arrangement['percussion'],role_levels=arrangement.get('role_levels'),tick_multiplier=arrangement.get('tick_multiplier',1))
    (args.out/'percussion.mod').write_bytes(drum)
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
