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


def working_module(notes, bpm, duration):
    """Eight-channel editing master: retain held notes on their assigned lane.

    Chord ranks are not instrument identities. This allocator stabilizes lanes
    while preserving detected pitches; musical part separation remains future
    work. The 8CHN file is an editing asset, not LSP/Paula replay input.
    """
    if not 32 <= bpm <= 255 or not 0 < duration <= 120:
        raise ValueError('BPM must be 32..255; duration must be 0..120 seconds')
    step = 7.5 / bpm
    rows = math.ceil(duration / step)
    patterns = math.ceil(rows / 64)
    data = bytearray(patterns * 64 * 8 * 4)
    lanes = [None] * 8
    starts = dropped = 0
    cycles = (16, 32, 64, 128, 256)
    for row in range(rows):
        t = row * step
        active = {i for i, n in enumerate(notes) if n[0] <= t < n[1]}
        assigned = set()
        for ch, i in enumerate(lanes):
            if i is not None and i not in active:
                lanes[ch] = None
                at = row*32 + ch*4
                data[at:at+4] = cell(effect=12)
            elif i is not None:
                assigned.add(i)
        pending = sorted(active-assigned, key=lambda i: (notes[i][2], i))
        # Preserve bass and melody first on overload, then stronger inner notes.
        priority = []
        if pending:
            priority.append(pending.pop(0))
        if pending:
            priority.append(pending.pop())
        priority.extend(sorted(pending, key=lambda i: -notes[i][3]))
        free = [ch for ch, i in enumerate(lanes) if i is None]
        dropped += max(0, len(priority)-len(free))
        for ch, i in zip(free, priority):
            n = notes[i]
            frequency = 440 * 2 ** ((n[2]-69)/12)
            options = [(j, round(3546895/(frequency*cycle)))
                       for j, cycle in enumerate(cycles)]
            valid = [(j, period) for j, period in options if 113 <= period <= 856]
            if not valid:
                raise ValueError('detected pitch outside sample/period range')
            j, period = min(valid, key=lambda item: abs(
                3546895/(item[1]*cycles[item[0]])-frequency))
            at = row*32 + ch*4
            data[at:at+4] = cell(j+1, period, 12,
                                max(8, min(48, round(n[3]*48))))
            lanes[ch] = i
            starts += 1
    for ch, value in enumerate((3, bpm)):
        data[ch*4+2] = (data[ch*4+2] & 240) | 15
        data[ch*4+3] = value
    at = (rows-1)*32 + 7*4
    data[at+2] = (data[at+2] & 240) | 11
    data[at+3] = 0
    header = bytearray(1084)
    header[:20] = b'Eight voice master'.ljust(20, b'\0')
    samples = []
    for i, cycle in enumerate(cycles):
        wave = bytes(round(90*2/math.pi*math.asin(math.sin(2*math.pi*j/cycle))) & 255
                     for j in range(cycle))
        samples.append(wave)
        at = 20+i*30
        header[at:at+22] = ('Triangle '+str(cycle)).encode().ljust(22, b'\0')
        struct.pack_into('>HBBHH', header, at+22, cycle//2, 0, 40, 0, cycle//2)
    header[950] = patterns
    header[952:952+patterns] = bytes(range(patterns))
    header[1080:1084] = b'8CHN'
    result = bytes(header+data+b''.join(samples))
    return result, dict(channels=8, rows=rows, duration=rows*step,
                        bpm=bpm, note_starts=starts, omitted_note_rows=dropped,
                        sample_bytes=sum(cycles), file_bytes=len(result),
                        sha256=hashlib.sha256(result).hexdigest(),
                        scope='Editing master only; stable event lanes, no octave folding; not hardware replay input')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--duration', type=float, default=24)
    p.add_argument('--legacy-two-channel', action='store_true',
                   help='Also export the rejected two-voice baseline for comparison')
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
                  limitations='Unreviewed mixed-audio pitch sketch; synthetic timbres; no percussion; eight-channel master uses stable lanes without octave folding; legacy reductions use row-wise ranks and octave folding; not shipping music.', modules={})
    master, entry = working_module(notes, bpm, duration)
    (args.out/'eight-channel.mod').write_bytes(master)
    report['modules']['eight-channel'] = entry
    variants = [('four-channel', False)]
    if args.legacy_two_channel:
        variants.append(('two-channel', True))
    for name, reduced in variants:
        data, entry = module(notes, bpm, duration, reduced)
        (args.out/(name+'.mod')).write_bytes(data)
        report['modules'][name] = entry
    (args.out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
