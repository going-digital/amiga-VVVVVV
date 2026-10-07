#!/usr/bin/env python3
"""Interactive bounded save/load slice with a retained writable DF1 disk."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from run_tower_probe import ROOT,EMU,diagnostics
from save_disk import create_save_disk,read_record
DEFAULT=ROOT/'build/amiga-tower-interactive-save'
KEYS='actions saves loads errors busy pauses resumes last_action last_result before_hash after_hash frames_before frames_after ticks_before ticks_after loaded_x loaded_y phase'.split()
def config(build,data_disk):
    path=build/'interactive-save.toml'
    path.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
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
path = {json.dumps(str(build/'tower.adf'))}
write_protected = true
[floppy.df1]
path = {json.dumps(str(data_disk))}
write_protected = false
''')
    return path
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=DEFAULT)
    parser.add_argument('--capture',action='store_true')
    parser.add_argument('--physical',action='store_true',help='Use real emulated mouse/joystick controls rather than replay injection')
    args=parser.parse_args();build=args.build.resolve()
    disk=build/('capture-save-disk.adf' if args.capture else 'save-disk.adf')
    if args.capture:disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);before=(build/'tower.adf').read_bytes()
    if not args.capture:
        print('Right mouse: save; fire + right mouse: load; left mouse: exit. Saves stay on',disk)
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--joystick','keyboard'],check=True);return
    dump=build/'ui-save.bin';dump.unlink(missing_ok=True)
    end=42 if args.physical else 41
    env=dict(os.environ,COPPERLINE_DBG_AFTER=str(end),COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    inputs=['--click-after','28','right','600','--joy-after','40','fire','600','--click-after','40','right','600'] if args.physical else []
    with (build/'ui-save.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,
            '--screenshot-after',str(end+1),str(build/'ui-save.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();offset=data.index(b'V6UI\0\0\0\1')
    ui=dict(zip(KEYS,struct.unpack_from('>18I',data,offset+8)));display=diagnostics(dump)
    offset=data.index(b'V6IT\0\0\0\1');count=struct.unpack_from('>I',data,offset+8)[0]
    events=list(struct.iter_unpack('>10I',data[offset+16:offset+16+count*40]))
    assert ui['last_result']==0 and ui['loaded_x']==140 and ui['loaded_y']==1822,ui
    assert ui['saves']==ui['loads']==1 and ui['pauses']==ui['resumes'],ui
    assert display['missed']==0 and display['max_work_lines']<=250 and display['chip_bytes']==111510,display
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968,display
    assert (build/'tower.adf').read_bytes()==before  # boot disk remains read-only
    for action,result,before_hash,after_hash,fb,fa,tb,ta,x,y in events:
        assert tb==ta and fa-fb<=4,(action,result,fb,fa,tb,ta)
        if action==1 or result:assert before_hash==after_hash,(action,result,before_hash,after_hash)
    if args.physical:
        assert ui['actions']==2 and ui['errors']==ui['busy']==0 and display['status']==1,ui
        saved_record=read_record(disk)
        # Verify committed disk contents with a fresh boot, independently of
        # the filesystem cache held in the first emulator session.
        env.update(COPPERLINE_DBG_AFTER='37',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{build/"ui-exit.bin"}')
        with (build/'ui-exit.log').open('w') as log:
            subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                '--joy-after','28','fire','600','--click-after','28','right','600',
                '--click-after','34','left','100','--screenshot-after','38',str(build/'ui-exit.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        cold_data=(build/'ui-exit.bin').read_bytes();cold_offset=cold_data.index(b'V6UI\0\0\0\1')
        cold_ui=dict(zip(KEYS,struct.unpack_from('>18I',cold_data,cold_offset+8)))
        cold_display=diagnostics(build/'ui-exit.bin')
        assert cold_display['status']==2 and cold_display['error']==0 and cold_display['missed']==0 and cold_display['max_work_lines']<=250,cold_display
        assert cold_ui['actions']==cold_ui['loads']==1 and cold_ui['saves']==cold_ui['errors']==0,cold_ui
        assert cold_ui['loaded_x']==140 and cold_ui['loaded_y']==1822 and cold_ui['last_result']==0,cold_ui
        assert read_record(disk)==saved_record
    else:
        assert ui['actions']==4 and ui['errors']==ui['busy']==1 and ui['pauses']==3 and display['status']==2,ui
        assert [(e[0],e[1]) for e in events]==[(2,3),(1,5),(1,0),(2,0)],events
        from tower_route_trace import verify
        verify(display,dump,False,True,True,False,prefix_only=True)
    fields=struct.unpack_from('>7iI',read_record(disk),8)
    assert fields==(140,1822,1,1,109,109,505147,7 if not args.physical else 0),fields
    report=dict(ui=ui,display=display,events=events,disk_record_verified=True,restored=True,physical_controls=args.physical)
    if args.physical:report.update(cold_boot_ui=cold_ui,cold_boot_display=cold_display)
    (build/'capture.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
