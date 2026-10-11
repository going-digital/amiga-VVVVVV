#!/usr/bin/env python3
"""Completed outbound/return arrival: DF1 save, fresh boot, semantic rejection."""
import json
import ctypes as C
import os
from pathlib import Path
import struct
import subprocess
from run_tower_probe import ROOT,EMU,diagnostics
from run_interactive_save import config
from run_building_save import corrupt_centre
from save_disk import create_save_disk,read_record
FLAGS='-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_SHAKE -DV6_BUILDING_SAVE -DV6_TOWER_ARRIVAL_SAVE'

def values(dump):
    raw=dump.read_bytes();at=raw.index(b'V6BS\0\0\0\1')
    return struct.unpack_from('>20I',raw,at+8)

def capture(build,name):
    dump=build/(name+'.bin');dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='39',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/(name+'.log')).open('w') as log:
        subprocess.run([EMU,'--config',str(build/'interactive-save.toml'),'--floppy-drives','2','--noaudio',
            '--screenshot-after','40',str(build/(name+'.png'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    return values(dump),dump

def verify_cold_route(dump,ticks,checkpoint):
    from test_tower_route import libraries,RouteRoom,encode
    from test_building_route import fixture
    from test_teleporter import Teleporter
    from test_teleporter_animation import Animation,libraries as animations
    from tower_gameplay_data import energize_room
    core,_=libraries();anim,_=animations();r,s,w,building,keep=fixture(core)
    desc=energize_room();tiles=(C.c_uint16*1200)(*desc['tiles']);blob=encode(desc['tiles'])
    packed=(C.c_uint8*len(blob)).from_buffer_copy(blob);tele=Teleporter(36,68,0,1,1,0)
    rooms=(RouteRoom*6)()
    for i in range(5):rooms[i]=keep[1][i]
    rooms[5]=RouteRoom(110,105,packed,len(blob),None,0,tiles,C.pointer(tele),0)
    r.rooms=rooms;r.count=6
    x,y,gravity,direction,rx,ry,ident=checkpoint
    w.save.x=x;w.save.y=y;w.save.gravity=gravity;w.save.dir=direction
    w.save.room_x=rx;w.save.room_y=ry;w.save.id=ident
    assert core.v6_tower_route_load(C.byref(r),rx,ry,1)
    raw=dump.read_bytes();at=raw.index(b'V6BR\0\0\0\1')
    assert struct.unpack_from('>I',raw,at+8)[0]==ticks
    animation=Animation(1,0,0);seed=1
    for tick in range(ticks):
        assert core.v6_tower_route_step(C.byref(r),0)
        t=rooms[r.index].teleporter.contents
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        anim.v6_teleporter_animate(C.byref(animation),t.tile,0,(seed>>16)%6)
        expected=(r.index,s.player.x,s.player.y,t.tile,t.state,r.tele_events,animation.frame,
            w.save.x,w.save.y,w.save.room_x,w.save.room_y,r.tele_region.active)
        actual=struct.unpack_from('>12i',raw,at+12+48*tick)
        assert actual==expected,(tick+1,actual,expected)
    return ticks*12

def verify_early():
    build=ROOT/'build/amiga-arrival-save-early';build.mkdir(parents=True,exist_ok=True)
    with (build/'build.log').open('w') as log:
        subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={build}',
            f'CPPFLAGS={FLAGS} -DV6_ENERGIZE_CAPTURE_TICKS=64 -DV6_TOWER_ARRIVAL_SAVE_EARLY',str(build/'tower.adf')],
            stdout=log,stderr=subprocess.STDOUT,check=True)
    disk=build/'early-save-disk.adf';disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk);config(build,disk)
    before=disk.read_bytes();boot=(build/'tower.adf').read_bytes()
    rejected,dump=capture(build,'early');display=diagnostics(dump)
    assert rejected[:3]==(1,1,0) and rejected[3:9]==(80,112,1,110,105,0),rejected
    assert display['status']==2 and display['logic_ticks']==23 and display['error']==display['missed']==0,display
    raw=dump.read_bytes();at=raw.index(b'V6AR\0\0\0\1');count=struct.unpack_from('>I',raw,at+8)[0]
    arrival=struct.unpack_from('>14i',raw,at+12+(count-1)*56)
    assert count==23 and arrival[0]==4011 and not arrival[2] and arrival[5]==1,arrival
    assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
    report=dict(rejected=rejected,display=display,last_arrival=arrival,
        scope='Valid handoff centre is not persisted while the arrival script still owns control; private DF1 and boot image unchanged')
    (build/'early-save-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS premature arrival save rejected:',json.dumps(report),flush=True)
    return report

def main():
    reports=[]
    for ticks,x,y,rx,ry,direction in ((64,80,112,110,105,1),(128,156,92,111,104,1)):
        build=ROOT/f'build/amiga-arrival-save-{ticks}';build.mkdir(parents=True,exist_ok=True)
        with (build/'build.log').open('w') as log:
            subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={build}',
                f'CPPFLAGS={FLAGS} -DV6_ENERGIZE_CAPTURE_TICKS={ticks}',str(build/'tower.adf')],stdout=log,stderr=subprocess.STDOUT,check=True)
        disk=build/'arrival-save-disk.adf';disk.unlink(missing_ok=True)
        create_save_disk(build/'tower.adf',disk);config(build,disk);boot=(build/'tower.adf').read_bytes()
        with (build/'save-verify.log').open('w') as log:
            subprocess.run(['python3',str(ROOT/'tools/amiga/run_energize.py'),'--roundtrip','--shake',
                *(['--outbound'] if ticks==64 else []),'--save-disk',str(disk),'--build-dir',str(build)],stdout=log,stderr=subprocess.STDOUT,check=True)
        first=values(build/'energize.bin');source=json.loads((build/'energize-capture.json').read_text())
        assert first[:3]==(1,0,0) and first[3:9]==(x,y,direction,rx,ry,0),first
        record=read_record(disk)
        assert struct.unpack_from('>7iI',record,8)==(x,y,0,direction,rx,ry,0,0),record
        cold,dump=capture(build,'cold');display=diagnostics(dump)
        assert cold[:3]==(2,0,0) and cold[3:9]==first[3:9] and cold[9:12]==(x,y,1),cold
        assert cold[12:]==(x,y,0,0,0,direction,0,0),cold
        assert display['status']==2 and display['error']==display['missed']==0 and display['max_work_lines']<=250,display
        assert display['logic_ticks']==ticks and read_record(disk)==record
        raw=dump.read_bytes()
        for tag,fields in ((b'V6DR\0\0\0\1',8),(b'V6AR\0\0\0\1',14)):
            at=raw.index(tag);assert struct.unpack_from('>I',raw,at+8)[0]==ticks
            assert all(struct.unpack_from('>i',raw,at+12+i*fields*4)[0]==0 for i in range(ticks)),tag
        cold_fields=verify_cold_route(dump,ticks,[x,y,0,direction,rx,ry,0])
        corrupt_centre(disk,x+1);before=disk.read_bytes();rejected,bad=capture(build,'invalid')
        assert rejected[:3]==(2,4,1),rejected
        raw=bad.read_bytes();at=raw.index(b'V6TP\0\0\0\6')
        assert struct.unpack_from('>I',raw,at+8)[0]==0
        assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
        report=dict(ticks=ticks,checkpoint=[x,y,0,direction,rx,ry,0],first=first,cold=cold,rejected=rejected,
            display=source['display'],cold_display=display,trace_fields=source['trace_fields'],cold_trace_fields=cold_fields,
            scope='Completed source arrival SAVE gate, real DF1 commit, fresh-boot room/centre/history restore and CRC-valid wrong-centre rejection before takeover; bounded zero-story fixture')
        (build/'arrival-save-capture.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
        print('PASS arrival save:',ticks,json.dumps(report),flush=True)
    early=verify_early()
    (ROOT/'build/amiga-arrival-save-capture.json').write_text(json.dumps(dict(arrivals=reports,early=early),indent=2)+'\n')
if __name__=='__main__':main()
