#!/usr/bin/env python3
"""Shenanigan route boundaries, deferred checkpoints and remote restore guards."""
import ctypes as C
from test_tower_route import RouteRoom,Checkpoint,route_setup,libraries,encode
from test_tower_player import OUT
from probe_feasibility import tower_probe
from tower_gameplay_data import frown_room,shenanigan_room
from test_player import Player,FIELDS

def main():
    core,ref=libraries();tower_probe(OUT);r,s,w,keep=route_setup(core,index=14)
    rooms=(RouteRoom*6)()
    for i in range(4):rooms[i]=keep[2][i]
    retained=[]
    for i,desc in enumerate((frown_room(),shenanigan_room()),4):
        blob=encode(desc['tiles']);payload=(C.c_uint8*len(blob)).from_buffer_copy(blob)
        tiles=(C.c_uint16*1200)(*desc['tiles'])
        rows=desc.get('checkpoints',[desc.get('checkpoint')])
        bank=(Checkpoint*len(rows))(*(Checkpoint(*row,0,0) for row in rows))
        rooms[i]=RouteRoom(desc['x'],desc['y'],payload,len(payload),bank,len(bank),tiles,None,0)
        retained.append((payload,tiles,bank))
    r.rooms=rooms;r.count=6
    core.v6_tower_route_boundary.argtypes=[C.POINTER(type(r))]
    core.v6_tower_session_init(C.byref(s),234,238,0,0)
    assert core.v6_tower_route_load(C.byref(r),111,105,0)
    assert core.v6_tower_route_boundary(C.byref(r)) and r.index==5
    assert (s.player.x,s.player.y,s.player.old_y)==(234,-2,-2)
    assert w.count==2 and list(r.room.tiles[:1200])==shenanigan_room()['tiles']
    # Static terrain independently compared with original player methods.
    ref.reference_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int,C.c_int]
    ref.reference_step.argtypes=[C.c_uint];ref.reference_read.argtypes=[C.POINTER(Player)]
    ticks=0
    for x,y in ((234,0),(140,161),(20,110),(84,185)):
        for gravity in (0,1):
            p=Player();core.v6_player_init(C.byref(p),x,y,gravity)
            ref.reference_init(C.byref(p),retained[1][1],0,0)
            for tick in range(64):
                buttons=2 if tick<16 else 1 if tick<32 else 0
                core.v6_player_step(C.byref(p),C.byref(r.room),buttons)
                ref.reference_step(buttons);expected=Player();ref.reference_read(C.byref(expected))
                assert all(getattr(p,f)==getattr(expected,f) for f in FIELDS),(x,y,gravity,tick)
                ticks+=1
    for row in shenanigan_room()['checkpoints']:
        x,y,tile,identity=row
        core.v6_player_init(C.byref(s.player),x-4,y-(2 if tile==20 else 7),tile==20)
        s.death_timer=-1;s.life_timer=0
        assert core.v6_tower_route_load(C.byref(r),111,106,0)
        assert core.v6_tower_route_step(C.byref(r),0)
        assert core.v6_tower_route_step(C.byref(r),0)
        assert (w.save.x,w.save.y,w.save.gravity,w.save.room_x,w.save.room_y,w.save.id)==(x-4,y-(2 if tile==20 else 7),tile==20,111,106,identity)
        s.player.x=234;s.player.y=-3
        assert core.v6_tower_route_boundary(C.byref(r)) and r.index==4
        core.v6_tower_session_die(C.byref(s))
        for _ in range(31):assert core.v6_tower_route_step(C.byref(r),0)
        assert r.index==5 and s.player.gravity==(tile==20)
        assert (s.player.x,s.player.y)==(w.save.x,w.save.y)
    before=bytes(r),bytes(s),bytes(w)
    assert not core.v6_tower_route_load(C.byref(r),111,107,0)
    assert (bytes(r),bytes(s),bytes(w))==before
    print(f'PASS Shenanigan: {ticks} original static physics ticks; south/north history transforms, both deferred canonical checkpoints, remote death restores and unsupported room guard')
if __name__=='__main__':main()
