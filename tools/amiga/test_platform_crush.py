#!/usr/bin/env python3
"""Solid-wall compression and spike pushes through the ordered platform loop."""
import ctypes as C
import hashlib
import json
import subprocess
from pack_rooms import ROOT
from test_player import BUILD,Player,Room,Terrain,DynamicBlock,FIELDS
from test_enemy import Enemy,FIELDS as ENEMY_FIELDS
from test_carry import Motion,Push
from test_platform_loop import reference_source


def main():
    source=reference_source()+r"""
extern "C" int damage_after_collision(void) {
    // The source-derived hazard wrapper rebuilds the map's damage blocks.
    // Keep the moving collision blocks for the next live update.
    const std::vector<blockclass> saved=obj.blocks;
    int hurt=reference_hurt();
    obj.blocks=saved;
    return hurt;
}
"""
    path=BUILD/'crush_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'crush_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','platform.c','enemy.c','blocks.c','terrain.c','slice.c')],
        '-I'+str(ROOT/'amiga_version'),str(ROOT/'tools/amiga/crush_session.c'),
        '-o',str(BUILD/'crush.so')],check=True)
    core=C.CDLL(str(BUILD/'crush.so'));ref=C.CDLL(str(BUILD/'crush_reference.so'))
    pp=C.POINTER(Player);rp=C.POINTER(Room);ep=C.POINTER(Enemy);bp=C.POINTER(DynamicBlock)
    core.v6_player_init.argtypes=[pp]+[C.c_int]*3
    core.v6_platform_init.argtypes=[ep]+[C.c_int]*8
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),rp]
    core.v6_player_input.argtypes=[pp,C.c_uint,C.POINTER(Motion)]
    core.v6_player_physics.argtypes=[pp,rp,C.POINTER(Motion),C.c_void_p,C.c_void_p]
    core.v6_platform_transport.argtypes=[pp,rp,ep,C.c_uint,bp,C.c_uint,C.c_uint,C.c_int,C.POINTER(Push)]
    core.v6_platform_disable_overlaps.argtypes=[pp,ep,C.c_uint,bp,C.c_uint]
    core.v6_player_unstick.argtypes=[pp,rp]
    core.v6_player_hurt.argtypes=[pp,rp]
    ref.loop_init.argtypes=[pp,C.POINTER(C.c_uint16),C.c_int,C.c_int,bp,C.c_uint,ep,C.c_uint]
    ref.loop_step.argtypes=[C.c_uint,C.c_uint,C.c_int,ep,C.c_uint,bp,C.c_uint,C.POINTER(Push)]
    ref.reference_read.argtypes=[pp]
    core.crush_session_init.argtypes=[C.c_int]*6
    core.crush_session_read.argtypes=[pp,ep,bp,C.POINTER(C.c_int)]
    cases=ticks=reversals=deaths=0;frozen_ticks=0
    traces=[]
    for tileset in (0,1):
        for down in (False,True):
            for tile in (80,6,7,8,9,49,50):
                for speed in (1,2,3,6):
                    for x in (103,108,115):
                        tiles=(C.c_uint16*1200)()
                        row=15 if down else 8
                        for tx in range(9,20):tiles[row*40+tx]=tile
                        p=Player();core.v6_player_init(C.byref(p),x,97 if down else 70,int(down))
                        e=(Enemy*1)()
                        assert core.v6_platform_init(C.byref(e[0]),104,91 if down else 93,
                                                     0 if down else 1,speed,48,32,224,200)
                        b=(DynamicBlock*1)(DynamicBlock(e[0].x,e[0].y,32,8,0,0))
                        ref.loop_init(C.byref(p),tiles,tileset,0,b,1,e,1)
                        expected_e=(Enemy*1).from_buffer_copy(e);expected_b=(DynamicBlock*1).from_buffer_copy(b)
                        expected_push=Push(p.y,0,0)
                        states=[]
                        for cached in (False,True):
                            actual=Player.from_buffer_copy(p)
                            actors=(Enemy*1).from_buffer_copy(e);blocks=(DynamicBlock*1).from_buffer_copy(b)
                            room=Room(tiles,tileset,0);room.blocks=blocks;room.block_count=1
                            terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
                            if cached:room.terrain=C.pointer(terrain)
                            assert not core.v6_player_hurt(C.byref(actual),C.byref(room))
                            states.append((actual,actors,blocks,room,terrain,Motion(0,p.y),Push(p.y,0,0)))
                        death_tick=0
                        for tick in range(1,17):
                            ref.loop_step(0,1,0,expected_e,1,expected_b,1,C.byref(expected_push))
                            expected=Player();ref.reference_read(C.byref(expected))
                            hurt=ref.damage_after_collision()
                            for cached,(actual,actors,blocks,room,terrain,motion,push) in enumerate(states):
                                core.v6_player_input(C.byref(actual),0,C.byref(motion))
                                push.pending_y=motion.pending_y
                                core.v6_platform_transport(C.byref(actual),C.byref(room),actors,1,blocks,1,1,0,C.byref(push))
                                core.v6_player_physics(C.byref(actual),C.byref(room),C.byref(motion),None,None)
                                core.v6_platform_disable_overlaps(C.byref(actual),actors,1,blocks,1)
                                core.v6_player_unstick(C.byref(actual),C.byref(room))
                                for field in FIELDS:
                                    assert getattr(actual,field)==getattr(expected,field),(cases,tick,cached,field)
                                for field in ENEMY_FIELDS:
                                    assert getattr(actors[0],field)==getattr(expected_e[0],field),(cases,tick,cached,'platform',field)
                                assert bytes(blocks)==bytes(expected_b),(cases,tick,cached,'blocks')
                                assert motion.pending_y==ref.reference_pending()
                                assert (push.visual_ground,push.visual_roof)==(expected_push.visual_ground,expected_push.visual_roof)
                                assert core.v6_player_hurt(C.byref(actual),C.byref(room))==hurt,(cases,tick,cached,'damage')
                            if tile==80 and tick==1:
                                # The platform is still far from the wall; only
                                # its unsuccessful player push schedules reversal.
                                assert expected_e[0].y==e[0].y+(speed if down else -speed)
                                assert expected_e[0].state==expected_e[0].onwall
                                assert expected_e[0].state!=1 and not hurt
                                reversals+=1
                            ticks+=1
                            if hurt:
                                death_tick=tick;deaths+=1
                                break  # Death handling replaces further live movement.
                        assert (death_tick==0)==(tile==80),(tileset,down,tile,speed,x,death_tick)
                        # Repeat through the session callback to check that the
                        # matched damage result starts the actual slice lifecycle.
                        for cached in (False,True):
                            core.crush_session_init(tileset,int(down),tile,speed,x,int(cached))
                            session_p=Player();session_e=Enemy();session_b=DynamicBlock()
                            status=(C.c_int*6)()
                            for frame in range(1,(death_tick or 16)+1):
                                core.crush_session_step()
                                core.crush_session_read(C.byref(session_p),C.byref(session_e),C.byref(session_b),status)
                                assert status[0]==(30 if frame==death_tick else -1),(cases,frame,'death trigger')
                            assert bytes(session_p)==bytes(expected),(cases,cached,'session player')
                            assert bytes(session_e)==bytes(expected_e[0]) and bytes(session_b)==bytes(expected_b[0])
                            if death_tick:
                                frozen_player=Player.from_buffer_copy(session_p);frozen_platform=bytes(session_e);frozen_block=bytes(session_b)
                                for delay in range(1,31):
                                    core.crush_session_step()
                                    core.crush_session_read(C.byref(session_p),C.byref(session_e),C.byref(session_b),status)
                                    assert status[4]==death_tick and status[2]==1
                                    assert bytes(session_e)==frozen_platform and bytes(session_b)==frozen_block
                                    if delay<30:
                                        assert status[0]==30-delay and status[3]==0
                                        for field in FIELDS:
                                            if field not in ('ground','roof'):
                                                assert getattr(session_p,field)==getattr(frozen_player,field),(cases,delay,field)
                                    else:
                                        assert status[0]==-1 and status[1]==10 and status[3]==1
                                        assert status[5]&8
                                        assert session_p.x==x and session_p.y==(97 if down else 70)
                                        assert session_p.gravity==int(down) and session_p.vx==session_p.vy==0
                                    frozen_ticks+=1
                        traces.append(dict(tileset=tileset,down=down,tile=tile,speed=speed,x=x,
                                           damage_tick=death_tick,final_x=expected.x,final_y=expected.y))
                        cases+=1
    report=dict(cases=cases,compared_ticks=ticks,cached_compared_ticks=ticks,
        blocked_push_reversals=reversals,spike_push_damage_cases=deaths,death_delay_ticks=frozen_ticks,
        reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Synthetic compression and spike pushes through source-derived live movement, collision and damage checks; movement comparison stops at damage; separate native slice checks verify 30-tick freeze and respawn, not full desktop lifecycle or target replay.',
        fixtures=traces)
    (BUILD/'crush-test-report.json').write_text(json.dumps(report,indent=2)+chr(10))
    print('PASS:',json.dumps({k:v for k,v in report.items() if k!='fixtures'}))


if __name__=='__main__':main()
