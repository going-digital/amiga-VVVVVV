#!/usr/bin/env python3
"""Verify moving Building Apport activation, animation and inactive DMA banks."""
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
from test_teleporter_capture import EMU,ROOT
from run_tower_probe import diagnostics
from test_teleporter import libraries as activation_libraries,Teleporter,Region,Save,Player,read
from test_teleporter_animation import libraries as animation_libraries,Animation
from tower_gameplay_data import building_room
BUILD=ROOT/'build/amiga-teleporter-live'
def main():
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
    dump=BUILD/'live.bin';png=BUILD/'live.png'
    dump.unlink(missing_ok=True);png.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='39',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (BUILD/'capture.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio','--screenshot-after','40',str(png)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump)
    assert not display['error'] and not display['missed'] and display['max_work_lines']<=250,display
    assert display['camera']==0
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
    data=dump.read_bytes();offset=data.index(b'V6TL\0\0\0\1')
    count=struct.unpack_from('>I',data,offset+8)[0];assert count==256,count
    records=[struct.unpack_from('>12i',data,offset+12+i*48) for i in range(count)]
    core,reference=activation_libraries();_,anim_ref=animation_libraries()
    from test_player import Room
    core.v6_player_init.argtypes=[C.POINTER(Player),C.c_int,C.c_int,C.c_int]
    core.v6_player_step.argtypes=[C.POINTER(Player),C.POINTER(Room),C.c_uint]
    tiles=(C.c_uint16*1200)(*building_room());room=Room();room.tiles=tiles;room.tileset=2
    player=Player();core.v6_player_init(C.byref(player),80,80,0);player.dir=1
    t=Teleporter();region=Region();save=Save();a=Animation(1,0,0)
    reference.reference_init(112,48,0,C.byref(save));core.v6_teleporter_init(C.byref(t),112,48,0)
    saves=messages=0;seed=1;activation=[]
    for tick,record in enumerate(records):
        if tick==180:t.state=2
        events=reference.reference_update(C.byref(player),t.state,t.tile,111,104,0,0)
        tbytes,rbytes,sbytes,_=read(reference)
        t=Teleporter.from_buffer_copy(tbytes);region=Region.from_buffer_copy(rbytes);save=Save.from_buffer_copy(sbytes)
        saves+=bool(events&1);messages+=bool(events&2)
        if events:activation.append(tick+1)
        core.v6_player_step(C.byref(player),C.byref(room),2 if tick<40 else 1 if tick<80 else 0)
        reference.reference_collide(C.byref(player));t=Teleporter.from_buffer_copy(read(reference)[0])
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        anim_ref.reference(C.byref(a),t.tile,0,(seed>>16)%6)
        expected=(player.x,player.y,t.tile,t.state,a.frame,a.delay,a.walking,saves,messages,save.x,save.y,region.active)
        assert record==expected,(tick+1,record,expected)
    assert len(activation)==saves==messages==1,activation
    assert (save.x,save.y,save.id)==(156,92,0)
    assert records[179][2]==2 and records[180][2]==6
    assert len({r[4] for r in records[20:180]})>=4
    assert len({r[4] for r in records[180:]})>=4
    report=dict(display=display,trace_fields=count*12,activation_ticks=activation,
        checkpoint=(save.x,save.y,save.gravity,save.dir,save.room_x,save.room_y,save.id),
        arrival_tick=181,scope='Scripted normal-input fixture; source teleporter activation/animation and host player physics; arrival state injected at tick 181; frozen tints; no campaign travel or disk save')
    (BUILD/'live-capture.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS live teleporter:',json.dumps(report))
if __name__=='__main__':main()
