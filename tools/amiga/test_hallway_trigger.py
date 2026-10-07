#!/usr/bin/env python3
"""Source trigger intersection/dispatch, one-shot state, and script export."""
import ctypes as C
import json
import subprocess
from test_player import ROOT,Player,block
from test_hallway_crew import Story
from hallway_scripts import export,scripts

class Trigger(C.Structure):
    _fields_=[('active',C.c_int),('pending',C.c_int),('requests',C.c_uint)]
def bind(core):
    core.v6_hallway_trigger_init.argtypes=[C.POINTER(Trigger)]
    core.v6_hallway_trigger_enter.argtypes=[C.POINTER(Trigger),C.c_int,C.c_int,C.POINTER(Story)]
    core.v6_hallway_trigger_step.argtypes=[C.POINTER(Trigger),C.POINTER(Story),C.POINTER(Player)]
    core.v6_hallway_trigger_take.argtypes=[C.POINTER(Trigger)]
def state(t,s,crew=1):
    return (s.rescue_triggered,s.red_rescued,s.companion,t.active,t.pending,t.requests,crew)

def main():
    out=ROOT/'build/amiga-hallway-trigger';out.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    check=block(entity,entity.index('int entityclass::checktrigger('))
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    start=game.index('        case 36:',game.index('case 35:'))
    dispatch=game[start:game.index('        case 37:',start)]
    shim='''#include <SDL3/SDL.h>
#include <vector>
#include <string>
struct Ent {int rule,xp,yp,cx,cy,w,h;};
struct Block {int type,trigger;SDL_Rect rect;};
struct Help {bool intersects(SDL_Rect a,SDL_Rect b){return SDL_HasRectIntersection(&a,&b);}} help;
enum {TRIGGER=1};
struct entityclass {std::vector<Ent> entities;std::vector<Block> blocks;int checktrigger(int*);};
'''+check+'''
struct Obj {int flags[64],removed;void removetrigger(int t){removed=t;}} obj;
void setstate(int) {}
extern "C" int reference(int x,int y,int flag,int *out) {
entityclass entities;entities.entities.push_back({0,x,y,6,2,12,21});
entities.blocks.push_back({TRIGGER,36,{208,0,32,240}});
int index,trigger=entities.checktrigger(&index);obj.flags[8]=flag;obj.removed=0;
bool startscript=false;std::string newscript;
switch(trigger) {
'''+dispatch+'''
}
out[0]=obj.flags[8];out[1]=obj.removed;out[2]=startscript;
return trigger;
}
'''
    (out/'reference.cpp').write_text(shim)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,'-I/opt/homebrew/include',str(out/'reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',*[str(ROOT/'amiga_version'/name) for name in ('hallway_trigger.c','hallway_crew.c')],'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));bind(core)
    reference=C.CDLL(str(out/'reference.so')).reference
    reference.argtypes=[C.c_int,C.c_int,C.c_int,C.POINTER(C.c_int)]
    cases=0
    for x in range(184,241):
        for y in (-24,-23,-22,-2,0,105,185,217,237,238,239):
            for flag in (0,1):
                s=Story(0,0,0,flag,0);t=Trigger(1,0,0);p=Player();p.x=x;p.y=y
                expected=(C.c_int*3)();hit=reference(x,y,flag,expected)
                made=core.v6_hallway_trigger_step(C.byref(t),C.byref(s),C.byref(p))
                assert made==expected[2] and s.rescue_triggered==expected[0]
                assert t.active==(hit==-1) and bool(t.pending)==bool(expected[2])
                assert t.requests==expected[2] and not s.red_rescued and not s.companion
                cases+=1
    # Retain the request through repeat contacts and room reloads; flag 8
    # prevents a new trigger. Taking the request is a consumer action only.
    s=Story();t=Trigger();p=Player();p.x=200;p.y=185
    core.v6_hallway_trigger_init(C.byref(t));core.v6_hallway_trigger_enter(C.byref(t),110,104,C.byref(s))
    assert core.v6_hallway_trigger_step(C.byref(t),C.byref(s),C.byref(p))
    for tick in range(128):assert not core.v6_hallway_trigger_step(C.byref(t),C.byref(s),C.byref(p))
    for x,y in ((109,104),(110,104),(108,109),(110,104)):
        core.v6_hallway_trigger_enter(C.byref(t),x,y,C.byref(s));assert t.pending==1 and not t.active
    assert core.v6_hallway_trigger_take(C.byref(t))==1
    assert core.v6_hallway_trigger_take(C.byref(t))==0 and t.requests==1
    assert s.rescue_triggered and not s.red_rescued and not s.companion
    core.v6_hallway_trigger_init(C.byref(t));assert not t.active and not t.pending and not t.requests
    values=export(out);assert json.loads((out/'hallway-scripts.json').read_text())['scripts']==values
    report=dict(source_trigger_cases=cases,repeat_contacts=128,script_lines={name:len(value['lines']) for name,value in scripts().items()},speech_boxes=len(values['rescuered']['speeches']),scope='Source trigger geometry and Game state 36 dispatch; retained handoff and validated rescue scripts, no dialogue presentation')
    (out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
