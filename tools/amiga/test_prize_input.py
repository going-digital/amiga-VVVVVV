#!/usr/bin/env python3
"""Input-only Shenanigan -> Prize checkpoint route and natural death return."""
import ctypes as C
import subprocess
from pathlib import Path
from tower_gameplay_data import shenanigan_room,prize_room
ROOT=Path(__file__).resolve().parents[2]
COUNT=224

def expected():
    build=ROOT/'build/amiga-prize-input-host';build.mkdir(parents=True,exist_ok=True)
    sources=('prize','platform_gate','disappearing','trinkets','checkpoints','platform',
             'enemy','player','terrain','blocks','tower_route','tower_session',
             'tower_camera','tower_gameplay','teleporter','room_codec')
    library=build/'core.so'
    subprocess.run(['cc','-std=c99','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',
                    '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
                    str(ROOT/'tools/amiga/prize_input_fixture.c'),
                    *[str(ROOT/'amiga_version'/(s+'.c')) for s in sources],'-o',str(library)],check=True)
    core=C.CDLL(str(library));core.prize_input_fixture.argtypes=[C.POINTER(C.c_uint16)]*2+[C.POINTER(C.c_int32),C.c_uint]
    north=(C.c_uint16*1200)(*shenanigan_room()['tiles']);south=(C.c_uint16*1200)(*prize_room()['tiles'])
    trace=(C.c_int32*(COUNT*24))()
    assert core.prize_input_fixture(north,south,trace,COUNT)
    rows=[tuple(trace[i*24:(i+1)*24]) for i in range(COUNT)]
    assert [i+1 for i,r in enumerate(rows) if r[4]==30]==[62,193]
    assert [i+1 for i,r in enumerate(rows) if i and r[0]!=rows[i-1][0]]==[126,223]
    assert rows[125][:5]==(8,10,6,0,-1)
    assert rows[155][20:23]==(3,0,0) and rows[173][20:23]==(3,3,0)
    assert rows[189][20:23]==(3,3,3)
    assert rows[193][16]==1 and rows[193][19]==59
    assert rows[222][0:5]==(7,140,161,0,-1) and rows[222][23]==2
    assert all(r[5:11]==(442490,140,161,0,111,106) for r in rows)
    assert all(r[15]==r[17]==0 for r in rows)
    return rows

if __name__=='__main__':
    rows=expected()
    print(f'PASS Prize input route: {len(rows)} ticks; conveyor/flip movement, two source spike deaths, south crossing, three collapses, special tile and remote checkpoint return; no post-start placements')
