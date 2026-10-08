#!/usr/bin/env python3
"""Host Building/Energize round trips through source departure and arrival phases."""
import ctypes as C
from test_player import Player,FIELDS
from test_tower_route import libraries,RouteRoom,encode
from test_building_route import fixture
from test_teleporter import Teleporter,Region
from test_teleporter_departure import Departure,libraries as departures
from test_teleporter_arrival import Arrival,libraries as arrivals
from test_teleporter_travel import reference as handoffs
from test_arrival_route import PHASE,SCRIPT,physics_reference
from tower_gameplay_data import energize_room

def decay(state):
    if state.flash:state.flash-=1
    if state.shake:state.shake-=1

def main():
    core,_=libraries();_,departure_source=departures();_,arrival_source=arrivals()
    ref=physics_reference();handoff=handoffs();ticks=0
    core.v6_tower_route_step_phase.argtypes=[C.c_void_p,C.c_uint,PHASE,C.c_void_p]
    core.v6_tower_route_teleport.argtypes=[C.c_void_p,C.c_int,C.c_int]
    for direction in (0,1):
        r,s,w,building,keep=fixture(core);desc=energize_room()
        tiles=(C.c_uint16*1200)(*desc['tiles']);blob=encode(desc['tiles'])
        data=(C.c_uint8*len(blob)).from_buffer_copy(blob);energize=Teleporter(36,68,0,1,1,0)
        rooms=(RouteRoom*6)()
        for i in range(5):rooms[i]=keep[1][i]
        rooms[5]=RouteRoom(110,105,data,len(blob),None,0,tiles,C.pointer(energize),0)
        r.rooms=rooms;r.count=6
        assert core.v6_tower_route_load(C.byref(r),111,104,0)
        core.v6_player_init(C.byref(s.player),156,92,0);s.player.dir=direction
        for i in range(2):assert core.v6_tower_route_step(C.byref(r),0)
        assert building.tile==2 and r.tele_region.active and w.save.id==0
        # Selection is staged: this checks phases and physics, not menu
        # exploration/readiness or native scene-bank transitions.
        for tx,ty in ((110,105),(111,104)):
            t=rooms[r.index].teleporter.contents
            d=Departure();core.v6_teleporter_departure_init(C.byref(d))
            assert core.v6_teleporter_departure_start(C.byref(d),C.byref(t),C.byref(r.tele_region))
            expected=Departure.from_buffer_copy(d);rt=Teleporter.from_buffer_copy(t)
            invisible=C.c_int(s.invisible);saved=bytes(w.save)
            ref.reference_init(C.byref(s.player),r.room.tiles,r.room.tileset,r.room.extra_row)
            @PHASE
            def depart_phase(route,context):
                return core.v6_teleporter_departure_tick(C.byref(d),
                    C.byref(s,type(s).invisible.offset),C.byref(t))
            @SCRIPT
            def depart_script(p,m):
                departure_source.reference(C.byref(expected),C.byref(invisible),C.byref(rt))
            ref.set_script(depart_script)
            requests=[]
            for tick in range(22):
                assert core.v6_tower_route_step_phase(C.byref(r),7|8,depart_phase,None)
                ref.reference_step(7|8);p=Player();ref.reference_read(C.byref(p))
                assert tuple(getattr(s.player,f) for f in FIELDS)==tuple(getattr(p,f) for f in FIELDS),(tx,tick+1)
                assert bytes(d)==bytes(expected) and bytes(t)==bytes(rt)
                assert s.invisible==invisible.value and s.death_timer==-1
                assert bytes(w.save)==saved and not r.tele_region.active
                if d.events:requests.append((tick+1,d.events))
                decay(d);decay(expected);ticks+=1
            assert requests==[(1,1),(11,2),(22,4)] and d.travel and not d.control
            # Failure retains the pending request, source scene and checkpoint.
            before=tuple(bytes(v) for v in (r,s,w,t,d))
            assert not core.v6_tower_route_teleport(C.byref(r),119,119)
            assert before==tuple(bytes(v) for v in (r,s,w,t,d))
            target=building if tx==111 else energize
            staged=(C.c_int*13)()
            handoff.stage(staged,tx,ty,target.x,target.y,target.id,s.player.dir)
            assert core.v6_tower_route_teleport(C.byref(r),tx,ty)
            t=rooms[r.index].teleporter.contents
            got=(s.player.x,s.player.y,s.player.old_x,s.player.old_y,s.player.gravity,
                w.save.x,w.save.y,w.save.gravity,w.save.dir,w.save.room_x,w.save.room_y,w.save.id,t.state)
            assert got==tuple(staged),(got,tuple(staged))
            d.travel=0
            a=Arrival();core.v6_teleporter_arrival_init(C.byref(a))
            a.flash=d.flash;a.shake=d.shake
            assert core.v6_teleporter_arrival_start(C.byref(a))
            expected_arrival=Arrival.from_buffer_copy(a)
            # Source silent entity state-2 setup is independently validated by
            # test_teleporter; it precedes the next meaningful arrival change.
            rt=Teleporter(t.x,t.y,t.id,6,0,0)
            region=Region(1,t.x-32,t.y-32,160,160)
            ref.reference_init(C.byref(s.player),r.room.tiles,r.room.tileset,r.room.extra_row)
            @PHASE
            def arrive_phase(route,context):
                return core.v6_teleporter_arrival_tick(C.byref(a),C.byref(s.player),C.byref(s.motion),
                    C.byref(s,type(s).invisible.offset),C.byref(t),C.byref(r.tele_region))
            @SCRIPT
            def arrive_script(p,m):
                arrival_source.reference(C.byref(expected_arrival),p,m,C.byref(invisible),C.byref(rt),C.byref(region))
            ref.set_script(arrive_script);requests=[];saved=bytes(w.save)
            for tick in range(42):
                assert core.v6_tower_route_step_phase(C.byref(r),7|8,arrive_phase,None)
                ref.reference_step(7|8);p=Player();ref.reference_read(C.byref(p))
                assert tuple(getattr(s.player,f) for f in FIELDS)==tuple(getattr(p,f) for f in FIELDS),(tx,tick+1)
                assert bytes(a)==bytes(expected_arrival) and bytes(t)==bytes(rt)
                assert bytes(r.tele_region)==bytes(region) and s.invisible==invisible.value
                assert s.death_timer==-1 and bytes(w.save)==saved
                if a.events:requests.append((tick+1,a.events))
                decay(a);decay(expected_arrival);ticks+=1
            assert requests==[(1,1),(16,2),(42,4)] and a.control and not a.state and not s.invisible
            assert s.player.flips==0
        assert r.index==4 and (w.save.room_x,w.save.room_y,w.save.x,w.save.y)==(111,104,156,92)
    print(f'PASS host round trips: {ticks} coupled source departure/arrival/input/physics ticks, four Script handoffs, pending-request retention and centre checkpoints; native travel/effects/save pending')
if __name__=='__main__':main()
