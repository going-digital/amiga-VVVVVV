#!/usr/bin/env python3
"""Native Frown game completion and first-128-tick integration trace."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
from run_tower_probe import diagnostics,EMU
from test_player import ROOT
from test_building_route import fixture
from test_tower_route import libraries,RouteRoom,encode
from test_teleporter import Teleporter
from test_checkpoints import Checkpoint
from test_rescue_script import VM,Signals,Program
from test_station_trigger import Story,Trigger
from test_companion import Companion,bind,state
from tower_gameplay_data import energize_room,frown_room

def verify(data,skip):
    core,_=libraries();bind(core);r,s,w,t,keep=fixture(core)
    rooms=(RouteRoom*7)()
    for i in range(5):rooms[i]=keep[1][i]
    blobs=[];tiles=[];tele=Teleporter(36,68,0,1,1,0);bank=(Checkpoint*1)(Checkpoint(192,88,20,441490,0,0))
    for i,desc in enumerate((energize_room(),frown_room()),5):
        blob=encode(desc['tiles']);raw=(C.c_uint8*len(blob)).from_buffer_copy(blob);decoded=(C.c_uint16*1200)(*desc['tiles'])
        blobs.append(raw);tiles.append(decoded)
        rooms[i]=RouteRoom(desc['x'],desc['y'],raw,len(raw),bank if i==6 else None,int(i==6),decoded,C.pointer(tele) if i==5 else None,0)
    r.rooms=rooms;r.count=7
    core.v6_tower_session_init(C.byref(s),188,86,1,0)
    for name,value in zip('x y gravity dir room_x room_y id'.split(),(188,86,1,0,111,105,441490)):setattr(w.save,name,value)
    assert core.v6_tower_route_load(C.byref(r),111,105,1)
    v=VM();v.control=v.mood=1;story=Story();trigger=Trigger();crew=Companion()
    core.v6_companion_init(C.byref(crew));core.v6_station_companion_idle.argtypes=[C.POINTER(Companion),C.c_int]
    core.v6_station_companion_idle(C.byref(crew),1)
    vm=C.CDLL(str(ROOT/'build/amiga-station-rescue/core.so'));vm.program.restype=C.POINTER(Program)
    vm.v6_rescue_start.argtypes=[C.POINTER(VM),C.POINTER(Program),C.POINTER(Program),C.c_int]
    vm.v6_station_rescue_tick.argtypes=[C.POINTER(VM),C.POINTER(Story),C.POINTER(Signals)]
    triggers=C.CDLL(str(ROOT/'build/amiga-station-trigger/core.so'))
    triggers.v6_station_trigger_enter.argtypes=[C.POINTER(Trigger),C.c_int,C.c_int,C.POINTER(Story)]
    triggers.v6_station_trigger_step.argtypes=[C.POINTER(Trigger),C.POINTER(Story),C.POINTER(type(s.player))]
    triggers.v6_station_trigger_take.argtypes=[C.POINTER(Trigger)]
    triggers.v6_station_trigger_enter(C.byref(trigger),111,105,C.byref(story))
    def records(magic,n):
        at=data.index(magic);count=struct.unpack_from('>I',data,at+8)[0];assert count==128
        return [struct.unpack_from('>'+str(n)+'I',data,at+16+4*n*i) for i in range(count)]
    rescue=records(b'V6RV\0\0\0\1',18);companions=records(b'V6CT\0\0\0\1',14)
    bars=fade=mode=fire=0;fields=0
    final=None
    for tick in range(1000):
        buttons=(4 if v.waiting and tick%30==0 else 0) if story.rescue_triggered else 1
        core.v6_companion_step(C.byref(crew),C.byref(s.player),C.byref(r.room),s.death_timer)
        bars=min(361,bars+25) if v.bars else max(0,bars-25)
        if v.fade!=mode:mode=v.fade;fade=416 if mode<0 else 0
        elif mode>0:fade=min(432,fade+24)
        elif mode<0:fade=max(0,fade-24)
        signals=Signals(bars>=360 if v.bars else bars==0,fade>416 if v.fade>0 else fade==0,s.player.roof>0,bool(buttons&4) and not fire)
        fire=bool(buttons&4)
        if v.active:
            buttons&=~4
            if not v.control:buttons|=8
        assert core.v6_tower_route_step(C.byref(r),buttons)
        assert r.index==6
        triggers.v6_station_trigger_step(C.byref(trigger),C.byref(story),C.byref(s.player))
        if trigger.pending and not v.active:
            assert triggers.v6_station_trigger_take(C.byref(trigger))==1
            assert vm.v6_rescue_start(C.byref(v),vm.program(0),vm.program(1),int(skip))
        vm.v6_station_rescue_tick(C.byref(v),C.byref(story),C.byref(signals))
        crew.following=v.following
        if v.tile_serial:crew.mood=0
        final=tuple(x&0xffffffff for x in (v.pc,v.active,v.error,v.delay,v.waiting,v.bars,v.control,v.mood,v.following,v.ui_serial,v.cues,v.flips,v.fade,v.speech.contents.index+1 if v.speech else 0,story.yellow_rescued,story.companion,bars,fade))
        if tick<128:
            assert rescue[tick]==final,(tick,rescue[tick],final)
            assert companions[tick]==state(crew),(tick,companions[tick],state(crew))
            fields+=32
    at=data.index(b'V6RA\0\0\0\1');assert struct.unpack_from('>18I',data,at+8)==final
    assert story.yellow_rescued and story.companion==7 and not v.active and not v.error
    assert v.cues==(1 if skip else 11) and not v.flips and crew.following
    return fields,list(final)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--skip',action='store_true');args=parser.parse_args();build=args.build.resolve()
    config=build/'station.toml';config.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
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
''')
    dump=build/'station.bin';dump.unlink(missing_ok=True);before=(build/'tower.adf').read_bytes()
    env=dict(os.environ,COPPERLINE_DBG_AFTER='75',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    for name in ('paula','paula-0','paula-1','paula-2','paula-3','drivesounds'):
        (build/'audio-stems'/(name+'.wav')).unlink(missing_ok=True)
    with (build/'station.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio','--audio-stems',str(build/'audio-stems'),'--audio-stems-mode','source,channel','--screenshot-after','76',str(build/'station.png'),'--click-after','78','left','200'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump);assert display['status']==1 and display['error']==display['missed']==0 and display['max_work_lines']<=250,display
    assert display['logic_ticks']==1000,display
    audio_bytes=json.loads((ROOT/'build/amiga-feasibility/station-cue-samples.json').read_text())['chip_bytes']
    assert display['chip_bytes']==111328+audio_bytes,display
    fields,final=verify(dump.read_bytes(),args.skip)
    assert (build/'tower.adf').read_bytes()==before
    report=dict(display=display,source_core_fields=fields,final=final,skip=args.skip,boot_disk_unchanged=True)
    from audio_capture import verify as verify_audio
    verify_audio(report,dump,build/'audio-stems',args.skip,station=True)
    (build/'station-capture.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native station game:',json.dumps(report))
if __name__=='__main__':main()
