#!/usr/bin/env python3
"""Default arrival phases against actual Game.cpp switch cases and delays."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD,Player
from test_teleporter import Teleporter,Region
class Arrival(C.Structure):
    _fields_=[(n,C.c_int) for n in ('state','delay','control','flash','shake','advance_text')]+[('events',C.c_uint)]
class Motion(C.Structure):
    _fields_=[('ax',C.c_int32),('pending_y',C.c_int)]
def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Game.cpp').read_text()
    start=source.index('        case 4010:');cases=source[start:source.index('        case 4020:',start)]
    shim='''#include <vector>
#include "teleporter_arrival.h"
enum {EntityColour_TELEPORTER_ACTIVE,EntityColour_CREW_CYAN,Sound_FLASH=1,Sound_TELEPORT=2};
struct E {int xp,yp,lerpoldxp,lerpoldyp,dir,tile,colour;bool invis;float ax,ay,vx,vy;};
struct Obj {std::vector<E> entities;int getplayer(){return 0;}int getteleporter(){return 1;}} obj;
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
unsigned events;
struct Music {void playef(int cue){events|=cue;}} music;
struct Game {int state,statedelay,flashlight,screenshake;bool hascontrol,activetele,advancetext,
 intimetrial,nodeathmode,inintermission;struct {int x,y,w,h;} teleblock;
void incstate(){++state;}void setstate(int v){state=v;}void setstatedelay(int v){statedelay=v;}
void savetele(){events|=4;}void tick(){
statedelay--;if(statedelay<=0)statedelay=0;
if(statedelay<=0){switch(state){
'''+cases+'''
}}}} game;
extern "C" void reference(V6TeleporterArrival *a,V6Player *p,V6PlayerMotion *motion,int *invisible,V6Teleporter *t,V6TeleporterRegion *r){
obj.entities={{p->x,p->y,p->old_x,p->old_y,p->dir,0,0,*invisible!=0,
 (float)motion->ax/V6_ONE,(float)p->ay/V6_ONE,(float)p->vx/V6_ONE,(float)p->vy/V6_ONE},
 {t->x,t->y,0,0,0,t->tile,0,false,0,0,0,0}};
game.state=a->state;game.statedelay=a->delay;game.flashlight=a->flash;game.screenshake=a->shake;
game.hascontrol=a->control;game.advancetext=a->advance_text;
game.activetele=r->active;game.teleblock={r->x,r->y,r->w,r->h};
game.intimetrial=game.nodeathmode=game.inintermission=false;events=0;
game.tick();a->state=game.state;a->delay=game.statedelay;a->control=game.hascontrol;
a->flash=game.flashlight;a->shake=game.screenshake;a->advance_text=game.advancetext;a->events=events;
p->x=obj.entities[0].xp;p->y=obj.entities[0].yp;p->old_x=obj.entities[0].lerpoldxp;p->old_y=obj.entities[0].lerpoldyp;
p->dir=obj.entities[0].dir;*invisible=obj.entities[0].invis;
motion->ax=(int)(obj.entities[0].ax*V6_ONE);p->ay=(int)(obj.entities[0].ay*V6_ONE);
p->vx=(int)(obj.entities[0].vx*V6_ONE);p->vy=(int)(obj.entities[0].vy*V6_ONE);t->tile=obj.entities[1].tile;
r->active=game.activetele;r->x=game.teleblock.x;r->y=game.teleblock.y;r->w=game.teleblock.w;r->h=game.teleblock.h;
}
'''
    path=BUILD/'arrival-reference.cpp';path.write_text(shim)
    common=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
    subprocess.run(['c++','-std=c++11',*common,str(path),'-o',str(BUILD/'arrival-reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*common,str(ROOT/'amiga_version/teleporter_arrival.c'),'-o',str(BUILD/'arrival.so')],check=True)
    core=C.CDLL(str(BUILD/'arrival.so'));ref=C.CDLL(str(BUILD/'arrival-reference.so'))
    args=[C.POINTER(Arrival),C.POINTER(Player),C.POINTER(Motion),C.POINTER(C.c_int),C.POINTER(Teleporter),C.POINTER(Region)]
    core.v6_teleporter_arrival_tick.argtypes=args;ref.reference.argtypes=args
    core.v6_teleporter_arrival_init.argtypes=[C.POINTER(Arrival)];core.v6_teleporter_arrival_start.argtypes=[C.POINTER(Arrival)]
    return core,ref

def main():
    core,ref=libraries();cases=0
    def run(a,p,m,inv,t,r):
        original=(Arrival.from_buffer_copy(a),Player.from_buffer_copy(p),Motion.from_buffer_copy(m),C.c_int(inv.value),Teleporter.from_buffer_copy(t),Region.from_buffer_copy(r))
        values=(a,p,m,inv,t,r)
        assert core.v6_teleporter_arrival_tick(*[C.byref(v) for v in values])
        ref.reference(*[C.byref(v) for v in original])
        assert all(bytes(v)==bytes(expected) for v,expected in zip(values,original)),(a.state,a.delay,[(bytes(v),bytes(e)) for v,e in zip(values,original) if bytes(v)!=bytes(e)])
    for state in range(4010,4020):
        for delay in (0,1,2,5,15):
            for x,y in ((112,48),(36,68)):
                for direction in (0,1):
                    for hidden in (0,1):
                        a=Arrival(state,delay,0,2,7,1,7);p=Player();p.x=150;p.y=110;p.old_x=149;p.old_y=109;p.dir=direction
                        p.vx=8388608;p.vy=-8388608;p.ay=3*16777216
                        m=Motion(0,110);inv=C.c_int(hidden);t=Teleporter(x,y,0,6,0,0);r=Region(0,123,234,13,14)
                        run(a,p,m,inv,t,r);cases+=1
    timeline=[];a=Arrival();core.v6_teleporter_arrival_init(C.byref(a))
    assert core.v6_teleporter_arrival_start(C.byref(a))
    before=bytes(a);assert not core.v6_teleporter_arrival_start(C.byref(a)) and bytes(a)==before
    p=Player();p.x=p.old_x=150;p.y=p.old_y=110;p.dir=0
    m=Motion();inv=C.c_int(1);t=Teleporter(36,68,0,6,0,0);r=Region()
    for tick in range(70):
        old=a.state;run(a,p,m,inv,t,r)
        if old!=a.state:timeline.append((tick+1,old,a.state,a.delay,a.events))
    assert timeline==[(1,4010,4011,15,1),(16,4011,4012,0,2),(17,4012,4013,5,0),
        (22,4013,4014,0,0),(23,4014,4015,0,0),(24,4015,4016,0,0),(25,4016,4017,0,0),
        (26,4017,4018,0,0),(27,4018,4019,15,0),(42,4019,0,0,4)],timeline
    assert (p.x,p.y,p.old_x,p.old_y,p.dir)==(118,112,80,112,1)
    assert a.control==1 and a.advance_text==0 and not inv.value and t.tile==2
    assert (r.active,r.x,r.y,r.w,r.h)==(1,4,36,160,160) and not a.events
    for field,value in (('state',4000),('state',4020),('delay',-1),('delay',16)):
        a=Arrival(4010,0,0,0,0,1,7);setattr(a,field,value);values=(a,p,m,inv,t,r);before=tuple(bytes(v) for v in values)
        assert not core.v6_teleporter_arrival_tick(*[C.byref(v) for v in values]) and tuple(bytes(v) for v in values)==before
    a=Arrival(4010,0,0,0,0,1,7);t.x=277;values=(a,p,m,inv,t,r);before=tuple(bytes(v) for v in values)
    assert not core.v6_teleporter_arrival_tick(*[C.byref(v) for v in values]) and tuple(bytes(v) for v in values)==before
    print(f'PASS default arrival: {cases} extracted source phases, 70 sequential ticks, exact 42-tick completion, one-shot cues/save request, control/visibility/motion and invalid-state preservation')
if __name__=='__main__':main()
