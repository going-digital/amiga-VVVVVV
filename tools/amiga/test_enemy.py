#!/usr/bin/env python3
"""Differential tests for the bounded ordinary-enemy movement core."""
import ctypes as C
import hashlib
import json
import random
import re
import struct
import subprocess
from pack_rooms import ROOT, extract
from test_player import BUILD, Room, Terrain, block, original_reference

FIELDS = 'x y old_x old_y vx vy behavior speed state onwall x1 y1 x2 y2 cx cy w h'.split()
class Enemy(C.Structure):
    _fields_ = [(name, C.c_int32) for name in FIELDS]
class Block(C.Structure):
    _fields_ = [(name, C.c_int) for name in 'x y w h type trigger'.split()]


def main():
    original_reference()
    source = (BUILD/'player_reference.cpp').read_text()
    entity = (ROOT/'desktop_version/src/Entity.cpp').read_text()
    ent = (ROOT/'desktop_version/src/Ent.cpp').read_text()
    start = entity.index('case 0: //Bounce, Start moving down')
    end = entity.index('case 4: //Always move left', start)
    behavior = entity[start:end]
    outside = block(ent, ent.index('bool entclass::outside(void)'))
    source += '\n#include "enemy.h"\n' + outside
    source += '\nbool entityclass::updateentities(int i) { switch(entities[i].behave) {\n' + behavior + '\n} return false; }\n'
    source += r'''
extern "C" void enemy_reference_init(const V6Enemy *p, const uint16_t *tiles,
    int tileset, int extra, const V6EnemyBlock *blocks, unsigned count) {
    V6Player dummy={}; reference_init(&dummy,tiles,tileset,extra);
    entclass& e=obj.entities[0];
    e.type=EntityType_MOVING; e.rule=1; e.gravity=false;
    e.xp=p->x; e.yp=p->y; e.oldxp=p->old_x; e.oldyp=p->old_y;
    e.cx=p->cx; e.cy=p->cy; e.w=p->w; e.h=p->h;
    e.x1=p->x1; e.y1=p->y1; e.x2=p->x2; e.y2=p->y2;
    e.behave=p->behavior; e.para=p->speed;
    for(unsigned i=0;i<count;++i) {
        blockclass b={};
        b.type=blocks[i].type==V6_ENEMY_SAFE ? SAFE :
               blocks[i].type==V6_ENEMY_DIRECTIONAL ? DIRECTIONAL : BLOCK;
        b.trigger=blocks[i].trigger;
        b.rect={blocks[i].x,blocks[i].y,blocks[i].w,blocks[i].h};
        obj.blocks.push_back(b);
    }
    obj.updateentities(0);
}
extern "C" void enemy_reference_step(V6Enemy *p) {
    obj.updateentities(0); obj.updateentitylogic(0); obj.entitymapcollision(0);
    const entclass& e=obj.entities[0];
    p->x=e.xp; p->y=e.yp; p->old_x=e.oldxp; p->old_y=e.oldyp;
    p->vx=e.vx; p->vy=e.vy; p->state=e.state; p->onwall=e.onwall;
}
'''
    path=BUILD/'enemy_reference.cpp'; path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
                    '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
                    '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),
                    str(path),'-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'enemy_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
                    '-fsanitize=undefined',str(ROOT/'amiga_version/enemy.c'),str(ROOT/'amiga_version/terrain.c'),
                    '-o',str(BUILD/'enemy.so')],check=True)
    core=C.CDLL(str(BUILD/'enemy.so')); ref=C.CDLL(str(BUILD/'enemy_reference.so'))
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),C.POINTER(Room)]
    core.v6_enemy_init.argtypes=[C.POINTER(Enemy)]+[C.c_int]*12
    core.v6_enemy_step.argtypes=[C.POINTER(Enemy),C.POINTER(Room),C.POINTER(Block),C.c_uint]
    ref.enemy_reference_init.argtypes=[C.POINTER(Enemy),C.POINTER(C.c_uint16),C.c_int,C.c_int,C.POINTER(Block),C.c_uint]
    ref.enemy_reference_step.argtypes=[C.POINTER(Enemy)]
    rng=random.Random(51268000); ticks=0
    records=extract()
    for scenario in range(528):
        scene=[0]*1200
        if scenario%4==1:
            scene=[80 if x in (0,39) or y in (0,29) or (x==20 and 8<y<23) else 0
                   for y in range(30) for x in range(40)]
        elif scenario%4==2:
            scene=list(struct.unpack('>1200H',records[rng.randrange(len(records))][1]))
        elif scenario%4==3:
            for y in range(10,20): scene[y*40+20]=14+(scenario//4)%4
        tileset=scenario%3; extra=scenario%2
        raw=(C.c_uint16*1200)(*scene); room=Room(raw,tileset,extra)
        terrain=Terrain(); core.v6_terrain_build(C.byref(terrain),C.byref(room))
        # The original loader generates these blocks from directional tiles.
        blocks=[Block(x*8,y*8,8,8,2,scene[y*40+x]-14)
                for y in range(29+extra) for x in range(40) if 14<=scene[y*40+x]<=17]
        additional=[Block(144,72,16,80,scenario%3,(scenario//3)%4)]
        native=(Block*(len(blocks)+1))(*(blocks+additional))
        custom=(Block*1)(*additional)
        p=Enemy(); w=rng.choice((8,12,16,24,32)); h=rng.choice((8,12,16,24,32))
        assert core.v6_enemy_init(C.byref(p),rng.randrange(-20,320),rng.randrange(-20,240),
            scenario%4,(scenario//4)%33-16,0,0,320,240,rng.randrange(4),rng.randrange(4),w,h)
        expected=Enemy.from_buffer_copy(p)
        cached=Enemy.from_buffer_copy(p)
        ref.enemy_reference_init(C.byref(p),raw,tileset,extra,custom,1)
        for tick in range(240):
            room.terrain=C.pointer(terrain)
            core.v6_enemy_step(C.byref(cached),C.byref(room),native,len(native))
            room.terrain=None
            core.v6_enemy_step(C.byref(p),C.byref(room),native,len(native))
            ref.enemy_reference_step(C.byref(expected))
            for name in FIELDS:
                assert getattr(cached,name)==getattr(expected,name), (scenario,tick,name,"cached")
                assert getattr(p,name)==getattr(expected,name), (scenario,tick,name,getattr(p,name),getattr(expected,name))
            ticks+=1
    p=Enemy()
    for kind,speed,w,h in ((4,2,16,16),(0,17,16,16),(0,2,0,16),(0,2,16,33)):
        assert not core.v6_enemy_init(C.byref(p),80,80,kind,speed,0,0,320,240,0,0,w,h)
    report=dict(scenarios=528,compared_ticks=ticks,cached_compared_ticks=ticks,reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Movement only: behaviours 0..3, integer speeds, tile/block collisions and patrol bounds; no rendering, damage, platforms or complete entity-loop equivalence.')
    (BUILD/'enemy-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))

if __name__=='__main__': main()
