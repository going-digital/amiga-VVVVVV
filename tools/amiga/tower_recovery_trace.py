"""Reference replay for the native camera-only recovery fixture."""
import ctypes as C
import subprocess
from test_tower_camera import ROOT,OUT

def verify(report):
    # These tests compile the original desktop source blocks into reference libs.
    for name in ('test_tower_camera.py','test_tower_camera_recovery.py'):
        subprocess.run(['python3',str(ROOT/'tools/amiga'/name)],check=True)
    early=C.CDLL(str(OUT/'reference.so')).reference
    recovery=C.CDLL(str(OUT/'recovery.so')).reference
    early.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*5
    recovery.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*3
    state=(C.c_int*10)();life=delay=calls=0
    assert report['logic_ticks']>100,report
    for tick in range(report['logic_ticks']):
        if tick==70:life=5
        early(state,300,1,1,0,0)
        r=(C.c_int*6)(state[2],state[4],delay,state[9],0,life)
        recovery(r,life,life-1,30 if 60<=tick<70 else -1)
        state[2],state[4],delay,state[9],count,life=r
        calls+=count
    expected=dict(camera=state[0],camera_mode=state[2],recovery_seek_frames=state[4],
                  recovery_delay=delay,recovery_calls=calls,recovery_life=life)
    for key,value in expected.items():
        assert report[key]==value,(key,report[key],value)
    assert calls==5 and life==0,expected
    report['reference_recovery_ticks']=report['logic_ticks']
