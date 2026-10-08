#!/usr/bin/env python3
"""Normal selection and short departure against extracted desktop source."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD,block
from test_teleporter import Teleporter,Region

class Departure(C.Structure):
    _fields_=[(n,C.c_int) for n in ('state','delay','control','flash','shake','locked','travel')]+[('events',C.c_uint)]

def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    begin=game.index('        case 4000:');cases=game[begin:game.index('        case 4010:',begin)]
    inp=(ROOT/'desktop_version/src/Input.cpp').read_text()
    begin=inp.index('//cancel!',inp.index('void teleporterinput('))
    begin=inp.index('{',inp.index('else',begin));selection=block(inp,begin)
    shim='''#include <vector>
#include "teleporter_departure.h"
enum {EntityColour_CREW_CYAN,EntityColour_TELEPORTER_INACTIVE,
 EntityColour_TELEPORTER_FLASHING,Sound_FLASH=1,Sound_TELEPORT=2};
struct E {int tile,colour;bool invis;};
struct Obj {std::vector<E> entities;int getplayer(){return 0;}int getteleporter(){return 1;}} obj;
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
unsigned events;
struct Music {void playef(int cue){events|=cue;}} music;
struct Graphics {bool resumegamemode;} graphics;
struct Game {int state,statedelay,flashlight,screenshake,teleport_to_x,teleport_to_y;
bool hascontrol,activetele,statelocked,teleport_to_new_area;
void setstate(int s){if(!statelocked)state=s;}
void setstatedelay(int d){if(!statelocked)statedelay=d;}
void unlockstate(){statelocked=false;}
void tick(){
statedelay--;if(statedelay<=0)statedelay=0;
if(statedelay<=0){switch(state){
'''+cases+'''
}}}} game;
static void load(V6TeleporterDeparture *d,int *invisible,V6Teleporter *t) {
game.state=d->state;game.statedelay=d->delay;game.hascontrol=d->control;
game.flashlight=d->flash;game.screenshake=d->shake;game.statelocked=d->locked;
game.teleport_to_new_area=d->travel;events=0;
obj.entities={{0,EntityColour_TELEPORTER_FLASHING,*invisible!=0},
 {t->tile,EntityColour_TELEPORTER_FLASHING,false}};
}
static void read(V6TeleporterDeparture *d,int *invisible,V6Teleporter *t) {
d->state=game.state;d->delay=game.statedelay;d->control=game.hascontrol;
d->flash=game.flashlight;d->shake=game.screenshake;d->locked=game.statelocked;
d->travel=game.teleport_to_new_area;d->events=events;
*invisible=obj.entities[0].invis;t->tile=obj.entities[1].tile;
}
extern "C" void reference(V6TeleporterDeparture *d,int *invisible,V6Teleporter *t) {
load(d,invisible,t);bool old=game.teleport_to_new_area;game.tick();
if(!old && game.teleport_to_new_area)events|=4;
read(d,invisible,t);
}
extern "C" void reference_start(V6TeleporterDeparture *d,V6Teleporter *t,V6TeleporterRegion *r) {
int invisible=0;load(d,&invisible,t);game.activetele=r->active;
int tempx=10,tempy=5;
'''+selection+'''
read(d,&invisible,t);r->active=game.activetele;
}
'''
    path=BUILD/'departure-reference.cpp';path.write_text(shim)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined',
        '-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
    subprocess.run(['c++','-std=c++11',*flags,str(path),'-o',str(BUILD/'departure-reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/teleporter_departure.c'),
        '-o',str(BUILD/'departure.so')],check=True)
    core=C.CDLL(str(BUILD/'departure.so'));ref=C.CDLL(str(BUILD/'departure-reference.so'))
    args=[C.POINTER(Departure),C.POINTER(C.c_int),C.POINTER(Teleporter)]
    core.v6_teleporter_departure_tick.argtypes=args;ref.reference.argtypes=args
    args=[C.POINTER(Departure),C.POINTER(Teleporter),C.POINTER(Region)]
    core.v6_teleporter_departure_start.argtypes=args;ref.reference_start.argtypes=args
    core.v6_teleporter_departure_init.argtypes=[C.POINTER(Departure)]
    return core,ref

def main():
    core,ref=libraries();cases=0
    def tick(d,invisible,t):
        values=(d,invisible,t)
        expected=(Departure.from_buffer_copy(d),C.c_int(invisible.value),Teleporter.from_buffer_copy(t))
        assert core.v6_teleporter_departure_tick(*[C.byref(v) for v in values])
        ref.reference(*[C.byref(v) for v in expected])
        assert tuple(bytes(v) for v in values)==tuple(bytes(v) for v in expected),(d.state,d.delay)
    for state in range(4000,4004):
        for delay in (0,1,2,5,10):
            for locked in (0,1):
                for hidden in (0,1):
                    for tile in (1,6):
                        d=Departure(state,delay,0,2,7,locked,0,7)
                        invisible=C.c_int(hidden);t=Teleporter(112,48,0,tile,0,0)
                        tick(d,invisible,t);cases+=1
    d=Departure();core.v6_teleporter_departure_init(C.byref(d))
    t=Teleporter(112,48,0,2,0,0);r=Region(1,80,16,160,160)
    expected=tuple(type(v).from_buffer_copy(v) for v in (d,t,r))
    assert core.v6_teleporter_departure_start(C.byref(d),C.byref(t),C.byref(r))
    ref.reference_start(*[C.byref(v) for v in expected])
    assert tuple(bytes(v) for v in (d,t,r))==tuple(bytes(v) for v in expected)
    assert not d.control and not r.active and t.tile==6
    before=tuple(bytes(v) for v in (d,t,r))
    assert not core.v6_teleporter_departure_start(C.byref(d),C.byref(t),C.byref(r))
    assert before==tuple(bytes(v) for v in (d,t,r))
    invisible=C.c_int(0);timeline=[];requests=[]
    for i in range(40):
        previous=d.state;tick(d,invisible,t)
        if d.state!=previous:timeline.append((i+1,d.state,d.delay))
        if d.events:requests.append((i+1,d.events))
        assert invisible.value==(i>=11)
        if d.flash:d.flash-=1
        if d.shake:d.shake-=1
    assert timeline==[(1,4001,10),(11,4002,0),(12,4003,10),(22,0,0)],timeline
    assert requests==[(1,1),(11,2),(22,4)],requests
    assert d.travel and not d.events and not d.control and t.tile==1
    assert not core.v6_teleporter_departure_start(C.byref(d),C.byref(t),C.byref(r))
    # Locked departure states manually advance and unlock at the handoff.
    d=Departure(4000,0,0,0,0,1,0,0)
    for i in range(22):tick(d,invisible,t)
    assert d.travel and not d.locked and d.events==4
    for field,value in (('state',3999),('state',4004),('delay',-1),('delay',11)):
        d=Departure(4000,0,0,2,7,1,0,7);setattr(d,field,value)
        values=(d,invisible,t);before=tuple(bytes(v) for v in values)
        assert not core.v6_teleporter_departure_tick(*[C.byref(v) for v in values])
        assert before==tuple(bytes(v) for v in values)
    for field,value in (('locked',1),('travel',1),('delay',1)):
        d=Departure();core.v6_teleporter_departure_init(C.byref(d));setattr(d,field,value)
        values=(d,t,r);before=tuple(bytes(v) for v in values)
        assert not core.v6_teleporter_departure_start(*[C.byref(v) for v in values])
        assert before==tuple(bytes(v) for v in values)
    d=Departure(4000,0,0,0,0,0,0,7);t.x=277
    values=(d,invisible,t);before=tuple(bytes(v) for v in values)
    assert not core.v6_teleporter_departure_tick(*[C.byref(v) for v in values])
    assert before==tuple(bytes(v) for v in values)
    d=Departure();core.v6_teleporter_departure_init(C.byref(d))
    values=(d,t,r);before=tuple(bytes(v) for v in values)
    assert not core.v6_teleporter_departure_start(*[C.byref(v) for v in values])
    assert before==tuple(bytes(v) for v in values)
    t.x=112
    for fn,values in ((core.v6_teleporter_departure_start,(d,t,r)),
                      (core.v6_teleporter_departure_tick,(d,invisible,t))):
        for index in range(3):
            args=[C.byref(v) for v in values];args[index]=None
            before=tuple(bytes(v) for v in values)
            assert not fn(*args) and before==tuple(bytes(v) for v in values)
    print(f'PASS departure: extracted Input selection, {cases} source phases, 22-tick travel, locked-state bypass/unlock, one-shot cues and invalid-state preservation')
if __name__=='__main__':main()
