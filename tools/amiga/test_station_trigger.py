#!/usr/bin/env python3
"""Frown Upside Down entry and trigger against extracted desktop methods."""
import ctypes as C
import itertools
import json
import subprocess
from test_player import ROOT,Player,block
from tower_gameplay_data import frown_room,export_frown

class Story(C.Structure):
    _fields_=[(n,C.c_int) for n in 'time_trial translator_exploring companion rescue_triggered yellow_rescued'.split()]
class Trigger(C.Structure):
    _fields_=[('active',C.c_int),('pending',C.c_int),('requests',C.c_uint)]

def main():
    out=ROOT/'build/amiga-station-trigger';out.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text();check=block(entity,entity.index('int entityclass::checktrigger('))
    game=(ROOT/'desktop_version/src/Game.cpp').read_text();start=game.index('        case 34:',game.index('case 33:'))
    dispatch=game[start:game.index('        case 35:',start)]
    station=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text();start=station.index('case rn(49,41):')
    entry=station[start:station.index('case rn(',start+5)]
    shim='''#include <SDL3/SDL.h>
#include <vector>
#include <string>
struct Ent {int rule,xp,yp,cx,cy,w,h;};
struct Block {int type,trigger;SDL_Rect rect;};
struct Help {bool intersects(SDL_Rect a,SDL_Rect b){return SDL_HasRectIntersection(&a,&b);}} help;
enum {TRIGGER=1};
struct entityclass {std::vector<Ent> entities;std::vector<Block> blocks;int checktrigger(int*);};
'''+check+'''
struct Obj {int flags[64],removed,crew,trigger;
void removetrigger(int t){removed=t;}
void createentity(int,int,int type,int,int=0){if(type==16)crew++;}
void createblock(int,int,int,int,int,int t){trigger=t;}
} obj;
struct Game {int intimetrial,translator_exploring,companion,crewstats[6];} game;
void setstate(int) {}
extern "C" int reference(int x,int y,int flag,int *out) {
entityclass entities;entities.entities.push_back({0,x,y,6,2,12,21});
entities.blocks.push_back({TRIGGER,34,{0,0,140,240}});
int index,trigger=entities.checktrigger(&index);obj.flags[10]=flag;obj.removed=0;
bool startscript=false;std::string newscript;
switch(trigger) {
'''+dispatch+'''
}
out[0]=obj.flags[10];out[1]=obj.removed;out[2]=startscript;
out[3]=newscript=="rescueyellow";return trigger;
}
constexpr int rn(int x,int y){return x+y*100;}
const short *result;std::string roomname;
extern "C" int reference_entry(int x,int y,int trial,int exploring,int companion,int flag,int rescued){
game.intimetrial=trial;game.translator_exploring=exploring;game.companion=companion;
game.crewstats[2]=rescued;obj.flags[10]=flag;obj.crew=obj.trigger=0;
switch(rn(x-62,y-64)) {
'''+entry+'''
}
return obj.crew==1 && obj.trigger==34;
}
extern "C" int reference_tile(int n){return result[n];}
'''
    (out/'reference.cpp').write_text(shim)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,'-I/opt/homebrew/include',str(out/'reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',str(ROOT/'amiga_version/station_trigger.c'),'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));ref=C.CDLL(str(out/'reference.so'))
    core.v6_station_crew_visible.argtypes=[C.c_int,C.c_int,C.POINTER(Story)]
    core.v6_station_trigger_init.argtypes=[C.POINTER(Trigger)]
    core.v6_station_trigger_enter.argtypes=[C.POINTER(Trigger),C.c_int,C.c_int,C.POINTER(Story)]
    core.v6_station_trigger_step.argtypes=[C.POINTER(Trigger),C.POINTER(Story),C.POINTER(Player)]
    core.v6_station_trigger_take.argtypes=[C.POINTER(Trigger)]
    ref.reference.argtypes=[C.c_int,C.c_int,C.c_int,C.POINTER(C.c_int)]
    ref.reference_entry.argtypes=[C.c_int]*7
    entries=contacts=0
    for x,y in itertools.product(range(100,120),repeat=2):
        for trial,exploring,companion,flag,rescued in itertools.product((0,1),(0,1),(0,2,9),(0,1),(0,1)):
            s=Story(trial,exploring,companion,flag,rescued)
            expected=ref.reference_entry(x,y,trial,exploring,companion,flag,rescued)
            assert core.v6_station_crew_visible(x,y,C.byref(s))==expected
            t=Trigger();core.v6_station_trigger_enter(C.byref(t),x,y,C.byref(s));assert t.active==expected
            entries+=1
    ref.reference_entry(111,105,0,0,0,0,0)
    room=export_frown(out);assert room==frown_room()
    assert [ref.reference_tile(n) for n in range(1200)]==room['tiles']
    for x in range(-24,141):
        for y in (-24,-23,-22,-2,0,86,105,217,237,238,239):
            for flag in (0,1):
                s=Story(0,0,0,flag,0);t=Trigger(1,0,0);p=Player();p.x=x;p.y=y
                expected=(C.c_int*4)();hit=ref.reference(x,y,flag,expected)
                made=core.v6_station_trigger_step(C.byref(t),C.byref(s),C.byref(p))
                assert made==expected[2]==expected[3] and s.rescue_triggered==expected[0]
                assert t.active==(hit==-1) and bool(t.pending)==bool(expected[2])
                assert t.requests==expected[2] and not s.yellow_rescued and not s.companion
                contacts+=1
    s=Story();t=Trigger();p=Player();p.x=42;p.y=86
    core.v6_station_trigger_init(C.byref(t));core.v6_station_trigger_enter(C.byref(t),111,105,C.byref(s))
    assert core.v6_station_trigger_step(C.byref(t),C.byref(s),C.byref(p))
    for tick in range(128):assert not core.v6_station_trigger_step(C.byref(t),C.byref(s),C.byref(p))
    for x,y in ((110,105),(111,105),(110,104),(111,105)):
        core.v6_station_trigger_enter(C.byref(t),x,y,C.byref(s));assert t.pending==1 and not t.active
    assert core.v6_station_trigger_take(C.byref(t))==1 and core.v6_station_trigger_take(C.byref(t))==0
    assert t.requests==1 and s.rescue_triggered and not s.yellow_rescued and not s.companion
    # Retained pending requests also prevent starting a second script after flag rollback.
    t.pending=1;s.rescue_triggered=0;core.v6_station_trigger_enter(C.byref(t),111,105,C.byref(s))
    before=bytes(t),bytes(s);assert not core.v6_station_trigger_step(C.byref(t),C.byref(s),C.byref(p))
    assert (bytes(t),bytes(s))==before
    for args in ((None,C.byref(s),C.byref(p)),(C.byref(t),None,C.byref(p)),(C.byref(t),C.byref(s),None)):
        assert not core.v6_station_trigger_step(*args)
    assert not core.v6_station_crew_visible(111,105,None) and not core.v6_station_trigger_take(None)
    report=dict(room_entry_cases=entries,trigger_cases=contacts,source_tiles=1200,repeat_contacts=128,
        scope='Yellow crew entry and Game trigger 34; candidate collision export, no native renderer/script/persistence admission')
    (out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS station trigger:',report)
if __name__=='__main__':main()
