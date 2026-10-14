#!/usr/bin/env python3
"""Boot the north ADF directly under Kickstart and bundled AROS, without DF1."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from run_tower_probe import ROOT, EMU, diagnostics


def startup(data):
    # DOS disk buffers can contain unexecuted copies of the diagnostic header.
    entries = []
    at = 0
    while True:
        at = data.find(b'V6ST\0\0\0\1', at)
        if at < 0:
            break
        values = struct.unpack_from('>10I', data, at)
        if values[2]:
            entries.append(values)
        at += 8
    assert len(entries) == 1, entries
    return entries[0]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build', type=Path, default=ROOT/'build/amiga-north')
    p.add_argument('--rom', type=Path, default=Path.home()/'amiga/KICK13.ROM')
    a = p.parse_args()
    b = a.build.resolve()
    reports = {}
    for name, rom, fast in [('kickstart', a.rom.resolve(), '0'),
                            ('aros-stock', None, '0'), ('aros-fast', None, '1M')]:
        cfg = b/(name+'-boot.toml')
        cfg.write_text((f'rom = {json.dumps(str(rom))}\n' if rom else '')+f'''
[machine]
model = "A500"
[cpu]
model = "68000"
[memory]
chip = "512K"
slow = "512K"
fast = "{fast}"
[chipset]
revision = "OCS"
video = "PAL"
[emulation]
pacing_budget = "cycles"
[floppy.df0]
path = {json.dumps(str(b/'tower.adf'))}
write_protected = true
''')
        dump = b/(name+'-boot.bin')
        dump.unlink(missing_ok=True)
        region = '200000:100000' if fast != '0' else 'C00000:80000'
        env = dict(os.environ, COPPERLINE_DBG_AFTER='90',
                   COPPERLINE_DBG_RAMDUMP=f'{region}:{dump}')
        with (b/(name+'-boot.log')).open('w') as log:
            subprocess.run([EMU, '--config', str(cfg), '--floppy-drives', '1',
                            '--noaudio', '--screenshot-after', '91',
                            str(b/(name+'-boot.png'))], env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        values = startup(dump.read_bytes())
        assert values[2] == (10 if name == 'aros-stock' else 3), values
        report = {'startup': values}
        if name != 'aros-stock':
            d = diagnostics(dump)
            assert d['status'] == 1 and d['error'] == d['missed'] == 0, d
            assert d['max_work_lines'] <= 280, d
            report['display'] = d
        reports[name] = report
        print('PASS direct DF0 boot:', name, values, flush=True)
    (b/'standalone-boot-report.json').write_text(json.dumps(reports, indent=2)+'\n')


if __name__ == '__main__':
    main()
