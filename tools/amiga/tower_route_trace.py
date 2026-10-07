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
def verify(report,path,upper=False,trigger=False,rescue=False,skip=False):
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
        if rescue:
            from rescue_trace import Rescue
            runner=Rescue(core,skip)
            from test_companion import state as crew_state
            offset=data.index(b'V6CT\0\0\0\1');count,capacity=struct.unpack_from('>II',data,offset+8)
            assert count==capacity==128
            crew_records=list(struct.iter_unpack('>14I',data[offset+16:offset+16+count*56]))
            offset=data.index(b'V6CF\0\0\0\1');crew_final=struct.unpack_from('>14I',data,offset+8)
            offset=data.index(b'V6RV\0\0\0\1');count,capacity=struct.unpack_from('>II',data,offset+8)
            assert count==capacity==128
            rescue_records=list(struct.iter_unpack('>18I',data[offset+16:offset+16+count*72]))
            offset=data.index(b'V6RA\0\0\0\1');rescue_final=struct.unpack_from('>18I',data,offset+8)
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
        buttons=route[tick] if tick<len(route) else 0
        if rescue:
            runner.crew_step(s.player,r.room,s.death_timer)
            buttons=runner.input(tick,buttons,s.player)
        assert core.v6_tower_route_step(C.byref(r),buttons)
        if trigger:
            if r.index!=previous:core.v6_hallway_trigger_enter(C.byref(t),r.rooms[r.index].x,r.rooms[r.index].y,C.byref(story))
            if core.v6_hallway_trigger_step(C.byref(t),C.byref(story),C.byref(s.player)):trigger_ticks.append(tick+1)
            if rescue:runner.tick(t,story)
            if tick<128:
                assert trigger_records[tick]==trigger_state(t,story),('trigger',tick)
                if rescue:assert crew_records[tick]==crew_state(runner.crew),('companion',tick,crew_records[tick],crew_state(runner.crew))
                if rescue:assert rescue_records[tick]==runner.state(story),('rescue',tick,rescue_records[tick],runner.state(story))
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
    report.update(trace_fields=128*(79 if rescue else 47 if trigger else 40),crossings=crossings,room_transitions=r.transitions,
        remote_returns=r.returns,loading_frames=final[3],deaths=s.deaths,respawns=s.respawns,
        saved_id=w.save.id,death_ticks=death_ticks)
    if trigger:
        assert trigger_final==trigger_state(t,story)==((1,1,9,0,0,1,1) if rescue else (1,0,0,0,1,1,1))
        assert trigger_ticks==[4] and not death_ticks and w.save.id==505147
        report.update(trigger_ticks=trigger_ticks,script_request=t.pending,script_requests=t.requests,
            rescue_triggered=story.rescue_triggered,red_rescued=story.red_rescued,companion=story.companion,
            crew_retained=trigger_final[6])
        if rescue:
            assert crew_final==crew_state(runner.crew)
            assert runner.crew.follow_steps>0 and runner.crew.body.x!=264
            report.update(companion_follow_steps=runner.crew.follow_steps,companion_x=runner.crew.body.x,companion_y=runner.crew.body.y)
            assert rescue_final==runner.state(story)
            assert not runner.vm.active and not runner.vm.error and runner.vm.following and runner.vm.control
            assert runner.shown==([] if skip else list(range(6)))
            report.update(speech_order=runner.shown,rescue_completed=True,skip_cutscene=skip,
                cue_requests=runner.vm.cues,following_requested=runner.vm.following)
