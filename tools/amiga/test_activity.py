#!/usr/bin/env python3
"""Original activity selection/input guards and delayed terminal highlighting."""
import ctypes as C
import random
import subprocess
from test_player import ROOT, BUILD, Player, DynamicBlock, block

class Signals(C.Structure):
    _fields_=[(n,C.c_int) for n in 'pressed control dying life script_running teleporter_ready'.split()]
class Result(C.Structure):
    _fields_=[('action',C.c_uint),*[(n,C.c_int) for n in 'consumed index script'.split()]]
class Terminal(C.Structure):
    _fields_=[(n,C.c_int) for n in 'x y tile parameter state onentity active'.split()]

def reference_source():
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    inp=(ROOT/'desktop_version/src/Input.cpp').read_text()
    methods='\n'.join(block(entity,entity.index(start)) for start in (
        'int entityclass::checkactivity(void)', 'void entityclass::disableblock(',
        'bool entityclass::entitycollide(', 'bool entityclass::checkblocks('))
    guard=inp[inp.index('if (game.hascontrol && game.deathseq == -1 && game.lifeseq <= 5)'):]
    guard=guard[:guard.index('{')]
    tele=inp[inp.index('if (game.activetele && game.readytotele > 20 &&'):]
    tele=tele[:tele.index('{')]
    stationary=inp[inp.index('if(int(SDL_fabsf(obj.entities[ie].vx))<=1 &&'):]
    stationary=stationary[:stationary.index('{')]
    activity=block(inp,inp.index('else if (INBOUNDS_VEC(game.activeactivity, obj.blocks))'))
    create=entity[entity.index('case 20: //Terminal'):entity.index('case 22:',entity.index('case 20: //Terminal'))]
    contact=entity[entity.index('case 3:   //Entity to entity'):entity.index('case 4:   //Person vs horizontal line!')]
    tick=entity[entity.index('case EntityType_TERMINAL: //Terminals'):entity.index('case EntityType_SUPERCREWMATE: //Super Crew member')]
    prefix=r'''
#include <SDL3/SDL.h>
#include <vector>
#include <string>
#include "activity.h"
#include "terminal.h"
#define INBOUNDS_VEC(i,v) ((i)>=0 && (size_t)(i)<(v).size())
#define vlog_error(...) ((void)0)
enum {BLOCK=0,DIRECTIONAL=3,SAFE=4,ACTIVITY=5,EntityType_TERMINAL=20,EntityColour_INACTIVE_ENTITY=0,EntityColour_ACTIVE_ENTITY=1,Sound_TERMINALTOUCH=1};
struct blockclass {int type,trigger;SDL_Rect rect;int wp,hp;std::string script;};
struct entclass {int rule,cx,cy,w,h,xp,yp,type,size,tile,colour,onentity,animate,para,state;float vx,vy;};
struct entityclass {
 std::vector<entclass> entities;std::vector<blockclass> blocks;
 int checkactivity();void disableblock(int);bool entitycollide(int,int);
 bool checkblocks(const SDL_Rect&,float,float,int,bool);
 void terminal_tick(int i);void terminal_contact(int i,int j);
} obj;
struct Help {bool intersects(SDL_Rect a,SDL_Rect b){return SDL_HasRectIntersection(&a,&b);}} help;
struct Music {unsigned cues;void playef(int){++cues;}} music;
struct Game {int hascontrol,deathseq,lifeseq,activetele,readytotele,intimetrial,translator_exploring_allowtele,activeactivity;} game;
struct Script {int running,key;void load(const std::string& s){key=std::stoi(s);}} script;
static void setup(const V6Block *b,unsigned n,const V6Player *p){
 obj.blocks.clear();obj.entities.clear();entclass e={};e.rule=0;e.cx=6;e.cy=2;e.w=12;e.h=21;
 e.xp=p->x;e.yp=p->y;e.vx=(float)((double)p->vx/16777216.0);e.vy=(float)((double)p->vy/16777216.0);obj.entities.push_back(e);
 for(unsigned i=0;i<n;++i)obj.blocks.push_back({b[i].type==V6_ACTIVITY?ACTIVITY:b[i].type==V6_SAFE?SAFE:b[i].type==V6_DIRECTIONAL?DIRECTIONAL:BLOCK,b[i].trigger,
    {b[i].x,b[i].y,b[i].w,b[i].h},b[i].w,b[i].h,std::to_string(b[i].trigger)});
}
extern "C" int source_solid(const V6Block *b,const V6Player *p,int enemy){setup(b,1,p);return obj.checkblocks({p->x+6,p->y+2,12,21},1,1,enemy,false);}
extern "C" int source_find(const V6Block *b,unsigned n,const V6Player *p){setup(b,n,p);return obj.checkactivity();}
extern "C" V6ActivityResult source_input(V6Block *b,unsigned n,int active,const V6Player *p,const V6ActivitySignals *s){
 setup(b,n,p);game.hascontrol=s->control;game.deathseq=s->dying?0:-1;game.lifeseq=s->life;
 game.activetele=s->teleporter_ready;game.readytotele=21;game.intimetrial=game.translator_exploring_allowtele=0;
 game.activeactivity=active;script.running=s->script_running;script.key=-1;
 bool interact_pressed=s->pressed,enter_already_processed=false;size_t ie=0;
 V6ActivityResult out={V6_INTERACT_NONE,0,-1,-1};
'''
    body=guard+'{ if (interact_pressed && !script.running) {'+tele+'{enter_already_processed=true;'+stationary+'{out.action=V6_INTERACT_TELEPORTER;}}'+activity+'}}'
    tail=r'''
 out.consumed=enter_already_processed;
 if(script.key!=-1){out.action=V6_INTERACT_ACTIVITY;out.index=active;out.script=script.key;}
 for(unsigned i=0;i<n;++i){b[i].w=obj.blocks[i].rect.w;b[i].h=obj.blocks[i].rect.h;}
 return out;
}
extern "C" void source_terminal_init(V6Terminal *t,int x,int y,int meta1,int meta2,int highlight){
 entclass entity={};entity.xp=x;entity.yp=y;switch(highlight?20:21){
'''+create+r'''
 }
 *t={x,y,entity.tile,entity.para,entity.state,entity.onentity,0};
}
void entityclass::terminal_tick(int i){switch(EntityType_TERMINAL){
'''+tick+r'''
}}
void entityclass::terminal_contact(int i,int j){switch(3){
'''+contact+r'''
}}
static void setup_terminal(const V6Terminal *t,const V6Player *p){
 setup(nullptr,0,p);entclass e={};e.xp=t->x;e.yp=t->y;e.w=e.h=16;
 e.state=t->state;e.onentity=t->onentity;e.colour=t->active;obj.entities.push_back(e);
}
extern "C" unsigned source_terminal_step(V6Terminal *t,const V6Player *p,int contact){
 setup_terminal(t,p);music.cues=0;
 if(contact)obj.terminal_contact(0,1);else obj.terminal_tick(1);
 auto& e=obj.entities[1];t->state=e.state;t->onentity=e.onentity;t->active=e.colour;return music.cues;
}
'''
    return prefix+body+tail+methods

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    path=BUILD/'activity_reference.cpp';path.write_text(reference_source())
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'amiga_version'),str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'activity_reference.so')],check=True)
    api=BUILD/'activity_test_api.c';api.write_text('#include "activity.h"\nint native_solid(const V6Block *b,const V6Player *p,int enemy){return v6_block_hit(b,p->x+6,p->y+2,12,21,1,1,enemy); }\n')
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(api),
        *[str(ROOT/'amiga_version'/(n+'.c')) for n in ('activity','terminal','player','terrain','blocks')],
        '-o',str(BUILD/'activity.so')],check=True)
    core=C.CDLL(str(BUILD/'activity.so'));ref=C.CDLL(str(BUILD/'activity_reference.so'))
    bp=C.POINTER(DynamicBlock);pp=C.POINTER(Player);tp=C.POINTER(Terminal);sp=C.POINTER(Signals)
    for f in (core.native_solid,ref.source_solid):f.argtypes=[bp,pp,C.c_int]
    for f in (core.v6_activity_find,ref.source_find):f.argtypes=[bp,C.c_uint,pp]
    for f in (core.v6_activity_input,ref.source_input):f.argtypes=[bp,C.c_uint,C.c_int,pp,sp];f.restype=Result
    for f in (core.v6_terminal_init,ref.source_terminal_init):f.argtypes=[tp]+[C.c_int]*5
    core.v6_terminal_contact.argtypes=[tp,pp];core.v6_terminal_tick.argtypes=[tp];core.v6_terminal_tick.restype=C.c_uint
    ref.source_terminal_step.argtypes=[tp,pp,C.c_int];ref.source_terminal_step.restype=C.c_uint
    rng=random.Random(68000113);selection=activation=touches=collision=0
    p=Player()
    for i in range(12000):
        p.x=rng.randrange(-32,352);p.y=rng.randrange(-32,272)
        bank=(DynamicBlock*5)(*(DynamicBlock(rng.randrange(-16,320),rng.randrange(-16,240),rng.choice((-1,0,1,20,64,320)),rng.choice((-1,0,1,16,240)),rng.randrange(4),j+6) for j in range(5)))
        assert core.v6_activity_find(bank,5,C.byref(p))==ref.source_find(bank,5,C.byref(p));selection+=1
        for enemy in (0,1):
            assert core.native_solid(bank,C.byref(p),enemy)==ref.source_solid(bank,C.byref(p),enemy)
            collision+=1
    # Fractional velocity boundaries are binary32-representable Q8.24 values.
    velocities=(-3*16777216,-2*16777216,-2*16777216+2,-16777216,-16777216+1,0,16777216-1,16777216,2*16777216-2,2*16777216,3*16777216)
    for vx in velocities:
      for vy in velocities:
       for bits in range(64):
        p.vx=vx;p.vy=vy;s=Signals(bits&1,(bits>>1)&1,(bits>>2)&1,6 if bits&8 else 5,(bits>>4)&1,(bits>>5)&1)
        for active in (-1,0,1,2):
         bank=(DynamicBlock*2)(DynamicBlock(248,200,20,16,3,6),DynamicBlock(248,200,20,16,0,9))
         wanted=(DynamicBlock*2).from_buffer_copy(bank)
         a=core.v6_activity_input(bank,2,active,C.byref(p),C.byref(s));b=ref.source_input(wanted,2,active,C.byref(p),C.byref(s))
         assert bytes(a)==bytes(b) and bytes(bank)==bytes(wanted),(vx,vy,bits,active)
         activation+=1
    for highlight in (0,1):
     for x,y in ((252,200),(0,0),(-16,-16)):
      actual=Terminal();wanted=Terminal()
      core.v6_terminal_init(C.byref(actual),x,y,1,0,highlight);ref.source_terminal_init(C.byref(wanted),x,y,1,0,highlight)
      assert bytes(actual)==bytes(wanted)
      for tick in range(500):
       p.x=x+rng.randrange(-20,24);p.y=y+rng.randrange(-25,24)
       if tick%47==0:actual.state=wanted.state=1
       cue=core.v6_terminal_tick(C.byref(actual));expected=ref.source_terminal_step(C.byref(wanted),C.byref(p),0)
       assert cue==expected and bytes(actual)==bytes(wanted),(tick,'tick')
       core.v6_terminal_contact(C.byref(actual),C.byref(p));ref.source_terminal_step(C.byref(wanted),C.byref(p),1)
       assert bytes(actual)==bytes(wanted),(tick,'contact');touches+=1
    # Actual Linear Collider activity edges and first-match order, including
    # disabling the selected slot while retaining script metadata.
    bank=(DynamicBlock*2)(DynamicBlock(248,200,20,16,3,6),DynamicBlock(248,200,20,16,3,7))
    for y in range(174,218):
     for x in range(228,269):
      p.x=x;p.y=y
      assert core.v6_activity_find(bank,2,C.byref(p))==ref.source_find(bank,2,C.byref(p));selection+=1
    p.x=248;p.y=198;p.vx=p.vy=0;s=Signals(1,1,0,0,0,0)
    assert core.v6_activity_input(bank,2,0,C.byref(p),C.byref(s)).script==6
    assert core.v6_activity_find(bank,2,C.byref(p))==1
    print('PASS source activities:',selection,'rectangle/order cases,',activation,'input/velocity/precedence cases,',touches,'terminal update/contact steps,',collision,'solid-block queries')

if __name__=='__main__':main()
