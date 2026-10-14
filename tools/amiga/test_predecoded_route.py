#!/usr/bin/env python3
"""Native route configuration: smaller storage, unchanged prepared-bank behavior."""
import ctypes as C
from test_tower_player import libraries
from test_tower_route import Route,RouteRoom,route_setup,hallway_rooms,Session,World,Tiles

class PreparedRoute(C.Structure):
    _fields_=[(name,C.c_uint16*1 if name=='tiles' else kind) for name,kind in Route._fields_]

def main():
    generic,_=libraries()
    prepared,_=libraries(['-DV6_ROUTE_PREDECODED=1'],'predecoded.so')
    r0,s0,w0,k0=route_setup(generic)
    unused,s1,w1,k1=route_setup(generic)
    views=[]
    for keep in (k0,k1):
        for i,desc in enumerate(hallway_rooms()):
            view=(C.c_uint16*1200)(*desc['tiles']);views.append(view)
            keep[2][i+2].decoded=view
    marker=(C.c_uint8*1)(0)
    for bank in k1[2]:
        if bank.packed:
            bank.packed=marker;bank.bytes=0
    prepared.v6_tower_route_init.argtypes=[C.POINTER(PreparedRoute),C.POINTER(Session),C.POINTER(World),
        C.POINTER(RouteRoom),C.c_uint,C.c_int,C.c_int,C.POINTER(Tiles)]
    prepared.v6_tower_route_step.argtypes=[C.POINTER(PreparedRoute),C.c_uint]
    prepared.v6_tower_route_load.argtypes=[C.POINTER(PreparedRoute),C.c_int,C.c_int,C.c_int]
    r1=PreparedRoute()
    assert prepared.v6_tower_route_init(C.byref(r1),C.byref(s1),C.byref(w1),k1[2],4,109,109,C.byref(k1[0][3]))
    for tick in range(480):
        buttons=1 if tick<12 else 2 if tick<40 else 4 if tick%67<3 else 0
        assert generic.v6_tower_route_step(C.byref(r0),buttons)
        assert prepared.v6_tower_route_step(C.byref(r1),buttons)
        assert bytes(s0)==bytes(s1),(tick,'session')
        for field in ('index','transitions','returns','error','tele_events'):
            assert getattr(r0,field)==getattr(r1,field),(tick,field)
        assert bytes(w0.save)==bytes(w1.save)
        assert bytes(r0.tele_region)==bytes(r1.tele_region)
    for index,desc in enumerate(hallway_rooms()):
        assert generic.v6_tower_route_load(C.byref(r0),desc['x'],desc['y'],0)
        assert prepared.v6_tower_route_load(C.byref(r1),desc['x'],desc['y'],0)
        assert bytes(s0)==bytes(s1) and list(r0.room.tiles[:1200])==list(r1.room.tiles[:1200])
    k1[2][2].decoded=None
    before=bytes(r1),bytes(s1),bytes(w1)
    assert not prepared.v6_tower_route_load(C.byref(r1),108,109,0)
    assert (bytes(r1),bytes(s1),bytes(w1))==before
    assert C.sizeof(PreparedRoute)<C.sizeof(Route)-2300
    print('PASS prepared route: 480 identical gameplay updates, both room banks with shared packet marker, rejection without mutation; reduced scratch storage')

if __name__=='__main__':main()
