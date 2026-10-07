#!/usr/bin/env python3
"""Type-14 creation, collision and activation against extracted desktop code."""
import ctypes as C
import subprocess
import re
from test_checkpoints import Checkpoint, Save
from test_player import ROOT, BUILD, Player
class Teleporter(C.Structure):
    _fields_=[(n,C.c_int) for n in ('x','y','id','tile','onentity','state')]
class Region(C.Structure):
    _fields_=[(n,C.c_int) for n in ('active','x','y','w','h')]

def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    start=entity.index('    case 14: // Teleporter')
    create=entity[start:entity.index('    case 15:',start)]
    start=entity.index('        case EntityType_TELEPORTER: //The teleporter')
    update=entity[start:entity.index('        case EntityType_INVALID:',start)]
    start=entity.index('    case 3:   //Entity to entity')
    collide=entity[start:entity.index('    case 4:',start)]
    source=r'''
#include <vector>
#include <SDL3/SDL.h>
#include "teleporter.h"
#define INBOUNDS_VEC(i,v) ((i)>=0 && static_cast<size_t>(i)<(v).size())
enum {EntityType_TELEPORTER=1,EntityType_CHECKPOINT,EntityColour_TELEPORTER_INACTIVE,
EntityColour_TELEPORTER_ACTIVE,EntityColour_TELEPORTER_FLASHING,EntityColour_INACTIVE_ENTITY,Sound_GAMESAVED};
struct E {int xp=0,yp=0,w=0,h=0,dir=0,rule=0,type=0,size=0,tile=0,
colour=0,onentity=0,animate=0,para=0,state=0;};
struct Game {int savepoint,savex,savey,savegc,saverx,savery,savedir,roomx,roomy,message,delay;
bool intimetrial,nodeathmode,activetele;
SDL_Rect teleblock;
void setstate(int v){message=v;}
void setstatedelay(int v){delay=v;}
} game;
struct Music {int sounds=0;void playef(int){++sounds;}} music;
struct Reference {
std::vector<E> entities;
int getplayer(){return 0;}
bool entitycollide(int i,int j) {
SDL_Rect a={entities[i].xp+6,entities[i].yp+2,12,21};
SDL_Rect b={entities[j].xp,entities[j].yp,entities[j].w,entities[j].h};
return SDL_HasRectIntersection(&a,&b);
}
void create(E& entity,int meta2){switch(14){
'''+create+r'''
}}
void update(int i){switch(entities[i].type){
'''+update+r'''
}}
void collide(int i,int j){switch(entities[j].rule){
'''+collide+r'''
}}
} ref;
extern "C" void reference_init(int x,int y,int id,const V6CheckpointSave *s){
game={};music.sounds=0;ref.entities.clear();ref.entities.resize(5);
game.savepoint=s->id;game.savex=s->x;game.savey=s->y;game.savegc=s->gravity;
game.savedir=s->dir;game.saverx=s->room_x;game.savery=s->room_y;
E& t=ref.entities[1];t.xp=x;t.yp=y;ref.create(t,id);
for(int j=2;j<5;++j){ref.entities[j].type=EntityType_CHECKPOINT;ref.entities[j].onentity=0;}
}
extern "C" void reference_collide(const V6Player *p){
ref.entities[0].xp=p->x;ref.entities[0].yp=p->y;ref.collide(0,1);
}
extern "C" unsigned reference_update(const V6Player *p,int state,int tile,int rx,int ry,int trial,int nodeath){
ref.entities[0].dir=p->dir;ref.entities[1].state=state;ref.entities[1].tile=tile;
game.roomx=rx;game.roomy=ry;game.intimetrial=trial;game.nodeathmode=nodeath;
game.message=0;music.sounds=0;ref.update(1);
return (music.sounds?1:0)|(game.message==2000?2:0);
}
extern "C" void reference_read(V6Teleporter *t,V6TeleporterRegion *r,V6CheckpointSave *s,int *active){
E& e=ref.entities[1];*t={e.xp,e.yp,e.para,e.tile,e.onentity,e.state};
*r={game.activetele,game.teleblock.x,game.teleblock.y,game.teleblock.w,game.teleblock.h};
*s={game.savex,game.savey,game.savegc,game.savedir,game.saverx,game.savery,game.savepoint};
for(int j=0;j<3;++j)active[j]=ref.entities[j+2].onentity==0;
}
'''
    path=BUILD/'teleporter_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-fsanitize=undefined',
        '-fno-sanitize-recover=all','-I/opt/homebrew/include','-I'+str(ROOT/'amiga_version'),
        str(path),'-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'teleporter_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('teleporter.c','player.c','terrain.c')],
        '-o',str(BUILD/'teleporter.so')],check=True)
    core=C.CDLL(str(BUILD/'teleporter.so'));ref=C.CDLL(str(BUILD/'teleporter_reference.so'))
    tp=C.POINTER(Teleporter);rp=C.POINTER(Region);sp=C.POINTER(Save);pp=C.POINTER(Player)
    core.v6_teleporter_init.argtypes=[tp,C.c_int,C.c_int,C.c_int]
    core.v6_teleporter_collide.argtypes=[tp,pp]
    core.v6_teleporter_update.argtypes=[tp,rp,C.POINTER(Checkpoint),C.c_uint,pp,*([C.c_int]*4),sp]
    core.v6_teleporter_checkpoint_valid.argtypes=[tp,sp]
    ref.reference_init.argtypes=[C.c_int,C.c_int,C.c_int,sp]
    ref.reference_collide.argtypes=[pp]
    ref.reference_update.argtypes=[pp,*([C.c_int]*6)]
    ref.reference_read.argtypes=[tp,rp,sp,C.POINTER(C.c_int)]
    return core,ref

def read(ref):
    t,r,s=Teleporter(),Region(),Save();active=(C.c_int*3)()
    ref.reference_read(C.byref(t),C.byref(r),C.byref(s),active)
    return bytes(t),bytes(r),bytes(s),list(active)

def main():
    room=(ROOT/'desktop_version/src/Finalclass.cpp').read_text()
    start=room.index('case rn(111,104):');room=room[start:room.index('case rn(',start+5)]
    calls=re.findall(r'obj.createentity\(([^;]+)\);',room)
    assert len(calls)==1 and re.sub(r'\s+','',calls[0])=='128-16,80-32,14'
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    assert 'createentity(xp, yp, t, meta1, 0);' in entity
    core,ref=libraries();cases=0
    # Building Apport's literal call uses type 14 at (128-16,80-32), default ID 0.
    for x,y,identity in ((112,48,0),(0,0,42),(224,144,73)):
        for state in (0,1,2,3):
            for tile in (1,2,6):
                for trial in (0,1):
                    for nodeath in (0,1):
                        for direction in (0,1):
                            t=Teleporter();r=Region();s=Save(140,1822,1,0,109,109,505147)
                            bank=(Checkpoint*3)(*[Checkpoint(0,0,20,i,1,i%2) for i in range(3)])
                            p=Player();p.dir=direction
                            core.v6_teleporter_init(C.byref(t),x,y,identity)
                            ref.reference_init(x,y,identity,C.byref(s))
                            assert (bytes(t),bytes(r),bytes(s),[1]*3)==read(ref)
                            t.state=state;t.tile=tile
                            got=core.v6_teleporter_update(C.byref(t),C.byref(r),bank,3,C.byref(p),111,104,trial,nodeath,C.byref(s))
                            expected=ref.reference_update(C.byref(p),state,tile,111,104,trial,nodeath)
                            assert got==expected
                            assert (bytes(t),bytes(r),bytes(s),[c.active for c in bank])==read(ref)
                            assert [c.pending for c in bank]==[0,1,0]
                            if got:
                                assert core.v6_teleporter_checkpoint_valid(C.byref(t),C.byref(s))
                                before=bytes(s)
                                for repeat in range(30):
                                    core.v6_teleporter_collide(C.byref(t),C.byref(p))
                                    assert not core.v6_teleporter_update(C.byref(t),C.byref(r),bank,3,C.byref(p),111,104,trial,nodeath,C.byref(s))
                                assert bytes(s)==before
                            cases+=1
    # Production order: first update does nothing, collision arms state 1,
    # and the next update saves even if the player has since moved away.
    t=Teleporter();r=Region();s=Save(140,1822,1,0,109,109,505147)
    p=Player();p.x=112;p.y=48;p.dir=1
    core.v6_teleporter_init(C.byref(t),112,48,0)
    ref.reference_init(112,48,0,C.byref(s))
    bank=(Checkpoint*3)(*[Checkpoint(0,0,20,i,1,0) for i in range(3)])
    def tick():
        events=core.v6_teleporter_update(C.byref(t),C.byref(r),bank,3,C.byref(p),111,104,0,0,C.byref(s))
        expected=ref.reference_update(C.byref(p),read_state[0],read_state[1],111,104,0,0)
        assert events==expected
        assert (bytes(t),bytes(r),bytes(s),[c.active for c in bank])==read(ref)
        return events
    read_state=(t.state,t.tile);assert tick()==0
    core.v6_teleporter_collide(C.byref(t),C.byref(p));ref.reference_collide(C.byref(p))
    assert t.state==1 and s.id==505147
    p.x=300;p.y=200;read_state=(t.state,t.tile);assert tick()==3
    assert (s.x,s.y,s.gravity,s.dir,s.room_x,s.room_y,s.id)==(156,92,0,1,111,104,0)
    for repeat in range(120):
        read_state=(t.state,t.tile);assert tick()==0
    collisions=0
    for dx in range(-20,105):
        for dy in (-24,-23,-22,-3,-2,0,73,93,94,95,96):
            t=Teleporter();p=Player();s=Save();core.v6_teleporter_init(C.byref(t),112,48,0)
            ref.reference_init(112,48,0,C.byref(s));p.x=112+dx;p.y=48+dy
            core.v6_teleporter_collide(C.byref(t),C.byref(p));ref.reference_collide(C.byref(p))
            assert bytes(t)==read(ref)[0]
            collisions+=1
    t=Teleporter();core.v6_teleporter_init(C.byref(t),112,48,0)
    s=Save(156,92,0,1,111,104,0)
    assert core.v6_teleporter_checkpoint_valid(C.byref(t),C.byref(s))
    for field in ('x','y','gravity','dir','id'):
        bad=Save.from_buffer_copy(s);setattr(bad,field,getattr(bad,field)+2)
        assert not core.v6_teleporter_checkpoint_valid(C.byref(t),C.byref(bad))
    print(f'PASS teleporter: {cases} source activation cases, {collisions} source collision cases, repeat suppression and canonical checkpoint guards')
if __name__=='__main__':main()
