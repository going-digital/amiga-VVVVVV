#!/usr/bin/env python3
"""Teleporter frame delays against the actual desktop animation branch."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD
class Animation(C.Structure):
    _fields_=[(n,C.c_int) for n in ('frame','delay','walking')]
def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    start=source.index('        case EntityType_TELEPORTER: //the teleporter!')
    branch=source[start:source.index('        default:',start)]
    fixture='''#include "teleporter_animation.h"
enum {EntityType_TELEPORTER=1};
struct E {int tile,drawframe,framedelay,walkingframe;} entities[1];
struct Game {bool noflashingmode;} game;
unsigned selected;
double fRandom(){return selected/6.0;}
extern "C" void reference(V6TeleporterAnimation *a,int tile,int noflashing,unsigned choice){
int _i=0;entities[0]={tile,a->frame,a->delay,a->walking};
game.noflashingmode=noflashing;selected=choice;
switch(EntityType_TELEPORTER){
'''+branch+'''
}
a->frame=entities[0].drawframe;a->delay=entities[0].framedelay;a->walking=entities[0].walkingframe;
}
'''
    path=BUILD/'teleporter_animation_reference.cpp';path.write_text(fixture)
    options=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
    subprocess.run(['c++','-std=c++11',*options,str(path),'-o',str(BUILD/'teleporter_animation_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*options,str(ROOT/'amiga_version/teleporter_animation.c'),'-o',str(BUILD/'teleporter_animation.so')],check=True)
    core=C.CDLL(str(BUILD/'teleporter_animation.so'));ref=C.CDLL(str(BUILD/'teleporter_animation_reference.so'))
    args=[C.POINTER(Animation),C.c_int,C.c_int,C.c_uint]
    core.v6_teleporter_animate.argtypes=args;ref.reference.argtypes=args
    return core,ref

def main():
    core,ref=libraries();cases=0
    for tile in (1,2,6,9):
        for noflashing in (0,1):
            for delay in (-2,0,1,2,4):
                for walking in (-5,-1,0,3,5):
                    for choice in range(6):
                        a=Animation(8,delay,walking);b=Animation.from_buffer_copy(a)
                        assert core.v6_teleporter_animate(C.byref(a),tile,noflashing,choice)
                        ref.reference(C.byref(b),tile,noflashing,choice)
                        assert bytes(a)==bytes(b),(tile,noflashing,delay,walking,choice)
                        cases+=1
    a=Animation();b=Animation();seed=1
    for tick in range(1200):
        tile=1 if tick<30 else 2 if tick<400 else 6
        noflashing=500<=tick<600
        seed=(seed*1664525+1013904223)&0xffffffff;choice=(seed>>16)%6
        core.v6_teleporter_animate(C.byref(a),tile,noflashing,choice)
        ref.reference(C.byref(b),tile,noflashing,choice)
        assert bytes(a)==bytes(b),tick
    before=bytes(a)
    assert not core.v6_teleporter_animate(C.byref(a),2,0,6) and bytes(a)==before
    print(f'PASS teleporter animation: {cases} source state cases, 1200 sequential ticks, no-flashing and invalid-choice preservation')
if __name__=='__main__':main()
