#!/usr/bin/env python3
"""Bounded normal-mode selector: readiness, input latch and request isolation."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD,Player
from test_teleporter import Region
class Destination(C.Structure):
    _fields_=[('room_x',C.c_int),('room_y',C.c_int)]
class Menu(C.Structure):
    _fields_=[(n,C.c_uint) for n in ('ready','open','selected','held')]+[(n,C.c_int) for n in ('room_x','room_y')]
def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    libpath=BUILD/'teleporter-menu.so'
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/n) for n in ('teleporter_menu.c','player.c','terrain.c')],'-o',str(libpath)],check=True)
    lib=C.CDLL(str(libpath))
    lib.v6_teleporter_menu_ready.argtypes=[C.POINTER(Menu),C.POINTER(Region),C.POINTER(Player),C.c_int]
    lib.v6_teleporter_menu_tick.argtypes=[C.POINTER(Menu),C.POINTER(Destination),C.c_uint,C.c_int,C.c_int,C.POINTER(Player),C.c_uint,C.POINTER(Destination)]
    p=Player();lib.v6_player_init(C.byref(p),156,92,0)
    region=Region(1,80,16,160,160);m=Menu();out=Destination(77,88)
    destinations=(Destination*3)(Destination(100,100),Destination(111,104),Destination(118,107))
    def tick(buttons,ds=destinations,count=None):
        before=bytes(p),bytes(region)
        result=lib.v6_teleporter_menu_tick(C.byref(m),ds,len(ds) if count is None else count,111,104,C.byref(p),buttons,C.byref(out))
        assert (bytes(p),bytes(region))==before
        if result!=4:assert (out.room_x,out.room_y)==(77,88)
        return result
    cases=0
    # Readiness boundaries and disabled/region exit decay; no physics mutation.
    for ready in range(256):
        for active in (0,1):
            for enabled in (0,1):
                for x in (0,76,80,156,240):
                    m=Menu(ready,0,0,0,0,0);region.active=active;p.x=x
                    inside=x+6<240 and x+12>80  # source 6px collision body
                    expected=min(255,ready+25) if active and enabled and inside else max(0,ready-50)
                    before=bytes(p)
                    lib.v6_teleporter_menu_ready(C.byref(m),C.byref(region),C.byref(p),enabled)
                    assert m.ready==expected,(ready,active,enabled,x,m.ready,expected)
                    assert bytes(p)==before;cases+=1
    p.x=156;region.active=1
    # Source truncation admits fractional movement up to the integer limits.
    one=16777216
    for vx in (-2*one,-2*one+1,-one,0,one,2*one-1,2*one):
        for vy in (-one,-one+1,0,one-1,one):
            for ready in (0,20,21,255):
                m=Menu(ready,0,0,0,0,0);p.vx=vx;p.vy=vy
                expected=ready>20 and -2*one<vx<2*one and -one<vy<one
                assert tick(4)==int(expected)
                assert bool(m.open)==expected;cases+=1
    p.vx=p.vy=0;m=Menu(25,0,0,0,0,0)
    assert tick(4)==1 and m.selected==1
    assert tick(4)==0 and m.open # held interact cannot immediately confirm
    assert tick(2)==0 and m.selected==1 # shared latch waits for all buttons up
    tick(0);assert tick(1)==2 and m.selected==0
    tick(0);assert tick(1)==2 and m.selected==2
    tick(0);assert tick(2)==2 and m.selected==0
    tick(0);assert tick(4)==4 and (out.room_x,out.room_y)==(100,100) and not m.open
    out=Destination(77,88);tick(0);assert tick(4)==1
    tick(0);assert tick(4)==3 and not m.open # current room cancels
    tick(0);assert tick(4)==1
    tick(0);assert tick(8)==3 and not m.open
    single=(Destination*1)(Destination(111,104));tick(0);assert tick(4,single)==1
    tick(0,single);assert tick(2,single)==2 and m.selected==0
    tick(0,single);assert tick(4,single)==3
    # No eligible/current destination or malformed lists cannot touch the menu.
    badlists=[(destinations,0),((Destination*1)(Destination(100,100)),1),
        ((Destination*2)(Destination(111,104),Destination(111,104)),2),
        ((Destination*2)(Destination(111,104),Destination(120,104)),2)]
    for ds,count in badlists:
        before=bytes(m);assert tick(4,ds,count)==0 and bytes(m)==before
    before=bytes(m);assert tick(16)==0 and bytes(m)==before
    m=Menu(255,1,3,0,111,104);before=bytes(m)
    assert tick(4)==0 and bytes(m)==before
    m=Menu(255,1,1,0,111,104);before=bytes(m)
    lib.v6_teleporter_menu_ready(C.byref(m),C.byref(region),C.byref(p),0)
    assert bytes(m)==before # menu pause freezes readiness
    print(f'PASS teleporter menu: {cases} readiness/velocity cases, wrap selection, shared release latch, current-room/cancel, bounded destinations and gameplay isolation')
if __name__=='__main__':main()
