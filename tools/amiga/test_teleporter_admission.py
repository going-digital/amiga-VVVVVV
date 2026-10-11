#!/usr/bin/env python3
"""Source-order exploration filtering and transactional admission checks."""
import ctypes as C
import re
import subprocess
from test_player import ROOT,BUILD
from test_teleporter_menu import Destination
class Exploration(C.Structure):_fields_=[('rooms',C.c_uint8*50)]
def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    path=BUILD/'teleporter-admission.so'
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined',
        '-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/teleporter_admission.c'),'-o',str(path)],check=True)
    lib=C.CDLL(str(path));lib.v6_exploration_visit.argtypes=lib.v6_exploration_seen.argtypes=[C.POINTER(Exploration),C.c_int,C.c_int]
    lib.v6_teleporter_admit.argtypes=[C.POINTER(Exploration),C.POINTER(Destination),C.c_uint,C.POINTER(Destination),C.c_uint,C.POINTER(C.c_uint)]
    text=(ROOT/'desktop_version/src/Map.cpp').read_text();start=text.index('//Set up static map information like teleporters')
    source=[(100+int(x),100+int(y)) for x,y in re.findall(r'setteleporter\((\d+), (\d+)\)',text[start:text.index('settrinket(',start)])]
    assert len(source)==17
    e=Exploration();out=(Destination*17)();count=C.c_uint(999)
    residents=(Destination*17)(*[Destination(*p) for p in reversed(source)])
    for x in range(100,120):
        for y in range(100,120):
            lib.v6_exploration_init(C.byref(e));assert not lib.v6_exploration_seen(C.byref(e),x,y)
            assert lib.v6_exploration_visit(C.byref(e),x,y)
            assert sum(byte.bit_count() for byte in e.rooms)==1 and lib.v6_exploration_seen(C.byref(e),x,y)
    for mask in range(1<<17):
        e.rooms[:]=[0]*50
        for i,(x,y) in enumerate(source):
            if mask&(1<<i):assert lib.v6_exploration_visit(C.byref(e),x,y)
        assert lib.v6_teleporter_admit(C.byref(e),residents,17,out,17,C.byref(count))
        assert [(out[i].room_x,out[i].room_y) for i in range(count.value)]==[p for i,p in enumerate(source) if mask&(1<<i)]
    # Only supported AND visited destinations, in source order.
    supported=(Destination*2)(Destination(111,104),Destination(110,105))
    for seen in range(4):
        lib.v6_exploration_init(C.byref(e))
        for i,p in enumerate(((111,104),(110,105))):
            if seen&(1<<i):lib.v6_exploration_visit(C.byref(e),*p)
        assert lib.v6_teleporter_admit(C.byref(e),supported,2,out,17,C.byref(count))
        assert [(out[i].room_x,out[i].room_y) for i in range(count.value)]==[p for p in source if p in ((111,104),(110,105)) and lib.v6_exploration_seen(C.byref(e),*p)]
    # Exploration does not unlock an unimplemented canonical destination.
    lib.v6_exploration_visit(C.byref(e),100,100)
    assert lib.v6_teleporter_admit(C.byref(e),supported,2,out,17,C.byref(count)) and count.value==2
    for bad,n,capacity in (((Destination*2)(Destination(111,104),Destination(111,104)),2,17),
        ((Destination*1)(Destination(109,109)),1,17),(supported,2,1)):
        before=bytes(out);count.value=999
        assert not lib.v6_teleporter_admit(C.byref(e),bad,n,out,capacity,C.byref(count))
        assert bytes(out)==before and count.value==999
    before=bytes(e)
    for x,y in ((99,104),(120,104),(111,99),(111,120),(-1,100)):
        assert not lib.v6_exploration_visit(C.byref(e),x,y) and not lib.v6_exploration_seen(C.byref(e),x,y)
        assert bytes(e)==before
    assert lib.v6_teleporter_admit(C.byref(e),None,0,None,0,C.byref(count)) and count.value==0
    print('PASS admission: all 131072 explored-teleporter subsets in extracted source order, 400 rooms, resident filtering, invalid/capacity preservation')
if __name__=='__main__':main()
