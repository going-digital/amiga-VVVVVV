#!/usr/bin/env python3
"""Compare the camera helper with the unmodified desktop early-camera block."""
import ctypes as C
import json
from pathlib import Path
import random
import subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/amiga-camera'
FIELDS=('y','old_y','mode','seek','seek_frames','spike_top','spike_bottom',
        'old_spike_top','old_spike_bottom','colour_superstate')
SOURCE_FIELDS=('ypos','oldypos','cameramode','cameraseek','cameraseekframe',
               'spikeleveltop','spikelevelbottom','oldspikeleveltop',
               'oldspikelevelbottom','colsuperstate')
class Camera(C.Structure):
    _fields_=[(f,C.c_int16) for f in FIELDS]

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=source.index('        map.oldypos = map.ypos;',source.index('if (map.towermode)'))
    end=source.index('        if (game.lifeseq > 0)',start)
    block=source[start:end]
    wrapper='''#define INBOUNDS_VEC(i,v) ((i)==0)
struct Map { int '''+','.join(SOURCE_FIELDS)+'''; bool towermode,minitowermode; };
struct Entity { int yp; };
struct Obj { Entity entities[1]; int index; int getplayer() { return index; } };
extern "C" void reference(int *v,int player_y,int valid,int direction,int stopped,int mini) {
Map map={}; Obj obj={};
struct { bool completestop; } game;
struct { struct { int scrolldir; } towerbg; } graphics;
map.towermode=true;map.minitowermode=mini;
obj.entities[0].yp=player_y;obj.index=valid?0:-1;
game.completestop=stopped;graphics.towerbg.scrolldir=direction;
'''+''.join(f'map.{f}=v[{i}];\n' for i,f in enumerate(SOURCE_FIELDS))+block+''.join(f'v[{i}]=map.{f};\n' for i,f in enumerate(SOURCE_FIELDS))+'}\n'
    (OUT/'reference.cpp').write_text(wrapper)
    flags=['-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,str(OUT/'reference.cpp'),'-o',str(OUT/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/tower_camera.c'),'-o',str(OUT/'camera.so')],check=True)
    ref=C.CDLL(str(OUT/'reference.so')).reference
    port=C.CDLL(str(OUT/'camera.so')).v6_tower_camera_tick
    ref.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*5
    port.argtypes=[C.POINTER(Camera)]+[C.c_int]*5
    rng=random.Random(68000);checks=0
    for case in range(3000):
        values=[rng.randint(-200,5600),0,rng.choice([0,1,2,3,4,5]),rng.randint(-600,600),
                rng.choice([-1,0,1,10,20]),rng.randint(0,20),rng.randint(0,20),0,0,rng.randint(0,6)]
        c=Camera(*values);r=(C.c_int*10)(*values)
        # Multi-tick traces include ten-step seeking, no-player fallback and
        # target motion, stopped/resumed ticks and both tower bounds.
        for tick in range(24):
            args=(rng.randint(-256,5856),int(rng.random()>.1),case&1,int(tick%9==0),(case>>1)&1)
            ref(r,*args);port(C.byref(c),*args)
            assert list(r)==[getattr(c,f) for f in FIELDS],(case,tick,list(r),[getattr(c,f) for f in FIELDS])
            checks+=1
    report=dict(ticks=checks,scope='Early desktop tower-camera phase through bounds only; extracted source, no full game loop, interpolation or native scheduling')
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))
if __name__=='__main__':main()
