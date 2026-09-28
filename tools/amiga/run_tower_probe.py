#!/usr/bin/env python3
"""Capture the standalone tower on Copperline's PAL A500 profile."""
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build/amiga-tower'
EMU = '/Applications/Copperline.app/Contents/MacOS/copperline'


def diagnostics(path):
    data = path.read_bytes()
    for offset in range(0, len(data)-48+1, 2):
        if data[offset:offset+8] == b'V6TP\0\0\0\2':
            values = struct.unpack_from('>12I', data, offset)
            if values[2] in (1, 2):
                return dict(zip(('magic', 'version', 'status', 'frames', 'camera',
                                 'max_work_lines', 'missed', 'error', 'chip_bytes', 'forward_wraps',
                                 'reverse_wraps', 'max_rows'), values))
    raise RuntimeError('No live tower diagnostics')


def main():
    config = BUILD / 'tower.toml'
    config.write_text(f'''rom = {json.dumps(str(Path.home() / 'amiga/KICK13.ROM'))}
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
path = {json.dumps(str(BUILD / 'tower.adf'))}
write_protected = true
''')
    env = dict(os.environ, COPPERLINE_DBG_AFTER='41',
               COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{BUILD / "slow.bin"}')
    with (BUILD / 'capture.log').open('w') as log:
        subprocess.run([EMU, '--config', str(config), '--noaudio',
                        '--save-state-after', '40', str(BUILD / 'tower.clstate'),
                        '--screenshot-after', '42', str(BUILD / 'tower.png')],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    report = diagnostics(BUILD / 'slow.bin')
    assert report['status'] == 1 and report['error'] == 0, report
    assert report['frames'] > 256 and report['missed'] == 0, report
    assert 0 < report['max_work_lines'] < 312, report
    assert report['forward_wraps'] >= 1 and report['reverse_wraps'] >= 1, report
    assert report['max_rows'] <= 1, report
    env.update(COPPERLINE_DBG_AFTER='43',
               COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{BUILD / "exit.bin"}')
    with (BUILD / 'exit.log').open('w') as log:
        subprocess.run([EMU, '--config', str(config), '--noaudio',
                        '--load-state', str(BUILD / 'tower.clstate'),
                        '--click-after', '41', 'left', '100',
                        '--screenshot-after', '44', str(BUILD / 'exit.png')],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    stopped = diagnostics(BUILD / 'exit.bin')
    assert stopped['status'] == 2 and stopped['error'] == 0, stopped
    report['restored'] = True
    report['scope'] = 'Native forward/reverse source-map seam and exit smoke test; screenshot not pixel-compared; bounded 5344..5856 camera route'
    (BUILD / 'capture.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
