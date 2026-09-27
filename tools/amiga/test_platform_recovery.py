#!/usr/bin/env python3
"""Ordinary moving-platform recovery vs extracted life and ordered movement."""
import ctypes as C
import hashlib
import json
import subprocess
from test_player import ROOT,BUILD,Player,DynamicBlock,FIELDS,block
from test_enemy import Enemy,FIELDS as ENEMY_FIELDS
from test_carry import Push
from test_platform_loop import reference_source


def main():
    source=reference_source()
    shim=(ROOT/'tools/amiga/reference_shim.h').read_text().replace(
        '    int lifeseq;','    int lifeseq,savegc; bool noflashingmode; void lifesequence();')
    (BUILD/'platform_recovery_shim.h').write_text(shim)
    source=source.replace('"reference_shim.h"','"platform_recovery_shim.h"')
    # Use original life method before the extracted platform scheduling passes.
    source=source.replace('    reference_input(input);','''    if(game.lifeseq>5) input|=V6_NO_CONTROL;
    reference_input(input);
    game.lifesequence();''').replace('game.lifeseq=life;', '(void)life;')
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    source+='\n'+block(game,game.index('void Game::lifesequence(void)'))+r'''
extern "C" void recovery_start(int gravity) { game.lifeseq=10;game.savegc=gravity; }
extern "C" int recovery_life() { return game.lifeseq; }
'''
    (BUILD/'platform_recovery_reference.cpp').write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(BUILD),
        str(BUILD/'platform_recovery_reference.cpp'),'-L/opt/homebrew/lib','-lSDL3',
        '-o',str(BUILD/'platform_recovery_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','slice.c','terrain.c','platform.c','enemy.c','blocks.c')],
        str(ROOT/'tools/amiga/recovery_session.c'),'-o',str(BUILD/'platform_recovery.so')],check=True)
    core=C.CDLL(str(BUILD/'platform_recovery.so'));ref=C.CDLL(str(BUILD/'platform_recovery_reference.so'))
    pp=C.POINTER(Player);tp=C.POINTER(C.c_uint16);ep=C.POINTER(Enemy);bp=C.POINTER(DynamicBlock)
    core.v6_platform_init.argtypes=[ep]+[C.c_int]*8
    core.recovery_platform_init.argtypes=[pp,tp,C.c_int,C.c_int,ep,C.c_uint,C.c_uint]
    core.recovery_step.argtypes=[C.c_uint,C.c_int];core.recovery_read.argtypes=[pp,C.POINTER(C.c_int)]
    core.recovery_platform_read.argtypes=[ep,bp,C.POINTER(C.c_int),C.POINTER(Push)]
    ref.loop_init.argtypes=[pp,tp,C.c_int,C.c_int,bp,C.c_uint,ep,C.c_uint]
    ref.loop_step.argtypes=[C.c_uint,C.c_uint,C.c_int,ep,C.c_uint,bp,C.c_uint,C.POINTER(Push)]
    ref.reference_read.argtypes=[pp];ref.recovery_start.argtypes=[C.c_int]
    tiles=(C.c_uint16*1200)()
    for y in range(30):
        for x in range(40):
            if x in (0,39) or y in (0,28):tiles[y*40+x]=80
    cases=ticks=0
    for behavior in range(5): # Fifth case has both axes and overlapping origins.
        for speed in (0,1,3,6):
            for gravity in (0,1):
                for held in (0,1):
                    for pattern in range(3):
                        for cached in (0,1):
                            n=4 if behavior==4 else 1
                            axes=3 if n==4 else (1 if behavior<2 else 2)
                            actors=(Enemy*n)();blocks=(DynamicBlock*n)()
                            for i in range(n):
                                assert core.v6_platform_init(C.byref(actors[i]),144,120,i if n==4 else behavior,speed,64,64,256,192)
                                blocks[i]=DynamicBlock(144,120,32,8,0,0)
                            p=Player();p.x=p.old_x=150;p.y=p.old_y=126 if gravity else 97
                            p.dir=1;p.gravity=gravity;p.held=held;p.buffer=4 if held else 0
                            p.ground=-20 if gravity else 2;p.roof=2 if gravity else -20
                            core.recovery_platform_init(C.byref(p),tiles,gravity,cached,actors,n,axes)
                            ref.loop_init(C.byref(p),tiles,0,0,blocks,n,actors,n);ref.recovery_start(gravity)
                            actual_actors=(Enemy*n)();actual_blocks=(DynamicBlock*n)()
                            expected=Player();state=(C.c_int*5)();pending=C.c_int();visual=Push();expected_visual=Push()
                            for tick in range(24):
                                buttons=(0,4,4 if tick%8<4 else 2)[pattern]
                                ref.loop_step(buttons,axes,0,actors,n,blocks,n,C.byref(expected_visual))
                                ref.reference_read(C.byref(expected))
                                core.recovery_step(buttons,0);core.recovery_read(C.byref(p),state)
                                core.recovery_platform_read(actual_actors,actual_blocks,C.byref(pending),C.byref(visual))
                                for field in FIELDS:
                                    assert getattr(p,field)==getattr(expected,field),(cases,tick,field,getattr(p,field),getattr(expected,field))
                                for i in range(n):
                                    for field in ENEMY_FIELDS:
                                        assert getattr(actual_actors[i],field)==getattr(actors[i],field),(cases,tick,i,field)
                                    assert bytes(actual_blocks[i])==bytes(blocks[i]),(cases,tick,i,'block')
                                assert pending.value==ref.reference_pending(),(cases,tick,'pending')
                                assert (visual.visual_ground,visual.visual_roof)==(expected_visual.visual_ground,expected_visual.visual_roof),(cases,tick,'visual')
                                assert state[0]==ref.recovery_life() and state[1]==-1 and not any(state[2:]),(cases,tick,list(state))
                                if behavior==3 and speed==3 and gravity==0 and held==0 and pattern==0 and tick<3:
                                    assert p.x==(150 if tick<2 else 153),(tick,'recovery carry gate',p.x)
                                ticks+=1
                            cases+=1
    report=dict(cases=cases,ticks=ticks,reference_sha256=hashlib.sha256((shim+source).encode()).hexdigest(),
        scope='Synthetic recovery on ordinary platforms, cached/uncached: source life timer, input, reverse-order platform transport, physics and overlap/stuck correction. Single directions plus four overlapping mixed-axis actors. No complete preceding death, checkpoint entities, rendering, conveyors or campaign loop.')
    (BUILD/'platform-recovery-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
