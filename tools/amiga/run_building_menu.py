#!/usr/bin/env python3
"""Real joystick menu open/navigation/confirmation/cancel, with paused-state checks."""
import json
import os
import struct
import subprocess
from run_interactive_save import ROOT,EMU,config,KEYS
from run_tower_probe import diagnostics
from save_disk import create_save_disk
BUILD=ROOT/'build/amiga-building-menu'
def main():
    disk=BUILD/'capture-menu-disk.adf';disk.unlink(missing_ok=True)
    create_save_disk(BUILD/'tower.adf',disk);cfg=config(BUILD,disk)
    boot_before=(BUILD/'tower.adf').read_bytes();disk_before=disk.read_bytes()
    dump=BUILD/'menu.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='34',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    # Movement uses the bounded source route fixture; every menu/save input
    # below reaches the emulated hardware, without menu button injection.
    inputs=['--joy-after','28','down','200','--joy-after','28','fire','200',
        '--joy-after','29','left','200','--joy-after','29.5','right','200',
        '--joy-after','30','fire','500','--joy-after','30.2','down','100',
        '--joy-after','31','down','200','--joy-after','31','fire','200',
        '--joy-after','32','down','200','--joy-after','32','fire','200',
        '--joy-after','33','down','200','--joy-after','33','fire','200',
        '--click-after','33.5','right','200']
    with (BUILD/'menu.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,
            '--screenshot-after','35',str(BUILD/'menu.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();at=data.index(b'V6TM\0\0\0\1')
    menu=dict(zip('opened changed closed travel selected paused_ticks before_hash after_hash initial_flips final_flips'.split(),struct.unpack_from('>10I',data,at+8)))
    at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    display=diagnostics(dump)
    assert menu['opened']==3 and menu['closed']==2 and menu['changed']==2,menu
    assert menu['travel']==menu['selected']==0 and menu['paused_ticks']>60,menu
    assert menu['before_hash']==menu['after_hash'],menu
    assert menu['initial_flips']==menu['final_flips']==1,menu
    assert ui['actions']==ui['busy']==1 and ui['pauses']==ui['resumes']==0,ui
    assert display['status']==1 and display['error']==display['missed']==0 and display['max_work_lines']<=250,display
    assert display['chip_bytes']==92128
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
    assert disk.read_bytes()==disk_before and (BUILD/'tower.adf').read_bytes()==boot_before
    report=dict(menu=menu,ui=ui,display=display,physical_menu_controls=True,disks_unchanged=True)
    (BUILD/'menu-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Building menu:',json.dumps(report))
if __name__=='__main__':main()
