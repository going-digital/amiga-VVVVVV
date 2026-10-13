#!/usr/bin/env python3
"""Normal menu slide timing versus the original fixed-update statements."""
import ctypes as C
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
class Transition(C.Structure):
    _fields_=[(n,C.c_uint) for n in ('active','closing','previous','offset')]
def main():
    out=ROOT/'build/amiga-map-transition';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/RenderFixed.cpp').read_text()
    start=source.index('    graphics.oldmenuoffset = graphics.menuoffset;')
    fixed=source[start:source.index('    if (map.cursorstate == 0)',start)]
    shim='''#include "map_transition.h"
struct {int oldmenuoffset,menuoffset;bool resumegamemode;} graphics;
struct {int prevgamestate,gamestate;bool mapheld;} game;
struct {bool running;} script;
const int GAMEMODE=1;
extern "C" unsigned reference(V6MapTransition *t){
 graphics.oldmenuoffset=t->previous;graphics.menuoffset=t->offset;
 graphics.resumegamemode=t->closing;game.prevgamestate=GAMEMODE;
 game.gamestate=2;game.mapheld=false;script.running=false;
'''+fixed+'''
 t->previous=graphics.oldmenuoffset;t->offset=graphics.menuoffset;
 t->closing=graphics.resumegamemode;t->active=game.gamestate!=GAMEMODE;
 return game.mapheld;
}
'''
    (out/'reference.cpp').write_text(shim)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/map_transition.c'),'-o',str(out/'transition.so')],check=True)
    subprocess.run(['c++','-std=c++11',*flags,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
    lib=C.CDLL(str(out/'transition.so'));ref=C.CDLL(str(out/'reference.so'))
    for name in ('init','open','close','tick','input_locked'):
        getattr(lib,'v6_map_transition_'+name).argtypes=[C.POINTER(Transition)]
    lib.v6_map_transition_offset.argtypes=[C.POINTER(Transition),C.c_uint]
    ref.reference.argtypes=[C.POINTER(Transition)]
    checks=0
    # All offsets, including interrupted openings; production closes only at zero.
    for closing in range(2):
      for offset in range(241):
        t=Transition(1,closing,offset,offset);r=Transition.from_buffer_copy(t)
        assert lib.v6_map_transition_tick(C.byref(t))==ref.reference(C.byref(r))
        assert bytes(t)==bytes(r)
        for remainder in range(35):
          expected=(t.previous*(34-remainder)+t.offset*remainder)//34
          assert lib.v6_map_transition_offset(C.byref(t),remainder)==expected
          checks+=1
        assert lib.v6_map_transition_input_locked(C.byref(t))==bool(t.active and (t.closing or t.offset))
    t=Transition();lib.v6_map_transition_init(C.byref(t))
    assert not t.active and t.offset==240
    assert not lib.v6_map_transition_tick(C.byref(t))
    lib.v6_map_transition_close(C.byref(t));assert not t.closing
    for _ in range(100):
      lib.v6_map_transition_open(C.byref(t))
      for tick in range(10):
        assert not lib.v6_map_transition_tick(C.byref(t))
        assert t.offset==max(0,240-25*(tick+1))
        assert bool(lib.v6_map_transition_input_locked(C.byref(t)))==(tick<9)
      for _ in range(5):lib.v6_map_transition_tick(C.byref(t))
      assert t.previous==t.offset==0 and t.active
      lib.v6_map_transition_close(C.byref(t))
      for tick in range(10):
        assert lib.v6_map_transition_tick(C.byref(t))==(tick==9)
        assert t.offset==min(240,25*(tick+1))
      assert not t.active and not t.closing
    assert lib.v6_map_transition_offset(C.byref(t),1000)==240
    print(f'Map transition: 482 original fixed updates, {checks} rational interpolation checks, 100 complete opening/closing cycles passed')
if __name__=='__main__':main()
