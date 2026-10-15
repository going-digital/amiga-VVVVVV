#!/usr/bin/env python3
"""Check the isolated station-terminal fixture on a stock PAL A500."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
from run_tower_probe import ROOT, EMU
from run_copperline import audio_peak
from test_map_draw import arrays

FIELDS = ('magic version status frames ticks max_work missed error chip_bytes '
          'opens closes touch_cues read_cues audio_starts audio_completed clipped '
          'visible bars phase buttons enemy_x0 enemy_x1 enemy_y0 enemy_y1 '
          'ui_bitmap list sprite_dma samples period sample_bytes').split()


def diagnostics(data):
    for match in re.finditer(b'V6TN\x00\x00\x00\x01', data):
        values = struct.unpack_from('>30I', data, match.start())
        if values[2] in (1, 2):
            return dict(zip(FIELDS, values))
    raise AssertionError('No live terminal diagnostics')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/amiga-terminal-native')
    p.add_argument('--run', action='store_true')
    a = p.parse_args()
    build = a.build.resolve()
    cfg = build/'terminal.toml'
    cfg.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
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
path = {json.dumps(str(build/'terminal.adf'))}
write_protected = true
''')
    if a.run:
        subprocess.run([EMU, '--config', str(cfg)], check=True)
        return
    controls = ['--key-after', '20', '0x44', '500']
    results = {}
    for name, end, extra in [('reading', 23, []),
                             ('closed', 28, ['--key-after', '25', '0x40', '500']),
                             ('exit', 30, ['--key-after', '25', '0x40', '500',
                                           '--click-after', '29', 'left', '500'])]:
        dump = build/f'terminal-{name}.bin'
        env = dict(os.environ, COPPERLINE_DBG_AFTER=str(end),
                   COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
        with (build/f'terminal-{name}.log').open('w') as log:
            subprocess.run([EMU, '--config', str(cfg), '--noaudio', *controls, *extra,
                            '--screenshot-after', str(end+.02),
                            str(build/f'terminal-{name}.png')], env=env,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        d = diagnostics(dump.read_bytes())
        assert d['status'] == (2 if name == 'exit' else 1) and d['error'] == d['missed'] == 0, d
        assert d['max_work'] <= 280, d
        assert d['opens'] == d['touch_cues'] == d['read_cues'] == 1, d
        assert d['audio_starts'] == d['audio_completed'] == 2, d
        assert d['clipped'] > 0, d
        assert (d['visible'], d['bars'], d['closes']) == ((1, 361, 0) if name == 'reading' else (0, 0, 1)), d
        results[name] = d
    # Repeat the reading capture with Chip RAM and float PCM output. Compare
    # actual DMA data, independently of the fixture's diagnostic counters.
    dump = build/'terminal-chip.bin'
    wav = build/'terminal.wav'
    env = dict(os.environ, COPPERLINE_DBG_AFTER='23',
               COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
    with (build/'terminal-chip.log').open('w') as log:
        subprocess.run([EMU, '--config', str(cfg), '--noaudio', *controls,
                        '--audio-wav', str(wav), '--screenshot-after', '23.02',
                        str(build/'terminal-chip.png')], env=env,
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    data = dump.read_bytes()
    d = results['reading']
    header = build/'terminal_fixture_assets.h'
    expected = bytes(arrays(header, 'fixture_read'))
    cover = bytes(arrays(header, 'fixture_cover'))
    for plane in range(3):
        start = plane*9600+16*40
        end = plane*9600+224*40
        assert data[d['ui_bitmap']+start:d['ui_bitmap']+end] == expected[start:end]
    covered = uncovered = 0
    for channel in range(8):
        words = struct.unpack_from('>68H', data, d['sprite_dma']+channel*136)
        start = (words[0] >> 8) | ((words[1] & 4) << 6)
        stop = (words[1] >> 8) | ((words[1] & 2) << 7)
        x = (words[0] & 255)*2+(words[1] & 1)-128
        for y in range(start, stop):
            bits = words[2+2*(y-start)] | words[3+2*(y-start)]
            for k in range(16):
                px, py = x+k, y-52
                if 0 <= px < 320 and 0 <= py < 240:
                    if cover[py*40+px//8] & (128 >> (px & 7)):
                        assert not bits & (32768 >> k)
                        covered += 1
                    elif bits & (32768 >> k):
                        uncovered += 1
    assert covered > 0 and uncovered > 0, (covered, uncovered)
    peak = audio_peak(wav, 20, 22)
    assert peak > .01, peak
    results['chip_check'] = dict(covered_pixels=covered, visible_sprite_pixels=uncovered,
                                 read_audio_peak=peak, bitmap_bytes=3*208*40)
    (build/'terminal-native-results.json').write_text(json.dumps(results, indent=2)+'\n')
    print('PASS native terminal: Enter/read/advance/close, sprite occlusion, two Paula cues;',
          max(results[n]['max_work'] for n in ('reading', 'closed', 'exit')),
          'work lines; no missed fields; bitmap/DMA/PCM and OS return checked')


if __name__ == '__main__':
    main()
