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


def working_module(notes, bpm, duration, quantize=True, roles=None, percussion=None, role_levels=None, vibrato=None, tick_multiplier=1):
    """Eight-channel editing master: retain held notes on their assigned lane.

    Held events keep their lanes. Optional roles select distinct timbres and
    preferred channels with spillover; channel 7 is then reserved for supplied
    one-shot percussion. Roles are supplied guesses, not instrument recognition.
    The 8CHN file is an editing asset, not LSP/Paula replay input.
    """
    if not 32 <= bpm <= 255 or not 0 < duration <= 120:
        raise ValueError('BPM must be 32..255; duration must be 0..120 seconds')
    if tick_multiplier not in (1,2) or bpm*tick_multiplier>255:
        raise ValueError('invalid replay tick multiplier/tempo')
    step = 7.5 / bpm
    rows = math.ceil(duration / step)
    patterns = math.ceil(rows / 64)
    original_notes = notes
    if vibrato is not None and (len(vibrato)!=len(notes) or any(
            v is not None and (set(v)!={'speed','depth'} or
                any(not isinstance(v[k],int) or not 1<=v[k]<=15 for k in ('speed','depth')))
            for v in vibrato)):
        raise ValueError('one optional valid vibrato speed/depth per note')
    vibrato = vibrato or [None]*len(notes)
    vibrato_rows=0
    arranged = roles is not None
    if arranged and (len(roles) != len(notes) or any(r not in ('bass','lead','harmony') for r in roles)):
        raise ValueError('one valid role is required per detected note')
    if percussion is not None and not arranged:
        raise ValueError('percussion requires role arrangement')
    percussion = percussion or dict(samples=[], hits=[])
    role_levels = role_levels or dict(bass=1,lead=1.2,harmony=.5)
    if any(not math.isfinite(role_levels[r]) or not 0 <= role_levels[r] <= 2
           for r in ('bass','lead','harmony')):
        raise ValueError('role levels must be finite gains from 0 to 2')
    if len(percussion['samples']) > 3:
        raise ValueError('at most three percussion samples')
    if quantize:
        notes = []
        for start, end, pitch, strength in original_notes:
            first = max(0, math.floor(start/step+.5))
            last = max(first+1, math.floor(end/step+.5))
            notes.append([first*step, last*step, pitch, strength])
    onset_errors = [n[0]-old[0] for n, old in zip(notes, original_notes)]
    data = bytearray(patterns * 64 * 8 * 4)
    lanes = [None] * 8
    starts = dropped = 0
    role_spills = 0
    cycles = (16, 32, 64, 128, 256)
    preferred = dict(bass=[0,1], lead=[2,3], harmony=[4,5,6])
    role_bank = dict(bass=0, lead=5, harmony=10)
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
                if vibrato[i] is not None:
                    at=row*32+ch*4
                    data[at:at+4]=cell(effect=4,value=(vibrato[i]['speed']<<4)|vibrato[i]['depth'])
                    vibrato_rows+=1
        pending = sorted(active-assigned, key=lambda i: (notes[i][2], i))
        # Preserve bass and melody first on overload, then stronger inner notes.
        priority = []
        if pending:
            priority.append(pending.pop(0))
        if pending:
            priority.append(pending.pop())
        priority.extend(sorted(pending, key=lambda i: -notes[i][3]))
        free = [ch for ch, i in enumerate(lanes) if i is None and (not arranged or ch != 7)]
        dropped += max(0, len(priority)-len(free))
        for i in priority[:len(free)]:
            if arranged:
                role = roles[i]
                wanted = [ch for ch in free if ch in preferred[role]]
                ch = wanted[0] if wanted else free[0]
                role_spills += not bool(wanted)
            else:
                ch = free[0]
            free.remove(ch)
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
            sample = j+1+(role_bank[roles[i]] if arranged else 0)
            gain = role_levels[roles[i]] if arranged else 1
            data[at:at+4] = cell(sample, period, 12,
                                max(0 if arranged else 8, min(48, round(n[3]*48*gain))))
            lanes[ch] = i
            starts += 1
    drum_rows = {}
    drum_delays = {}
    drum_boundary_skips = drum_collisions = 0
    tick_timing = percussion.get('timing') == 'ticks'
    for hit in percussion['hits']:
        if tick_timing:
            tick = max(0, math.floor(hit['time']/(step/3)+.5))
            row, delay = divmod(tick,3)
            delay *= tick_multiplier
        else:
            row, delay = max(0, math.floor(hit['time']/step+.5)), 0
        if row >= rows or (tick_timing and row == rows-1):
            # The last percussion cell carries B00; do not overwrite EDx.
            drum_boundary_skips += 1
            continue
        if not 0 <= hit['sample'] < len(percussion['samples']):
            raise ValueError('invalid percussion sample index')
        drum_collisions += row in drum_rows
        if row not in drum_rows or hit['strength'] > drum_rows[row]['strength']:
            drum_rows[row] = hit
            drum_delays[row] = delay
    for row, hit in drum_rows.items():
        at = row*32+7*4
        if tick_timing:
            # Delayed notes use instrument header volume: one MOD cell cannot
            # carry both Cxx volume and EDx delay. Template levels are constant.
            data[at:at+4] = cell(16+hit['sample'],322,14,208+drum_delays[row])
        else:
            data[at:at+4] = cell(16+hit['sample'], 322, 12,
                                max(8, min(48, round(hit['strength']*48))))
    for ch, value in enumerate((3*tick_multiplier, bpm*tick_multiplier)):
        data[ch*4+2] = (data[ch*4+2] & 240) | 15
        data[ch*4+3] = value
    at = (rows-1)*32 + 7*4
    data[at+2] = (data[at+2] & 240) | 11
    data[at+3] = 0
    header = bytearray(1084)
    header[:20] = b'Eight voice master'.ljust(20, b'\0')
    samples = []
    banks = ('bass','lead','harmony') if arranged else ('triangle',)
    for bank, role in enumerate(banks):
        for j, cycle in enumerate(cycles):
            values = []
            for point in range(cycle):
                phase = 2*math.pi*point/cycle
                if role == 'bass':
                    value = math.sin(phase)+.25*math.sin(2*phase)
                elif role == 'lead':
                    # Bright pulse-like wave, softened to seven harmonics.
                    value = sum(math.sin(k*math.pi/4)/k * math.cos(k*phase)
                                for k in range(1,min(8,cycle//2)))
                elif role == 'harmony':
                    value = math.sin(phase)+.2*math.sin(3*phase)+.1*math.sin(5*phase)
                else:
                    value = 2/math.pi*math.asin(math.sin(phase))
                values.append(value)
            peak = max(abs(v) for v in values)
            wave = bytes(round(90*v/peak) & 255 for v in values)
            samples.append(wave)
            at = 20+(bank*5+j)*30
            header[at:at+22] = (role+' '+str(cycle)).encode().ljust(22, b'\0')
            default_volume = min(48, round(40*role_levels[role])) if arranged else 40
            struct.pack_into('>HBBHH', header, at+22, cycle//2, 1, default_volume, 0, cycle//2)
    for i, drum in enumerate(percussion['samples']):
        wave = bytes(drum['pcm'])
        if not wave or len(wave)%2 or len(wave)>131070:
            raise ValueError('percussion sample must have a nonempty even MOD length')
        samples.append(wave)
        at = 20+(15+i)*30
        header[at:at+22] = drum['name'].encode()[:22].ljust(22,b'\0')
        volume = drum.get('volume',40)
        if not 0<=volume<=64:
            raise ValueError('invalid percussion volume')
        struct.pack_into('>HBBHH', header, at+22, len(wave)//2, 0, volume, 0, 1)
    header[950] = patterns
    header[952:952+patterns] = bytes(range(patterns))
    header[1080:1084] = b'8CHN'
    result = bytes(header+data+b''.join(samples))
    return result, dict(channels=8, rows=rows, duration=rows*step,
                        bpm=bpm, replay_bpm=bpm*tick_multiplier, replay_speed=3*tick_multiplier, note_starts=starts, omitted_note_rows=dropped,
                        quantized=quantize, sample_finetune=1, vibrato_rows=vibrato_rows,
                        onset_rms_error_ms=1000*math.sqrt(sum(e*e for e in onset_errors)/max(1,len(onset_errors))),
                        onset_max_error_ms=1000*max([abs(e) for e in onset_errors], default=0),
                        sample_bytes=sum(len(wave) for wave in samples), file_bytes=len(result),
                        role_arrangement=arranged, role_spills=role_spills,
                        role_levels=role_levels if arranged else None,
                        percussion_hits=len(drum_rows), percussion_tick_timing=tick_timing,
                        percussion_row_collisions=drum_collisions,
                        percussion_boundary_skips=drum_boundary_skips,
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
    p.add_argument('--master-bpm', type=int, help='Independent eight-channel timing grid BPM')
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
    master, entry = working_module(notes, args.master_bpm or bpm, duration)
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
