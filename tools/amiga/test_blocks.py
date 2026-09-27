#!/usr/bin/env python3
"""Dynamic collision blocks: original checkblocks/lifecycle/player comparisons.

Prescribed block motion tests collision only, not platform carry/crush ordering.
"""
import ctypes as C
import hashlib
import json
import random
import subprocess
from pack_rooms import ROOT
from test_player import BUILD, Player, Room, Terrain, DynamicBlock, FIELDS, block, build_libraries


def main():
    core, _, _ = build_libraries()
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    source=(BUILD/'player_reference.cpp').read_text()
    source+='\n#include "blocks.h"\n'
    for name in ('disableblock','disableblockat','moveblockto'):
        source+=block(entity,entity.index('void entityclass::'+name+'('))+'\n'
    source+=r'''
static int original_type(int type) {
    return type==V6_BLOCK?BLOCK:type==V6_SAFE?SAFE:DIRECTIONAL;
}
extern "C" void reference_blocks(const V6Block *p,unsigned count) {
    obj.blocks.clear();
    for(int i=0;i<(29+map.extrarow)*40;++i) {
        int tile=map.contents[i];
        if(tile>=14 && tile<=17) {
            blockclass b={DIRECTIONAL,tile-14,{(i%40)*8,(i/40)*8,8,8},0,0,0,0};
            obj.blocks.push_back(b);
        }
    }
    for(unsigned i=0;i<count;++i) {
        blockclass b={original_type(p[i].type),p[i].trigger,{p[i].x,p[i].y,p[i].w,p[i].h},p[i].x,p[i].y,p[i].w,p[i].h};
        obj.blocks.push_back(b);
    }
}
extern "C" int reference_hit(const V6Block *p,int x,int y,int w,int h,int dx,int dy,int enemy) {
    obj.blocks.clear();
    blockclass b={original_type(p->type),p->trigger,{p->x,p->y,p->w,p->h},0,0,0,0};
    obj.blocks.push_back(b);
    return obj.checkblocks({x,y,w,h},dx,dy,enemy?1:0,false);
}
extern "C" void reference_lifecycle(V6Block *p,unsigned count,int move,int ox,int oy,int x,int y,int w,int h) {
    obj.blocks.clear();
    for(unsigned i=0;i<count;++i) {
        blockclass b={p[i].type,p[i].trigger,{p[i].x,p[i].y,p[i].w,p[i].h},p[i].x,p[i].y,p[i].w,p[i].h};
        obj.blocks.push_back(b);
    }
    if(move) obj.moveblockto(ox,oy,x,y,w,h); else obj.disableblockat(ox,oy);
    for(unsigned i=0;i<count;++i) {
        const blockclass& b=obj.blocks[i];
        p[i]={b.xp,b.yp,b.rect.w,b.rect.h,b.type,b.trigger};
    }
}
'''
    (BUILD/'blocks_reference.cpp').write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),
        str(BUILD/'blocks_reference.cpp'),'-L/opt/homebrew/lib','-lSDL3',
        '-o',str(BUILD/'blocks_reference.so')],check=True)
    (BUILD/'blocks_test_api.c').write_text('''#include "blocks.h"
int native_hit(const V6Block *p,int x,int y,int w,int h,int dx,int dy,int enemy) {
    return v6_block_hit(p,x,y,w,h,dx,dy,enemy);
}
''')
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        str(ROOT/'amiga_version/blocks.c'),str(BUILD/'blocks_test_api.c'),
        '-o',str(BUILD/'blocks.so')],check=True)
    ref=C.CDLL(str(BUILD/'blocks_reference.so')); native=C.CDLL(str(BUILD/'blocks.so'))
    bp=C.POINTER(DynamicBlock)
    for fn in (native.native_hit,ref.reference_hit): fn.argtypes=[bp]+[C.c_int]*7
    native.v6_blocks_disable_at.argtypes=[bp,C.c_uint,C.c_int,C.c_int]
    native.v6_blocks_move.argtypes=[bp,C.c_uint]+[C.c_int]*6
    ref.reference_lifecycle.argtypes=[bp,C.c_uint]+[C.c_int]*7
    ref.reference_blocks.argtypes=[bp,C.c_uint]
    ref.reference_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int,C.c_int]
    ref.reference_step.argtypes=[C.c_uint]; ref.reference_read.argtypes=[C.POINTER(Player)]
    rng=random.Random(6800032)
    hits=0
    for kind in range(3):
        for trigger in range(4):
            for dx in (-1,0,1):
                for dy in (-1,0,1):
                    for enemy in (0,1):
                        for _ in range(100):
                            b=DynamicBlock(80,80,rng.choice((-1,0,1,8,32,64)),rng.choice((-1,0,1,8,32)),kind,trigger)
                            args=(rng.randrange(60,145),rng.randrange(60,113),rng.choice((0,1,12,32)),rng.choice((0,1,21,32)),dx,dy,enemy)
                            assert native.native_hit(C.byref(b),*args)==ref.reference_hit(C.byref(b),*args), (kind,trigger,args)
                            hits+=1
    lifecycle=0
    for _ in range(2000):
        # Duplicate origins deliberately exercise all-disable vs first-move.
        blocks=(DynamicBlock*4)(*(DynamicBlock(80+(i%2)*8,80,32,8,i%3,i%4) for i in range(4)))
        expected=(DynamicBlock*4).from_buffer_copy(blocks)
        for step in range(8):
            ox,oy=(blocks[rng.randrange(4)].x,80) if step%3 else (300,200)
            move=step%2
            args=(ox,oy,rng.randrange(60,100),80,rng.choice((0,8,32)),rng.choice((0,8)))
            if move: native.v6_blocks_move(blocks,4,*args)
            else: native.v6_blocks_disable_at(blocks,4,ox,oy)
            ref.reference_lifecycle(expected,4,move,*args)
            assert bytes(blocks)==bytes(expected)
            lifecycle+=1
    ticks=flips=grounds=roofs=0
    for scenario in range(240):
        tiles=(C.c_uint16*1200)()
        for y in range(30):
            for x in range(40):
                tiles[y*40+x]=80 if x in (0,39) or y in (0,29) else 0
        if scenario%3==0: tiles[12*40+14]=14+scenario%4
        room=Room(tiles,scenario%2,1)
        terrain=Terrain(); core.v6_terrain_build(C.byref(terrain),C.byref(room))
        blocks=(DynamicBlock*3)(DynamicBlock(80,104,64,8,0,0),DynamicBlock(144,64,8,72,scenario%3,scenario%4),DynamicBlock(80,104,0,0,0,0))
        room.blocks=blocks; room.block_count=3
        p=Player(); core.v6_player_init(C.byref(p),100,81 if scenario%2==0 else 110,scenario%2)
        cached=Player.from_buffer_copy(p); expected=Player()
        ref.reference_init(C.byref(p),tiles,room.tileset,1)
        for tick in range(180):
            # No transport is injected: only the rectangles move/disable.
            blocks[0].x=80+(tick//8%4)*2 if scenario%4==0 else 80
            blocks[0].w=0 if scenario%5==0 and tick%50>=35 else 64
            blocks[0].h=8
            buttons=(4 if tick%17 in (2,3) else 0) | (0 if tick<12 else rng.choice((0,1,2)))
            if tick%37==0: buttons|=8
            ref.reference_blocks(blocks,3); ref.reference_step(buttons); ref.reference_read(C.byref(expected))
            room.terrain=None; core.v6_player_step(C.byref(p),C.byref(room),buttons)
            room.terrain=C.pointer(terrain); core.v6_player_step(C.byref(cached),C.byref(room),buttons)
            for field in FIELDS:
                assert getattr(p,field)==getattr(expected,field), (scenario,tick,field,'plain')
                assert getattr(cached,field)==getattr(expected,field), (scenario,tick,field,'cache')
            grounds+=p.ground==2; roofs+=p.roof==2; ticks+=1
        flips+=p.flips
    assert flips and grounds and roofs
    report=dict(block_queries=hits,lifecycle_operations=lifecycle,scenarios=240,player_ticks=ticks,
                cached_player_ticks=ticks,flips=flips,floor_contacts=grounds,roof_contacts=roofs,
                reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
                scope='Dynamic rectangle collision and block lifecycle only; no platform carrying, crushing or complete game-loop equivalence.')
    (BUILD/'blocks-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__': main()
