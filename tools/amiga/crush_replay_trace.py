#!/usr/bin/env python3
"""Host integration trace for the rendered synthetic spike-push fixture."""
import ctypes as C
import json
import subprocess
from test_player import ROOT,BUILD,Player,DynamicBlock
from test_enemy import Enemy


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','slice.c','terrain.c','platform.c','enemy.c','blocks.c')],
        str(ROOT/'tools/amiga/crush_session.c'),'-o',str(BUILD/'crush_replay.so')],check=True)
    core=C.CDLL(str(BUILD/'crush_replay.so'))
    core.crush_session_init.argtypes=[C.c_int]*6
    core.crush_session_read.argtypes=[C.POINTER(Player),C.POINTER(Enemy),C.POINTER(DynamicBlock),C.POINTER(C.c_int)]
    core.crush_session_init(0,0,6,3,108,1)
    p=Player();e=Enemy();b=DynamicBlock();state=(C.c_int*6)();trace=[]
    for tick in range(240):
        core.crush_session_step();core.crush_session_read(C.byref(p),C.byref(e),C.byref(b),state)
        trace.append(dict(player_x=p.x,player_y=p.y,player_vx=p.vx,player_vy=p.vy,
            gravity=p.gravity,flips=p.flips,death_timer=state[0],deaths=state[2],respawns=state[3],
            enemy_x=e.x,enemy_y=e.y,enemy_ticks=state[4]))
    assert trace[0]['death_timer']==30 and trace[30]['respawns']==1,trace[:31]
    (BUILD/'crush-replay-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    print('PASS: 240-tick synthetic spike-push host trace')


if __name__=='__main__':main()
