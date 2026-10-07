"""Native staged hallway transitions against host route gameplay."""
import ctypes as C
import re
import struct
from test_tower_route import libraries,route_setup,OUT,ROOT
from tower_recovery_trace import read_trace
from test_tower_camera import FIELDS
from tower_world_trace import state
def inputs(upper=False):
    text=(ROOT/('tools/amiga/tower_upper_replay.h' if upper else 'tools/amiga/tower_route_replay.h')).read_text()
    return [int(v) for v in re.search(r'\{(.*?)\}',text,re.S)[1].split(',') if v.strip()]
def verify(report,path,upper=False):
    core,_=libraries();r,s,w,keep=route_setup(core,index=14 if upper else 0)
    if upper:
        core.v6_tower_session_init(C.byref(s),280,80,0,1)
    cameras,players=read_trace(path);data=path.read_bytes()
    offset=data.index(b'V6WT\0\0\0\1');count,capacity=struct.unpack_from('>II',data,offset+8)
    assert count==capacity==128
    records=list(struct.iter_unpack('>12I',data[offset+16:offset+16+count*48]))
    offset=data.index(b'V6RR\0\0\0\1');count=struct.unpack_from('>I',data,offset+8)[0]
    assert count==128
    routes=list(struct.iter_unpack('>3I',data[offset+12:offset+12+count*12]))
    offset=data.index(b'V6RT\0\0\0\1');final=struct.unpack_from('>5I',data,offset+8)
    offset=data.index(b'V6WG\0\0\0\1');world_final=struct.unpack_from('>13I',data,offset+8)
    route=inputs(upper);crossings=[]
    for tick in range(report['logic_ticks']):
        previous=r.index
        if upper and tick==60:core.v6_tower_session_die(C.byref(s))
        assert core.v6_tower_route_step(C.byref(r),route[tick] if tick<len(route) else 0)
        if r.index!=previous:crossings.append((tick+1,r.index))
        if tick<128:
            c=tuple(getattr(s.camera,f) for f in FIELDS)+(s.life_timer,s.resume_delay,s.life_calls)
            p=s.player;v=(p.x,p.y,p.vx,p.vy,p.gravity,p.dir,s.death_timer,s.invisible,s.deaths,s.respawns,p.old_x,p.old_y)
            assert cameras[tick]==c,('camera',tick,cameras[tick],c)
            assert players[tick]==v,('player',tick,players[tick],v)
            bank=w.checkpoints[:w.count]
            assert records[tick]==tuple(value&0xffffffff for value in state(w,bank)),('world',tick)
            assert routes[tick]==(r.index,r.transitions,r.returns),('route',tick)
    assert crossings==([(7,3),(14,1),(90,3)] if upper else [(11,2),(18,0)])
    assert r.transitions==(3 if upper else 2) and not r.error
    if upper:assert r.returns==1 and w.save.id==50520
    assert final[:3]==(r.index,r.transitions,r.returns) and not final[4]
    assert world_final[:12]==tuple(value&0xffffffff for value in state(w,w.checkpoints[:w.count]))
    assert final[3]==(96 if upper else 64) and s.respawns>0 and report['camera']==s.camera.y
    report.update(trace_fields=128*40,crossings=crossings,room_transitions=r.transitions,
        remote_returns=r.returns,loading_frames=final[3],deaths=s.deaths,respawns=s.respawns,
        saved_id=w.save.id)
