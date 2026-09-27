#!/usr/bin/env python3
"""Compare the source-checked compression session on host and A500."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--emulator',required=True)
    args=parser.parse_args();build=args.build.resolve()
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-DV6_HOST_TEST',
        '-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/f) for f in
          ('player.c','platform.c','enemy.c','blocks.c','terrain.c','slice.c','animation.c')],
        str(ROOT/'tools/amiga/crush_session.c'),str(ROOT/'tools/amiga/crush_target.c'),
        '-o',str(build/'crush_host')],check=True)
    expected=json.loads(subprocess.check_output([str(build/'crush_host')]))
    assert expected['cases']==672 and expected['respawns']==576,expected
    config=build/'copperline.toml'
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
path = {json.dumps(str(build/'crush.adf'))}
write_protected = true
''')
    env=dict(os.environ,RUST_LOG='info',COPPERLINE_DBG_AFTER='240',
             COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{build/"slow.bin"}')
    for name in ('slow.bin','crush.png','crush-target-report.json'):
        (build/name).unlink(missing_ok=True)
    with (build/'copperline.log').open('w') as log:
        subprocess.run([args.emulator,'--config',str(config),'--noaudio',
            '--screenshot-after','241',str(build/'crush.png')],env=env,
            stdout=log,stderr=subprocess.STDOUT,check=True)
    ram=(build/'slow.bin').read_bytes();records=[]
    for offset in range(0,len(ram)-28+1,2):
        if ram[offset:offset+8]==b'V6CR\0\0\0\1':
            values=struct.unpack_from('>7I',ram,offset)
            records.append(dict(zip(('magic','version','complete','cases','ticks','respawns','digest'),values)))
    assert len(records)==1,records
    actual=records[0]
    report=dict(target='A500 / 68000 / OCS / 512K Chip + 512K slow',
        expected=expected,actual=actual,
        scope='Standalone logic regression; host/68000 state digest across cached and uncached fixtures, including death freeze and respawn. No rendered gameplay or independent desktop lifecycle comparison.')
    (build/'crush-target-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert actual['complete']==1,actual
    for key,value in expected.items():assert actual[key]==value,(key,actual,expected)
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
