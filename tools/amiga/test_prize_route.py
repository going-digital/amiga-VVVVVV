#!/usr/bin/env python3
"""Prize resident terrain, checkpoint and saved-room boundary contracts."""
import ctypes as C
from test_tower_route import RouteRoom,Checkpoint,route_setup,libraries,encode
from test_tower_player import OUT
from probe_feasibility import tower_probe
from tower_gameplay_data import frown_room,shenanigan_room,prize_room
from test_player import Player,FIELDS

def main():
    core,reference=libraries();tower_probe(OUT);r,s,w,keep=route_setup(core,index=14)
    rooms=(RouteRoom*7)()
    for i in range(4):rooms[i]=keep[2][i]
    retained=[]
    for i,desc in enumerate((frown_room(),shenanigan_room(),prize_room()),4):
        blob=encode(desc['tiles']);packed=(C.c_uint8*len(blob)).from_buffer_copy(blob)
        tiles=(C.c_uint16*1200)(*desc['tiles'])
        checkpoints=desc.get('checkpoints',[desc.get('checkpoint')])
        bank=(Checkpoint*len(checkpoints))(*(Checkpoint(*row,0,0) for row in checkpoints))
        rooms[i]=RouteRoom(desc['x'],desc['y'],packed,len(packed),bank,len(bank),tiles,None,0)
        retained.append((packed,tiles,bank))
    r.rooms=rooms;r.count=7
    core.v6_tower_route_boundary.argtypes=[C.POINTER(type(r))]
    assert core.v6_tower_route_load(C.byref(r),111,106,0)
    s.player.x=234;s.player.y=238
    assert core.v6_tower_route_boundary(C.byref(r)) and r.index==6
    assert (s.player.x,s.player.y,s.player.old_y)==(234,-2,-2)
    assert w.count==1 and w.checkpoints[0].id==443490
    assert C.addressof(r.room.tiles.contents)==C.addressof(retained[2][1])
    assert list(r.room.tiles[:1200])==prize_room()['tiles']
    reference.reference_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int,C.c_int]
    ticks=0
    # Static physics differential excludes the separately tested actors.
    for x,y in ((234,0),(124,70),(192,128),(236,134)):
        for gravity in (0,1):
            player=Player();core.v6_player_init(C.byref(player),x,y,gravity)
            reference.reference_init(C.byref(player),retained[2][1],0,0)
            for tick in range(64):
                buttons=2 if tick<16 else 1 if tick<32 else 0
                core.v6_player_step(C.byref(player),C.byref(r.room),buttons)
                reference.reference_step(buttons);expected=Player();reference.reference_read(C.byref(expected))
                assert all(getattr(player,f)==getattr(expected,f) for f in FIELDS),(x,y,gravity,tick)
                ticks+=1
    core.v6_player_init(C.byref(s.player),236,134,1);s.death_timer=-1;s.life_timer=0
    for _ in range(2):assert core.v6_tower_route_step(C.byref(r),0)
    assert (w.save.x,w.save.y,w.save.gravity,w.save.room_x,w.save.room_y,w.save.id)==(236,134,1,111,107,443490)
    retained[2][1][9*40+18]=59
    s.player.x=234;s.player.y=-3
    assert core.v6_tower_route_boundary(C.byref(r)) and r.index==5
    assert (s.player.y,s.player.old_y)==(237,237)
    core.v6_tower_session_die(C.byref(s))
    for _ in range(30):assert core.v6_tower_route_step(C.byref(r),0)
    assert r.index==6 and s.respawns==1 and r.returns==1
    assert (s.player.x,s.player.y,s.player.gravity)==(236,134,1)
    assert r.room.tiles[9*40+18]==59 and w.checkpoints[0].active
    # Saved room must still be canonical in its source checkpoint bank.
    before=bytes(r),bytes(w)
    assert not core.v6_tower_route_load(C.byref(r),999,999,0)
    assert (bytes(r),bytes(w))==before
    print(f'PASS Prize route: {ticks} source static-physics ticks, south/north history, checkpoint, remote death restore and retained mutable tile')
if __name__=='__main__':main()
