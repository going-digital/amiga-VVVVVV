#!/usr/bin/env python3
"""Bounded tower/hallway loads, live crossings and remote checkpoint returns."""
import ctypes as C
import json
import re
from test_player import FIELDS
from test_tower_world import *
from tower_gameplay_data import hallway_rooms
from pack_rooms import encode
from test_teleporter import Teleporter,Region
class RouteRoom(C.Structure):
    _fields_=[('x',C.c_int),('y',C.c_int),('packed',C.POINTER(C.c_uint8)),
              ('bytes',C.c_size_t),('checkpoints',C.POINTER(Checkpoint)),('count',C.c_uint),('decoded',C.POINTER(C.c_uint16)),('teleporter',C.POINTER(Teleporter))]
class Route(C.Structure):
    _fields_=[('session',C.POINTER(Session)),('world',C.POINTER(World)),
              ('rooms',C.POINTER(RouteRoom)),('count',C.c_uint),('index',C.c_uint),
              ('transitions',C.c_uint),('returns',C.c_uint),('error',C.c_uint),
              ('tower',C.POINTER(Tiles)),('room',Room),('tiles',C.c_uint16*1200),('tele_region',Region),('tele_events',C.c_uint)]
def route_setup(core,index=0):
    room,keep=room_for(core);s,w,bank=setup(core,index=index)
    s.camera.y=s.camera.old_y=max(0,min(5368,s.player.y-120))
    rooms=(RouteRoom*4)();payloads=[];banks=[]
    rooms[0]=RouteRoom(109,109,None,0,bank,len(bank))
    rooms[1]=RouteRoom(109,104,None,0,bank,len(bank))
    for i,desc in enumerate(hallway_rooms()):
        packed=encode(desc['tiles']);data=(C.c_uint8*len(packed)).from_buffer_copy(packed)
        cp=(Checkpoint*1)(Checkpoint(*desc['checkpoint'],0,0))
        rooms[i+2]=RouteRoom(desc['x'],desc['y'],data,len(data),cp,1)
        payloads.append(data);banks.append(cp)
    core.v6_tower_route_init.argtypes=[C.POINTER(Route),C.POINTER(Session),C.POINTER(World),
        C.POINTER(RouteRoom),C.c_uint,C.c_int,C.c_int,C.POINTER(Tiles)]
    core.v6_tower_route_load.argtypes=[C.POINTER(Route),C.c_int,C.c_int,C.c_int]
    core.v6_tower_route_step.argtypes=[C.POINTER(Route),C.c_uint]
    route=Route();assert core.v6_tower_route_init(C.byref(route),C.byref(s),C.byref(w),rooms,4,109,109,C.byref(keep[3]))
    return route,s,w,(keep,bank,rooms,payloads,banks)

def entry_reference(core):
    source=(ROOT/'desktop_version/src/Map.cpp').read_text()
    start=source.index('        if (t == 3)',source.index('void mapclass::loadlevel('))
    entry=block(source,start)
    start=source.index('    if (INBOUNDS_VEC(player_idx, obj.entities))',source.index('void mapclass::gotoroom('))
    history=block(source,start)
    wrapper='''#include <vector>
#define INBOUNDS_VEC(i,v) ((i)==0)
struct entclass { int xp,yp,oldxp,oldyp,lerpoldxp,lerpoldyp,vx,vy; };
struct Obj {std::vector<entclass> entities;int getplayer(){return 0;}} obj;
struct Bg {int colstate;};struct Graphics {Bg towerbg;} graphics;
void setbgobjlerp(Bg&) {}
extern "C" void reference_entry(int *v,int ry) {
obj.entities.resize(1);obj.entities[0]={v[0],v[1],0,0,0,0,0,0};
int t=3,ypos=0,oldypos=0,cameramode=7,colsuperstate=1;
'''+entry+'''\nint player_idx=0;\n'''+history+'''
v[0]=obj.entities[0].xp;v[1]=obj.entities[0].yp;
v[2]=obj.entities[0].oldxp;v[3]=obj.entities[0].oldyp;
v[4]=ypos;v[5]=oldypos;v[6]=cameramode;}
'''
    path=OUT/'entry_reference.cpp';path.write_text(wrapper)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-fsanitize=undefined',
        '-fno-sanitize-recover=all',str(path),'-o',str(OUT/'entry_reference.so')],check=True)
    reference=C.CDLL(str(OUT/'entry_reference.so')).reference_entry
    reference.argtypes=[C.POINTER(C.c_int),C.c_int]
    r,s,w,keep=route_setup(core);cases=0
    for ry in (104,109):
        for x in (-16,-9,0,140,304,320):
            for y in (-20,0,81,120,238):
                assert core.v6_tower_route_load(C.byref(r),108,109,0)
                s.player.x=x;s.player.y=y;s.player.old_x=-123;s.player.old_y=-456
                s.player.vx=3*16777216;s.player.vy=-2*16777216
                expected=(C.c_int*7)(x,y,0,0,0,0,0);reference(expected,ry)
                assert core.v6_tower_route_load(C.byref(r),109,ry,0)
                got=(s.player.x,s.player.y,s.player.old_x,s.player.old_y,
                    s.camera.y,s.camera.old_y,s.camera.mode)
                assert got==tuple(expected),(x,y,ry,got,tuple(expected))
                assert s.player.vx==3*16777216 and s.player.vy==-2*16777216
                cases+=1
    return cases
def upper_traversal(core,ref):
    # Full input-only route: a source-map spike, rather than an injected death,
    # must drive the return to Seeing Red's saved checkpoint.
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text()
    raw=source[source.index('void towerclass::loadmap('):]
    raw=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',raw,re.S)[1]
    raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
    values=[int(v) for v in raw.split(',') if v.strip()]
    data=(C.c_uint16*len(values))(*values)
    r,s,w,keep=route_setup(core,index=14)
    core.v6_tower_session_init(C.byref(s),280,80,0,1)
    crossings=[];deaths=[]
    for tick in range(128):
        previous=r.index;previous_deaths=s.deaths
        assert core.v6_tower_route_step(C.byref(r),2 if tick<8 else 1 if tick<58 else 0)
        if previous!=r.index:crossings.append((tick+1,r.index))
        if previous_deaths!=s.deaths:
            deaths.append(tick+1)
            ref.tower_init(C.byref(s.player),data,len(values)//40,0)
            assert ref.tower_hurt()==1
            assert (s.player.x,s.player.y)==(96,193)
        if tick==8:assert w.save.id==50520 and (w.save.room_x,w.save.room_y)==(110,104)
    assert crossings==[(7,3),(14,1),(85,3)] and deaths==[56]
    assert r.returns==1 and s.respawns==1 and not r.error
    assert (s.player.x,s.player.y,s.player.gravity)==(12,105,0)
    return dict(crossings=crossings,death_ticks=deaths,remote_returns=r.returns)

def main():
    from probe_feasibility import tower_probe
    tower_probe(OUT);core,ref=libraries();r,s,w,keep=route_setup(core)
    crossings=[]
    for tick in range(160):
        previous=r.index
        buttons=1 if tick<12 else 2 if tick<40 else 0
        assert core.v6_tower_route_step(C.byref(r),buttons),(tick,r.index,s.player.x,s.player.y)
        if r.index!=previous:crossings.append((tick+1,r.index,s.player.x,s.player.y))
    print('Crossings',crossings,'respawns',s.respawns)
    assert any(c[1]==2 for c in crossings) and any(c[1]==0 for c in crossings)
    # Both literal hallway maps decode unchanged, use ordinary tileset 2, and
    # reinitialize checkpoint entities from the global saved ID.
    for index,desc in enumerate(hallway_rooms()):
        assert core.v6_tower_route_load(C.byref(r),desc['x'],desc['y'],0)
        assert list(r.tiles)==desc['tiles'] and r.room.tileset==2 and not r.room.extra_row
        assert w.count==1 and w.checkpoints[0].id==desc['checkpoint'][3]
        # Remote tower save is retained while in either hallway.
        assert (w.save.room_x,w.save.room_y)==(109,109)
        s.death_timer=30
        for tick in range(30):assert core.v6_tower_route_step(C.byref(r),0)
        assert r.index==0 and s.life_timer==10 and s.invisible
        assert (s.player.x,s.player.y,s.player.gravity,s.player.dir)==(w.save.x,w.save.y,w.save.gravity,w.save.dir)
        assert s.camera.y==max(0,min(5368,w.save.y-120))
    remote_returns=r.returns
    before=r.index,bytes(w)
    assert not core.v6_tower_route_load(C.byref(r),999,999,0)
    assert (r.index,bytes(w))==before
    # Source-extracted ordinary player methods run against each hallway's
    # actual terrain, rather than the tower's wrapped full-tile spike probes.
    ref.ordinary_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16)]
    movement_ticks=0
    for desc in hallway_rooms():
        assert core.v6_tower_route_load(C.byref(r),desc['x'],desc['y'],0)
        for x in (-8,48,144,280,312):
            for y in (32,80,128,192):
                for gravity in (0,1):
                    p=Player();expected=Player();core.v6_player_init(C.byref(p),x,y,gravity)
                    ref.ordinary_init(C.byref(p),r.room.tiles)
                    for tick in range(48):
                        buttons=(1 if tick<16 else 2 if tick<32 else 0)|(4 if tick%11<3 else 0)
                        ref.reference_step(buttons);core.v6_player_step(C.byref(p),C.byref(r.room),buttons)
                        ref.reference_read(C.byref(expected))
                        assert bytes(p)==bytes(expected),(desc['x'],x,y,gravity,tick,[(f,getattr(p,f),getattr(expected,f)) for f in FIELDS if getattr(p,f)!=getattr(expected,f)])
                        assert core.v6_player_hurt(C.byref(p),C.byref(r.room))==ref.reference_hurt()
                        movement_ticks+=1
    # Predecoded resident views produce the same crossings without a full
    # room decode in the frame loop. Invalid packets must retain live terrain.
    r,s,w,keep=route_setup(core);resident=[]
    for i,desc in enumerate(hallway_rooms()):
        array=(C.c_uint16*1200)(*desc['tiles']);resident.append(array)
        keep[2][i+2].decoded=array
    for tick in range(160):
        assert core.v6_tower_route_step(C.byref(r),1 if tick<12 else 2 if tick<40 else 0)
    assert r.index==0 and r.transitions==2
    assert core.v6_tower_route_load(C.byref(r),108,109,0)
    bad=(C.c_uint8*4)(128,0,0,0)
    keep[2][3].packed=bad;keep[2][3].bytes=4
    keep[2][3].decoded=None
    before=bytes(r),bytes(w),list(r.room.tiles[:1200])
    assert not core.v6_tower_route_load(C.byref(r),110,104,0)
    assert (bytes(r),bytes(w),list(r.room.tiles[:1200]))==before
    # Save in each hallway, die there without rebuilding its entity bank,
    # then return to that save after dying in the tower. Room identity must
    # survive entry without activation of a different checkpoint.
    for desc in hallway_rooms():
        r,s,w,keep=route_setup(core)
        assert core.v6_tower_route_load(C.byref(r),desc['x'],desc['y'],0)
        c=w.checkpoints[0];s.player.x=c.x-4;s.player.y=c.y-7
        s.player.vx=s.player.vy=s.player.ay=0;s.player.gravity=0
        for tick in range(2):assert core.v6_tower_route_step(C.byref(r),0)
        assert w.save.id==c.id and (w.save.room_x,w.save.room_y)==(desc['x'],desc['y'])
        transitions=r.transitions;s.death_timer=30
        for tick in range(30):assert core.v6_tower_route_step(C.byref(r),0)
        assert r.transitions==transitions and not r.returns
        assert (s.player.x,s.player.y)==(w.save.x,w.save.y)
        assert core.v6_tower_route_load(C.byref(r),109,desc['y'],0)
        s.death_timer=30;s.life_timer=0
        for tick in range(30):assert core.v6_tower_route_step(C.byref(r),0)
        assert (r.rooms[r.index].x,r.rooms[r.index].y)==(desc['x'],desc['y'])
        assert (s.player.x,s.player.y,s.player.gravity,s.player.dir)==(w.save.x,w.save.y,w.save.gravity,w.save.dir)
        assert s.life_timer==10 and r.returns==1 and not s.camera.y
    upper=upper_traversal(core,ref)
    entries=entry_reference(core)
    report=dict(crossings=crossings,remote_returns=remote_returns,source_entry_cases=entries,
        source_hallway_movement_ticks=movement_ticks,upper_natural_route=upper,
        scope='Literal hallway terrain/checkpoints, normal-input lower entrance crossing, saved tower returns; crew/scripts and full desktop loop excluded')
    (OUT/'route-tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
