#!/usr/bin/env python3
"""Main-tower boundary reference and checkpoint-area gameplay route."""
import ctypes as C
import json
import subprocess
import random
from test_player import ROOT, Player, Room, block
from test_tower_player import libraries, Tiles, READ, OUT
from test_tower_stream import Stream
from tower_play_trace import Session
from test_checkpoints import Checkpoint, Save
from tower_gameplay_data import checkpoints
class Exit(C.Structure):
    _fields_=[(n,C.c_int) for n in ('room_x','room_y','lerp_dx')]
class World(C.Structure):
    _fields_=[('checkpoints',C.POINTER(Checkpoint)),('count',C.c_uint),('save',Save),
              ('activations',C.c_uint),('wrap_left',C.c_uint),('wrap_right',C.c_uint),('exit',Exit),
              ('active_mask',C.c_uint32),('pending_mask',C.c_uint32)]

def boundary_reference(core):
    source=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=source.index('        else if (map.towermode)',source.index('//Right so! Screenwraping for tower:'))
    code=block(source,start)
    wrapper='''#include <vector>
#define INBOUNDS_VEC(i,v) ((i)==0)
#define GOTOROOM(x,y) do { rx=(x);ry=(y); } while(0)
struct E {int xp,yp,lerpoldxp;};
extern "C" void reference(int *v,int camera) {
struct {int ypos;bool towermode;} map={camera,true};
struct {std::vector<E> entities;int getplayer(){return 0;}} obj;
obj.entities.push_back({v[0],v[1],v[2]});int rx=0,ry=0;
if(false) {}\n'''+code+'''
v[0]=obj.entities[0].xp;v[1]=obj.entities[0].yp;v[2]=obj.entities[0].lerpoldxp;v[3]=rx;v[4]=ry;}
'''
    (OUT/'boundary.cpp').write_text(wrapper)
    subprocess.run(['c++','-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all',str(OUT/'boundary.cpp'),'-o',str(OUT/'boundary.so')],check=True)
    ref=C.CDLL(str(OUT/'boundary.so')).reference
    ref.argtypes=[C.POINTER(C.c_int),C.c_int]
    core.v6_tower_boundary.argtypes=[C.POINTER(Player),C.c_int];core.v6_tower_boundary.restype=Exit
    cases=0
    for camera in (0,499,500,501,4999,5000,5001,5368):
        for x in (-320,-16,-15,-14,-11,-10,-9,0,307,308,309,310,311,312,630):
            for y in (-20,0,1641,1822,5456):
                p=Player();p.x=x;p.y=y;p.old_x=x-3;p.old_y=y+3
                expected=(C.c_int*5)(x,y,x-3,0,0);ref(expected,camera)
                result=core.v6_tower_boundary(C.byref(p),camera)
                assert (p.x,p.y,p.old_x+result.lerp_dx,result.room_x,result.room_y)==tuple(expected)
                assert p.old_x==x-3 and p.old_y==y+3
                cases+=1
    return cases

def setup(core,index=14,saved=True):
    core.v6_tower_session_init.argtypes=[C.POINTER(Session)]+[C.c_int]*4
    core.v6_tower_session_play_world.argtypes=[C.POINTER(Session),C.POINTER(Room),C.c_uint,C.POINTER(World)]
    rows=checkpoints();bank=(Checkpoint*len(rows))()
    c=rows[index];identifier=c[3] if saved else -1
    for i,(x,y,tile,cpid) in enumerate(rows):bank[i]=Checkpoint(x,y,tile,cpid,cpid==identifier,0)
    save=Save(c[0]-4,c[1]-(2 if c[2]==20 else 7),c[2]==20,1,109,109,identifier)
    s=Session();core.v6_tower_session_init(C.byref(s),save.x,save.y,save.gravity,save.dir)
    s.camera.y=s.camera.old_y=s.player.y-120
    world=World(bank,len(rows),save,0,0,0,Exit())
    core.v6_tower_gameplay_init.argtypes=[C.POINTER(World),C.POINTER(Checkpoint),C.c_uint,C.POINTER(Save)]
    assert core.v6_tower_gameplay_init(C.byref(world),bank,len(rows),C.byref(save))
    return s,world,bank

def room_for(core):
    stream=Stream();blob=(OUT/'loadmap.v6tr').read_bytes()
    assert core.v6_tower_open(C.byref(stream),blob,len(blob))
    reader=READ(('v6_tower_tile',core));tiles=Tiles(reader,C.addressof(stream),0);room=Room()
    tiles.walls=C.cast(core.v6_tower_walls,C.c_void_p).value
    core.v6_player_tower_room(C.byref(room),C.byref(tiles))
    return room,(stream,blob,reader,tiles)

def checkpoint_masks(core):
    # Exercise cached masks through the session, including bit 31, duplicate
    # IDs and simultaneous pending contacts. An empty map isolates entities.
    import test_checkpoints
    test_checkpoints.main()
    ref=C.CDLL(str(test_checkpoints.BUILD/'checkpoint_reference.so'))
    cp=C.POINTER(Checkpoint);pp=C.POINTER(Player);sp=C.POINTER(Save)
    ref.reference_init.argtypes=[cp,C.c_uint,C.c_int,sp]
    ref.reference_update.argtypes=[pp,C.c_int,C.c_int]
    ref.reference_collide.argtypes=[pp];ref.reference_read.argtypes=[cp,sp]
    reader=READ(lambda context,x,y:0);tiles=Tiles(reader,None,0);room=Room()
    core.v6_player_tower_room(C.byref(room),C.byref(tiles))
    rng=random.Random(505167);ticks=0;high_bit=False
    for scenario in range(66):
        n=scenario%33;bank=(Checkpoint*n)();expected=(Checkpoint*n)()
        save=Save(1,2,0,1,109,109,-1);expected_save=Save()
        for i in range(n):
            bank[i]=Checkpoint(96 if scenario%2 else 64+i*8,
                1824 if scenario%3 else 1800+i*4,20+i%2,505140+i%7,0,0)
        s,w,_=setup(core);assert core.v6_tower_gameplay_init(C.byref(w),bank,n,C.byref(save))
        ref.reference_init(bank,n,-1,C.byref(save));events=0
        for tick in range(128):
            x=rng.randrange(48,330);y=rng.randrange(1780,1960)
            if tick%4==0:x=96;y=1822
            if n==32 and tick==0:x=bank[31].x-4;y=bank[31].y-2
            core.v6_player_init(C.byref(s.player),x,y,0);s.player.dir=tick%2
            s.camera.y=s.camera.old_y=y-120;s.camera.mode=0
            s.camera.seek=s.camera.seek_frames=0;s.life_timer=s.resume_delay=0;s.death_timer=-1
            events+=ref.reference_update(C.byref(s.player),109,109)
            core.v6_tower_session_play_world(C.byref(s),C.byref(room),0,C.byref(w))
            ref.reference_collide(C.byref(s.player));ref.reference_read(expected,C.byref(expected_save))
            assert bytes(bank)==bytes(expected) and bytes(w.save)==bytes(expected_save),(scenario,tick)
            assert w.activations==events
            assert w.active_mask==sum(int(c.active)<<i for i,c in enumerate(bank))
            assert w.pending_mask==sum(int(c.pending)<<i for i,c in enumerate(bank))
            high_bit|=bool((w.pending_mask|w.active_mask)&0x80000000)
            ticks+=1
    assert high_bit
    bank=(Checkpoint*33)(*[Checkpoint(i,2,20,i,1,1) for i in range(33)])
    before=bytes(w),bytes(bank)
    assert not core.v6_tower_gameplay_init(C.byref(w),bank,33,C.byref(save))
    assert (bytes(w),bytes(bank))==before
    assert not core.v6_tower_gameplay_init(C.byref(w),None,1,C.byref(save))
    assert (bytes(w),bytes(bank))==before
    return ticks

def main():
    from probe_feasibility import tower_probe
    tower_probe(OUT)
    core,ref=libraries();cases=boundary_reference(core)
    room,keep=room_for(core);s,world,bank=setup(core,saved=False)
    from tower_world_trace import inputs
    from test_player import FIELDS
    from tower_gameplay_data import ROOT as DATA_ROOT
    source=(DATA_ROOT/'desktop_version/src/Tower.cpp').read_text()
    import re
    raw=source[source.index('void towerclass::loadmap('):]
    raw=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',raw,re.S)[1]
    raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
    values=[int(v) for v in raw.split(',') if v.strip()]
    tiles=(C.c_uint16*len(values))(*values);expected=Player();activations=[]
    route=inputs()
    for tick,buttons in enumerate(route):
        # Each source step begins at the actual prior state; camera and
        # checkpoint bookkeeping do not change live movement in this route.
        ref.tower_init(C.byref(s.player),tiles,700,0)
        ref.reference_step(buttons);ref.reference_read(C.byref(expected))
        previous=world.activations
        core.v6_tower_session_play_world(C.byref(s),C.byref(room),buttons,C.byref(world))
        assert bytes(s.player)==bytes(expected),(tick,[(f,getattr(s.player,f),getattr(expected,f)) for f in FIELDS if getattr(s.player,f)!=getattr(expected,f)])
        assert s.death_timer==-1 and not world.exit.room_x
        if world.activations!=previous:activations.append((tick+1,world.save.id))
    assert activations==[(2,505147),(72,505167)]
    assert (world.save.x,world.save.y,world.save.gravity,world.save.dir)==(220,1641,0,1)
    assert bank[16].active and not bank[14].active
    for tick in range(240):
        previous=s.respawns
        core.v6_tower_session_play_world(C.byref(s),C.byref(room),0,C.byref(world))
        if s.respawns>previous:
            assert (s.player.x,s.player.y,s.player.gravity,s.player.dir)==(220,1641,0,1)
    assert s.respawns>0
    mask_ticks=checkpoint_masks(core)
    report=dict(boundary_cases=cases,source_player_route_ticks=len(route),activations=activations,
        checkpoint_mask_ticks=mask_ticks,
        recovery_ticks=240,respawns=s.respawns,
        scope='Extracted main-tower boundaries and per-step desktop movement on a normal-input checkpoint route; host checkpoint/recovery integration; no full desktop entity loop or room loads')
    (OUT/'world-tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
