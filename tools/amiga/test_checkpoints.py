#!/usr/bin/env python3
"""Multi-checkpoint state and save records versus extracted desktop branches."""
import ctypes as C
import hashlib
import json
import random
import subprocess
from pack_rooms import ROOT
from test_player import BUILD, Player


class Checkpoint(C.Structure):
    _fields_=[(n,C.c_int) for n in ('x','y','tile','id','active','pending')]


class Save(C.Structure):
    _fields_=[(n,C.c_int) for n in ('x','y','gravity','dir','room_x','room_y','id')]


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    start=entity.index('    case 10: //Savepoint')
    create=entity[start:entity.index('    case 11: //Horizontal Gravity Line',start)]
    start=entity.index('        case EntityType_CHECKPOINT: //Savepoints')
    update=entity[start:entity.index('        case EntityType_HORIZONTAL_GRAVITY_LINE:',start)]
    start=entity.index('    case 3:   //Entity to entity')
    collide=entity[start:entity.index('    case 4:',start)]
    source=r'''
#include <vector>
#include <SDL3/SDL.h>
#include "checkpoints.h"
#define INBOUNDS_VEC(i,v) ((i)>=0 && static_cast<size_t>(i)<(v).size())
enum { EntityType_CHECKPOINT=1,EntityColour_INACTIVE_ENTITY,EntityColour_ACTIVE_ENTITY,Sound_CHECKPOINT };
struct Game {
    int savepoint,savex,savey,savegc,saverx,savery,savedir,roomx,roomy,saves;
    bool nodeathmode;
    void checkpoint_save() { ++saves; }
} game;
struct Music { void playef(int) {} } music;
struct E {
    int xp=0,yp=0,w=0,h=0,dir=0,rule=0,type=0,size=0,tile=0,
        colour=0,onentity=0,animate=0,para=0,state=0;
};
struct Reference {
    std::vector<E> entities;
    int getplayer() { return 0; }
    bool entitycollide(int i,int j) {
        SDL_Rect a={entities[i].xp+6,entities[i].yp+2,12,21};
        SDL_Rect b={entities[j].xp,entities[j].yp,entities[j].w,entities[j].h};
        return SDL_HasRectIntersection(&a,&b);
    }
    void create(E& entity,int meta1,int meta2) { switch(10) {
'''+create+r'''
    } }
    void update(int i) { switch(entities[i].type) {
'''+update+r'''
    } }
    void collide(int i,int j) { switch(entities[j].rule) {
'''+collide+r'''
    } }
} ref;
extern "C" void reference_init(const V6Checkpoint *c,unsigned n,int saved_id,const V6CheckpointSave *s) {
    game={};game.savepoint=saved_id;
    game.savex=s->x;game.savey=s->y;game.savegc=s->gravity;game.savedir=s->dir;
    game.saverx=s->room_x;game.savery=s->room_y;
    ref.entities.clear();ref.entities.resize(n+1);
    for(unsigned j=0;j<n;++j) {
        E& e=ref.entities[j+1];e.xp=c[j].x;e.yp=c[j].y;
        ref.create(e,c[j].tile-20,c[j].id);
    }
}
extern "C" int reference_update(const V6Player *p,int rx,int ry) {
    game.roomx=rx;game.roomy=ry;game.saves=0;
    ref.entities[0].dir=p->dir;
    for(int i=int(ref.entities.size())-1;i>0;--i) ref.update(i);
    return game.saves;
}
extern "C" void reference_collide(const V6Player *p) {
    ref.entities[0].xp=p->x;ref.entities[0].yp=p->y;
    for(unsigned j=1;j<ref.entities.size();++j) ref.collide(0,j);
}
extern "C" void reference_read(V6Checkpoint *c,V6CheckpointSave *s) {
    for(unsigned j=1;j<ref.entities.size();++j) {
        const E& e=ref.entities[j];
        c[j-1]={e.xp,e.yp,e.tile,e.para,e.onentity==0,e.state==1};
    }
    *s={game.savex,game.savey,game.savegc,game.savedir,game.saverx,game.savery,game.savepoint};
}
'''
    path=BUILD/'checkpoint_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'amiga_version'),str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'checkpoint_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('checkpoints.c','player.c','terrain.c')],
        '-o',str(BUILD/'checkpoints.so')],check=True)
    core=C.CDLL(str(BUILD/'checkpoints.so'));ref=C.CDLL(str(BUILD/'checkpoint_reference.so'))
    cp=C.POINTER(Checkpoint);pp=C.POINTER(Player);sp=C.POINTER(Save)
    core.v6_checkpoint_init.argtypes=[cp]+[C.c_int]*5
    core.v6_checkpoints_update.argtypes=[cp,C.c_uint,pp,C.c_int,C.c_int,sp]
    core.v6_checkpoints_collide.argtypes=[cp,C.c_uint,pp]
    ref.reference_init.argtypes=[cp,C.c_uint,C.c_int,sp]
    ref.reference_update.argtypes=[pp,C.c_int,C.c_int]
    ref.reference_collide.argtypes=[pp];ref.reference_read.argtypes=[cp,sp]
    rng=random.Random(445550);ticks=activations=multiple=0
    for scenario in range(256):
        n=scenario%9
        c=(Checkpoint*n)();expected=(Checkpoint*n)()
        saved_id=rng.choice((-1,445550,445551))
        save=Save(1,2,1,0,112,106,saved_id);expected_save=Save()
        for i in range(n):
            # Duplicate IDs and overlapping coordinates are deliberate.
            x=96 if scenario%2 else 64+i*16
            y=80 if scenario%3 else 80+i*16
            assert core.v6_checkpoint_init(C.byref(c[i]),x,y,20+i%2,445550+i%3,saved_id)
        ref.reference_init(c,n,saved_id,C.byref(save))
        for tick in range(128):
            p=Player();p.x=rng.randrange(48,210);p.y=rng.randrange(48,170);p.dir=rng.randrange(2)
            if tick%4==0:p.x=96;p.y=78
            rx=100+scenario%20;ry=100+tick%20
            # Compare before collision as well: contact cannot save immediately.
            got=core.v6_checkpoints_update(c,n,C.byref(p),rx,ry,C.byref(save))
            want=ref.reference_update(C.byref(p),rx,ry)
            assert got==want,(scenario,tick,'events')
            ref.reference_read(expected,C.byref(expected_save))
            assert bytes(c)==bytes(expected) and bytes(save)==bytes(expected_save),(scenario,tick,'update')
            core.v6_checkpoints_collide(c,n,C.byref(p));ref.reference_collide(C.byref(p))
            ref.reference_read(expected,C.byref(expected_save))
            assert bytes(c)==bytes(expected) and bytes(save)==bytes(expected_save),(scenario,tick,'collision')
            ticks+=1;activations+=got;multiple+=got>1
    assert activations and multiple
    invalid=Checkpoint(1,2,3,4,5,6);before=bytes(invalid)
    assert not core.v6_checkpoint_init(C.byref(invalid),0,0,19,0,0) and bytes(invalid)==before
    report=dict(scenarios=256,ticks=ticks,activations=activations,multiple_save_ticks=multiple,
        reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Checkpoint creation, reverse activation, deferred collisions and save records; no persistence I/O, renderer, nodeath mode or complete entity/lifecycle loop.')
    (BUILD/'checkpoint-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
