#!/usr/bin/env python3
"""Experimental mixed-audio note recognition and constrained MOD sketch.

Optional dependencies: basic-pitch (ONNX), librosa, numpy. Assets stay private.
This approximates pitches with looping synthetic waves; it does not recover
original instruments, percussion, tracker effects or an original score.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from audit_music import audit


def cell(sample=0, period=0, effect=0, value=0):
    return bytes(((sample & 16) | (period >> 8), period & 255,
                  (sample & 15) << 4 | effect, value))


def module(notes, bpm, duration, reduced=False):
    if not 32 <= bpm <= 255 or not 0 < duration <= 120:
        raise ValueError('BPM must be 32..255; duration must be 0..120 seconds')
    step = 2.5 * 3 / bpm  # speed 3: eight rows per quarter note
    rows = math.ceil(duration / step)
    patterns = math.ceil(rows / 64)
    data = bytearray(patterns * 1024)
    channels = [2, 3] if reduced else [0, 1, 2, 3]
    previous = [None] * 4
    allocated = 0
    dropped = 0
    # Each row independently keeps the lowest bass and highest melody, then
    # strongest inner notes. This intentionally exposes chord/voice churn.
    for row in range(rows):
        t = row * step
        active = sorted([n for n in notes if n[0] <= t < n[1]], key=lambda n: n[2])
        unique = {int(n[2]): n for n in active}
        active = list(unique.values())
        chosen = []
        if active:
            chosen.append(active.pop(0))
        if active:
            chosen.append(active.pop(-1))
        chosen.extend(sorted(active, key=lambda n: -n[3])[:len(channels)-2])
        dropped += max(0, len(unique) - len(chosen))
        for i, ch in enumerate(channels):
            n = chosen[i] if i < len(chosen) else None
            key = (n[2], n[0]) if n else None
            at = row * 16 + ch * 4
            if key != previous[ch]:
                if n:
                    # Bass loop has 64 samples/cycle; other voices have 32.
                    cycle = 64 if i == 0 else 32
                    pitch = int(n[2])
                    period = round(3546895 / (440 * 2 ** ((pitch-69)/12) * cycle))
                    while period > 856:
                        period = round(period / 2)
                    while period < 113:
                        period *= 2
                    volume = max(8, min(48, round(float(n[3]) * 48)))
                    data[at:at+4] = cell(1 if i == 0 else 2, period, 12, volume)
                    allocated += 1
                else:
                    data[at:at+4] = cell(effect=12, value=0)
            previous[ch] = key
    # Timing effects occupy only owned channels. Header volumes supply row 0.
    for ch, value in zip(channels, (3, bpm)):
        at = ch * 4
        data[at+2] = (data[at+2] & 240) | 15
        data[at+3] = value
    at = (rows-1)*16 + channels[-1]*4
    data[at+2] = (data[at+2] & 240) | 11
    data[at+3] = 0  # loop exactly at the excerpt boundary, without padding
    header = bytearray(1084)
    header[:20] = b'Audio pitch sketch'.ljust(20, b'\0')
    samples = []
    for i, cycle in enumerate((64, 32)):
        wave = bytes(round(90 * (2/math.pi) * math.asin(math.sin(2*math.pi*j/cycle))) & 255
                     for j in range(cycle))
        samples.append(wave)
        at = 20 + i*30
        header[at:at+22] = ('Bass triangle' if i == 0 else 'Voice triangle').encode().ljust(22, b'\0')
        struct.pack_into('>HBBHH', header, at+22, cycle//2, 0, 40, 0, cycle//2)
    header[950] = patterns
    header[952:952+patterns] = bytes(range(patterns))
    header[1080:1084] = b'M.K.'
    result = bytes(header + data + b''.join(samples))
    report = audit(result, 3 if reduced else 0)
    report.update(rows=rows, duration=rows*step, bpm=bpm, note_starts=allocated,
                  omitted_note_rows=dropped, reduced=reduced)
    return result, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--duration', type=float, default=24)
    p.add_argument('--bpm', type=int, help='Override uncertain automatic tempo estimate')
    args = p.parse_args()
    import librosa
    import numpy as np
    from basic_pitch.inference import predict
    y, sr = librosa.load(args.audio, sr=22050, duration=args.duration)
    if not len(y):
        p.error('empty audio')
    duration = min(args.duration, len(y)/sr)
    args.out.mkdir(parents=True, exist_ok=True)
    # Predict the bounded excerpt, never accidentally the whole source file.
    import soundfile as sf
    excerpt = args.out/'excerpt.wav'
    sf.write(excerpt, y, sr)
    _, midi, events = predict(excerpt)
    notes = [[float(n[0]), float(n[1]), int(n[2]), float(n[3])] for n in events]
    (args.out/'notes.json').write_text(json.dumps(notes, indent=2)+'\n')
    midi.write(str(args.out/'detected.mid'))
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = args.bpm or round(float(np.asarray(tempo).reshape(-1)[0]))
    report = dict(source_sha256=hashlib.sha256(args.audio.read_bytes()).hexdigest(),
                  detected_notes=len(notes), estimated_bpm=float(np.asarray(tempo).reshape(-1)[0]),
                  limitations='Unreviewed mixed-audio pitch sketch; synthetic timbres; no percussion; octave folding; row-wise voice selection; not shipping music.', modules={})
    for name, reduced in [('four-channel', False), ('two-channel', True)]:
        data, entry = module(notes, bpm, duration, reduced)
        (args.out/(name+'.mod')).write_bytes(data)
        report['modules'][name] = entry
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
