"""Pre-rescued companion entry/exclusion against native route transitions."""
import ctypes as C
import struct
from test_tower_route import libraries,route_setup
from test_companion import Companion,bind,state
from tower_route_trace import inputs

def verify(report,path):
    core,_=libraries();bind(core);r,s,w,keep=route_setup(core,index=14)
    core.v6_tower_session_init(C.byref(s),280,80,0,1)
    crew=Companion();core.v6_companion_init(C.byref(crew))
    core.v6_companion_enter(C.byref(crew),9,1,109,C.byref(s.player));crew.mood=0;crew.following=1
    data=path.read_bytes();offset=data.index(b'V6CT\0\0\0\1')
    count,capacity=struct.unpack_from('>II',data,offset+8);assert count==capacity==128
    records=list(struct.iter_unpack('>14I',data[offset+16:offset+16+count*56]))
    offset=data.index(b'V6CF\0\0\0\1');final=struct.unpack_from('>14I',data,offset+8)
    buttons=inputs(upper=True);entries=[]
    for tick in range(report['logic_ticks']):
        core.v6_companion_step(C.byref(crew),C.byref(s.player),C.byref(r.room),s.death_timer)
        previous=r.index
        assert core.v6_tower_route_step(C.byref(r),buttons[tick] if tick<len(buttons) else 0)
        if r.index!=previous:
            core.v6_companion_enter(C.byref(crew),9,r.index<2,r.rooms[r.index].x,C.byref(s.player))
            entries.append((tick+1,r.index,crew.visible,crew.body.x,crew.body.vx,crew.body.dir))
        crew.mood=0;crew.following=1
        if tick<128:assert records[tick]==state(crew),('companion route',tick,records[tick],state(crew))
    assert final==state(crew)
    assert [(tick,index,visible) for tick,index,visible,*_ in entries]==[(7,3,1),(14,1,0),(85,3,1)]
    assert crew.spawns==2 and crew.follow_steps>0
    report.update(trace_fields=report['trace_fields']+14*128,companion_entries=entries,
        companion_spawns=crew.spawns,companion_follow_steps=crew.follow_steps,
        companion_x=crew.body.x,companion_y=crew.body.y)
