#!/usr/bin/env python3
"""Native Energize foreground, silent arrival entity and moving animation."""
import argparse
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
from test_teleporter_arrival import Arrival

BUILD=ROOT/'build/amiga-energize'
def main():
    global BUILD
    parser=argparse.ArgumentParser();parser.add_argument('--arrival',action='store_true')
    parser.add_argument('--flash',action='store_true')
    args=parser.parse_args()
    if args.flash:args.arrival=True
    if args.arrival:BUILD=ROOT/('build/amiga-energize-arrival-flash' if args.flash else 'build/amiga-energize-arrival')
    ticks=1 if args.flash else 128
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
    assert display['logic_ticks']==ticks
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
    data=dump.read_bytes();at=data.index(b'V6BR\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
    assert count==ticks
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
    arrival=Arrival();arrival_records=[]
    if args.arrival:
        at=data.index(b'V6AR\0\0\0\1');assert struct.unpack_from('>I',data,at+8)[0]==ticks
        arrival_records=[struct.unpack_from('>14i',data,at+12+56*i) for i in range(ticks)]
        core.v6_teleporter_arrival_init(C.byref(arrival));assert core.v6_teleporter_arrival_start(C.byref(arrival))
        s.invisible=1
    PHASE=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p)
    @PHASE
    def phase(route,context):
        return core.v6_teleporter_arrival_tick(C.byref(arrival),C.byref(s.player),C.byref(s.motion),
            C.byref(s, type(s).invisible.offset),C.byref(tele),C.byref(r.tele_region))
    core.v6_tower_route_step_phase.argtypes=[C.c_void_p,C.c_uint,PHASE,C.c_void_p]
    animation=Animation(1,0,0);seed=1
    for tick,record in enumerate(records):
        if args.arrival:
            assert core.v6_tower_route_step_phase(C.byref(r),0 if arrival.control else 8,phase,None)
            expected_arrival=(arrival.state,arrival.delay,arrival.control,arrival.flash,arrival.shake,arrival.events,
                s.invisible,s.player.vx,s.player.vy,s.player.ay,s.player.old_x,s.player.old_y,s.player.dir,s.death_timer)
            assert arrival_records[tick]==expected_arrival,(tick+1,arrival_records[tick],expected_arrival)
            if arrival.flash:arrival.flash-=1
            if arrival.shake:arrival.shake-=1
        else:assert core.v6_tower_route_step(C.byref(r),0)
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        anim.v6_teleporter_animate(C.byref(animation),tele.tile,0,(seed>>16)%6)
        expected=(r.index,s.player.x,s.player.y,tele.tile,tele.state,r.tele_events,animation.frame,
            w.save.x,w.save.y,w.save.room_x,w.save.room_y,r.tele_region.active)
        assert record==expected,(tick+1,record,expected)
    assert all(row[0]==5 and row[5]==0 for row in records)
    if args.arrival:
        assert [(i+1,row[5]) for i,row in enumerate(arrival_records) if row[5]]==([(1,1)] if args.flash else [(1,1),(16,2),(42,4)])
        assert all(row[2]==0 for row in arrival_records[:41]) and all(row[2]==1 for row in arrival_records[41:])
        assert all(row[6]==1 for row in arrival_records[:16]) and all(row[6]==0 for row in arrival_records[16:])
    else:assert all(row[3]==6 for row in records)
    assert (w.save.x,w.save.y,w.save.room_x,w.save.room_y,w.save.id)==(80,112,110,105,0)
    if args.flash:
        dimensions,rgba=subprocess.check_output([str(ROOT/'build/amiga-feasibility/png_rgba'),str(BUILD/'energize.png')]).split(b'\n',1)
        width,height=map(int,dimensions.split())
        # Interior includes foreground, backdrop and teleporter pixels. All
        # palette entries must produce the source's full-screen grey flash.
        colours={tuple(rgba[(y*width+x)*4:(y*width+x)*4+3])
            for y in range(40,height-40) for x in range(25,width-25)}
        assert colours=={(187,187,187)},colours
    assert (BUILD/'tower.adf').read_bytes()==before
    report=dict(display=display,trace_fields=count*(26 if args.arrival else 12),checkpoint=[80,112,110,105,0],
        scope=('Native arrival motion, control, visibility and flash; audio, screen shake, departure and playable destinations pending' if args.arrival else 'Native Energize compact foreground and teleporter; frozen tower backdrop; arrival effects and playable menu destination pending'))
    (BUILD/'energize-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Energize:',json.dumps(report))
if __name__=='__main__':main()
