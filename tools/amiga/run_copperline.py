#!/usr/bin/env python3
"""Launch the minimum A500 profile, or capture deterministic diagnostic runs."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def read_diagnostics(path):
    ram = path.read_bytes()
    # Require a running/stopped record, not a coincidental executable byte string.
    for offset in range(0, len(ram) - 96, 2):
        if ram[offset:offset+8] == b'V6DG\0\0\0\2':
            values = struct.unpack_from('>14I6i4I', ram, offset)
            if values[13] not in (1, 2):
                continue
            names = ('magic', 'version', 'frames', 'ticks', 'renders', 'max_work_lines',
                     'missed_frames', 'flips', 'scroll_mode', 'chip_free', 'other_free',
                     'chip_allocated', 'error', 'status', 'player_x', 'player_y',
                     'player_vx', 'player_vy', 'gravity', 'death_timer',
                     'deaths', 'respawns', 'checkpoint', 'exits')
            return dict(zip(names, values))
    raise RuntimeError(f'No live prototype diagnostics in {path}')


def audio_peak(path):
    blob = path.read_bytes()
    assert blob[:4] == b'RIFF' and blob[8:12] == b'WAVE'
    pos, fmt, audio = 12, None, None
    while pos + 8 <= len(blob):
        tag, length = struct.unpack_from('<4sI', blob, pos)
        value = blob[pos+8:pos+8+length]
        if tag == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', value)
            if fmt[0] == 0xfffe:  # WAVE_FORMAT_EXTENSIBLE subtype GUID
                assert len(value) >= 40
                fmt = (struct.unpack_from('<I', value, 24)[0],) + fmt[1:]
        if tag == b'data': audio = value
        pos += 8 + length + (length & 1)
    assert fmt and audio and fmt[0] == 3 and fmt[5] == 32, 'Expected float32 PCM capture'
    # Check the flip cue at 13s, rather than counting floppy/boot audio as success.
    start = int(12.9 * fmt[2]) * fmt[4]
    end = int(13.5 * fmt[2]) * fmt[4]
    return max(abs(v[0]) for v in struct.iter_unpack('<f', audio[start:end]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path.home() / 'amiga/KICK13.ROM')
    parser.add_argument('--emulator', default='/Applications/Copperline.app/Contents/MacOS/copperline')
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    build = ROOT / 'build/amiga'
    config = build / 'copperline.toml'
    config.write_text(f'''rom = {json.dumps(str(args.rom.resolve()))}
[machine]
model = "A500"
[cpu]
model = "68000"
[memory]
chip = "512K"
slow = "512K"
fast = "0"
[chipset]
revision = "OCS"
video = "PAL"
[emulation]
pacing_budget = "cycles"
[floppy.df0]
path = {json.dumps(str(build / 'prototype.adf'))}
write_protected = true
''')
    command = [args.emulator, '--config', str(config)]
    if args.capture:
        env = dict(os.environ, RUST_LOG='info', COPPERLINE_DBG_AFTER='16.5',
                   COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{build / "slow.bin"}')
        command += ['--noaudio',
                    '--joy-after', '13', 'fire', '100',
                    '--joy-after', '15.5', 'right', '300',
                    '--joy-after', '16', 'left', '300',
                    '--save-state-after', '16', str(build / 'prototype.clstate'),
                    '--audio-wav', str(build / 'prototype.wav'),
                    '--screenshot-after', '17', str(build / 'prototype.png')]
        with (build / 'copperline.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env, check=True)
        report = read_diagnostics(build / 'slow.bin')
        assert report['error'] == 0 and report['status'] == 1, report
        assert report['flips'] == 1 and report['checkpoint'] == 1, report
        assert report['deaths'] >= 1 and report['respawns'] >= 1, report
        # Snapshot can land between a tick and completion of its render.
        assert report['ticks'] > 100 and 0 <= report['ticks'] - report['renders'] <= 1, report
        assert report['missed_frames'] == 0 and report['max_work_lines'] < 312, report
        report['max_work_ms'] = round(report['max_work_lines'] * 227 / 3546895 * 1000, 3)
        report['flip_audio_peak'] = audio_peak(build / 'prototype.wav')
        assert report['flip_audio_peak'] > 0.001, report
        # Resume the same binary/state to verify the OS restoration path.
        env['COPPERLINE_DBG_AFTER'] = '18.5'
        env['COPPERLINE_DBG_RAMDUMP'] = f'C00000:80000:{build / "exit-slow.bin"}'
        with (build / 'exit.log').open('w') as log:
            subprocess.run([args.emulator, '--config', str(config), '--noaudio',
                            '--load-state', str(build / 'prototype.clstate'),
                            '--click-after', '17', 'left', '100',
                            '--screenshot-after', '19', str(build / 'exit.png')],
                           stdout=log, stderr=subprocess.STDOUT, env=env, check=True)
        exited = read_diagnostics(build / 'exit-slow.bin')
        assert exited['status'] == 2, exited
        report['exit_restored'] = True
        (build / 'smoke-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        print(f'PASS: render/input/audio/exit smoke test; capture: {build / "prototype.png"}')
    else:
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
