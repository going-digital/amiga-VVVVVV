#!/usr/bin/env python3
"""Yellow source AI 1 restraint, rule-7 physics, death frames and Map entry."""
import ctypes as C
import subprocess
from test_companion import Companion,bind
from test_tower_player import libraries,OUT
from test_player import ROOT,Player,Room,Terrain,block
from tower_gameplay_data import energize_room,frown_room,building_room,north_route_room

class Rest(C.Structure):
    _fields_=[('body',C.c_int32*10),('ax',C.c_int32),('pending_y',C.c_int32),
              ('tiles',C.c_void_p),('terrain',C.c_void_p),('tileset',C.c_int),('extra_row',C.c_int),('valid',C.c_uint)]

def main():
    core,_=libraries();bind(core)
    core.v6_station_companion_step.argtypes=[C.POINTER(Companion),C.POINTER(Player),C.POINTER(Room),C.c_int,C.c_int,C.c_int]
    core.v6_station_companion_step_rest.argtypes=core.v6_station_companion_step.argtypes+[C.POINTER(Rest)]
    core.v6_station_companion_enter.argtypes=[C.POINTER(Companion),C.c_int,C.c_int,C.c_int,C.POINTER(Player)]
    core.v6_station_companion_idle.argtypes=[C.POINTER(Companion),C.c_int]
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),C.POINTER(Room)]
    source=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    at=source.index('case EntityType_CREWMATE: //Crew member')
    ai=block(source,source.index('if (entities[i].state == 1)',at));ai=ai[ai.index('{')+1:-1].replace('getplayer()','obj.getplayer()').replace('entities','obj.entities')
    shim=(OUT/'tower_shim.h').read_text().replace('type == EntityType_PLAYER;', 'type == EntityType_PLAYER || type == EntityType_CREWMATE;').replace('struct Game {','struct Game { int roomx,roomy;').replace('struct mapclass {','struct mapclass { bool custommode;')
    (OUT/'station_crew_shim.h').write_text(shim)
    code=(OUT/'reference.cpp').read_text().replace('#include "tower_shim.h"','#include "station_crew_shim.h"')
    code+='\n'+block(source,source.index('void entityclass::animatehumanoidcollision('))+'''
extern "C" void crew_init(const V6Player *p,const uint16_t *tiles,int tileset) {
reference_init(p,tiles,tileset,0);obj.entities[0].rule=7;obj.entities[0].type=EntityType_CREWMATE;
}
extern "C" void crew_tick(int hero,int roomx,int roomy,int follow,int death,V6Player *out,int *frame) {
obj.entities.push_back(obj.entities[0]);obj.entities[0].xp=hero;
int i=1,k=1;auto &e=obj.entities[i];e.tile=6;game.roomx=roomx;game.roomy=roomy;game.deathseq=death;map.custommode=false;
if(follow) {
'''+ai+'''
}
if(obj.entitycollidefloor(i))e.onground=2;else --e.onground;
if(obj.entitycollideroof(i))e.onroof=2;else --e.onroof;
e.visualonground=e.onground;e.visualonroof=e.onroof;
obj.animatehumanoidcollision(i);obj.updateentitylogic(i);obj.entitymapcollision(i);
*frame=e.drawframe;obj.entities[0]=e;obj.entities.resize(1);reference_read(out);
}
'''
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    (OUT/'station_crew_reference.cpp').write_text(code)
    subprocess.run(['c++','-std=c++11',*flags,'-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),str(OUT/'station_crew_reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(OUT/'station_crew_reference.so')],check=True)
    ref=C.CDLL(str(OUT/'station_crew_reference.so'));ref.crew_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int]
    ref.crew_tick.argtypes=[C.c_int]*5+[C.POINTER(Player),C.POINTER(C.c_int)]
    ticks=0
    for desc in (energize_room(),frown_room(),dict(x=111,y=104,tiles=building_room(),tileset=2),north_route_room('yesmen')):
        tiles=(C.c_uint16*1200)(*desc['tiles']);room=Room(tiles,desc.get("tileset",0),0);terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
        for x in (42,154,155,156,320):
            for vx in (-3,0,3):
                for following in (0,1):
                    crew=Companion();core.v6_companion_init(C.byref(crew));core.v6_station_companion_idle(C.byref(crew),1)
                    crew.body.x=crew.body.old_x=x;crew.body.vx=vx*16777216;crew.following=following;crew.mood=0
                    resting=Companion.from_buffer_copy(crew);rest=Rest()
                    cached=Companion.from_buffer_copy(crew);ref.crew_init(C.byref(crew.body),tiles,desc.get("tileset",0))
                    hero=Player();expected=Player();frame=C.c_int()
                    for tick in range(240):
                        hero.x=crew.body.x+(-100,-46,-45,-6,-5,0,5,6,45,46,100)[(tick//8)%11]
                        death=30 if tick>=220 else -1
                        ref.crew_tick(hero.x,desc['x'],desc['y'],following,death,C.byref(expected),C.byref(frame))
                        core.v6_station_companion_step(C.byref(crew),C.byref(hero),C.byref(room),death,desc['x'],desc['y'])
                        room.terrain=C.pointer(terrain);core.v6_station_companion_step(C.byref(cached),C.byref(hero),C.byref(room),death,desc['x'],desc['y']);room.terrain=None
                        room.terrain=C.pointer(terrain)
                        core.v6_station_companion_step_rest(C.byref(resting),C.byref(hero),C.byref(room),death,desc['x'],desc['y'],C.byref(rest))
                        room.terrain=None
                        assert bytes(resting)==bytes(crew),(desc['x'],desc['y'],x,vx,tick,'rest cache')
                        assert bytes(cached)==bytes(crew),(desc['name'],x,vx,tick,'terrain cache')
                        for field in ('x','y','old_x','old_y','vx','vy','ay','ground','roof','dir'):
                            assert getattr(crew.body,field)==getattr(expected,field),(desc['name'],x,vx,tick,field,getattr(crew.body,field),getattr(expected,field))
                        if death>=0:assert crew.frame==frame.value,(crew.frame,frame.value)
                        ticks+=1
    desc=north_route_room('yesmen');tiles=(C.c_uint16*1200)(*desc['tiles']);room=Room(tiles,0,0)
    terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room));room.terrain=C.pointer(terrain)
    crew=Companion();hero=Player();hero.x=60;core.v6_companion_init(C.byref(crew))
    core.v6_station_companion_enter(C.byref(crew),7,112,105,C.byref(hero));resting=Companion.from_buffer_copy(crew);rest=Rest();stable=0
    for tick in range(240):
        hero.x=60 if tick<200 else 54
        if rest.valid:stable+=1
        if tick==100:rest.valid=0
        core.v6_station_companion_step(C.byref(crew),C.byref(hero),C.byref(room),-1,112,105)
        core.v6_station_companion_step_rest(C.byref(resting),C.byref(hero),C.byref(room),-1,112,105,C.byref(rest))
        assert bytes(resting)==bytes(crew),('static fixed point',tick)
    assert stable>200,stable
    # Compile the original case 7 rather than reimplementing its entry branches.
    maps=(ROOT/'desktop_version/src/Map.cpp').read_text();start=maps.index('    case 7:',maps.index('void mapclass::spawncompanion('));spawn=maps[start:maps.index('    case 8:',start)]
    wrapper='''#include <vector>
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
struct E {int xp,yp,vx,dir;};struct Obj {std::vector<E> entities;
void createentity(int x,int y,int,int){entities.push_back({x,y,0,0});}
int getcompanion(){return entities.size()-1;}} obj;
struct {int roomx,roomy;} game;
extern "C" void entry(int roomx,int roomy,int x,int vx,int dir,int *out){
int i=0;obj.entities={{x,0,vx,dir}};game.roomx=roomx;game.roomy=roomy;
switch(7){
'''+spawn+'''}
out[0]=obj.entities.size()==2;if(out[0]){auto e=obj.entities[1];out[1]=e.xp;out[2]=e.yp;out[3]=e.vx;out[4]=e.dir;}}
'''
    (OUT/'station_crew_entry.cpp').write_text(wrapper);subprocess.run(['c++',*flags,str(OUT/'station_crew_entry.cpp'),'-o',str(OUT/'station_crew_entry.so')],check=True)
    entry=C.CDLL(str(OUT/'station_crew_entry.so')).entry;entry.argtypes=[C.c_int]*5+[C.POINTER(C.c_int)];cases=0
    for rx in (109,110,111):
        for ry in (104,105,106):
            for x in (-15,0,154,155,304):
                for direction in (0,1):
                    hero=Player();hero.x=x;hero.dir=direction;hero.vx=(3 if direction else -3)*16777216
                    crew=Companion();core.v6_companion_init(C.byref(crew));core.v6_station_companion_enter(C.byref(crew),7,rx,ry,C.byref(hero));expected=(C.c_int*5)();entry(rx,ry,x,hero.vx,direction,expected)
                    assert crew.visible==expected[0]
                    if crew.visible:assert (crew.body.x,crew.body.y,crew.body.vx,crew.body.dir)==tuple(expected)[1:] and crew.body.gravity==1
                    cases+=1
    print(f'PASS station companion: {ticks} source rule-7 AI/physics ticks and cached matches, death frames, {cases} original Map entry cases')
if __name__=='__main__':main()
