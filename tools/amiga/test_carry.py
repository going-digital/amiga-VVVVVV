#!/usr/bin/env python3
"""Horizontal transport and pending-position collision vs original methods."""
import ctypes as C
import hashlib
import json
import random
import subprocess
from pack_rooms import ROOT
from test_player import BUILD,Player,Room,Terrain,DynamicBlock,FIELDS,block,original_reference
from test_enemy import Enemy

class Push(C.Structure):
    _fields_=[(name,C.c_int) for name in ("pending_y","visual_ground","visual_roof")]


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    original_reference()
    source=(BUILD/'player_reference.cpp').read_text()
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    logic=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    for name,kind in [('checkplatform','bool'),('hplatformat','float'),('entitycollideplatformfloor','float'),('entitycollideplatformroof','float'),('entitycollide','bool'),('movingplatformfix','void')]:
        source+=block(entity,entity.index(kind+' entityclass::'+name+'('))+'\n'
    start=logic.index('//is the player standing on a moving platform?')
    end=logic.index('\n            }\n\n            for',start)
    source+='\n#include "platform.h"\n'+r'''
extern "C" void carry_init(const V6Player *p,const uint16_t *tiles,int set,int extra,
    const V6Block *blocks,unsigned count,const V6Platform *platforms,unsigned n) {
    reference_init(p,tiles,set,extra);
    for(unsigned j=0;j<count;++j) {
        const V6Block& b=blocks[j];
        blockclass q={b.type==V6_BLOCK?BLOCK:b.type==V6_SAFE?SAFE:DIRECTIONAL,b.trigger,{b.x,b.y,b.w,b.h},b.x,b.y,b.w,b.h};
        obj.blocks.push_back(q);
    }
    for(unsigned j=0;j<n;++j) {
        entclass e;
        e.rule=2;e.behave=platforms[j].behavior;e.xp=platforms[j].x;e.yp=platforms[j].y;e.vx=platforms[j].vx;e.vy=platforms[j].vy;
        e.cx=platforms[j].cx;e.cy=platforms[j].cy;e.w=platforms[j].w;e.h=platforms[j].h;
        e.state=platforms[j].state;e.onwall=platforms[j].onwall;
        obj.entities.push_back(e);
    }
}
extern "C" void carry_reference(int life,int pending_y) {
    game.lifeseq=life;obj.entities[0].newyp=pending_y;
'''+logic[start:end]+r'''
}
extern "C" void push_reference(V6Platform *platform,V6PlatformPush *state) {
    obj.entities[0].newyp=state->pending_y;
    obj.entities[0].visualonground=state->visual_ground;obj.entities[0].visualonroof=state->visual_roof;
    obj.movingplatformfix(1,0);
    platform->state=obj.entities[1].state;
    state->pending_y=obj.entities[0].newyp;
    state->visual_ground=obj.entities[0].visualonground;state->visual_roof=obj.entities[0].visualonroof;
}
extern "C" void map_move_reference(int x,int y) {
    obj.entities[0].newxp=x; obj.entities[0].newyp=y; obj.entitymapcollision(0);
}
'''
    (BUILD/'carry_reference.cpp').write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),
        '-I'+str(ROOT/'tools/amiga'),str(BUILD/'carry_reference.cpp'),'-L/opt/homebrew/lib','-lSDL3',
        '-o',str(BUILD/'carry_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','enemy.c','platform.c','blocks.c','terrain.c')],
        '-o',str(BUILD/'carry.so')],check=True)
    core=C.CDLL(str(BUILD/'carry.so'));ref=C.CDLL(str(BUILD/'carry_reference.so'))
    pp=C.POINTER(Player);rp=C.POINTER(Room);bp=C.POINTER(DynamicBlock);ep=C.POINTER(Enemy)
    core.v6_player_init.argtypes=[pp]+[C.c_int]*3
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),rp]
    core.v6_player_map_move.argtypes=[pp,rp,C.c_int,C.c_int]
    core.v6_platform_carry_horizontal.argtypes=[pp,rp,ep,C.c_uint,C.c_int,C.c_int]
    ref.carry_init.argtypes=[pp,C.POINTER(C.c_uint16),C.c_int,C.c_int,bp,C.c_uint,ep,C.c_uint]
    ref.carry_reference.argtypes=[C.c_int,C.c_int]
    ref.map_move_reference.argtypes=[C.c_int,C.c_int];ref.reference_read.argtypes=[pp]
    ref.push_reference.argtypes=[ep,C.POINTER(Push)]
    core.v6_platform_push_vertical.argtypes=[ep,pp,rp,C.POINTER(Push)]
    rng=random.Random(680008)
    counts={'map_move':0,'horizontal_carry':0}; modes=tuple(counts);attempts=moved=0
    for scenario in range(120):
        tiles=(C.c_uint16*1200)()
        if scenario%3:
            for y in range(30):
                for x in range(40):
                    if x in (0,39) or y in (0,29) or (x==18 and 6<y<23):tiles[y*40+x]=80
        if scenario%4==0:tiles[12*40+14]=14+scenario%4
        room=Room(tiles,scenario%2,1)
        terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
        for trial in range(200):
            p=Player();core.v6_player_init(C.byref(p),rng.randrange(68,150),rng.choice((57,81,89,110)),trial%2)
            p.vx=(int(C.c_float(rng.choice((-5.7,-3.8,-1.9,1.9,3.8,5.7))).value*16777216)
                  if trial%2 else rng.randrange(-24,25)*4194304)
            p.vy=rng.randrange(-40,41)*4194304
            actors=(Enemy*3)();blocks=(DynamicBlock*4)()
            for i in range(3):
                actors[i].x=80+16*(i%2);actors[i].y=80+24*(i%2)
                actors[i].behavior=rng.randrange(4);actors[i].vx=rng.randrange(-16,17)
                blocks[i]=DynamicBlock(actors[i].x,actors[i].y,32 if trial%7 else 0,8,0,0)
            blocks[3]=DynamicBlock(136,80,8,64,trial%3,trial%4)
            room.blocks=blocks;room.block_count=4
            for mode in modes:
                ref.carry_init(C.byref(p),tiles,room.tileset,room.extra_row,blocks,4,actors,3)
                pending_y=p.y+rng.randrange(-4,5)
                target_x=p.x+rng.randrange(-16,17);life=rng.choice((-1,0,5,7,8,9,10))
                if mode=='map_move':ref.map_move_reference(target_x,pending_y)
                else:ref.carry_reference(life,pending_y)
                expected=Player();ref.reference_read(C.byref(expected))
                for cached in (False,True):
                    actual=Player.from_buffer_copy(p);room.terrain=C.pointer(terrain) if cached else None
                    if mode=='map_move':core.v6_player_map_move(C.byref(actual),C.byref(room),target_x,pending_y)
                    else:
                        attempted=core.v6_platform_carry_horizontal(C.byref(actual),C.byref(room),actors,3,life,pending_y)
                        if not cached:attempts+=attempted;moved+=actual.x!=p.x or actual.y!=p.y
                        if life>=8:assert not attempted and bytes(actual)==bytes(p)
                    for field in FIELDS:
                        assert getattr(actual,field)==getattr(expected,field),(scenario,trial,mode,cached,field,getattr(actual,field),getattr(expected,field))
                counts[mode]+=1
    pushes=reversals=snaps=0
    for trial in range(24000):
        p=Player();core.v6_player_init(C.byref(p),rng.randrange(68,130),rng.randrange(70,114),trial%2)
        p.vy=rng.randrange(-40,41)*4194304
        e=Enemy();e.x=96;e.y=96;e.w=32;e.h=8;e.vy=rng.randrange(-16,17);e.state=1;e.onwall=2
        blocks=(DynamicBlock*2)(DynamicBlock(96,96,32,8,0,0),DynamicBlock(72,80 if trial%2 else 112,96,8,0,0))
        if trial%3==0:blocks[1].w=0
        room.blocks=blocks;room.block_count=2
        state=Push(p.y+rng.randrange(-4,5),rng.randrange(-2,3),rng.randrange(-2,3))
        expected_e=Enemy.from_buffer_copy(e);expected_s=Push.from_buffer_copy(state)
        ref.carry_init(C.byref(p),tiles,room.tileset,room.extra_row,blocks,2,C.byref(e),1)
        ref.push_reference(C.byref(expected_e),C.byref(expected_s))
        expected=Player();ref.reference_read(C.byref(expected))
        for cached in (False,True):
            actual=Player.from_buffer_copy(p);actual_e=Enemy.from_buffer_copy(e);actual_s=Push.from_buffer_copy(state)
            room.terrain=C.pointer(terrain) if cached else None
            core.v6_platform_push_vertical(C.byref(actual_e),C.byref(actual),C.byref(room),C.byref(actual_s))
            for field in FIELDS:
                assert getattr(actual,field)==getattr(expected,field),('push',trial,cached,field)
            assert bytes(actual_e)==bytes(expected_e) and bytes(actual_s)==bytes(expected_s),('push-state',trial,cached)
        reversals+=expected_e.state!=e.state
        snaps+=expected.ground==2 or expected.roof==2
        pushes+=1
    assert reversals and snaps
    counts.update(vertical_push=pushes,platform_reversals=reversals,player_snaps=snaps)
    assert attempts>100 and moved>100
    report=dict(**counts,cached_and_uncached=True,transport_attempts=attempts,position_changes=moved,
        reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Isolated explicit-target collision, horizontal carry and movingplatformfix; no complete platform loop, crush-death equivalence or native scene.')
    (BUILD/'carry-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))

if __name__=='__main__':main()
