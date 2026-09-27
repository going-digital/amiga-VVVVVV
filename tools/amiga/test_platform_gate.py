#!/usr/bin/env python3
"""Compare waiting platform behaviour with the original recursive source branch."""
import ctypes as C
import random
import hashlib
import json
import subprocess
from test_enemy import Enemy, FIELDS
from test_disappearing import State
from test_player import ROOT, BUILD, block


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    start=entity.index('            case 14: //Very special hack:')
    behavior=entity[start:entity.index('            case 16:',start)]
    ent=(ROOT/'desktop_version/src/Ent.cpp').read_text()
    outside=block(ent,ent.index('bool entclass::outside(void)'))
    source='''#include <vector>
#include "Ent.h"
#include "platform_gate.h"
entclass::entclass() {}
struct Entity { std::vector<entclass> entities; bool updateentities(int i); } obj;
'''+outside+'\nbool Entity::updateentities(int i) { auto& entities=this->entities; switch(entities[i].behave) {\n'+behavior+'''
} return false; }
extern "C" void reference(V6Platform *p,const V6Disappearing *g,const int *x,unsigned n) {
    obj.entities.clear();obj.entities.resize(n+1);
    entclass& e=obj.entities[0];
    e.type=EntityType_MOVING;
    e.xp=p->x;e.yp=p->y;e.w=p->w;e.h=p->h;e.x1=p->x1;e.y1=p->y1;e.x2=p->x2;e.y2=p->y2;
    e.vx=p->vx;e.vy=p->vy;e.behave=p->behavior;e.para=p->speed;e.state=p->state;e.onwall=p->onwall;
    for(unsigned i=0;i<n;++i) {obj.entities[i+1].type=EntityType_DISAPPEARING_PLATFORM;
        obj.entities[i+1].xp=x[i];obj.entities[i+1].state=g[i].state;}
    obj.updateentities(0);
    p->x=e.xp;p->y=e.yp;p->vx=e.vx;p->vy=e.vy;p->state=e.state;p->onwall=e.onwall;
}
'''
    path=BUILD/'platform_gate_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-I/opt/homebrew/include',
        '-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),str(path),
        '-o',str(BUILD/'platform_gate_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/platform_gate.c'),
        '-o',str(BUILD/'platform_gate.so')],check=True)
    core=C.CDLL(str(BUILD/'platform_gate.so')).v6_platform_gate_behavior
    ref=C.CDLL(str(BUILD/'platform_gate_reference.so')).reference
    core.argtypes=ref.argtypes=[C.POINTER(Enemy),C.POINTER(State),C.POINTER(C.c_int),C.c_uint]
    rng=random.Random(1415);checks=0
    for kind in (14,15):
        for state in range(4):
            for speed in range(-16,17):
                for scenario in range(64):
                    p=Enemy();p.x=rng.choice((63,64,100,288,289));p.y=rng.choice((63,64,100,192,193))
                    p.w=32;p.h=8;p.x1=p.y1=64;p.x2=320;p.y2=200
                    p.behavior=kind;p.state=state;p.speed=speed;p.onwall=rng.choice((2,3));p.vx=0 if state==0 else rng.randrange(-16,17)
                    gates=(State*3)();xs=(C.c_int*3)()
                    for i in range(3):
                        gates[i].state=rng.randrange(6)
                        xs[i]=p.x+(32 if kind==15 else -32)+rng.choice((-1,0,0,1))
                    expected=Enemy.from_buffer_copy(p)
                    assert core(C.byref(p),gates,xs,3)==1
                    ref(C.byref(expected),gates,xs,3)
                    assert bytes(p)==bytes(expected),(kind,state,speed,scenario,
                        [(f,getattr(p,f),getattr(expected,f)) for f in FIELDS if getattr(p,f)!=getattr(expected,f)])
                    checks+=1
    for kind in (0,3,8,13,16):
        p=Enemy();p.behavior=kind;before=bytes(p)
        assert core(C.byref(p),None,None,0)==0 and bytes(p)==before
    for kind in (14,15):
        p=Enemy();p.behavior=kind;before=bytes(p)
        assert core(C.byref(p),None,None,0)==1 and bytes(p)==before
    (BUILD/'platform-gate-report.json').write_text(json.dumps(dict(cases=checks,
        source_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Source behaviour branches 14/15 and outside(); no movement, collision bank or player transport'),indent=2)+'\n')
    print(f'PASS: {checks} source-derived behaviour-14/15 gate, direction and bounds cases (UBSan core)')


if __name__=='__main__':main()
