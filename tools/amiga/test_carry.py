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

class Motion(C.Structure):
    _fields_=[("ax",C.c_int32),("pending_y",C.c_int)]

class Push(C.Structure):
    _fields_=[(name,C.c_int) for name in ("pending_y","visual_ground","visual_roof")]


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    original_reference()
    source=(BUILD/'player_reference.cpp').read_text()
    step=block(source,source.index('extern "C" void reference_step('))
    split=step.index('        entclass& e = obj.entities[0];')
    source+=step[:split].replace('reference_step','reference_input')+'}\n'
    source+='extern "C" void reference_physics(void) {\n'+step[split:]
    source+='\nextern "C" int reference_pending(void) { return obj.entities[0].newyp; }\n'
    source+='extern "C" int reference_ax(void) { return std::lround(obj.entities[0].ax*double(V6_ONE)); }\n'
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    logic=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    for name,kind in [('checkplatform','bool'),('hplatformat','float'),('entitycollideplatformfloor','float'),('entitycollideplatformroof','float'),('entitycollide','bool'),('movingplatformfix','void'),('stuckprevention','void'),('disableblockat','void'),('disableblock','void')]:
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
    # Extract the actual rule-2 collision branch, including its conveyor guard.
    collision=entity[entity.index('    case 2:   //Moving platforms'):entity.index('    case 3:   //Entity to entity')]
    source+='void entityclass::platformcollision(int i,int j) { switch(entities[j].rule) {\n'+collision+'} }\n'
    source+='extern "C" void post_reference(V6Block *blocks,unsigned count) { int i=0;\n'
    source+='for(int j=1;j<int(obj.entities.size());++j) obj.platformcollision(i,j);\n'
    source+='obj.stuckprevention(0);\n'
    source+='for(unsigned j=0;j<count;++j) { const blockclass& b=obj.blocks[obj.blocks.size()-count+j]; blocks[j].w=b.wp; blocks[j].h=b.hp; } }\n'
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
    core.v6_player_input.argtypes=[pp,C.c_uint,C.POINTER(Motion)]
    core.v6_player_physics.argtypes=[pp,rp,C.POINTER(Motion),C.c_void_p,C.c_void_p]
    ref.reference_input.argtypes=[C.c_uint]
    core.v6_player_unstick.argtypes=[pp,rp]
    core.v6_platform_disable_overlaps.argtypes=[pp,ep,C.c_uint,bp,C.c_uint]
    ref.post_reference.argtypes=[bp,C.c_uint]
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
    ordered=0
    for sequence in range(60):
        p=Player();core.v6_player_init(C.byref(p),100,81 if sequence%2==0 else 110,sequence%2)
        motion=Motion(0,p.y);push=Push(p.y,0,0)
        actors=(Enemy*2)()
        for i in range(2):
            actors[i].x=80;actors[i].y=104;actors[i].w=32;actors[i].h=8
            actors[i].behavior=0 if i==0 else 2;actors[i].vy=3 if i==0 else 0
            actors[i].vx=0 if i==0 else 3;actors[i].state=1;actors[i].onwall=2
        blocks=(DynamicBlock*2)()
        room.blocks=blocks;room.block_count=2
        for tick in range(200):
            for i in range(2):
                # Prescribed platform positions isolate stage order from movement.
                actors[i].x=80+(tick//4%8)*2
                actors[i].y=104+(tick//6%4)*2 if i==0 else 72
                blocks[i]=DynamicBlock(actors[i].x,actors[i].y,32,8,0,0)
            buttons=rng.choice((0,1,2,4,5,6));life=10-tick if tick<10 else 0
            if life>5:buttons|=8
            ref.carry_init(C.byref(p),tiles,room.tileset,room.extra_row,blocks,2,actors,2)
            ref.reference_input(buttons)
            expected_ax=ref.reference_ax()
            expected_s=Push(motion.pending_y,push.visual_ground,push.visual_roof)
            expected_e=Enemy.from_buffer_copy(actors[0])
            ref.push_reference(C.byref(expected_e),C.byref(expected_s))
            ref.carry_reference(life,expected_s.pending_y)
            ref.reference_physics()
            expected=Player();ref.reference_read(C.byref(expected))
            for cached in (False,True):
                actual=Player.from_buffer_copy(p);actual_m=Motion.from_buffer_copy(motion)
                actual_s=Push(motion.pending_y,push.visual_ground,push.visual_roof)
                actual_e=(Enemy*2).from_buffer_copy(actors)
                room.terrain=C.pointer(terrain) if cached else None
                core.v6_player_input(C.byref(actual),buttons,C.byref(actual_m))
                assert actual_m.ax==expected_ax
                core.v6_platform_push_vertical(C.byref(actual_e[0]),C.byref(actual),C.byref(room),C.byref(actual_s))
                core.v6_platform_carry_horizontal(C.byref(actual),C.byref(room),actual_e,2,life,actual_s.pending_y)
                core.v6_player_physics(C.byref(actual),C.byref(room),C.byref(actual_m),None,None)
                for field in FIELDS:
                    assert getattr(actual,field)==getattr(expected,field),('ordered',sequence,tick,cached,field)
                assert actual_m.ax==0 and actual_m.pending_y==ref.reference_pending()
                assert bytes(actual_s)==bytes(expected_s) and bytes(actual_e[0])==bytes(expected_e)
            p=actual;motion=actual_m;push=actual_s
            actors[0].state=actual_e[0].state
            ordered+=1
    counts['ordered_transport_ticks']=ordered
    corrected=disabled=retried=0
    for trial in range(12000):
        tiles=(C.c_uint16*1200)()
        # All tilesets, every directional orientation, and solid terrain.
        for y in range(9,15):
            for x in range(10,17):
                tiles[y*40+x]=rng.choice((0,0,0,1,14,15,16,17,80))
        room=Room(tiles,trial%3,trial%2)
        terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
        p=Player();core.v6_player_init(C.byref(p),rng.randrange(65,140),rng.randrange(65,125),trial%2)
        p.vx=int(C.c_float(rng.choice((-5.7,-3.8,-1.9,0,1.9,3.8,5.7))).value*16777216)
        actors=(Enemy*2)()
        blocks=(DynamicBlock*5)()
        for i in range(2):
            actors[i].x=88+i*16;actors[i].y=88+i*8
            actors[i].w=32;actors[i].h=8;actors[i].behavior=trial%4
            blocks[i]=DynamicBlock(actors[i].x,actors[i].y,32,8,0,0)
        blocks[2]=DynamicBlock(88,88,0 if trial%7==0 else 32,8,0,0)
        blocks[3]=DynamicBlock(104,80,8,48,2,trial%4)
        blocks[4]=DynamicBlock(96,104,32,8,trial%2,0)
        expected_blocks=(DynamicBlock*5).from_buffer_copy(blocks)
        ref.carry_init(C.byref(p),tiles,room.tileset,room.extra_row,blocks,5,actors,2)
        ref.post_reference(expected_blocks,5)
        expected=Player();ref.reference_read(C.byref(expected))
        for cached in (False,True):
            actual=Player.from_buffer_copy(p)
            actual_blocks=(DynamicBlock*5).from_buffer_copy(blocks)
            room.blocks=actual_blocks;room.block_count=5
            room.terrain=C.pointer(terrain) if cached else None
            core.v6_platform_disable_overlaps(C.byref(actual),actors,2,actual_blocks,5)
            core.v6_player_unstick(C.byref(actual),C.byref(room))
            for field in FIELDS:
                assert getattr(actual,field)==getattr(expected,field),('post',trial,cached,field,getattr(actual,field),getattr(expected,field))
            assert bytes(actual_blocks)==bytes(expected_blocks),('disabled',trial,cached)
        corrected+=expected.y!=p.y
        retried+=expected.vx!=p.vx
        disabled+=bytes(expected_blocks)!=bytes(blocks)
    assert corrected and retried and disabled
    counts.update(post_physics=12000,stuck_corrections=corrected,stuck_retries=retried,overlap_disables=disabled)
    assert attempts>100 and moved>100
    report=dict(**counts,cached_and_uncached=True,transport_attempts=attempts,position_changes=moved,
        reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Isolated explicit-target collision, horizontal carry, movingplatformfix and post-physics overlap/stuck correction; ordered input/push/carry/physics with prescribed platform positions; no complete platform loop, crush-death equivalence or native scene.')
    (BUILD/'carry-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))

if __name__=='__main__':main()
