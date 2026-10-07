#!/usr/bin/env python3
"""Verify moving Building Apport activation, animation and inactive DMA banks."""
import ctypes as C
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from test_teleporter_capture import EMU,ROOT
from run_tower_probe import diagnostics
BUILD=ROOT/'build/amiga-building-route'
def main():
    global BUILD
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=BUILD)
    parser.add_argument('--interactive',action='store_true')
    args=parser.parse_args();BUILD=args.build
    BUILD.mkdir(parents=True,exist_ok=True)
    config=BUILD/'tower.toml';config.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
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
path = {json.dumps(str(BUILD/'tower.adf'))}
write_protected = true
''')
    if args.interactive:
        print('Building Apport route: keyboard joystick; fire flips; left mouse exits.')
        subprocess.run([EMU,'--config',str(config),'--noaudio','--joystick','keyboard'],check=True)
        return
    dump=BUILD/'live.bin';png=BUILD/'live.png' 
    dump.unlink(missing_ok=True);png.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='39',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (BUILD/'capture.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio','--screenshot-after','40',str(png)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump)
    assert not display['error'] and not display['missed'] and display['max_work_lines']<=250,display
    assert display['camera']==0
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
    data=dump.read_bytes();offset=data.index(b'V6BR\0\0\0\1')
    count=struct.unpack_from('>I',data,offset+8)[0];assert count==128,count
    records=[struct.unpack_from('>12i',data,offset+12+i*48) for i in range(count)]
    from test_building_route import fixture,buttons
    from test_tower_route import libraries
    from test_teleporter_animation import Animation,libraries as animations
    core,_=libraries();anim,_=animations();r,session,world,tele,keep=fixture(core)
    animation=Animation();seed=1;transitions=[];activations=[]
    for tick,record in enumerate(records):
        previous=r.index
        assert core.v6_tower_route_step(C.byref(r),buttons(tick))
        if previous!=r.index:
            transitions.append((tick+1,r.index))
            if r.index==4:animation=Animation(1,0,0)
        if r.index==4:
            seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
            anim.v6_teleporter_animate(C.byref(animation),tele.tile,0,(seed>>16)%6)
        if r.tele_events:activations.append((tick+1,r.tele_events))
        expected=(r.index,session.player.x,session.player.y,tele.tile,tele.state,r.tele_events,
            animation.frame,world.save.x,world.save.y,world.save.room_x,world.save.room_y,r.tele_region.active)
        assert record==expected,(tick+1,record,expected)
    assert transitions==[(7,4)] and activations==[(41,3)]
    assert (world.save.x,world.save.y,world.save.id)==(156,92,0)
    report=dict(display=display,trace_fields=count*12,transitions=transitions,activation_ticks=activations,
        scope='Normal-input Seeing Red to Building Apport route and deferred teleporter save; in-memory checkpoint only; frozen tints; travel, disk saves and crew sharing pending')
    (BUILD/'live-capture.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS Building route:',json.dumps(report))
if __name__=='__main__':main()
