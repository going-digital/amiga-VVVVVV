#!/usr/bin/env python3
"""Hold the Prize pickup caption; verify frozen gameplay and busy save guard."""
import argparse
import json
import os
import struct
import subprocess
from pathlib import Path
from run_interactive_save import config, KEYS
from run_tower_probe import diagnostics, EMU
from save_disk import create_save_disk

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    build=parser.parse_args().build.resolve()
    disk=build/'pickup-save.adf';disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);boot=(build/'tower.adf').read_bytes();before=disk.read_bytes()
    dump=build/'pickup.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'pickup.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        '--screenshot-after','91',str(build/'pickup.png')],
                       env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump);data=dump.read_bytes()
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280,display
    at=data.index(b'V6PS\0\0\0\1');pickup=struct.unpack_from('>12I',data,at+8)
    assert pickup[0]==pickup[2]==1 and pickup[1]>20 and pickup[3]==0,pickup
    assert pickup[4]==15 and pickup[8:]==(0,1002,1,152),pickup
    assert display['logic_ticks']==152,display
    at=data.index(b'V6PB\0\0\0\1')
    presentation=struct.unpack_from('>8I',data,at+12)
    assert presentation==(361,361,76,76,32,32,1,17),presentation
    at=data.index(b'V6PA\0\0\0\1')
    audio=struct.unpack_from('>5I',data,at+8)
    assert audio==(2,1,0,1,0),audio
    at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    assert ui['actions']==1 and ui['busy']==1 and ui['saves']==ui['loads']==ui['errors']==0,ui
    assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
    assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
    report=dict(display=display,pickup=pickup,ui=ui,
                scope='Held action through pickup reveal; world and Prize actors frozen, save rejected as busy, disks unchanged. Source-positioned bordered textboxes, wordy count and fully extended bars; textbox fading remains outstanding. Source Prize effects complete while gameplay stays paused.')
    (build/'pickup-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Prize pickup:',json.dumps(report))

if __name__=='__main__':main()
