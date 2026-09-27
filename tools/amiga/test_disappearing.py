#!/usr/bin/env python3
"""Compare bounded disappearing-platform lifecycle with unmodified source branches."""
import ctypes as C
import hashlib
import json
import random
import subprocess
from test_player import ROOT,BUILD,DynamicBlock,block

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
    create=block(entity,entity.index('void entityclass::createblock('))
    allocation=create[create.index('    k = blocks.size();'):create.index('    switch(t)')]
    solid=create[create.index('        block.type = BLOCK;'):create.index('        break;',create.index('        block.type = BLOCK;'))]
    append=block(create,create.rindex('    if (!reuse)'))
    block_source=(ROOT/'desktop_version/src/BlockV.cpp').read_text()
    clear=block(block_source,block_source.index('void blockclass::clear(void)'))
    disable='\n'.join(block(entity,entity.index('void entityclass::'+name+'(')).replace('entityclass::','Entity::')
                      for name in ('disableblock','disableblockat'))
    source=r'''
#include <cstdlib>
#include <cstring>
#include <vector>
#include <string>
#include "Ent.h"
#include "disappearing.h"
#define INBOUNDS_VEC(i,v) ((i)>=0 && static_cast<size_t>(i)<(v).size())
#define vlog_error(...) std::abort()
static unsigned events;
enum { Sound_DISAPPEAR };
struct Music { void playef(int) { events|=1; } } music;
struct Game { int roomx=100,roomy=100; } game;
struct Map { bool custommode=false;void settile(int,int,int) { std::abort(); } } map;
enum { BLOCK=0 };
struct blockclass {
    int type,trigger,xp,yp,wp,hp,r,g,b,activity_y;SDL_Rect rect;
    std::string script,prompt;bool gettext;
    blockclass() { clear(); }
    void clear();
    void rectset(int x,int y,int w,int h) { rect={x,y,w,h}; }
};
struct Entity {
    std::vector<blockclass> blocks;size_t k;
    void disableblock(int);
    std::vector<entclass> entities;bool overlapping;
    bool updateentities(int);
    bool entitycollide(int,int) { return overlapping; }
    void disableblockat(int,int);
    void createblock(int,int,int,int,int);
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
    source+='\n'+clear+'\n'+disable
    # Capture side effects without replacing source allocation/disable logic.
    source=source.replace('disableblockat(entities[i].xp, entities[i].yp);','disableblockat(entities[i].xp, entities[i].yp); events|=2;')
    source+='\nvoid Entity::createblock(int,int xp,int yp,int w,int h) { events|=4;\n'+allocation+solid+append+'\n}\n'
    source+=r'''
extern "C" void bank_load(const V6Block *b,unsigned n,int x,int y) {
    obj.blocks.clear();
    for(unsigned i=0;i<n;++i) {
        blockclass v;v.type=b[i].type;v.trigger=b[i].trigger;
        v.xp=b[i].x;v.yp=b[i].y;v.wp=b[i].w;v.hp=b[i].h;
        v.rectset(v.xp,v.yp,v.wp,v.hp);obj.blocks.push_back(v);
    }
    obj.entities.resize(1);obj.entities[0].xp=x;obj.entities[0].yp=y;
}
extern "C" unsigned bank_read(V6Block *b) {
    for(unsigned i=0;i<obj.blocks.size();++i) {
        const blockclass& v=obj.blocks[i];b[i]={v.xp,v.yp,v.wp,v.hp,v.type,v.trigger};
    }
    return obj.blocks.size();
}
'''
    path=BUILD/'disappearing_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-I/opt/homebrew/include',
        '-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),str(path),
        '-o',str(BUILD/'disappearing_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/disappearing.c'),str(ROOT/'amiga_version/blocks.c'),
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
    bp=C.POINTER(DynamicBlock)
    core.v6_disappearing_update.argtypes=[pp,C.c_int,C.c_int,bp,C.POINTER(C.c_uint),C.c_uint,C.c_int]
    core.v6_blocks_create_solid.argtypes=[bp,C.POINTER(C.c_uint),C.c_uint]+[C.c_int]*4
    ref.bank_load.argtypes=[bp,C.c_uint,C.c_int,C.c_int];ref.bank_read.argtypes=[bp]
    bank_ticks=0
    for scenario in range(128):
        bank=(DynamicBlock*16)();expected_bank=(DynamicBlock*16)();count=C.c_uint(6)
        for i in range(6):
            bank[i]=DynamicBlock(80 if i<3 else 120,96,32,8,i%3,3)
        if scenario%2:bank[0].w=bank[0].h=0
        actual=State(4,0,4,0,1) if scenario%3==0 else State(0,0,0,1,0)
        expected=State.from_buffer_copy(actual)
        ref.bank_load(bank,count.value,80,96)
        for tick in range(240):
            dying=20<=tick%48<32;hit=rng.randrange(3)==0
            event=core.v6_disappearing_update(C.byref(actual),80,96,bank,C.byref(count),16,dying)
            want=ref.reference_step(C.byref(expected),dying,hit)
            assert event==want and bytes(actual)==bytes(expected),(scenario,tick,'bank update')
            expected_count=ref.bank_read(expected_bank)
            assert count.value==expected_count,(scenario,tick,'count')
            for i in range(count.value):
                assert bytes(bank[i])==bytes(expected_bank[i]),(scenario,tick,i,'slot')
            if not dying:
                core.v6_disappearing_contact(C.byref(actual),hit)
                ref.reference_contact(C.byref(expected),hit)
            bank_ticks+=1
    # Fixed-capacity failure is an Amiga contract, not desktop behavior.
    bank=(DynamicBlock*2)(DynamicBlock(1,2,8,8,1,3),DynamicBlock(3,4,8,8,2,2))
    count=C.c_uint(2);actual=State(4,0,4,0,1)
    before=(bytes(bank),bytes(actual))
    assert core.v6_disappearing_update(C.byref(actual),80,96,bank,C.byref(count),2,0)==8
    assert (bytes(bank),bytes(actual))==before and count.value==2
    bank[0].w=bank[0].h=0
    assert core.v6_disappearing_update(C.byref(actual),80,96,bank,C.byref(count),2,0)==4
    assert count.value==2 and bytes(bank[0])==bytes(DynamicBlock(80,96,32,8,0,0))
    # A zero dimension alone does not qualify as a fully disabled slot.
    bank[0]=DynamicBlock(1,2,0,8,0,0)
    assert core.v6_blocks_create_solid(bank,C.byref(count),2,80,96,32,8)==-1
    report=dict(bank_ticks=bank_ticks,capacity_failure_checks=3,ticks=ticks,states=counts,events=event_counts,reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Ordinary disappearing-platform update, collision arming and death recharge scheduling; collision-bank allocation/disable and sound events compared with source branches. Bounded-capacity failure tested separately. No room integration, rendering or room (111,107) tile exception.')
    (BUILD/'disappearing-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
