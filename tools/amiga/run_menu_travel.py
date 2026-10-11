#!/usr/bin/env python3
"""Physical explored-menu travel, source-core trace and completed-arrival autosave."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
from run_interactive_save import ROOT, EMU, config, KEYS
from run_tower_probe import diagnostics
from save_disk import create_save_disk, read_record
from test_tower_route import libraries, RouteRoom, encode
from test_building_route import fixture
from test_teleporter import Teleporter
from test_teleporter_animation import Animation, libraries as animations
from test_teleporter_arrival import Arrival
from test_teleporter_departure import Departure
from test_teleporter_colour import libraries as colours
from test_player import FIELDS
from tower_gameplay_data import energize_room


def verify_travel(data,returning=False,ticks=64):
    at=data.index(b'V6MT\0\0\0\1')
    count=struct.unpack_from('>I',data,at+8)[0]
    assert count==ticks,count
    snapshot=struct.unpack_from('>23i',data,at+12)
    records=[struct.unpack_from('>36i',data,at+104+144*i) for i in range(count)]
    core,_=libraries();anim,_=animations();colour,_=colours()
    r,s,w,building,keep=fixture(core)
    desc=energize_room();tiles=(C.c_uint16*1200)(*desc['tiles']);blob=encode(desc['tiles'])
    packed=(C.c_uint8*len(blob)).from_buffer_copy(blob);tele=Teleporter(36,68,0,1,1,0)
    rooms=(RouteRoom*6)()
    for i in range(5):rooms[i]=keep[1][i]
    rooms[5]=RouteRoom(110,105,packed,len(blob),None,0,tiles,C.pointer(tele),0)
    r.rooms=rooms;r.count=6
    rx,ry=(110,105) if returning else (111,104)
    target=(111,104) if returning else (110,105)
    sx,sy=(80,112) if returning else (156,92)
    assert core.v6_tower_route_load(C.byref(r),rx,ry,0)
    for name,value in zip(FIELDS,snapshot):setattr(s.player,name,value)
    s.motion.ax,s.motion.pending_y=snapshot[16:18]
    origin=rooms[r.index].teleporter.contents
    origin.tile=2;origin.state=0;origin.onentity=0;r.tele_region.active=1
    w.save.x=sx;w.save.y=sy;w.save.gravity=0;w.save.dir=s.player.dir
    w.save.room_x=rx;w.save.room_y=ry;w.save.id=0
    s.save_x=sx;s.save_y=sy;s.save_gravity=0
    departure=Departure();arrival=Arrival()
    core.v6_teleporter_departure_init(C.byref(departure));core.v6_teleporter_arrival_init(C.byref(arrival))
    assert core.v6_teleporter_departure_start(C.byref(departure),C.byref(origin),C.byref(r.tele_region))
    PHASE=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p)
    @PHASE
    def phase(route,context):
        t=rooms[r.index].teleporter.contents
        if departure.state or departure.travel:
            return core.v6_teleporter_departure_tick(C.byref(departure),C.byref(s,type(s).invisible.offset),C.byref(t))
        return core.v6_teleporter_arrival_tick(C.byref(arrival),C.byref(s.player),C.byref(s.motion),
            C.byref(s,type(s).invisible.offset),C.byref(t),C.byref(r.tele_region))
    core.v6_tower_route_step_phase.argtypes=[C.c_void_p,C.c_uint,PHASE,C.c_void_p]
    core.v6_tower_route_teleport.argtypes=[C.c_void_p,C.c_int,C.c_int]
    animation=Animation(*snapshot[18:21]);seed=snapshot[21]&0xffffffff;colour_seed=snapshot[22]&0xffffffff
    def flashing():
        nonlocal colour_seed
        samples=(C.c_uint16*4)()
        for i in range(4):
            colour_seed^=(colour_seed<<13)&0xffffffff;colour_seed^=colour_seed>>17;colour_seed^=(colour_seed<<5)&0xffffffff
            samples[i]=colour_seed>>16
        return colour.v6_teleporter_flash_colour(samples,s.noflashing)
    leg=0
    for tick,record in enumerate(records):
        index=r.index;departure.events=arrival.events=0
        assert core.v6_tower_route_step_phase(C.byref(r),8 if departure.state or not arrival.control else 0,phase,None)
        if departure.travel:
            assert core.v6_tower_route_teleport(C.byref(r),*target)
            departure.travel=0;leg+=1
            core.v6_teleporter_arrival_init(C.byref(arrival));arrival.flash=departure.flash;arrival.shake=departure.shake
            assert core.v6_teleporter_arrival_start(C.byref(arrival))
        d=(departure.state,departure.delay,departure.control,departure.flash,departure.shake,departure.events,departure.travel,leg)
        a=(arrival.state,arrival.delay,arrival.control,arrival.flash,arrival.shake,arrival.events,s.invisible,
           s.player.vx,s.player.vy,s.player.ay,s.player.old_x,s.player.old_y,s.player.dir,s.death_timer)
        if departure.flash:departure.flash-=1
        if departure.shake:departure.shake-=1
        if arrival.flash:arrival.flash-=1
        if arrival.shake:arrival.shake-=1
        if r.index!=index:animation=Animation(1,0,0)
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        t=rooms[r.index].teleporter.contents
        anim.v6_teleporter_animate(C.byref(animation),t.tile,0,(seed>>16)%6)
        tele_tint=flashing() if t.tile==6 else 0x444 if t.tile==1 else 0xaaf
        player_tint=flashing() if 4000<=departure.state<=4002 and not s.invisible else 0x6ff
        b=(r.index,s.player.x,s.player.y,t.tile,t.state,r.tele_events,animation.frame,w.save.x,w.save.y,
           w.save.room_x,w.save.room_y,r.tele_region.active,tele_tint,player_tint)
        assert record==d+a+b,(tick+1,record,d+a+b)
    assert [(i+1,row[13]) for i,row in enumerate(records) if row[13]]==[(tick,cue) for tick,cue in ((23,1),(38,2),(64,4)) if tick<=ticks]
    if ticks==64:assert arrival.control and not arrival.state and not s.invisible and leg==1
    return count*36,(w.save.x,w.save.y,0,w.save.dir,*target,0,0)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=ROOT/'build/amiga-menu-travel')
    parser.add_argument('--unexplored',action='store_true')
    parser.add_argument('--effects',action='store_true',help='Verify interactive shake, reserved Paula cues and audio drain before DOS')
    parser.add_argument('--exit-pending',action='store_true',help='Quit during the final cue tail; verify queued arrival save before OS exit')
    parser.add_argument('--load-return',type=Path,help='Load a saved Energize record into an unseeded build, then return to Building')
    args=parser.parse_args();build=args.build.resolve()
    assert not (args.unexplored and args.load_return)
    assert not args.exit_pending or (args.effects and not args.unexplored and not args.load_return)
    label='menu-exit' if args.exit_pending else 'menu-return' if args.load_return else 'menu-unexplored' if args.unexplored else 'menu-travel'
    disk=build/('capture-exit-disk.adf' if args.exit_pending else 'capture-return-disk.adf' if args.load_return else 'capture-menu-disk.adf');disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk);cfg=config(build,disk)
    if args.load_return:
        disk.write_bytes(args.load_return.read_bytes())
        assert struct.unpack_from('>7iI',read_record(disk),8)[4:6]==(110,105)
    boot_before=(build/'tower.adf').read_bytes();disk_before=disk.read_bytes()
    dump=build/(label+'.bin');dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='55',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    if args.effects:env['COPPERLINE_DBG_AFTER']='65'
    # The larger two-room executable boots later than the one-room menu
    # fixture. Allow the natural replay to settle before sending input.
    inputs=['--joy-after','35','down','200','--joy-after','35','fire','200',
            '--joy-after','36','left','200','--joy-after','37','fire','200']
    if args.load_return:
        env['COPPERLINE_DBG_AFTER']='70' if args.effects else '60'
        inputs=['--joy-after','35','fire','200','--click-after','35','right','200',
                '--joy-after','42','down','200','--joy-after','42','fire','200',
                '--joy-after','43','left','200','--joy-after','44','fire','200']
    elif not args.unexplored:
        # Saving while departure/arrival owns control must report busy;
        # only the final arrival event may enter the DOS save pause.
        inputs+=['--click-after','37.4','right','200','--click-after','39.6','right','200']
    if args.exit_pending:inputs+=['--click-after','40.6','left','200']
    elif args.effects and not args.unexplored and not args.load_return:
        # A new selector must not postpone a completed-arrival save while
        # its final cue drains. This press is also consumed without a flip.
        inputs+=['--joy-after','40.65','down','200','--joy-after','40.65','fire','200']
    if args.effects:
        for name in ('paula','paula-0','paula-1','paula-2','paula-3','drivesounds'):
            (build/(label+'-audio')/(name+'.wav')).unlink(missing_ok=True)
    with (build/(label+'.log')).open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,
            *(['--audio-stems',str(build/(label+'-audio')),'--audio-stems-mode','source,channel'] if args.effects else []),
            '--screenshot-after',str(int(env['COPPERLINE_DBG_AFTER'])+1),str(build/(label+'.png'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();at=data.index(b'V6TM\0\0\0\1')
    menu=dict(zip('opened changed closed travel selected paused_ticks before_hash after_hash initial_flips final_flips'.split(),struct.unpack_from('>10I',data,at+8)))
    at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    display=diagnostics(dump)
    assert menu['opened']==menu['changed']==1 and menu['selected']==int(bool(args.load_return)) and menu['paused_ticks']>30,menu
    assert menu['before_hash']==menu['after_hash'],menu
    assert menu['initial_flips']==menu['final_flips']==(0 if args.load_return else 1),menu
    assert display['status']==(2 if args.exit_pending else 1) and display['error']==display['missed']==0 and display['max_work_lines']<=250,display
    chip_bytes=95968
    if args.effects:
        manifest=json.loads((ROOT/'build/amiga-feasibility/teleporter-samples.json').read_text())
        chip_bytes+=9602+256+sum(s['pcm_bytes'] for s in manifest['samples'])+2
    assert display['chip_bytes']==chip_bytes,display
    if not args.exit_pending:assert display['logic_ticks']==600,display
    assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
    at=data.index(b'V6MT\0\0\0\1')
    if args.unexplored:
        assert menu['closed']==1 and menu['travel']==0 and struct.unpack_from('>I',data,at+8)[0]==0,menu
        assert ui['actions']==ui['pauses']==ui['resumes']==0,ui
        assert disk.read_bytes()==disk_before
        fields=0;events=[]
    else:
        assert menu['closed']==0 and menu['travel']==1,menu
        fields,checkpoint=verify_travel(data,bool(args.load_return))
        actions=2 if args.load_return else 3
        pauses=2 if args.load_return else 1
        assert ui['actions']==actions and ui['pauses']==ui['resumes']==pauses and ui['saves']==1,ui
        assert ui['loads']==int(bool(args.load_return)) and ui['busy']==(0 if args.load_return else 2),ui
        assert ui['errors']==ui['last_result']==0,ui
        at=data.index(b'V6IT\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
        assert count==actions,count
        events=[struct.unpack_from('>10I',data,at+16+40*i) for i in range(count)]
        assert [row[:2] for row in events]==([(2,0),(1,0)] if args.load_return else [(1,5),(1,5),(1,0)]),events
        for action,result,bh,ah,fb,fa,tb,ta,x,y in events:
            assert tb==ta and fa-fb<=4 and (action==2 or bh==ah),events
        if args.load_return:
            assert (ui['loaded_x'],ui['loaded_y'])==(80,112),ui
            assert disk.read_bytes()!=disk_before
            assert args.load_return.read_bytes()==disk_before
        else:
            # Tie both rejected writes to source-validated script states,
            # rather than accepting a generic busy result from any phase.
            at=data.index(b'V6ME\0\0\0\1');start_tick=struct.unpack_from('>I',data,at+8)[0]
            at=data.index(b'V6MT\0\0\0\1')
            for i,event in enumerate(events[:2]):
                tick=event[6]-start_tick
                assert 1<=tick<=64,tick
                state=struct.unpack_from('>36i',data,at+104+144*(tick-1))
                assert (state[0]!=0 if i==0 else state[0]==0 and state[8]!=0),state
        assert struct.unpack_from('>7iI',read_record(disk),8)==checkpoint
        if args.exit_pending:assert display['logic_ticks']==events[-1][6],(display,events)
    assert (build/'tower.adf').read_bytes()==boot_before
    report=dict(menu=menu,ui=ui,display=display,source_trace_fields=fields,events=events,
                physical_menu_controls=True,unexplored_excluded=args.unexplored,boot_disk_unchanged=True,
                completed_arrival_autosave=not args.unexplored)
    if args.load_return:report['loaded_room_admits_return']=True
    if args.effects and not args.unexplored:
        at=data.index(b'V6ME\0\0\0\1');effect=struct.unpack_from('>6I',data,at+8)
        assert effect[1]==effect[0]+64 and effect[2]>effect[1] and effect[3]>0 and effect[4]==0 and effect[5]==int(args.exit_pending),effect
        at=data.index(b'V6MH\0\0\0\1');count,seed=struct.unpack_from('>2I',data,at+8)
        assert count==64,count
        mt=data.index(b'V6MT\0\0\0\1');shake=[]
        for tick in range(count):
            row=struct.unpack_from('>3i',data,at+16+12*tick)
            travel=struct.unpack_from('>36i',data,mt+104+144*tick)
            assert row[0]==(travel[4] if travel[0] else travel[12]),(tick,row,travel)
            expected=[]
            for _ in range(2):
                if row[0]:
                    seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
                    numerator=(seed>>16)*7-262144
                    expected.append(abs(numerator)//65536*(-1 if numerator<0 else 1))
                else:expected.append(0)
            assert row[1:]==tuple(expected),(tick,row,expected)
            shake.append(row)
        from teleporter_audio_capture import verify
        verify(report,dump,build/(label+'-audio'),reserved=True,single=True,start_tick=effect[0])
        report.update(shake_records=shake,effect_diagnostics=effect,audio_idle_before_DOS=True)
        if args.exit_pending:report['queued_save_before_exit']=True
    (build/(label+'-capture.json')).write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native explored menu:',json.dumps(report))
if __name__=='__main__':main()
