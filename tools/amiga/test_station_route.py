#!/usr/bin/env python3
"""Candidate Energize/Frown terrain, canonical checkpoint and remote respawn."""
import ctypes as C
from test_tower_route import RouteRoom,Checkpoint,route_setup,libraries,encode
from test_teleporter import Teleporter
from test_player import Player
from test_tower_player import OUT
from probe_feasibility import tower_probe
from tower_gameplay_data import energize_room,frown_room

def main():
    core,ref=libraries();tower_probe(OUT);r,s,w,keep=route_setup(core,index=14)
    rooms=(RouteRoom*6)()
    for i in range(4):rooms[i]=keep[2][i]
    payloads=[];tiles=[]
    tele=Teleporter(36,68,0,1,1,0);frown=frown_room();bank=(Checkpoint*1)(Checkpoint(*frown['checkpoint'],0,0))
    for i,desc in enumerate((energize_room(),frown),4):
        blob=encode(desc['tiles']);payload=(C.c_uint8*len(blob)).from_buffer_copy(blob)
        decoded=(C.c_uint16*1200)(*desc['tiles']);payloads.append(payload);tiles.append(decoded)
        rooms[i]=RouteRoom(desc['x'],desc['y'],payload,len(payload),bank if i==5 else None,int(i==5),decoded,C.pointer(tele) if i==4 else None,0)
    r.rooms=rooms;r.count=6
    core.v6_tower_route_boundary.argtypes=[C.POINTER(type(r))]
    core.v6_tower_session_init(C.byref(s),321,86,1,1)
    assert core.v6_tower_route_load(C.byref(r),110,105,0)
    assert core.v6_tower_route_boundary(C.byref(r)) and r.index==5
    assert (s.player.x,s.player.y,s.player.old_x,s.player.old_y)==(1,86,1,86)
    assert (w.count,r.room.tileset,r.tele_region.active)==(1,0,0)
    assert list(r.room.tiles[:1200])==frown['tiles']
    # Original movement/collision methods independently check this tileset-0 room.
    ref.reference_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int,C.c_int]
    ref.reference_step.argtypes=[C.c_uint]
    physics=0
    for x,y in ((1,86),(42,86),(188,86),(234,160),(300,220)):
        for gravity in (0,1):
            p=Player();expected=Player();core.v6_player_init(C.byref(p),x,y,gravity)
            ref.reference_init(C.byref(p),tiles[1],0,0)
            for tick in range(64):
                buttons=(2 if tick<16 else 1 if tick<32 else 0)|(4 if tick%13<2 else 0)
                ref.reference_step(buttons);core.v6_player_step(C.byref(p),C.byref(r.room),buttons)
                ref.reference_read(C.byref(expected));assert bytes(p)==bytes(expected),(x,y,gravity,tick)
                physics+=1
    # Source checkpoint collision queues activation for the next entity update.
    core.v6_tower_session_init(C.byref(s),188,86,1,1)
    before=w.save.id
    assert core.v6_tower_route_step(C.byref(r),0) and bank[0].pending and w.save.id==before
    assert core.v6_tower_route_step(C.byref(r),0)
    expected=(188,86,1,1,111,105,441490)
    def saved():return tuple(getattr(w.save,n) for n in 'x y gravity dir room_x room_y id'.split())
    assert saved()==expected and bank[0].active and not bank[0].pending
    # Respawn restores this canonical checkpoint both locally and across rooms.
    for destination in ((111,105),(110,105)):
        assert core.v6_tower_route_load(C.byref(r),*destination,0)
        s.death_timer=30;s.life_timer=0
        for tick in range(30):assert core.v6_tower_route_step(C.byref(r),0)
        assert r.index==5 and saved()==expected
        assert (s.player.x,s.player.y,s.player.gravity,s.player.dir)==expected[:4]
    assert s.respawns==2 and r.returns==1
    # Loading still rejects malformed candidate data transactionally.
    rooms[5].decoded=None;rooms[5].packed=(C.c_uint8*1)(128);rooms[5].bytes=1
    before=bytes(r),bytes(s),bytes(w),bytes(bank)
    assert not core.v6_tower_route_load(C.byref(r),111,105,0)
    assert (bytes(r),bytes(s),bytes(w),bytes(bank))==before
    rooms[5].packed=payloads[1];rooms[5].bytes=len(payloads[1]);rooms[5].decoded=tiles[1]
    # No unrelated neighbor is silently admitted by the candidate bank.
    s.player.x=321;old=s.player.x,s.player.y,saved()
    assert not core.v6_tower_route_boundary(C.byref(r)) and r.error
    assert (s.player.x,s.player.y,saved())==old and r.index==5
    print(f'PASS station route: {physics} source physics ticks, source terrain, east entrance/history reset, deferred checkpoint activation, local/remote respawn, malformed load and unsupported exit guards; host candidate only')
if __name__=='__main__':main()
