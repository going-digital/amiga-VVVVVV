#!/usr/bin/env python3
"""Static-room post-respawn movement against source input, life and physics."""
import ctypes as C
import hashlib
import json
import subprocess
from test_player import ROOT,BUILD,Player,FIELDS,original_reference,block


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    original_reference()
    source=(BUILD/'player_reference.cpp').read_text()
    shim=(ROOT/'tools/amiga/reference_shim.h').read_text().replace(
        '    int lifeseq;', '    int lifeseq,savegc; bool noflashingmode; void lifesequence();')
    (BUILD/'recovery_reference_shim.h').write_text(shim)
    source=source.replace('"reference_shim.h"','"recovery_reference_shim.h"')
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    source+='\n'+block(game,game.index('void Game::lifesequence(void)'))
    step=block(source,source.index('extern "C" void reference_step('))
    step=step.replace('reference_step','recovery_reference_step').replace(
        'const bool has_control = !(input & V6_NO_CONTROL);',
        'const bool has_control = game.lifeseq<=5 && !(input & V6_NO_CONTROL);')
    # Contacts do not depend on the life timer; insert the original life method
    # between input and physics. No platforms, scripts, hazards or transitions.
    step=step.replace('        entclass& e = obj.entities[0];','        game.lifesequence();\n        entclass& e = obj.entities[0];')
    source+='\n'+step+r'''
extern "C" void recovery_reference_init(const V6Player *p,const uint16_t *tiles,int gravity) {
    reference_init(p,tiles,0,0);game.lifeseq=10;game.savegc=gravity;
}
extern "C" void recovery_reference_life_tick() { game.lifesequence(); }
extern "C" int recovery_reference_life() { return game.lifeseq; }
'''
    (BUILD/'recovery_reference.cpp').write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-fno-fast-math',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(BUILD),str(BUILD/'recovery_reference.cpp'),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'recovery_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','slice.c','terrain.c')],
        str(ROOT/'tools/amiga/recovery_session.c'),'-o',str(BUILD/'recovery.so')],check=True)
    ref=C.CDLL(str(BUILD/'recovery_reference.so'));core=C.CDLL(str(BUILD/'recovery.so'))
    pp=C.POINTER(Player);tp=C.POINTER(C.c_uint16)
    core.recovery_init.argtypes=[pp,tp,C.c_int,C.c_int]
    core.recovery_step.argtypes=[C.c_uint,C.c_int]
    core.recovery_read.argtypes=[pp,C.POINTER(C.c_int)]
    ref.recovery_reference_init.argtypes=[pp,tp,C.c_int]
    ref.recovery_reference_step.argtypes=[C.c_uint];ref.reference_read.argtypes=[pp]
    tiles=(C.c_uint16*1200)()
    for y in range(30):
        for x in range(40):
            if x in (0,39) or y in (9,20):tiles[y*40+x]=80
    cases=ticks=0
    for gravity in (0,1):
        for held in (0,1):
            for buffered in range(6):
                for pattern in range(5):
                    for cached in (0,1):
                        p=Player();p.x=p.old_x=150;p.y=p.old_y=78 if gravity else 137
                        p.gravity=gravity if pattern!=4 else 1-gravity;p.dir=1;p.held=held;p.buffer=buffered
                        p.ground=2 if not gravity else -30;p.roof=2 if gravity else -30
                        p.tap_left=3;p.tap_right=2;p.flips=7
                        core.recovery_init(C.byref(p),tiles,gravity,cached)
                        ref.recovery_reference_init(C.byref(p),tiles,gravity)
                        expected=Player();state=(C.c_int*5)()
                        for tick in range(24):
                            buttons=(0,4,4 if tick%8<4 else 0,2|4,1 if tick<12 else 2)[pattern]
                            ref.recovery_reference_step(buttons)
                            ref.reference_read(C.byref(expected))
                            core.recovery_step(buttons,0);core.recovery_read(C.byref(p),state)
                            for field in FIELDS:
                                assert getattr(p,field)==getattr(expected,field),(cases,tick,field,getattr(p,field),getattr(expected,field))
                            assert state[0]==ref.recovery_reference_life() and state[1]==-1 and not any(state[2:]),(cases,tick,list(state))
                            ticks+=1
                        cases+=1
    # Restart during recovery: Logic.cpp still calls lifesequence before death.
    for elapsed in range(10):
        p=Player();p.x=p.old_x=150;p.y=p.old_y=137;p.dir=1;p.ground=2
        core.recovery_init(C.byref(p),tiles,0,1)
        ref.recovery_reference_init(C.byref(p),tiles,0)
        for tick in range(elapsed):
            core.recovery_step(0,0);ref.recovery_reference_step(0)
        core.recovery_step(0,1);core.recovery_read(C.byref(p),state)
        ref.recovery_reference_life_tick()
        assert state[0]==ref.recovery_reference_life(),('restart during recovery',elapsed,state[0],ref.recovery_reference_life())
        for delay in range(1,12):
            core.recovery_step(0,0);core.recovery_read(C.byref(p),state)
            ref.recovery_reference_life_tick()
            assert state[0]==ref.recovery_reference_life() and state[1]==29-delay,('death recovery timer',elapsed,delay,list(state))
    report=dict(cases=cases,movement_ticks=ticks,recovery_restarts=10,death_life_ticks=120,
        reference_sha256=hashlib.sha256((shim+source).encode()).hexdigest(),
        scope='Synthetic static-room recovery states; source input, Game::lifesequence and player physics for 24 ticks, plus life-timer comparison on restart. No platforms, scripts, visibility or full campaign loop.')
    (BUILD/'recovery-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
