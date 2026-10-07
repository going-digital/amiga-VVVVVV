#!/usr/bin/env python3
"""Mouse save/load gestures, held-fire consumption and button edges."""
import ctypes as C
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
class Controls(C.Structure):
    _fields_=[('right_down',C.c_uint),('suppress_fire',C.c_uint)]
def main():
    out=ROOT/'build/amiga-save-controls';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/save_controls.c'),'-o',str(out/'controls.so')],check=True)
    lib=C.CDLL(str(out/'controls.so'));lib.v6_save_controls_tick.argtypes=[C.POINTER(Controls),C.c_int,C.c_int]
    lib.v6_save_controls_filter.argtypes=[C.POINTER(Controls),C.c_uint]
    s=Controls()
    def step(right,fire,action,suppress):
        assert lib.v6_save_controls_tick(C.byref(s),right,fire)==action
        assert s.suppress_fire==suppress
        for input in range(16):assert lib.v6_save_controls_filter(C.byref(s),input)==(input&~4 if suppress else input)
    step(1,0,1,0)
    for _ in range(200):step(1,0,0,0)
    step(1,1,0,1)  # pressing fire while right is held does not emit another action
    step(0,1,0,1)
    for _ in range(200):step(0,1,0,1)
    step(1,1,2,1);step(1,1,0,1);step(0,1,0,1);step(0,0,0,0)
    step(0,1,0,0)  # ordinary gameplay fire remains available
    step(1,1,2,1)
    for _ in range(200):step(1,1,0,1)
    step(0,0,0,0);step(1,0,1,0)
    print('PASS save controls: save/load edges, 600 held-button fields, chord fire consumption until release and all 16 gameplay masks')
if __name__=='__main__':main()
