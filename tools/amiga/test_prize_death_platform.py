#!/usr/bin/env python3
"""Compare Prize death relocation with extracted Logic/Entity source rules."""
import ctypes as C
import subprocess
from pathlib import Path
from test_player import block
from test_enemy import Enemy,Block
ROOT=Path(__file__).resolve().parents[2]

def main():
    build=ROOT/'build/amiga-prize-death-platform';build.mkdir(parents=True,exist_ok=True)
    logic=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=logic.index('if (obj.entities[i].type == EntityType_MOVING)',logic.index('if (game.deathseq != -1)'))
    relocation=block(logic,start)
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    methods='\n'.join(block(entity,entity.index('void entityclass::'+name)) for name in
                      ('disableblock( int t )','disableblockat(int x, int y)','moveblockto(int x1, int y1, int x2, int y2, int w, int h)'))
    source='''#include <vector>
#include "enemy.h"
#define INBOUNDS_VEC(i,v) ((unsigned)(i)<(v).size())
#define vlog_error(x) ((void)0)
#define EntityType_MOVING 0
struct Rect {int x,y,w,h;};
struct B {int xp,yp,wp,hp,type,trigger;Rect rect;
void rectset(int x,int y,int w,int h){rect={x,y,w,h};}};
struct E {int type,xp,yp,newxp,w,h;};
struct entityclass {std::vector<E> entities;std::vector<B> blocks;
void disableblock(int);void disableblockat(int,int);void moveblockto(int,int,int,int,int,int);} obj;
'''+methods+'''
extern "C" void reference(V6Enemy *p,V6Block *blocks,unsigned count) {
obj.entities={{0,p->x,p->y,p->x,p->w,p->h}};obj.blocks.clear();
for(unsigned k=0;k<count;++k){auto b=blocks[k];obj.blocks.push_back({b.x,b.y,b.w,b.h,b.type,b.trigger,{b.x,b.y,b.w,b.h}});}
unsigned i=0;
'''+relocation+'''
p->x=obj.entities[0].xp;
for(unsigned k=0;k<count;++k){auto b=obj.blocks[k];blocks[k]={b.xp,b.yp,b.rect.w,b.rect.h,b.type,b.trigger};}
}
'''
    (build/'reference.cpp').write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-I'+str(ROOT/'amiga_version'),
                    str(build/'reference.cpp'),'-o',str(build/'reference.so')],check=True)
    bridge='''#include "prize.h"
unsigned actual(V6Enemy *p,V6Block *blocks,unsigned count) {
V6Prize s={0};V6Room room={0};s.waiting=*p;s.block_count=count;
for(unsigned i=0;i<count;++i)s.blocks[i]=blocks[i];
unsigned events=v6_prize_death(&s,&room);*p=s.waiting;
for(unsigned i=0;i<count;++i)blocks[i]=s.blocks[i];return events;
}
'''
    (build/'bridge.c').write_text(bridge)
    sources=('prize','platform_gate','disappearing','trinkets','checkpoints','platform','enemy','player','terrain','blocks')
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all',
                    '-I'+str(ROOT/'amiga_version'),str(build/'bridge.c'),
                    *[str(ROOT/'amiga_version'/(s+'.c')) for s in sources],'-o',str(build/'core.so')],check=True)
    core=C.CDLL(str(build/'core.so')).actual;reference=C.CDLL(str(build/'reference.so')).reference
    core.argtypes=reference.argtypes=[C.POINTER(Enemy),C.POINTER(Block),C.c_uint]
    checks=0
    for x in range(-16,321):
        for state in range(4):
            for velocity in (-4,0,4):
                for layout in range(6):
                    p=Enemy(x,72,88,70,velocity,0,15,4,state,2,0,0,320,240,0,0,32,8)
                    wanted=Enemy.from_buffer_copy(p)
                    blocks=(Block*4)(Block(120,112,32,8,0,0),Block(x,72,32,8,0,1),
                                     Block(x if layout==2 else 200,72,32,8,0,2),Block(120,128,32,8,0,3))
                    if layout==1:blocks[1].w=blocks[1].h=0
                    if layout==3:blocks[1].y=73
                    if layout==4:blocks[1].x=x+1
                    if layout==5:blocks[0]=Block(x,72,0,0,0,9)
                    expected=(Block*4).from_buffer_copy(blocks)
                    reference(C.byref(wanted),expected,4)
                    assert core(C.byref(p),blocks,4)==0
                    assert bytes(p)==bytes(wanted) and bytes(blocks)==bytes(expected),(x,state,velocity,layout)
                    before=bytes(p),bytes(blocks)
                    assert core(C.byref(p),blocks,4)==0 and (bytes(p),bytes(blocks))==before
                    checks+=1
    print(f'PASS Prize death platform: {checks} original-source relocations; x=152 boundary, disabled/missing/duplicate blocks, retained velocity/state/history and idempotent death ticks')
if __name__=='__main__':main()
