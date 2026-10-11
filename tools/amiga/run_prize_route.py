#!/usr/bin/env python3
"""Native Prize route fixture; checkpoint/platform placements are test-only."""
import argparse,json,os,struct,subprocess
from run_tower_probe import diagnostics,EMU
from pathlib import Path

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve()
    from run_interactive_save import config
    from save_disk import create_save_disk
    disk=build/'prize-route-save.adf';disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);boot=(build/'tower.adf').read_bytes();before=disk.read_bytes()
    dump=build/'prize-route.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='60',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'prize-route.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        '--screenshot-after','61',str(build/'prize-route.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert (build/'tower.adf').read_bytes()==boot and disk.read_bytes()==before
    display=diagnostics(dump);data=dump.read_bytes()
    at=data.index(b'V6PR\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
    rows=[struct.unpack_from('>24i',data,at+12+i*96) for i in range(count)]
    (build/'prize-route-report.json').write_text(json.dumps(dict(display=display,records=rows),indent=2)+'\n')
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280,display
    assert count==224,count
    assert any(row[0]==7 for row in rows[:20]) and any(row[0]==8 for row in rows[20:30])
    assert all(row[11]==0 for row in rows if row[0]==8)
    assert any(row[0]==8 and row[14]==1 and row[13]>88 for row in rows)
    assert any(row[16]==1 and row[19]==59 for row in rows)
    matching=[row for row in rows if row[5]==443490]
    assert matching and all(row[6:11]==(236,134,1,111,107) for row in matching)
    assert rows[174][15:18]==(1,1,1),rows[174]
    assert any(row[0]==7 for row in rows[175:190])
    assert any(row[0]==8 for row in rows[190:]) and all(row[17]==1 and row[18]==0 and row[19]==59
                                      for row in rows[190:] if row[0]==8)
    assert rows[-1][23]>=2,rows[-1]
    assert all(row[13]==rows[60][13] and row[20]==4 for row in rows[60:90])
    # A V3-supported Shenanigan checkpoint cannot silently discard trinket 6.
    assert any(row[5]==442490 and row[17]==1 for row in rows[185:190])
    from run_interactive_save import KEYS
    at=data.index(b'V6UI\0\0\0\1')
    ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    assert ui['errors']==1 and ui['saves']==ui['loads']==0 and ui['last_result']==1,ui
    assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
    at=data.index(b'V6WG\0\0\0\1');sprite_channels=struct.unpack_from('>I',data,at+8+12*4)[0]
    assert sprite_channels==5,sprite_channels
    at=data.index(b'V6PF\0\0\0\1')
    profile=dict(zip(('magic','version','max_logic','max_render','peak_logic','peak_render','peak_tick','peak_rows'),
                     struct.unpack_from('>8I',data,at)))
    # Quit by physical mouse after the same replay; teardown must restore the OS.
    quit_dump=build/'prize-route-quit.bin';quit_dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='65',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{quit_dump}')
    with (build/'prize-route-quit.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        '--click-after','60','left','200','--screenshot-after','66',str(build/'prize-route-quit.png')],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    quit_display=diagnostics(quit_dump)
    assert quit_display['status']==2 and quit_display['error']==quit_display['missed']==0,quit_display
    assert (build/'tower.adf').read_bytes()==boot and disk.read_bytes()==before
    report=dict(display=display,profile=profile,quit_display=quit_display,ui=ui,sprite_channels=sprite_channels,records=rows,
                scope='Connected route with test-only placements; RAM collection/terrain retention and physical quit. No disk persistence, pickup UI or complete normal-input traversal.')
    (build/'prize-route-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Prize route:',json.dumps(dict(display=display,trace_ticks=count,
        scope='Source boundary handling with test-only checkpoint/gate/pickup placements; death terrain patch and collection retained across reentry. No V4 disk save, pickup screen or full normal-input traversal.')))
if __name__=='__main__':main()
