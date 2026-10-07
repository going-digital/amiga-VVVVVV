#!/usr/bin/env python3
"""Source Energize room and Script.cpp handoff, before arrival presentation."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD,Player,Room,build_libraries,FIELDS
from test_building_route import fixture,buttons
from test_tower_route import libraries,RouteRoom,Route,encode
from test_teleporter import Teleporter
from tower_gameplay_data import energize_room

def reference():
    source=(ROOT/'desktop_version/src/Script.cpp').read_text()
    start=source.index('void scriptclass::teleport(void)')
    prefix=source[start:source.index('    if(game.teleport_to_x==0',start)]+'}\n'
    shim='''#include <string>
#include <vector>
struct Entity {int xp,yp,lerpoldxp,lerpoldyp,dir,para,state;};
struct Obj {std::vector<Entity> entities;int getplayer(){return 0;}int getteleporter(){return 1;}} obj;
struct Game {int companion,teleport_to_x,teleport_to_y,gravitycontrol,teleport_to_new_area,
 savepoint,savex,savey,savegc,saverx,savery,savedir,roomx,roomy;std::string teleportscript;} game;
struct Map {void gotoroom(int x,int y){game.roomx=x;game.roomy=y;}} map;
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
struct scriptclass {int i,j;void teleport(void);};
'''+prefix+'''
extern "C" void stage(int *out,int tx,int ty,int ex,int ey,int id,int dir) {
obj.entities={{30,40,30,40,dir,0,0},{ex,ey,0,0,0,id,0}};
game.teleportscript="";game.teleport_to_x=tx-100;game.teleport_to_y=ty-100;
scriptclass script;script.teleport();
int a[]={obj.entities[0].xp,obj.entities[0].yp,obj.entities[0].lerpoldxp,obj.entities[0].lerpoldyp,
 game.gravitycontrol,game.savex,game.savey,game.savegc,game.savedir,game.saverx,game.savery,game.savepoint,obj.entities[1].state};
for(unsigned n=0;n<13;++n)out[n]=a[n];
}
'''
    path=BUILD/'travel-reference.cpp';path.write_text(shim)
    subprocess.run(['c++','-std=c++11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(path),'-o',str(BUILD/'travel-reference.so')],check=True)
    lib=C.CDLL(str(BUILD/'travel-reference.so'))
    lib.stage.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*6
    return lib

def main():
    core,_=libraries();ref=reference();desc=energize_room()
    r,s,w,building,keep=fixture(core)
    rooms=(RouteRoom*6)()
    for i in range(5):rooms[i]=keep[1][i]
    tiles=(C.c_uint16*1200)(*desc['tiles']);packed=encode(desc['tiles'])
    data=(C.c_uint8*len(packed)).from_buffer_copy(packed);tele=Teleporter(*desc['teleporter'],1,1,0)
    rooms[5]=RouteRoom(110,105,data,len(data),None,0,tiles,C.pointer(tele),0)
    r.rooms=rooms;r.count=6
    core.v6_tower_route_teleport.argtypes=[C.POINTER(Route),C.c_int,C.c_int]
    for tick in range(42):assert core.v6_tower_route_step(C.byref(r),buttons(tick))
    assert r.index==4 and building.tile==2
    def snapshot():return bytes(r),bytes(s),bytes(w),bytes(building),bytes(tele)
    # Unknown, tower, same room, no entity, malformed packed data, invalid
    # tileset, invalid checkpoint bank and noncanonical teleporter reject first.
    for x,y in ((119,119),(109,109),(111,104),(110,104)):
        before=snapshot();assert not core.v6_tower_route_teleport(C.byref(r),x,y) and snapshot()==before
    bad=(C.c_uint8*4)(128,0,0,0)
    for field,value in (('teleporter',None),('decoded',None),('tileset',3),('count',33)):
        old=getattr(rooms[5],field);setattr(rooms[5],field,value)
        if field=='decoded':rooms[5].packed=bad;rooms[5].bytes=4
        before=snapshot();result=core.v6_tower_route_teleport(C.byref(r),110,105)
        assert not result and snapshot()==before,(field,result)
        if field=='teleporter':rooms[5].teleporter=C.pointer(tele)
        elif field=='decoded':rooms[5].decoded=tiles
        else:setattr(rooms[5],field,old)
        rooms[5].packed=data;rooms[5].bytes=len(data)
    for field,value in (('x',277),('y',197),('id',-1)):
        old=getattr(tele,field);setattr(tele,field,value);before=snapshot()
        assert not core.v6_tower_route_teleport(C.byref(r),110,105) and snapshot()==before
        setattr(tele,field,old)
    s.death_timer=10;before=snapshot()
    assert not core.v6_tower_route_teleport(C.byref(r),110,105) and snapshot()==before
    s.death_timer=-1
    # Compare the actual source room-change/save prefix in both directions,
    # with packed decoding and immutable decoded collision views.
    cases=0
    for decoded in (False,True):
        rooms[5].decoded=tiles if decoded else None
        for direction in (0,1):
            for destination in (5,4):
                if r.index==destination:
                    other=4 if destination==5 else 5
                    assert core.v6_tower_route_load(C.byref(r),rooms[other].x,rooms[other].y,0)
                s.player.dir=direction;s.player.vx=s.player.vy=0;s.death_timer=-1
                s.player.gravity=1
                target=rooms[destination];t=tele if destination==5 else building
                expected=(C.c_int*13)();ref.stage(expected,target.x,target.y,t.x,t.y,t.id,direction)
                activations=w.activations
                assert core.v6_tower_route_teleport(C.byref(r),target.x,target.y),(decoded,direction,destination,r.index,r.error,s.death_timer,target.tileset,t.x,t.y,t.id)
                got=(s.player.x,s.player.y,s.player.old_x,s.player.old_y,s.player.gravity,
                     w.save.x,w.save.y,w.save.gravity,w.save.dir,w.save.room_x,w.save.room_y,w.save.id,t.state)
                assert got==tuple(expected),(got,tuple(expected))
                assert r.room.tileset==target.tileset and s.motion.pending_y==110
                assert (s.save_x,s.save_y,s.save_gravity,s.save_dir)==(w.save.x,w.save.y,0,direction)
                assert not r.tele_region.active and not r.tele_events and t.tile==1
                assert core.v6_tower_route_step(C.byref(r),0)
                assert t.tile==6 and t.state==0 and t.onentity==0 and r.tele_region.active
                assert not r.tele_events and w.activations==activations
                cases+=1
    # Source special spawn and fractional velocities survive the room-change
    # stage; visual arrival states will overwrite them later.
    assert core.v6_tower_route_load(C.byref(r),111,104,0)
    rooms[5].x=rooms[5].y=117;s.death_timer=-1;s.player.dir=0
    s.player.vx=8388608;s.player.vy=-8388608;s.player.ay=123
    expected=(C.c_int*13)();ref.stage(expected,117,117,tele.x,tele.y,tele.id,0)
    assert core.v6_tower_route_teleport(C.byref(r),117,117)
    got=(s.player.x,s.player.y,s.player.old_x,s.player.old_y,s.player.gravity,
        w.save.x,w.save.y,w.save.gravity,w.save.dir,w.save.room_x,w.save.room_y,w.save.id,tele.state)
    assert got==tuple(expected) and (s.player.vx,s.player.vy,s.player.ay)==(8388608,-8388608,123)
    cases+=1
    # Real Energize collision against the source player methods for both
    # gravities; tiles >=80 are solid in tileset 0, not the tower's tileset 2.
    physics,original,_=build_libraries();steps=0
    room=Room(tiles,0,0)
    for gravity in (0,1):
        p=Player();expected_p=Player();physics.v6_player_init(C.byref(p),80,112,gravity)
        original.reference_init(C.byref(p),tiles,0,0)
        for tick in range(240):
            input=0 if tick<80 else 2 if tick<120 else 1 if tick<160 else 4 if tick==180 else 0
            physics.v6_player_step(C.byref(p),C.byref(room),input);original.reference_step(input)
            original.reference_read(C.byref(expected_p))
            assert all(getattr(p,f)==getattr(expected_p,f) for f in FIELDS),(gravity,tick)
            steps+=1
    print(f'PASS Energize travel staging: {cases} extracted Script.cpp handoffs, silent state-2 arrival, transactional rejection and {steps} source collision ticks; renderer/effects remain pending')
if __name__=='__main__':main()
