#!/usr/bin/env python3
"""Bounded Vermilion AI/physics/room entry against extracted desktop methods."""
import ctypes as C
import json
import subprocess
import random
import struct
from test_tower_player import libraries,OUT
from test_player import ROOT,Player,Room,Terrain,FIELDS,block
from tower_gameplay_data import hallway_rooms

class Motion(C.Structure):
    _fields_=[('ax',C.c_int32),('pending_y',C.c_int)]
class Animation(C.Structure):
    _fields_=[('delay',C.c_int),('walk',C.c_int)]
class Companion(C.Structure):
    _fields_=[('body',Player),('motion',Motion),('animation',Animation),
        *[(name,C.c_int) for name in ('visible','following','mood','frame')],
        ('spawns',C.c_uint),('steps',C.c_uint),('follow_steps',C.c_uint)]
def bind(core):
    core.v6_companion_init.argtypes=[C.POINTER(Companion)]
    core.v6_companion_idle.argtypes=[C.POINTER(Companion),C.c_int]
    core.v6_companion_enter.argtypes=[C.POINTER(Companion),C.c_int,C.c_int,C.c_int,C.POINTER(Player)]
    core.v6_companion_step.argtypes=[C.POINTER(Companion),C.POINTER(Player),C.POINTER(Room),C.c_int]
def state(c):
    return tuple(v&0xffffffff for v in (c.visible,c.following,c.mood,c.frame,c.body.x,c.body.y,c.body.vx,c.body.vy,c.body.dir,c.animation.delay,c.animation.walk,c.spawns,c.steps,c.follow_steps))
def main():
    core,_=libraries();bind(core)
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),C.POINTER(Room)]
    source=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    ai=block(source,source.index('else if (entities[i].state == 10)'))
    ai=ai[ai.index('{')+1:-1].replace('getplayer()','obj.getplayer()').replace('entities','obj.entities')
    animate=block(source,source.index('void entityclass::animatehumanoidcollision('))
    code=(OUT/'reference.cpp').read_text()+ '\n'+animate+'''
extern "C" void crew_init(const V6Player *p,const uint16_t *tiles) {
ordinary_init(p,tiles);obj.entities[0].rule=6;obj.entities[0].type=EntityType_CREWMATE;
}
extern "C" void crew_tick(int hero,int follow,int mood,int death,V6Player *out,int *frame,int *delay,int *walk) {
obj.entities.push_back(obj.entities[0]);obj.entities[0].xp=hero;
int i=1;auto &e=obj.entities[i];e.tile=mood?144:0;game.deathseq=death;
if(follow) {
'''+ai+'''
}
if(obj.entitycollidefloor(i))e.onground=2;else --e.onground;
if(obj.entitycollideroof(i))e.onroof=2;else --e.onroof;
e.visualonground=e.onground;e.visualonroof=e.onroof;
obj.animatehumanoidcollision(i);obj.updateentitylogic(i);obj.entitymapcollision(i);
*frame=e.drawframe;*delay=e.collisionframedelay;*walk=e.collisionwalkingframe;
obj.entities[0]=e;obj.entities.resize(1);reference_read(out);
}
'''
    code+='\nextern "C" int crew_wall(int x,int y,int dx,int dy){return obj.checkwall(false,SDL_Rect{x+6,y+2,12,21},dx,dy,6,true,false); }\n'
    shim=(OUT/'tower_shim.h').read_text().replace('type == EntityType_PLAYER;','type == EntityType_PLAYER || type == EntityType_CREWMATE;')
    (OUT/'crew_shim.h').write_text(shim)
    code=code.replace('#include "tower_shim.h"','#include "crew_shim.h"')
    (OUT/'crew_reference.cpp').write_text(code)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++','-std=c++11',*flags,'-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),str(OUT/'crew_reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(OUT/'crew_reference.so')],check=True)
    ref=C.CDLL(str(OUT/'crew_reference.so'))
    ref.crew_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16)]
    ref.crew_tick.argtypes=[C.c_int,C.c_int,C.c_int,C.c_int,C.POINTER(Player),C.POINTER(C.c_int),C.POINTER(C.c_int),C.POINTER(C.c_int)]
    ticks=0
    for desc in hallway_rooms():
        tiles=(C.c_uint16*1200)(*desc['tiles']);room=Room(tiles,2,0)
        terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
        for x,y in ((264,185),(100,185),(10,80),(290,80)):
            for following in (0,1):
                c=Companion();core.v6_companion_init(C.byref(c));core.v6_companion_idle(C.byref(c),1)
                c.body.x=c.body.old_x=x;c.body.y=c.body.old_y=y;c.motion.pending_y=y
                c.following=following;c.mood=not following
                cached=Companion.from_buffer_copy(c)
                ref.crew_init(C.byref(c.body),tiles)
                hero=Player();expected=Player();frame=C.c_int();delay=C.c_int();walk=C.c_int()
                for tick in range(240):
                    offsets=(-46,-45,-6,-5,0,5,6,45,46,100,-100)
                    hero.x=c.body.x+offsets[(tick//8)%len(offsets)]
                    death=30 if tick>=220 else -1
                    ref.crew_tick(hero.x,following,c.mood,death,C.byref(expected),C.byref(frame),C.byref(delay),C.byref(walk))
                    core.v6_companion_step(C.byref(c),C.byref(hero),C.byref(room),death)
                    room.terrain=C.pointer(terrain)
                    core.v6_companion_step(C.byref(cached),C.byref(hero),C.byref(room),death)
                    room.terrain=None
                    assert bytes(cached)==bytes(c),(tick,"cached companion")
                    # Source reference_read also exports player input fields;
                    # crew never changes those and gravity is downward.
                    for name in ('x','y','old_x','old_y','vx','vy','ay','ground','roof','dir'):
                        assert getattr(c.body,name)==getattr(expected,name),(tick,name,getattr(c.body,name),getattr(expected,name))
                    assert (c.frame,c.animation.delay,c.animation.walk)==(frame.value,delay.value,walk.value),(tick,c.frame,frame.value)
                    ticks+=1
    # Source Map::spawncompanion case 9 is compiled with an independent small
    # environment; compare every branch including the strict x<20 condition.
    maps=(ROOT/'desktop_version/src/Map.cpp').read_text()
    start=maps.index('    case 9:',maps.index('void mapclass::spawncompanion('));end=maps.index('    case 10:',start)
    spawn=maps[start:end]
    wrapper='''#include <vector>
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
struct E {int xp,yp,vx,dir;};struct Obj {std::vector<E> entities;
void createentity(int x,int y,int,int,int,int){entities.push_back({x,y,0,0});}
int getcompanion(){return entities.size()-1;}} obj;
struct {int roomx;} game;
extern "C" void entry(int tower,int roomx,int x,int vx,int dir,int *out){
bool towermode=tower;int i=0;obj.entities={{x,0,vx,dir}};game.roomx=roomx;
switch(9){
'''+spawn+'''}
out[0]=obj.entities.size()==2;if(out[0]){auto e=obj.entities[1];out[1]=e.xp;out[2]=e.yp;out[3]=e.vx;out[4]=e.dir;}}
'''
    (OUT/'crew_entry.cpp').write_text(wrapper)
    subprocess.run(['c++',*flags,str(OUT/'crew_entry.cpp'),'-o',str(OUT/'crew_entry.so')],check=True)
    entry=C.CDLL(str(OUT/'crew_entry.so')).entry;entry.argtypes=[C.c_int]*5+[C.POINTER(C.c_int)]
    cases=0
    for tower in (0,1):
        for roomx in (108,109,110):
            for x in (-15,0,19,20,100,304):
                for direction in (0,1):
                    hero=Player();hero.x=x;hero.dir=direction;hero.vx=(-3 if direction==0 else 3)*16777216
                    c=Companion();core.v6_companion_init(C.byref(c))
                    core.v6_companion_enter(C.byref(c),9,tower,roomx,C.byref(hero));expected=(C.c_int*5)()
                    entry(tower,roomx,x,hero.vx,direction,expected)
                    assert c.visible==expected[0]
                    if c.visible:assert (c.body.x,c.body.y,c.body.vx,c.body.dir)==tuple(expected)[1:]
                    cases+=1
    # Independently check the bounded 32-bit position fast path against an
    # IEEE binary32 sum, with signed values and rounding at pixel boundaries.
    position_code='#include "'+str(ROOT/'amiga_version/player.c')+'"\nint position_test(int x,int32_t v){return position(x,v); }\nint walls_test(const V6Room *r,int x,int y,int32_t dx,int32_t dy){return wall(r,x,y,dx,dy); }\n'
    (OUT/'crew_position.c').write_text(position_code)
    subprocess.run(['cc',*flags,'-I'+str(ROOT/'amiga_version'),str(OUT/'crew_position.c'),str(ROOT/'amiga_version/blocks.c'),'-o',str(OUT/'crew_position.so')],check=True)
    position_lib=C.CDLL(str(OUT/'crew_position.so'))
    position=position_lib.position_test;position.argtypes=[C.c_int,C.c_int32]
    walls=position_lib.walls_test;walls.argtypes=[C.POINTER(Room),C.c_int,C.c_int,C.c_int32,C.c_int32]
    ref.crew_wall.argtypes=[C.c_int]*4
    def single(v):return struct.unpack('f',struct.pack('f',v))[0]
    rng=random.Random(0x6c726577);position_cases=0
    coordinates=(-16385,-16384,-8192,-320,-256,-128,-1,0,1,127,128,255,256,320,5368,8192,16384,16385)
    velocities=[0,1,-1,16777215,-16777215,16777216,-16777216,16777217,-16777217,10*16777216,-10*16777216]
    for x in coordinates:
        for v in velocities:
            v=int(single(v/16777216)*16777216)
            assert position(x,v)==int(single(x+v/16777216)),(x,v)
            position_cases+=1
    for trial in range(100000):
        x=rng.randint(-16384,16384);v=int(single(rng.uniform(-10,10))*16777216)
        assert position(x,v)==int(single(x+v/16777216)),(x,v)
        position_cases+=1
    collision_cases=0
    for scene in range(80):
        data=[rng.choice((0,0,0,0,12,14,15,16,17,27)) for cell in range(1200)]
        tiles=(C.c_uint16*1200)(*data);room=Room(tiles,2,0);terrain=Terrain()
        core.v6_terrain_build(C.byref(terrain),C.byref(room));body=Player()
        ref.crew_init(C.byref(body),tiles)
        for trial in range(250):
            x=rng.randint(-40,350);y=rng.randint(-40,265)
            dx,dy=rng.choice(((0,0),(-1,0),(1,0),(0,-1),(0,1)))
            expected=ref.crew_wall(x,y,dx,dy)
            room.terrain=None;assert walls(C.byref(room),x,y,dx*16777216,dy*16777216)==expected,(scene,x,y,dx,dy,'uncached')
            room.terrain=C.pointer(terrain);assert walls(C.byref(room),x,y,dx*16777216,dy*16777216)==expected,(scene,x,y,dx,dy,'cached')
            collision_cases+=1
    report=dict(source_movement_ticks=ticks,cached_movement_ticks=ticks,source_entry_cases=cases,binary32_position_cases=position_cases,source_cached_collision_cases=collision_cases,scope='Extracted source AI 10, crew rule 6 physics/collision animation and Map companion 9 entry; bounded static hallway terrain')
    (OUT/'companion-tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
