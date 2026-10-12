#!/usr/bin/env python3
"""V Stitch trigger/state and timed hint against extracted desktop methods."""
import ctypes as C
import subprocess
from test_player import ROOT,Player,block

class Trigger(C.Structure):
    _fields_=[(n,C.c_int) for n in 'active pending visible timer level mode'.split()]+[(n,C.c_uint) for n in ('contacts','hints')]

def main():
    out=ROOT/'build/amiga-vstitch-trigger';out.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    collision=block(entity,entity.index('int entityclass::checktrigger('))
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    start=game.index('        case 8:',game.index('case 7:'))
    dispatch=game[start:game.index('        case 9:',start)]
    assert 'obj.flags[13]' in dispatch and 'hascontrol' not in dispatch and 'advancetext' not in dispatch
    textbox=(ROOT/'desktop_version/src/Textbox.cpp').read_text()
    update=block(textbox,textbox.index('void textboxclass::update(void)'))
    graphics=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    assert 'textboxes[i].tm == 2 && textboxes[i].tl <= 0.5' in graphics
    station=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    start=station.index('case rn(50,43):');entry=station[start:station.index('case rn(',start+5)]
    shim='''#include <SDL3/SDL.h>
#include <vector>
#include <string>
#include <cmath>
struct Ent {int rule,xp,yp,cx,cy,w,h;};
struct Block {int type,trigger;SDL_Rect rect;};
struct Help {bool intersects(SDL_Rect a,SDL_Rect b){return SDL_HasRectIntersection(&a,&b);}} help;
enum {TRIGGER=1};
struct entityclass {std::vector<Ent> entities;std::vector<Block> blocks;int checktrigger(int*);};
'''+collision+'''
struct textboxclass {float prev_tl,tl;int tm,timer;void update();} box;
'''+update+'''
struct Obj {int flags[64],removed,trigger;
void removetrigger(int t){removed=t;}
void createentity(int,int,int,int,int){}
void createblock(int,int,int,int,int,int t){trigger=t;}
} obj;
struct Game {bool nocutscenes;} game;
struct Graphics {
int created,y,center,colour;
void createtextbox(const char*,int,int yy,int c){created++;y=yy;colour=c;box={.5f,.5f,0,0};}
void textboxprintflags(int){}
void textboxcenterx(){center++;}
void textboxtimer(int t){box.timer=t;}
void textboxtranslate(int,int){}
void textboxapplyposition(){}
} graphics;
#define TEXT_COLOUR(x) 0xaaaaaa
#define TEXTTRANSLATE_FUNCTION 0
#define PR_FONT_INTERFACE 0
int map_textbox=0;
void setstate(int){}
extern "C" int reference_contact(int x,int y){
entityclass e;e.entities.push_back({0,x,y,6,2,12,21});
e.blocks.push_back({TRIGGER,8,{0,0,112,112}});int index;
return e.checktrigger(&index)==8;
}
extern "C" void reference_dispatch(int seen,int *result){
obj.flags[13]=seen;obj.removed=0;graphics={0,0,0,0};
switch(8){
'''+dispatch+'''
}
result[0]=obj.flags[13];result[1]=obj.removed;result[2]=graphics.created;
result[3]=graphics.y;result[4]=graphics.center;result[5]=graphics.colour;
}
extern "C" void reference_tick(int *result){
box.update();result[0]=box.timer;result[1]=box.tm;
result[2]=!(box.tm==2 && box.tl<=.5f);result[3]=(int)std::lround(box.tl*10);
}
constexpr int rn(int x,int y){return x+y*100;}
const short *result;std::string roomname;
extern "C" int reference_entry(int x,int y,int disabled){
game.nocutscenes=disabled;obj.trigger=0;
switch(rn(x-62,y-64)){
'''+entry+'''
}return obj.trigger==8;
}
'''
    (out/'reference.cpp').write_text(shim)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,'-I/opt/homebrew/include',str(out/'reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',str(ROOT/'amiga_version/vstitch_trigger.c'),'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));ref=C.CDLL(str(out/'reference.so'))
    tp=C.POINTER(Trigger);ip=C.POINTER(C.c_int)
    core.v6_vstitch_trigger_init.argtypes=[tp]
    core.v6_vstitch_trigger_enter.argtypes=[tp,C.c_int,C.c_int,C.c_int]
    core.v6_vstitch_trigger_contact.argtypes=[tp,C.POINTER(Player)]
    core.v6_vstitch_trigger_dispatch.argtypes=[tp,ip]
    core.v6_vstitch_hint_tick.argtypes=[tp]
    t=Trigger();p=Player();count=0
    for x in range(-26,117):
        for y in range(-30,121):
            core.v6_vstitch_trigger_init(C.byref(t));core.v6_vstitch_trigger_enter(C.byref(t),112,107,0)
            p.x=x;p.y=y;wanted=ref.reference_contact(x,y)
            assert core.v6_vstitch_trigger_contact(C.byref(t),C.byref(p))==wanted,(x,y)
            assert t.active==1 and t.pending==wanted and t.contacts==wanted
            assert not core.v6_vstitch_trigger_contact(C.byref(t),C.byref(p))
            count+=1
    for x,y in ((112,107),(112,106),(111,107),(113,107)):
        for disabled in (0,1):
            core.v6_vstitch_trigger_enter(C.byref(t),x,y,disabled)
            assert t.active==ref.reference_entry(x,y,disabled)
    for seen in (0,1):
        core.v6_vstitch_trigger_init(C.byref(t));core.v6_vstitch_trigger_enter(C.byref(t),112,107,0)
        p.x=60;p.y=73;core.v6_vstitch_trigger_contact(C.byref(t),C.byref(p))
        # A pending trigger is not a visible hint until the state pass.
        assert t.pending and not t.visible and not t.timer
        flag=C.c_int(seen);result=(C.c_int*6)();ref.reference_dispatch(seen,result)
        assert core.v6_vstitch_trigger_dispatch(C.byref(t),C.byref(flag))==1-seen
        assert flag.value==result[0]==1 and result[1]==8 and t.hints==result[2]==1-seen
        assert not core.v6_vstitch_trigger_dispatch(C.byref(t),C.byref(flag))
        if not seen:
            assert tuple(result[3:])==(155,1,0xaaaaaa)
            states=(C.c_int*4)()
            for tick in range(65):
                ref.reference_tick(states);core.v6_vstitch_hint_tick(C.byref(t))
                assert (t.timer,t.mode,t.visible,t.level)==tuple(states),(tick,tuple(states),bytes(t))
            assert not t.visible and t.timer==0 and t.mode==2
        # Reentry rearms/removes the block but never repeats flag-13's hint.
        core.v6_vstitch_trigger_enter(C.byref(t),112,107,0)
        assert core.v6_vstitch_trigger_contact(C.byref(t),C.byref(p))
        assert not core.v6_vstitch_trigger_dispatch(C.byref(t),C.byref(flag))
    print(f'PASS V Stitch hint: {count} source trigger intersections, source room-entry gates/state-8 dispatch, 65 source textbox updates, persistent flag and reentry suppression; controls remain independent')
if __name__=='__main__':main()
