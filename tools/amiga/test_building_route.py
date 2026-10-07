#!/usr/bin/env python3
"""Building Apport resident route, teleporter checkpoint and remote returns."""
import ctypes as C
from test_tower_route import RouteRoom,route_setup,libraries,encode
from test_teleporter import Teleporter
from tower_gameplay_data import building_room

def fixture(core):
    r,s,w,old=route_setup(core,index=14)
    rooms=(RouteRoom*5)()
    for i in range(4):rooms[i]=old[2][i]
    packed=encode(building_room());payload=(C.c_uint8*len(packed)).from_buffer_copy(packed)
    tiles=(C.c_uint16*1200)(*building_room());tele=Teleporter(112,48,0,1,1,0)
    rooms[4]=RouteRoom(111,104,payload,len(payload),None,0,tiles,C.pointer(tele))
    r.rooms=rooms;r.count=5
    w.save.x=140;w.save.y=1822;w.save.gravity=1;w.save.dir=1;
    w.save.room_x=109;w.save.room_y=109;w.save.id=-1
    core.v6_tower_session_init(C.byref(s),280,185,0,1)
    assert core.v6_tower_route_load(C.byref(r),110,104,0)
    return r,s,w,tele,(old,rooms,payload,tiles)

def buttons(tick):
    return (2 if tick<40 else 1 if tick<80 else 0)|(4 if tick==30 else 0)

def main():
    core,_=libraries();r,s,w,t,keep=fixture(core)
    transitions=[];events=[]
    for tick in range(128):
        previous=r.index
        assert core.v6_tower_route_step(C.byref(r),buttons(tick)),(tick,r.index,s.player.x,s.player.y)
        if previous!=r.index:transitions.append((tick+1,r.index))
        if r.tele_events:events.append((tick+1,r.tele_events,w.save.x,w.save.y))
    print('Building route',transitions,events,'player',s.player.x,s.player.y,'save',w.save.id)
    assert events and len(events)==1 and w.save.id==0 and (w.save.x,w.save.y)==(156,92)
    assert transitions[0][1]==4
    assert r.tele_region.active and t.tile==2 and not t.onentity
    # Same-room death retains the entity bank; returning after a remote death
    # recreates the teleporter and restores the centre save before collision.
    assert core.v6_tower_route_load(C.byref(r),111,104,1)
    assert core.v6_tower_route_step(C.byref(r),0) and t.state==1
    assert core.v6_tower_route_step(C.byref(r),0) and r.tele_events==3
    changes=r.transitions;s.death_timer=30
    for i in range(30):assert core.v6_tower_route_step(C.byref(r),0)
    assert r.transitions==changes and (s.player.x,s.player.y)==(156,92)
    assert core.v6_tower_route_load(C.byref(r),109,104,0)
    s.death_timer=30;s.life_timer=0
    for i in range(30):assert core.v6_tower_route_step(C.byref(r),0)
    assert r.index==4 and (s.player.x,s.player.y)==(156,92)
    assert (s.save_x,s.save_y,s.save_gravity)==(156,92,0)
    assert t.tile==1 and t.onentity==1 and not r.tele_region.active
    bad=(C.c_uint8*4)(128,0,0,0)
    keep[1][4].packed=bad;keep[1][4].bytes=4;keep[1][4].decoded=None
    before=bytes(r),bytes(s),bytes(w),bytes(t)
    assert not core.v6_tower_route_load(C.byref(r),111,104,0)
    assert (bytes(r),bytes(s),bytes(w),bytes(t))==before
    keep[1][4].packed=keep[2];keep[1][4].bytes=len(keep[2]);keep[1][4].decoded=keep[3]
    print('PASS Building Apport: natural entrance/activation, centre checkpoint, same-room respawn and remote return')
if __name__=='__main__':main()
