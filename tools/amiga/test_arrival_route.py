#!/usr/bin/env python3
"""Arrival phase coupled to extracted desktop input and collision physics."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD,Player,FIELDS
from test_tower_route import libraries,RouteRoom,encode
from test_building_route import fixture
from test_teleporter import Teleporter,Region
from test_teleporter_arrival import Arrival,Motion,libraries as arrival_libraries
from tower_gameplay_data import energize_room

PHASE=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_void_p)
SCRIPT=C.CFUNCTYPE(None,C.POINTER(Player),C.POINTER(Motion))
def physics_reference():
    # Insert a script boundary into the existing unmodified desktop input and
    # physics extraction. Its callback runs the actual Game.cpp arrival cases.
    code=(BUILD/'player_reference.cpp').read_text()
    code=code.replace('#include "reference_shim.h"', '''#include "reference_shim.h"
#include "teleporter_arrival.h"
static void (*script_phase)(V6Player *,V6PlayerMotion *);
extern "C" void set_script(void (*phase)(V6Player *,V6PlayerMotion *)) {script_phase=phase;}
static void apply_script() {
    V6Player p;reference_read(&p);
    entclass& e=obj.entities[0];
    V6PlayerMotion m={(int32_t)std::lround(e.ax*double(V6_ONE)),0};
    script_phase(&p,&m);
    e.xp=p.x;e.yp=p.y;e.dir=p.dir;
    e.vx=p.vx/float(V6_ONE);e.vy=p.vy/float(V6_ONE);e.ay=p.ay/float(V6_ONE);
    e.ax=m.ax/float(V6_ONE);
}''')
    marker='        entclass& e = obj.entities[0];'
    assert code.count(marker)==1
    code=code.replace(marker,'        apply_script();\n'+marker)
    path=BUILD/'arrival-physics-reference.cpp';path.write_text(code)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-fsanitize=undefined',
        '-fno-sanitize-recover=all','-I'+str(ROOT/'tools/amiga'),'-I'+str(ROOT/'amiga_version'),
        '-I'+str(ROOT/'desktop_version/src'),'-I/opt/homebrew/include',str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'arrival-physics-reference.so')],check=True)
    ref=C.CDLL(str(BUILD/'arrival-physics-reference.so'))
    ref.set_script.argtypes=[SCRIPT]
    ref.reference_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int,C.c_int]
    ref.reference_read.argtypes=[C.POINTER(Player)]
    return ref

def main():
    core,_=libraries();_,source=arrival_libraries();ref=physics_reference()
    core.v6_tower_route_step_phase.argtypes=[C.c_void_p,C.c_uint,PHASE,C.c_void_p]
    core.v6_tower_route_teleport.argtypes=[C.c_void_p,C.c_int,C.c_int]
    cases=0
    for direction in (0,1):
        for vx,vy in ((0,0),(3,-2)):
            r,s,w,building,keep=fixture(core);desc=energize_room()
            tiles=(C.c_uint16*1200)(*desc['tiles']);blob=encode(desc['tiles'])
            data=(C.c_uint8*len(blob)).from_buffer_copy(blob);tele=Teleporter(36,68,0,1,1,0)
            rooms=(RouteRoom*6)()
            for i in range(5):rooms[i]=keep[1][i]
            rooms[5]=RouteRoom(110,105,data,len(blob),None,0,tiles,C.pointer(tele),0)
            r.rooms=rooms;r.count=6
            assert core.v6_tower_route_load(C.byref(r),111,104,0)
            s.player.dir=direction;s.player.vx=vx*16777216;s.player.vy=vy*16777216
            assert core.v6_tower_route_teleport(C.byref(r),110,105)
            a=Arrival(4010,0,0,0,0,0,0);expected=Arrival.from_buffer_copy(a)
            invisible=C.c_int(1);s.invisible=1
            rt=Teleporter(36,68,0,6,0,0);region=Region(1,4,36,160,160)
            ref.reference_init(C.byref(s.player),tiles,0,0)
            @PHASE
            def phase(route,context):
                return core.v6_teleporter_arrival_tick(C.byref(a),C.byref(s.player),C.byref(s.motion),
                    C.byref(s,type(s).invisible.offset),C.byref(tele),C.byref(r.tele_region))
            @SCRIPT
            def script(p,m):
                source.reference(C.byref(expected),p,m,C.byref(invisible),C.byref(rt),C.byref(region))
            ref.set_script(script)
            for tick in range(42):
                # Locked direction and held flip must not erase scripted motion
                # or increment flip count before control is restored.
                buttons=7|8
                assert core.v6_tower_route_step_phase(C.byref(r),buttons,phase,None)
                ref.reference_step(buttons);p=Player();ref.reference_read(C.byref(p))
                assert tuple(getattr(s.player,f) for f in FIELDS)==tuple(getattr(p,f) for f in FIELDS),(direction,vx,vy,tick+1,s.player.x,p.x)
                assert bytes(a)==bytes(expected),(tick+1,bytes(a),bytes(expected))
                assert s.invisible==invisible.value and s.death_timer==-1
                assert tele.tile==rt.tile and bytes(r.tele_region)==bytes(region)
                for state in (a,expected):
                    if state.flash:state.flash-=1
                    if state.shake:state.shake-=1
                cases+=1
            assert a.control and not a.state and a.events==4 and s.player.flips==0
            assert w.save.dir==direction and (w.save.x,w.save.y)==(80,112)
    # Failed phases stop before physics and latch an explicit route error.
    @PHASE
    def fail(route,context):return 0
    # The script boundary belongs only to live ordinary-room updates.
    s.death_timer=30
    assert core.v6_tower_route_step_phase(C.byref(r),8,fail,None) and s.death_timer==29
    s.death_timer=-1
    assert core.v6_tower_route_load(C.byref(r),109,104,0)
    assert core.v6_tower_route_step_phase(C.byref(r),8,fail,None) and not r.error
    assert core.v6_tower_route_load(C.byref(r),110,105,0)
    before=(s.player.x,s.player.y,s.player.vx,s.player.vy)
    assert not core.v6_tower_route_step_phase(C.byref(r),8,fail,None) and r.error
    assert before==(s.player.x,s.player.y,s.player.vx,s.player.vy)
    print(f'PASS arrival route: {cases} coupled desktop arrival/input/physics ticks, held-input lock, saved facing, dead/tower exclusion and phase failure')
if __name__=='__main__':main()
