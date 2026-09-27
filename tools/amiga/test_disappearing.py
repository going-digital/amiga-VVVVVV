#!/usr/bin/env python3
"""Compare bounded disappearing-platform lifecycle with unmodified source branches."""
import ctypes as C
import hashlib
import json
import random
import subprocess
from test_player import ROOT,BUILD

class State(C.Structure):
    _fields_=[(n,C.c_int) for n in ('state','life','walking_frame','on_entity','invisible')]


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    logic=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=entity.index('        case EntityType_DISAPPEARING_PLATFORM: //Disappearing platforms')
    update=entity[start:entity.index('        case EntityType_QUICKSAND:',start)]
    start=entity.index('    case 3:   //Entity to entity')
    contact=entity[start:entity.index('    case 4:',start)]
    start=logic.index('            if (obj.entities[i].type == EntityType_DISAPPEARING_PLATFORM && obj.entities[i].state == 3)')
    death=logic[start:logic.index('            else if (obj.entities[i].type == EntityType_GRAVITRON_ENEMY',start)]
    source=r'''
#include <cstdlib>
#include <cstring>
#include <vector>
#include "Ent.h"
#include "disappearing.h"
static unsigned events;
enum { Sound_DISAPPEAR };
struct Music { void playef(int) { events|=1; } } music;
struct Game { int roomx=100,roomy=100; } game;
struct Map { bool custommode=false;void settile(int,int,int) { std::abort(); } } map;
struct Entity {
    std::vector<entclass> entities;bool overlapping;
    bool updateentities(int);
    bool entitycollide(int,int) { return overlapping; }
    void disableblockat(int,int) { events|=2; }
    void createblock(int,int,int,int,int) { events|=4; }
} obj;
entclass::entclass() { std::memset(this,0,sizeof(*this)); }
static void load(const V6Disappearing *p) {
    obj.entities.resize(1);entclass& e=obj.entities[0];
    e.type=EntityType_DISAPPEARING_PLATFORM;e.state=p->state;e.life=p->life;
    e.walkingframe=p->walking_frame;e.onentity=p->on_entity;e.invis=p->invisible;
}
static void read(V6Disappearing *p) {
    const entclass& e=obj.entities[0];
    *p={e.state,e.life,e.walkingframe,e.onentity,e.invis};
}
bool Entity::updateentities(int i) { switch(entities[i].type) {
'''+update+r'''
    default: std::abort(); } return false;
}
extern "C" unsigned reference_step(V6Disappearing *p,int dying,int hit) {
    load(p);events=0;
    if(dying) { size_t i=0;
'''+death+r'''
    } else { obj.updateentities(0); }
    read(p);return events;
}
extern "C" void reference_contact(V6Disappearing *p,int hit) {
    load(p);obj.overlapping=hit;int i=0,j=0;
    auto& entities=obj.entities;
    auto entitycollide=[](int a,int b){return obj.entitycollide(a,b);};
    switch(3) {
'''+contact+r'''
    } read(p);
}
'''
    path=BUILD/'disappearing_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-I/opt/homebrew/include',
        '-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),str(path),
        '-o',str(BUILD/'disappearing_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/disappearing.c'),
        '-o',str(BUILD/'disappearing.so')],check=True)
    core=C.CDLL(str(BUILD/'disappearing.so'));ref=C.CDLL(str(BUILD/'disappearing_reference.so'))
    pp=C.POINTER(State)
    for name in ('v6_disappearing_init','v6_disappearing_step','v6_disappearing_death'):
        getattr(core,name).argtypes=[pp]
    core.v6_disappearing_contact.argtypes=[pp,C.c_int]
    ref.reference_step.argtypes=[pp,C.c_int,C.c_int];ref.reference_contact.argtypes=[pp,C.c_int]
    rng=random.Random(680003);ticks=0;counts=[0]*6;event_counts=[0]*3
    for scenario in range(256):
        actual=State();core.v6_disappearing_init(C.byref(actual));expected=State(0,0,0,1,0)
        for tick in range(160):
            dying=(scenario%24<=tick%48<scenario%24+12)
            hit=rng.randrange(4)==0
            event=(core.v6_disappearing_death if dying else core.v6_disappearing_step)(C.byref(actual))
            want=ref.reference_step(C.byref(expected),dying,hit)
            assert event==want and bytes(actual)==bytes(expected),(scenario,tick,'update')
            if not dying:
                core.v6_disappearing_contact(C.byref(actual),hit)
                ref.reference_contact(C.byref(expected),hit)
                assert bytes(actual)==bytes(expected),(scenario,tick,'collision')
            counts[actual.state]+=1
            for bit in range(3):event_counts[bit]+=bool(event&(1<<bit))
            ticks+=1
    assert all(counts) and all(event_counts),(counts,event_counts)
    report=dict(ticks=ticks,states=counts,events=event_counts,reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Ordinary disappearing-platform update, collision arming and death recharge scheduling; block/sound side effects compared as events. No room integration, rendering, actual block-bank mutations or room (111,107) tile exception.')
    (BUILD/'disappearing-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
