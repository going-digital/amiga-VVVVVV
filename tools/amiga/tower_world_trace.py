"""Compare native checkpoint/wrap state and player recovery with host replay."""
import ctypes as C
import re
import struct
from test_tower_world import libraries, setup, room_for, Session, World
from test_tower_camera import FIELDS
from tower_recovery_trace import read_trace
from test_player import ROOT

def inputs(wrap=False):
    text=(ROOT/('tools/amiga/tower_wrap_replay.h' if wrap else 'tools/amiga/tower_world_replay.h')).read_text()
    return [int(v) for v in re.search(r'\{(.*?)\}',text,re.S)[1].split(',') if v.strip()]

def state(world,bank):
    save=world.save
    assert world.active_mask==sum(int(c.active)<<i for i,c in enumerate(bank))
    assert world.pending_mask==sum(int(c.pending)<<i for i,c in enumerate(bank))
    return (save.id,save.x,save.y,save.gravity,save.dir,world.activations,
            sum(int(c.active)<<i for i,c in enumerate(bank)),
            sum(int(c.pending)<<i for i,c in enumerate(bank)),world.wrap_left,world.wrap_right,
            world.exit.room_x,world.exit.room_y)

def verify(report,path,wrap=False):
    core,_=libraries();room,keep=room_for(core);s,w,bank=setup(core,saved=False)
    cameras,players=read_trace(path);data=path.read_bytes()
    offset=data.index(b'V6WT\0\0\0\1');count,capacity=struct.unpack_from('>II',data,offset+8)
    assert count==capacity==128
    records=list(struct.iter_unpack('>12I',data[offset+16:offset+16+count*48]))
    offset=data.index(b'V6WG\0\0\0\1');final=struct.unpack_from('>13I',data,offset+8)
    route=inputs(wrap);changed_at=None;new_respawns=0;wrap_ticks=[]
    for tick in range(report['logic_ticks']):
        previous=s.respawns;old_wraps=(w.wrap_left,w.wrap_right)
        buttons=route[tick] if tick<len(route) else 0
        core.v6_tower_session_play_world(C.byref(s),C.byref(room),buttons,C.byref(w))
        if (w.wrap_left,w.wrap_right)!=old_wraps:wrap_ticks.append(tick+1)
        if changed_at is None and w.save.id==505167:changed_at=tick+1
        if s.respawns>previous and w.save.id==505167:
            assert (s.player.x,s.player.y,s.player.gravity,s.player.dir)==(w.save.x,w.save.y,w.save.gravity,w.save.dir)
            new_respawns+=1
        if tick<128:
            c=tuple(getattr(s.camera,f) for f in FIELDS)+(s.life_timer,s.resume_delay,s.life_calls)
            p=s.player;v=(p.x,p.y,p.vx,p.vy,p.gravity,p.dir,s.death_timer,s.invisible,s.deaths,s.respawns,p.old_x,p.old_y)
            assert cameras[tick]==c,('camera',tick,cameras[tick],c)
            assert players[tick]==v,('player',tick,players[tick],v)
            assert records[tick]==tuple(value&0xffffffff for value in state(w,bank)),('world',tick,records[tick],state(w,bank))
    assert tuple(final[:12])==tuple(value&0xffffffff for value in state(w,bank))
    assert report['camera']==s.camera.y
    if wrap:
        assert wrap_ticks==[30,36] and (w.wrap_left,w.wrap_right)==(1,1)
        assert w.save.id==505147 and w.activations==1 and s.respawns>0
    else:
        assert changed_at==72 and w.activations==2 and w.save.id==505167 and new_respawns>0
    assert not w.exit.room_x
    report.update(trace_fields=128*37,deaths=s.deaths,respawns=s.respawns,
        checkpoint_changed_at=changed_at,checkpoint_activations=w.activations,
        saved_id=w.save.id,saved_x=w.save.x,saved_y=w.save.y,
        verified_new_checkpoint_respawns=new_respawns,max_sprite_channels=final[12],
        wrap_left=w.wrap_left,wrap_right=w.wrap_right,wrap_ticks=wrap_ticks)
