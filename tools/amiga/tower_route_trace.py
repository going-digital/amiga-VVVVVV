"""Native staged hallway transitions against host route gameplay."""
import ctypes as C
import re
import struct
from test_tower_route import libraries,route_setup,OUT,ROOT
from tower_recovery_trace import read_trace
from test_tower_camera import FIELDS
from tower_world_trace import state
def inputs(upper=False,trigger=False):
    text=(ROOT/('tools/amiga/tower_trigger_replay.h' if trigger else 'tools/amiga/tower_upper_replay.h' if upper else 'tools/amiga/tower_route_replay.h')).read_text()
    return [int(v) for v in re.search(r'\{(.*?)\}',text,re.S)[1].split(',') if v.strip()]
def verify(report,path,upper=False,trigger=False):
    core,_=libraries();r,s,w,keep=route_setup(core,index=14 if upper or trigger else 0)
    if upper:
        core.v6_tower_session_init(C.byref(s),280,80,0,1)
    if trigger:
        from test_hallway_trigger import Trigger,Story,bind,state as trigger_state
        bind(core);t=Trigger();story=Story()
        core.v6_tower_session_init(C.byref(s),180,185,0,1)
        assert core.v6_tower_route_load(C.byref(r),110,104,0)
        core.v6_hallway_trigger_init(C.byref(t))
        core.v6_hallway_trigger_enter(C.byref(t),110,104,C.byref(story))
    cameras,players=read_trace(path);data=path.read_bytes()
    if trigger:
        offset=data.index(b'V6HT\0\0\0\1');count,capacity=struct.unpack_from('>II',data,offset+8)
        assert count==capacity==128
        trigger_records=list(struct.iter_unpack('>7I',data[offset+16:offset+16+count*28]))
        offset=data.index(b'V6HQ\0\0\0\1');trigger_final=struct.unpack_from('>7I',data,offset+8)
        trigger_ticks=[]
    offset=data.index(b'V6WT\0\0\0\1');count,capacity=struct.unpack_from('>II',data,offset+8)
    assert count==capacity==128
    records=list(struct.iter_unpack('>12I',data[offset+16:offset+16+count*48]))
    offset=data.index(b'V6RR\0\0\0\1');count=struct.unpack_from('>I',data,offset+8)[0]
    assert count==128
    routes=list(struct.iter_unpack('>3I',data[offset+12:offset+12+count*12]))
    offset=data.index(b'V6RT\0\0\0\1');final=struct.unpack_from('>5I',data,offset+8)
    offset=data.index(b'V6WG\0\0\0\1');world_final=struct.unpack_from('>13I',data,offset+8)
    route=inputs(upper,trigger);crossings=[];death_ticks=[]
    for tick in range(report['logic_ticks']):
        previous=r.index
        deaths=s.deaths
        assert core.v6_tower_route_step(C.byref(r),route[tick] if tick<len(route) else 0)
        if trigger:
            if r.index!=previous:core.v6_hallway_trigger_enter(C.byref(t),r.rooms[r.index].x,r.rooms[r.index].y,C.byref(story))
            if core.v6_hallway_trigger_step(C.byref(t),C.byref(story),C.byref(s.player)):trigger_ticks.append(tick+1)
            if tick<128:assert trigger_records[tick]==trigger_state(t,story),('trigger',tick)
        if r.index!=previous:crossings.append((tick+1,r.index))
        if s.deaths!=deaths:death_ticks.append(tick+1)
        if tick<128:
            c=tuple(getattr(s.camera,f) for f in FIELDS)+(s.life_timer,s.resume_delay,s.life_calls)
            p=s.player;v=(p.x,p.y,p.vx,p.vy,p.gravity,p.dir,s.death_timer,s.invisible,s.deaths,s.respawns,p.old_x,p.old_y)
            assert cameras[tick]==c,('camera',tick,cameras[tick],c)
            assert players[tick]==v,('player',tick,players[tick],v)
            bank=w.checkpoints[:w.count]
            assert records[tick]==tuple(value&0xffffffff for value in state(w,bank)),('world',tick)
            assert routes[tick]==(r.index,r.transitions,r.returns),('route',tick)
    assert crossings==([] if trigger else [(7,3),(14,1),(85,3)] if upper else [(11,2),(18,0)])
    assert r.transitions==(1 if trigger else 3 if upper else 2) and not r.error
    if upper:assert r.returns==1 and w.save.id==50520 and death_ticks==[56]
    assert final[:3]==(r.index,r.transitions,r.returns) and not final[4]
    assert world_final[:12]==tuple(value&0xffffffff for value in state(w,w.checkpoints[:w.count]))
    assert final[3]==(0 if trigger else 96 if upper else 64) and (trigger or s.respawns>0) and report['camera']==s.camera.y
    report.update(trace_fields=128*(47 if trigger else 40),crossings=crossings,room_transitions=r.transitions,
        remote_returns=r.returns,loading_frames=final[3],deaths=s.deaths,respawns=s.respawns,
        saved_id=w.save.id,death_ticks=death_ticks)
    if trigger:
        assert trigger_final==trigger_state(t,story)==(1,0,0,0,1,1,1)
        assert trigger_ticks==[4] and not death_ticks and w.save.id==505147
        report.update(trigger_ticks=trigger_ticks,script_request=t.pending,script_requests=t.requests,
            rescue_triggered=story.rescue_triggered,red_rescued=story.red_rescued,companion=story.companion,
            crew_retained=trigger_final[6])
