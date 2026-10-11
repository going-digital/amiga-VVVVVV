#!/usr/bin/env python3
"""PAL A500 Prize fixture; explicit placements, not a normal-input traversal."""
import argparse,ctypes as C,json,os,struct,subprocess
from pathlib import Path
from pack_rooms import ROOT,prize_record
from run_copperline import read_diagnostics

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--live',type=Path)
    args=parser.parse_args();build=args.build.resolve()
    config=build/'prize.toml'
    config.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
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
path = {json.dumps(str(build/'prototype.adf'))}
write_protected = true
''')
    dump=build/'prize.bin';dump.unlink(missing_ok=True)
    boot=(build/'prototype.adf').read_bytes()
    env=dict(os.environ,COPPERLINE_DBG_AFTER='20',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'prize.log').open('w') as log:
        subprocess.run(['/Applications/Copperline.app/Contents/MacOS/copperline','--config',str(config),
            '--noaudio','--screenshot-after','20.5',str(build/'prize.png')],env=env,
            stdout=log,stderr=subprocess.STDOUT,check=True)
    assert (build/'prototype.adf').read_bytes()==boot
    display=read_diagnostics(dump)
    assert display['status']==1 and display['error']==display['missed_frames']==0,display
    assert display['max_work_lines']<250 and display['max_sprite_channels']==4,display
    data=dump.read_bytes();at=data.index(b'V6PR\0\0\0\1')
    count=struct.unpack_from('>I',data,at+8)[0];assert count==160,count
    records=[struct.unpack_from('>16i',data,at+12+i*64) for i in range(count)]
    # Compile a host integration trace from the same six source actors. Timing
    # and entity lifecycle have separate original-source differential tests.
    names=('prize.c','slice.c','platform_gate.c','disappearing.c','trinkets.c',
           'checkpoints.c','platform.c','enemy.c','player.c','terrain.c','blocks.c')
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/name) for name in names],str(ROOT/'tools/amiga/prize_fixture.c'),
        '-o',str(build/'prize_fixture.so')],check=True)
    fixture=C.CDLL(str(build/'prize_fixture.so')).prize_fixture
    fixture.argtypes=[C.POINTER(C.c_uint16),C.POINTER(C.c_int32),C.c_uint]
    tiles=(C.c_uint16*1200)(*struct.unpack('>1200H',prize_record()[1]));trace=(C.c_int32*(count*16))()
    fixture(tiles,trace,count)
    for i,row in enumerate(records):
        assert row==tuple(trace[i*16:(i+1)*16]),(i+1,row,tuple(trace[i*16:(i+1)*16]))
    assert records[13][6]==3 and records[13][3]==88 and records[14][3]==92
    assert any(row[13]==59 for row in records)
    assert any(row[14]>=1 and row[6:9]==(0,0,0) for row in records)
    assert records[90][10:13]==(0,1,64) and all(row[10:13]==(0,1,64) for row in records[90:])
    assert records[-1][14]>=2 and display['exits']==0,display
    report=dict(display=display,trace_ticks=count,fields_compared=count*16,
        source=prize_record()[0],scope='Isolated normal-mode six-actor scene; test-only platform/pickup placements, two deaths, checkpoint respawns and terrain patch; no route, disk save or full pickup screen')
    if args.live:
        live=args.live.resolve();live_config=build/'prize-live.toml'
        live_config.write_text(config.read_text().replace(str(build/'prototype.adf'),str(live/'prototype.adf')))
        live_dump=build/'prize-live.bin';live_dump.unlink(missing_ok=True)
        live_boot=(live/'prototype.adf').read_bytes()
        env=dict(os.environ,COPPERLINE_DBG_AFTER='24',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{live_dump}')
        with (build/'prize-live.log').open('w') as log:
            subprocess.run(['/Applications/Copperline.app/Contents/MacOS/copperline','--config',str(live_config),
                '--noaudio','--joy-after','14','right','900','--click-after','17','right','200',
                '--click-after','22','left','200','--screenshot-after','25',str(build/'prize-live.png')],
                env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        live_display=read_diagnostics(live_dump)
        assert live_display['status']==2 and live_display['error']==live_display['missed_frames']==0,live_display
        assert live_display['max_work_lines']<250 and live_display['max_sprite_channels']==4,live_display
        assert live_display['deaths']>=1 and live_display['respawns']>=1,live_display
        assert live_display['enemy_y']==1 and live_display['enemy_x']!=88 and live_display['enemy_hits']==1,live_display
        assert live_display['exits']==0 and (live/'prototype.adf').read_bytes()==live_boot,live_display
        report['live_display']=live_display
        report['live_scope']='Physical joystick-right from north entrance releases waiting platform; right-button restart adds solid tile; left-button restores OS. No pickup or complete room traversal asserted'
    (build/'prize-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Prize:',json.dumps(report))
if __name__=='__main__':main()
