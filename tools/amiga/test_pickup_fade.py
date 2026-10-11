#!/usr/bin/env python3
"""Pickup fade lifecycle and OCS palette against extracted source updates."""
import ctypes as C
import subprocess
from pathlib import Path
from test_music_control import method
ROOT=Path(__file__).resolve().parents[2]
class Fade(C.Structure):
    _fields_=[(n,C.c_uint) for n in ('level','old_level','mode','visible')]
def main():
    out=ROOT/'build/amiga-pickup-fade';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Textbox.cpp').read_text()
    code='''#include <cmath>
struct textboxclass {float tl=0,prev_tl=0;int tm=0,timer=0;
void initcol(int,int,int);void update();void remove();int r,g,b;};
'''+ '\n'.join(method(source,s) for s in ('void textboxclass::initcol(', 'void textboxclass::update(', 'void textboxclass::remove('))+'''
textboxclass box;bool visible=false;
extern "C" {
void reset(){box=textboxclass();visible=false;}
void show(){box.initcol(174,174,174);box.tm=0;visible=true;}
void hide(){if(visible)box.remove();}
void tick(){if(!visible)return;box.update();if(box.tm==2 && box.tl<=.5)visible=false;}
void state(unsigned *out){out[0]=std::lround(box.tl*10);out[1]=std::lround(box.prev_tl*10);out[2]=box.tm;out[3]=visible;}
unsigned colours(unsigned phase){if(!visible)return 0;
float alpha=phase/34000.0f;float brightness=box.prev_tl+alpha*(box.tl-box.prev_tl);
int gray=174*brightness;unsigned fill=((gray/6+8)/17)*0x111,ink=((gray+8)/17)*0x111;
return (fill<<16)|ink;}
}
'''
    (out/'reference.cpp').write_text(code)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC',str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/pickup_fade.c'),'-o',str(out/'core.so')],check=True)
    core,ref=C.CDLL(str(out/'core.so')),C.CDLL(str(out/'reference.so'))
    for suffix in ('init','show','remove','tick'):getattr(core,'v6_pickup_fade_'+suffix).argtypes=[C.POINTER(Fade)]
    core.v6_pickup_fade_colours.argtypes=[C.POINTER(Fade),C.c_uint];core.v6_pickup_fade_colours.restype=C.c_uint32
    ref.state.argtypes=[C.c_void_p];ref.colours.restype=C.c_uint
    s=Fade();expected=(C.c_uint*4)();checks=0
    for hold in (0,1,2,3,4,5,20,100):
        core.v6_pickup_fade_init(C.byref(s));ref.reset()
        core.v6_pickup_fade_show(C.byref(s));ref.show()
        for tick in range(hold+8):
            if tick==hold:core.v6_pickup_fade_remove(C.byref(s));ref.hide()
            core.v6_pickup_fade_tick(C.byref(s));ref.tick();ref.state(expected)
            assert tuple(getattr(s,n) for n,_ in Fade._fields_)==tuple(expected),(hold,tick,tuple(expected),tuple(getattr(s,n) for n,_ in Fade._fields_))
            for phase in range(0,34001,16):
                actual=core.v6_pickup_fade_colours(C.byref(s),phase);wanted=ref.colours(phase)
                assert actual==wanted,(hold,tick,phase,hex(actual),hex(wanted))
                checks+=1
            assert core.v6_pickup_fade_colours(C.byref(s),65535)==core.v6_pickup_fade_colours(C.byref(s),34000)
    print('PASS pickup fades:',checks,'source lifecycle/palette phases; immediate/held dismissal, five-tick removal, brightness clamping')
if __name__=='__main__':main()
