#!/usr/bin/env python3
"""Native Energize foreground, silent arrival entity and moving animation."""
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
from run_tower_probe import ROOT,EMU,diagnostics
from test_tower_route import libraries,RouteRoom,encode
from test_building_route import fixture
from test_teleporter import Teleporter
from test_teleporter_animation import Animation,libraries as animations
from tower_gameplay_data import energize_room

BUILD=ROOT/'build/amiga-energize'
def main():
    config=BUILD/'energize.toml'
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
path = {json.dumps(str(BUILD/'tower.adf'))}
write_protected = true
''')
    dump=BUILD/'energize.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='38',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    before=(BUILD/'tower.adf').read_bytes()
    with (BUILD/'energize.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio','--screenshot-after','39',str(BUILD/'energize.png')],
            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump)
    assert display['status']==1 and not display['error'] and not display['missed'],display
    assert display['max_work_lines']<=250 and display['chip_bytes']==69088,display
    assert display['logic_ticks']==128
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
    data=dump.read_bytes();at=data.index(b'V6BR\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
    assert count==128
    records=[struct.unpack_from('>12i',data,at+12+48*i) for i in range(count)]
    core,_=libraries();anim,_=animations();r,s,w,building,keep=fixture(core)
    desc=energize_room();tiles=(C.c_uint16*1200)(*desc['tiles']);blob=encode(desc['tiles'])
    packed=(C.c_uint8*len(blob)).from_buffer_copy(blob);tele=Teleporter(36,68,0,1,1,0)
    rooms=(RouteRoom*6)()
    for i in range(5):rooms[i]=keep[1][i]
    rooms[5]=RouteRoom(110,105,packed,len(blob),None,0,tiles,C.pointer(tele),0)
    r.rooms=rooms;r.count=6
    assert core.v6_tower_route_load(C.byref(r),111,104,0)
    core.v6_tower_route_teleport.argtypes=[C.c_void_p,C.c_int,C.c_int]
    assert core.v6_tower_route_teleport(C.byref(r),110,105)
    animation=Animation(1,0,0);seed=1
    for tick,record in enumerate(records):
        assert core.v6_tower_route_step(C.byref(r),0)
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        anim.v6_teleporter_animate(C.byref(animation),tele.tile,0,(seed>>16)%6)
        expected=(r.index,s.player.x,s.player.y,tele.tile,tele.state,r.tele_events,animation.frame,
            w.save.x,w.save.y,w.save.room_x,w.save.room_y,r.tele_region.active)
        assert record==expected,(tick+1,record,expected)
    assert all(row[0]==5 and row[3]==6 and row[5]==0 for row in records)
    assert (w.save.x,w.save.y,w.save.room_x,w.save.room_y,w.save.id)==(80,112,110,105,0)
    assert (BUILD/'tower.adf').read_bytes()==before
    report=dict(display=display,trace_fields=count*12,checkpoint=[80,112,110,105,0],
        scope='Native Energize compact foreground and teleporter; frozen tower backdrop; arrival effects and playable menu destination pending')
    (BUILD/'energize-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Energize:',json.dumps(report))
if __name__=='__main__':main()
