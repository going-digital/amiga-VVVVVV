#!/usr/bin/env python3
"""Native Energize/arrival and staged Building/Energize round-trip captures."""
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
from test_teleporter_departure import Departure
from test_teleporter_colour import libraries as colour_libraries

BUILD=ROOT/'build/amiga-energize'
def main():
    global BUILD
    parser=argparse.ArgumentParser();parser.add_argument('--arrival',action='store_true')
    parser.add_argument('--flash',action='store_true')
    parser.add_argument('--roundtrip',action='store_true')
    parser.add_argument('--outbound',action='store_true')
    parser.add_argument('--colour',action='store_true')
    parser.add_argument('--audio',action='store_true')
    parser.add_argument('--reserved-audio',action='store_true')
    args=parser.parse_args()
    if args.reserved_audio and not args.audio:parser.error('--reserved-audio requires --audio')
    if args.audio and (not args.roundtrip or args.colour or args.outbound or args.flash):parser.error('--audio requires full roundtrip')
    if args.colour and (not args.roundtrip or args.outbound or args.flash):parser.error('--colour requires roundtrip without outbound/flash')
    if args.outbound and not args.roundtrip:parser.error('--outbound requires --roundtrip')
    if args.roundtrip and args.flash:parser.error('choose roundtrip or flash')
    if args.flash or args.roundtrip:args.arrival=True
    if args.arrival:BUILD=ROOT/('build/amiga-energize-arrival-flash' if args.flash else 'build/amiga-energize-arrival')
    if args.roundtrip:BUILD=ROOT/('build/amiga-teleporter-outbound' if args.outbound else 'build/amiga-teleporter-roundtrip')
    if args.colour:BUILD=ROOT/'build/amiga-teleporter-colour'
    if args.audio:BUILD=ROOT/('build/amiga-teleporter-reserved' if args.reserved_audio else 'build/amiga-teleporter-paula')
    ticks=6 if args.colour else 1 if args.flash else 64 if args.outbound else 128
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
    if args.audio:
        for name in ('paula','paula-0','paula-1','paula-2','paula-3','drivesounds'):
            (BUILD/'audio-stems'/(name+'.wav')).unlink(missing_ok=True)
    before=(BUILD/'tower.adf').read_bytes()
    with (BUILD/'energize.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio',*(['--audio-stems',str(BUILD/'audio-stems'),'--audio-stems-mode','source,channel'] if args.audio else []),'--screenshot-after','39',str(BUILD/'energize.png')],
            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump)
    assert display['status']==1 and not display['error'] and not display['missed'],display
    chip_bytes=69088
    if args.audio:
        manifest=json.loads((ROOT/'build/amiga-feasibility/teleporter-samples.json').read_text())
        chip_bytes+=sum(s['pcm_bytes'] for s in manifest['samples'])+2
    assert display['max_work_lines']<=250 and display['chip_bytes']==chip_bytes,display
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
    departure=Departure();departure_records=[];leg=0
    if args.roundtrip:
        core.v6_player_init(C.byref(s.player),156,92,0)
        for i in range(2):assert core.v6_tower_route_step(C.byref(r),0)
        core.v6_teleporter_departure_init(C.byref(departure))
        assert core.v6_teleporter_departure_start(C.byref(departure),C.byref(building),C.byref(r.tele_region))
        at=data.index(b'V6DR\0\0\0\1');assert struct.unpack_from('>I',data,at+8)[0]==ticks
        departure_records=[struct.unpack_from('>8i',data,at+12+32*i) for i in range(ticks)]
    else:assert core.v6_tower_route_teleport(C.byref(r),110,105)
    arrival=Arrival();arrival_records=[]
    if args.arrival:
        at=data.index(b'V6AR\0\0\0\1');assert struct.unpack_from('>I',data,at+8)[0]==ticks
        arrival_records=[struct.unpack_from('>14i',data,at+12+56*i) for i in range(ticks)]
        core.v6_teleporter_arrival_init(C.byref(arrival))
        if not args.roundtrip:
            assert core.v6_teleporter_arrival_start(C.byref(arrival));s.invisible=1
    PHASE=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p)
    @PHASE
    def phase(route,context):
        t=rooms[r.index].teleporter.contents
        if args.roundtrip and (departure.state or departure.travel):
            return core.v6_teleporter_departure_tick(C.byref(departure),
                C.byref(s,type(s).invisible.offset),C.byref(t))
        return core.v6_teleporter_arrival_tick(C.byref(arrival),C.byref(s.player),C.byref(s.motion),
            C.byref(s, type(s).invisible.offset),C.byref(t),C.byref(r.tele_region))
    core.v6_tower_route_step_phase.argtypes=[C.c_void_p,C.c_uint,PHASE,C.c_void_p]
    colour_records=[];colour_seed=7
    if args.roundtrip:
        colours,_=colour_libraries()
        at=data.index(b'V6CL\0\0\0\1');assert struct.unpack_from('>I',data,at+8)[0]==ticks
        colour_records=[struct.unpack_from('>2i',data,at+12+8*i) for i in range(ticks)]
    def flashing_colour():
        nonlocal colour_seed
        samples=(C.c_uint16*4)()
        for i in range(4):
            colour_seed^=(colour_seed<<13)&0xffffffff;colour_seed^=colour_seed>>17;colour_seed^=(colour_seed<<5)&0xffffffff
            samples[i]=colour_seed>>16
        return colours.v6_teleporter_flash_colour(samples,s.noflashing)
    animation=Animation(1,0,0);seed=1
    for tick,record in enumerate(records):
        index=r.index
        if args.roundtrip:
            departure.events=arrival.events=0
            if leg==1 and not arrival.state and not departure.state:
                t=rooms[r.index].teleporter.contents
                assert core.v6_teleporter_departure_start(C.byref(departure),C.byref(t),C.byref(r.tele_region))
        if args.arrival:
            assert core.v6_tower_route_step_phase(C.byref(r),8 if not arrival.control or departure.state else 0,phase,None)
            if args.roundtrip:
                if departure.travel:
                    assert core.v6_tower_route_teleport(C.byref(r),110 if leg==0 else 111,105 if leg==0 else 104)
                    departure.travel=0;leg+=1
                    core.v6_teleporter_arrival_init(C.byref(arrival))
                    arrival.flash=departure.flash;arrival.shake=departure.shake
                    assert core.v6_teleporter_arrival_start(C.byref(arrival))
                expected_departure=(departure.state,departure.delay,departure.control,departure.flash,
                    departure.shake,departure.events,departure.travel,leg)
                assert departure_records[tick]==expected_departure,(tick+1,departure_records[tick],expected_departure)
                if departure.flash:departure.flash-=1
                if departure.shake:departure.shake-=1
            expected_arrival=(arrival.state,arrival.delay,arrival.control,arrival.flash,arrival.shake,arrival.events,
                s.invisible,s.player.vx,s.player.vy,s.player.ay,s.player.old_x,s.player.old_y,s.player.dir,s.death_timer)
            assert arrival_records[tick]==expected_arrival,(tick+1,arrival_records[tick],expected_arrival)
            if arrival.flash:arrival.flash-=1
            if arrival.shake:arrival.shake-=1
        else:assert core.v6_tower_route_step(C.byref(r),0)
        if args.roundtrip and r.index!=index:animation=Animation(1,0,0)
        t=rooms[r.index].teleporter.contents
        seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
        anim.v6_teleporter_animate(C.byref(animation),t.tile,0,(seed>>16)%6)
        if args.roundtrip:
            tele_tint=flashing_colour() if t.tile==6 else 0x444 if t.tile==1 else 0xaaf
            player_tint=flashing_colour() if 4000<=departure.state<=4002 and not s.invisible else 0x6ff
            assert colour_records[tick]==(tele_tint,player_tint),(tick+1,colour_records[tick],tele_tint,player_tint)
        expected=(r.index,s.player.x,s.player.y,t.tile,t.state,r.tele_events,animation.frame,
            w.save.x,w.save.y,w.save.room_x,w.save.room_y,r.tele_region.active)
        assert record==expected,(tick+1,record,expected)
    assert all(row[5]==0 for row in records)
    if args.roundtrip:
        assert [row[0] for row in records]==([4]*21+[5]*64+[4]*43)[:ticks]
        assert [(i+1,row[5]) for i,row in enumerate(departure_records) if row[5]]==[event for event in [(1,1),(11,2),(22,4),(65,1),(75,2),(86,4)] if event[0]<=ticks]
        assert [(i+1,row[5]) for i,row in enumerate(arrival_records) if row[5]]==[event for event in [(23,1),(38,2),(64,4),(87,1),(102,2),(128,4)] if event[0]<=ticks]
        if args.colour:
            assert departure.state==4001 and departure.delay==5 and not departure.control and not s.invisible and not leg
        else:assert arrival.control and not arrival.state and not s.invisible and leg==(1 if args.outbound else 2)
        at=data.index(b'V6RT\0\0\0\1')
        route_diag=struct.unpack_from('>7I',data,at)
        assert route_diag[2:5]==(r.index,r.transitions,r.returns) and route_diag[5]>=62*leg and not route_diag[6],route_diag
    else:assert all(row[0]==5 for row in records)
    if args.arrival and not args.roundtrip:
        assert [(i+1,row[5]) for i,row in enumerate(arrival_records) if row[5]]==([(1,1)] if args.flash else [(1,1),(16,2),(42,4)])
        assert all(row[2]==0 for row in arrival_records[:41]) and all(row[2]==1 for row in arrival_records[41:])
        assert all(row[6]==1 for row in arrival_records[:16]) and all(row[6]==0 for row in arrival_records[16:])
    elif not args.roundtrip:assert all(row[3]==6 for row in records)
    checkpoint=(156,92,111,104,0) if args.roundtrip and not args.outbound else (80,112,110,105,0)
    assert (w.save.x,w.save.y,w.save.room_x,w.save.room_y,w.save.id)==checkpoint
    if args.flash:
        dimensions,rgba=subprocess.check_output([str(ROOT/'build/amiga-feasibility/png_rgba'),str(BUILD/'energize.png')]).split(b'\n',1)
        width,height=map(int,dimensions.split())
        # Interior includes foreground, backdrop and teleporter pixels. All
        # palette entries must produce the source's full-screen grey flash.
        colours={tuple(rgba[(y*width+x)*4:(y*width+x)*4+3])
            for y in range(40,height-40) for x in range(25,width-25)}
        assert colours=={(187,187,187)},colours
    if args.colour:
        from collections import Counter
        dimensions,rgba=subprocess.check_output([str(ROOT/'build/amiga-feasibility/png_rgba'),str(BUILD/'energize.png')]).split(b'\n',1)
        pixels=Counter(tuple(rgba[i:i+3]) for i in range(0,len(rgba),4))
        def rgb(c):return ((c>>8)*17,((c>>4)&15)*17,(c&15)*17)
        assert tele_tint!=player_tint
        assert pixels[rgb(tele_tint)]>500 and pixels[rgb(player_tint)]>20,(tele_tint,player_tint,pixels)
    assert (BUILD/'tower.adf').read_bytes()==before
    report=dict(display=display,trace_fields=count*(36 if args.roundtrip else 26 if args.arrival else 12),checkpoint=list(checkpoint),
        scope=('Native arrival motion, control, visibility and flash; audio, screen shake, departure and playable destinations pending' if args.arrival else 'Native Energize compact foreground and teleporter; frozen tower backdrop; arrival effects and playable menu destination pending'))
    if args.roundtrip:
        report['route_loading_frames']=route_diag[5]
        report['last_colours']=[tele_tint,player_tint]
        report['scope']='Native staged departure/handoff/arrival and cold scene banks; audio, screen shake, persistence and explored menu destinations pending'
    if args.audio:
        from teleporter_audio_capture import verify
        verify(report,dump,BUILD/'audio-stems',reserved=args.reserved_audio)
        if args.reserved_audio:report['scope']='Native two-channel SFX reservation and priority replacement; reserved channels idle; gameplay oracle and captured playback verified; music playback and shipping allocation pending'
        report['scope']='Native hard-panned Paula cue overlap and round trip; final music/SFX allocation, screen shake, saving and menu destinations pending'
    (BUILD/'energize-capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native teleporter round trip:' if args.roundtrip else 'PASS native Energize:',json.dumps(report))
if __name__=='__main__':main()
