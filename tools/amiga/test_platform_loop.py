#!/usr/bin/env python3
"""Ordinary-platform scheduling and player stages against extracted source."""
import ctypes as C
import hashlib
import json
import random
import re
import struct
import subprocess
from pack_rooms import ROOT, enemy_record
from test_player import BUILD, Player, Room, Terrain, DynamicBlock, FIELDS, block
from test_enemy import Enemy, FIELDS as ENEMY_FIELDS
from test_carry import reference_source as carry_reference_source, Motion, Push


def reference_source():
    source=carry_reference_source()
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    ent=(ROOT/'desktop_version/src/Ent.cpp').read_text()
    logic=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=entity.index('case 0: //Bounce, Start moving down')
    end=entity.index('case 4: //Always move left',start)
    source+=block(ent,ent.index('bool entclass::outside(void)'))+'\n'
    source+='bool entityclass::updateentities(int i) { switch(entities[i].behave) {\n'+entity[start:end]+'} return false; }\n'
    source+=block(entity,entity.index('void entityclass::moveblockto('))+'\n'
    start=logic.index('            if(obj.vertplatforms)',logic.index('//Ok, moving platform'))
    end=logic.index('\n            for (int ie',logic.index('//is the player standing on a moving platform?',start))
    scheduling=logic[start:end]
    source+=r'''
extern "C" void loop_init(const V6Player *p,const uint16_t *tiles,int set,int extra,
    const V6Block *blocks,unsigned count,const V6Platform *platforms,unsigned n) {
    carry_init(p,tiles,set,extra,blocks,count,platforms,n);
    obj.entities[0].newyp=p->y;
    for(unsigned i=0;i<n;++i) {
        entclass& e=obj.entities[i+1]; const V6Platform& a=platforms[i];
        e.type=EntityType_MOVING;e.isplatform=true;e.gravity=false;
        e.oldxp=a.old_x;e.oldyp=a.old_y;e.para=a.speed;
        e.x1=a.x1;e.y1=a.y1;e.x2=a.x2;e.y2=a.y2;
    }
}
extern "C" void loop_step(unsigned input,unsigned flags,int life,V6Platform *platforms,
    unsigned count,V6Block *blocks,unsigned block_count,V6PlatformPush *push) {
    reference_input(input);
    obj.vertplatforms=flags&1;obj.horplatforms=flags&2;game.lifeseq=life;
'''+scheduling+r'''
    reference_physics();
    post_reference(blocks,block_count);
    for(unsigned i=0;i<count;++i) {
        const entclass& e=obj.entities[i+1]; V6Platform& a=platforms[i];
        a.x=e.xp;a.y=e.yp;a.old_x=e.oldxp;a.old_y=e.oldyp;
        a.vx=e.vx;a.vy=e.vy;a.state=e.state;a.onwall=e.onwall;
    }
    for(unsigned i=0;i<block_count;++i) {
        const blockclass& b=obj.blocks[obj.blocks.size()-block_count+i];
        blocks[i].x=b.xp;blocks[i].y=b.yp;
    }
    push->visual_ground=obj.entities[0].visualonground;
    push->visual_roof=obj.entities[0].visualonroof;
}
'''
    return source


def main():
    source=reference_source()
    (BUILD/'platform_loop_reference.cpp').write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),
        str(BUILD/'platform_loop_reference.cpp'),'-L/opt/homebrew/lib','-lSDL3',
        '-o',str(BUILD/'platform_loop_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','enemy.c','platform.c','blocks.c','terrain.c')],
        '-o',str(BUILD/'platform_loop.so')],check=True)
    core=C.CDLL(str(BUILD/'platform_loop.so'));ref=C.CDLL(str(BUILD/'platform_loop_reference.so'))
    pp=C.POINTER(Player);rp=C.POINTER(Room);ep=C.POINTER(Enemy);bp=C.POINTER(DynamicBlock)
    core.v6_player_init.argtypes=[pp]+[C.c_int]*3
    core.v6_platform_init.argtypes=[ep]+[C.c_int]*8
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),rp]
    core.v6_player_input.argtypes=[pp,C.c_uint,C.POINTER(Motion)]
    core.v6_player_physics.argtypes=[pp,rp,C.POINTER(Motion),C.c_void_p,C.c_void_p]
    core.v6_platform_transport.argtypes=[pp,rp,ep,C.c_uint,bp,C.c_uint,C.c_uint,C.c_int,C.POINTER(Push)]
    core.v6_platform_disable_overlaps.argtypes=[pp,ep,C.c_uint,bp,C.c_uint]
    core.v6_player_unstick.argtypes=[pp,rp]
    ref.loop_init.argtypes=[pp,C.POINTER(C.c_uint16),C.c_int,C.c_int,bp,C.c_uint,ep,C.c_uint]
    ref.loop_step.argtypes=[C.c_uint,C.c_uint,C.c_int,ep,C.c_uint,bp,C.c_uint,C.POINTER(Push)]
    ref.reference_read.argtypes=[pp]
    rng=random.Random(6800016);ticks=0;fixture_trace=[];transport_ticks=0;reference_previous_x=156
    pick_trace=[]
    pick_buttons=[int(v) for v in re.findall(r'\d+',(ROOT/'tools/amiga/pick_replay.h').read_text().split('{',1)[1])]
    for scenario in range(98):
        tiles=(C.c_uint16*1200)()
        for y in range(30):
            for x in range(40):
                if x in (0,39) or y in (0,29):
                    tiles[y*40+x]=12 if scenario%3==2 else 80
                elif scenario%4==0 and x==20 and 6<y<22:
                    tiles[y*40+x]=14+(y%4)
        actors=(Enemy*4)()
        flags=scenario%4
        for i in range(4):
            # Zero speeds plus mixed-axis rooms expose membership in both passes.
            speed=(0,1,3,8)[(scenario//4+i)%4]
            assert core.v6_platform_init(C.byref(actors[i]),96+i*8,96+i*12,
                i,speed,64,64,248,184)
        initial=Player();core.v6_player_init(C.byref(initial),96,73 if scenario%2==0 else 106,scenario%2)
        blocks=(DynamicBlock*6)(*[DynamicBlock(a.x,a.y,32,8,0,0) for a in actors],
            DynamicBlock(96,96,32,8,0,0),DynamicBlock(144,72,8,96,2,scenario%4))
        count=4;block_count=6;tileset=scenario%3;extra=1
        if scenario==96:
            count=block_count=1;tileset=0;extra=0;flags=2
            for y in range(30):
                for x in range(40):tiles[y*40+x]=495 if y>=27 or x in (0,39) else 0
            actors=(Enemy*1)()
            assert core.v6_platform_init(C.byref(actors[0]),144,116,3,3,64,64,288,184)
            core.v6_player_init(C.byref(initial),156,93,0)
            blocks=(DynamicBlock*1)(DynamicBlock(144,116,32,8,0,0))
        if scenario==97:
            count=block_count=1;tileset=0;extra=0;flags=2
            tiles=(C.c_uint16*1200)(*struct.unpack('>1200H',enemy_record(scene='pick')[1]))
            actors=(Enemy*1)()
            assert core.v6_platform_init(C.byref(actors[0]),24,80,3,6,0,0,320,240)
            core.v6_player_init(C.byref(initial),60,174,1)
            blocks=(DynamicBlock*1)(DynamicBlock(24,80,32,8,0,0))
        expected_actors=(Enemy*count).from_buffer_copy(actors)
        expected_blocks=(DynamicBlock*block_count).from_buffer_copy(blocks)
        ref.loop_init(C.byref(initial),tiles,tileset,extra,blocks,block_count,actors,count)
        states=[]
        for cached in (False,True):
            p=Player.from_buffer_copy(initial)
            a=(Enemy*count).from_buffer_copy(actors);b=(DynamicBlock*block_count).from_buffer_copy(blocks)
            room=Room(tiles,tileset,extra);room.blocks=b;room.block_count=block_count
            terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
            if cached:room.terrain=C.pointer(terrain)
            states.append((p,a,b,room,terrain,Motion(0,p.y),Push(p.y,0,0)))
        expected_push=Push(initial.y,0,0)
        for tick in range(129 if scenario==97 else 240):
            buttons=rng.choice((0,0,1,2,4,5,6));life=max(0,10-tick)
            if scenario==96:buttons=life=0
            if scenario==97:buttons=pick_buttons[tick] if tick<len(pick_buttons) else 0;life=0
            if life>5:buttons|=8
            ref.loop_step(buttons,flags,life,expected_actors,count,expected_blocks,block_count,C.byref(expected_push))
            expected=Player();ref.reference_read(C.byref(expected))
            for cached,(p,a,b,room,terrain,motion,push) in enumerate(states):
                core.v6_player_input(C.byref(p),buttons,C.byref(motion))
                push.pending_y=motion.pending_y
                before=p.x
                core.v6_platform_transport(C.byref(p),C.byref(room),a,count,b,block_count,flags,life,C.byref(push))
                if scenario==96 and not cached and p.x!=before:transport_ticks+=1
                core.v6_player_physics(C.byref(p),C.byref(room),C.byref(motion),None,None)
                core.v6_platform_disable_overlaps(C.byref(p),a,count,b,block_count)
                core.v6_player_unstick(C.byref(p),C.byref(room))
                for field in FIELDS:
                    assert getattr(p,field)==getattr(expected,field),(scenario,tick,cached,field,getattr(p,field),getattr(expected,field))
                for i in range(count):
                    for field in ENEMY_FIELDS:
                        assert getattr(a[i],field)==getattr(expected_actors[i],field),(scenario,tick,cached,i,field)
                assert bytes(b)==bytes(expected_blocks),(scenario,tick,cached,'blocks')
                assert motion.pending_y==ref.reference_pending(),(scenario,tick,cached,'pending')
                assert (push.visual_ground,push.visual_roof)==(expected_push.visual_ground,expected_push.visual_roof),(scenario,tick,cached,'visual')
            if scenario==96:
                assert expected.vx==0
                reference_moved=expected.x!=reference_previous_x
                reference_previous_x=expected.x
                assert reference_moved
                assert transport_ticks==tick+1
                fixture_trace.append(dict(player_x=expected.x,player_y=expected.y,
                    player_vx=expected.vx,player_vy=expected.vy,gravity=expected.gravity,
                    enemy_x=expected_actors[0].x,enemy_y=expected_actors[0].y,
                    enemy_hits=tick+1))
            if scenario==97:
                pick_trace.append(dict(player_x=expected.x,player_y=expected.y,
                    player_vx=expected.vx,player_vy=expected.vy,gravity=expected.gravity,
                    flips=expected.flips,enemy_x=expected_actors[0].x,enemy_y=expected_actors[0].y))
            ticks+=1
    report=dict(scenarios=98,compared_ticks=ticks,cached_compared_ticks=ticks,
        reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Persistent ordinary-platform reverse-order scheduling, player input/transport/physics and overlap/stuck correction; no damage, lifecycle, scripts, conveyors, supercrewmates or native scene.')
    (BUILD/'platform-loop-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    (BUILD/'horizontal-reference-trace.json').write_text(json.dumps(fixture_trace,indent=2)+'\n')
    (BUILD/'pick-movement-reference.json').write_text(json.dumps(pick_trace,indent=2)+chr(10))
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
