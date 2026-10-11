#!/usr/bin/env python3
"""Source-extracted shake sampling and viewport/flip clipping checks."""
import ctypes as C
import random
import subprocess
from test_player import ROOT,BUILD


class State(C.Structure):_fields_=[('x',C.c_int16),('y',C.c_int16)]
class Plan(C.Structure):_fields_=[('x',C.c_int16),('y',C.c_int16)]+[(name,C.c_uint16) for name in ('source_x','source_y','destination_x','destination_y','width','height')]


def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    start=source.index('void Graphics::updatescreenshake(void)')
    method=source[start:source.index('\nvoid Graphics::draw_window_background',start)]
    code='''#include <stdint.h>
#include "screen_shake.h"
typedef int32_t Sint32;
const uint16_t *samples;unsigned at;
double fRandom(){return samples[at++]/65536.0;}
class Graphics {public:int screenshake_x,screenshake_y;void updatescreenshake(void);};
'''+method+'''
extern "C" void reference(const uint16_t *r,V6ScreenShake *out){
samples=r;at=0;Graphics g;g.updatescreenshake();out->x=g.screenshake_x;out->y=g.screenshake_y;}
extern "C" int pixels(const V6ScreenShakePlan *p,int dx,int dy,int flip){
for(int y=0;y<240;++y)for(int x=0;x<320;++x){
// Destination texture starts black; translated source pixels have unique IDs.
int expected=0,sx=x-dx,sy=(flip?239-y:y)-dy;
if(sx>=0 && sx<320 && sy>=0 && sy<240)expected=1+sy*320+sx;
int actual=0;
if(x>=p->destination_x && x<p->destination_x+p->width &&
   y>=p->destination_y && y<p->destination_y+p->height)
{int copied_y=y-p->destination_y+p->source_y;
actual=1+(flip?239-copied_y:copied_y)*320+x-p->destination_x+p->source_x;}
if(expected!=actual)return 0;
}return 1;}
'''
    path=BUILD/'screen-shake-reference.cpp';path.write_text(code)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
    subprocess.run(['c++','-std=c++11',*flags,str(path),'-o',str(BUILD/'screen-shake-reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/screen_shake.c'),'-o',str(BUILD/'screen-shake.so')],check=True)
    core=C.CDLL(str(BUILD/'screen-shake.so'));ref=C.CDLL(str(BUILD/'screen-shake-reference.so'))
    core.v6_screen_shake_init.argtypes=[C.POINTER(State)]
    core.v6_screen_shake_pre.argtypes=[C.POINTER(State),C.c_int,C.POINTER(C.c_uint16)]
    core.v6_screen_shake_plan.argtypes=[C.POINTER(State),C.c_int,C.c_int,C.c_int,C.POINTER(Plan)]
    ref.reference.argtypes=[C.POINTER(C.c_uint16),C.POINTER(State)]
    ref.pixels.argtypes=[C.POINTER(Plan),C.c_int,C.c_int,C.c_int]
    return core,ref


def main():
    core,ref=libraries();samples=(C.c_uint16*2)();state=State();expected=State();cases=0
    def check():
        assert core.v6_screen_shake_pre(C.byref(state),10,samples)==1
        ref.reference(samples,C.byref(expected))
        assert (state.x,state.y)==(expected.x,expected.y),(tuple(samples),state.x,state.y,expected.x,expected.y)
    for i in range(65536):samples[:]=[i,65535-i];check();cases+=1
    rng=random.Random(7)
    for _ in range(10000):samples[:]=[rng.randrange(65536),rng.randrange(65536)];check();cases+=1
    pixel_cases=0
    for x in range(-4,3):
        for y in range(-4,3):
            state=State(x,y)
            for timer in (0,1):
                for noflash in (0,1):
                    for flip in (0,1):
                        plan=Plan();assert core.v6_screen_shake_plan(C.byref(state),timer,noflash,flip,C.byref(plan))==1
                        dx=x if timer and not noflash else 0
                        dy=(-y if flip else y) if timer and not noflash else 0
                        assert (plan.x,plan.y)==(dx,dy)
                        assert ref.pixels(C.byref(plan),dx,y if timer and not noflash else 0,flip)==1
                        pixel_cases+=320*240
    state=State(-3,2);snapshot=bytes(state)
    assert core.v6_screen_shake_pre(C.byref(state),0,None)==1 and bytes(state)==snapshot
    assert core.v6_screen_shake_pre(C.byref(state),1,None)==0 and bytes(state)==snapshot
    assert core.v6_screen_shake_pre(None,1,samples)==0
    plan=Plan(9,9,9,9,9,9,9,9);snapshot=bytes(plan)
    assert core.v6_screen_shake_plan(C.byref(State(3,0)),1,0,0,C.byref(plan))==0 and bytes(plan)==snapshot
    assert core.v6_screen_shake_plan(None,1,0,0,C.byref(plan))==0 and bytes(plan)==snapshot
    core.v6_screen_shake_init(C.byref(state));assert (state.x,state.y)==(0,0)
    print(f'PASS screen shake: {cases} extracted-source sample comparisons; {pixel_cases} clipped/black-edge/flip pixel checks; inactive retention, invalid-call preservation and reset')


if __name__=='__main__':main()
