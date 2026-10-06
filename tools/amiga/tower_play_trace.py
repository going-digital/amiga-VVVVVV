"""Native gameplay trace against the host session using source-verified physics."""
import ctypes as C
from test_tower_player import libraries, Tiles, READ, OUT
from test_player import Player, Room
from test_tower_camera import Camera, FIELDS
from test_tower_stream import Stream
from tower_recovery_trace import read_trace
class Motion(C.Structure):
    _fields_=[('ax',C.c_int32),('pending_y',C.c_int)]
class Session(C.Structure):
    _fields_=[('player',Player),('motion',Motion),('camera',Camera)]+[(f,C.c_int) for f in
        'save_x save_y save_gravity save_dir death_timer life_timer invisible noflashing deaths respawns life_calls'.split()]+[('resume_delay',C.c_int16)]

def verify(report,path):
    core,_=libraries();stream=Stream();blob=(OUT/'loadmap.v6tr').read_bytes()
    assert core.v6_tower_open(C.byref(stream),blob,len(blob))
    reader=READ(('v6_tower_tile',core));tiles=Tiles(reader,C.addressof(stream),0);room=Room()
    core.v6_player_tower_room(C.byref(room),C.byref(tiles))
    core.v6_tower_session_init.argtypes=[C.POINTER(Session)]+[C.c_int]*4
    core.v6_tower_session_play.argtypes=[C.POINTER(Session),C.POINTER(Room),C.c_uint,C.c_int,C.c_int]
    s=Session();core.v6_tower_session_init(C.byref(s),140,1817,0,1)
    s.camera.y=s.camera.old_y=1697
    cameras,players=read_trace(path)
    for tick in range(report['logic_ticks']):
        buttons=(2 if tick<16 else 0)|(4 if 16<=tick<20 else 0)
        core.v6_tower_session_play(C.byref(s),C.byref(room),buttons,0,0)
        if tick<len(cameras):
            c=tuple(getattr(s.camera,f) for f in FIELDS)+(s.life_timer,s.resume_delay,s.life_calls)
            p=s.player
            v=(p.x,p.y,p.vx,p.vy,p.gravity,p.dir,s.death_timer,s.invisible,s.deaths,s.respawns,p.old_x,p.old_y)
            assert cameras[tick]==c,('camera',tick,cameras[tick],c)
            assert players[tick]==v,('player',tick,players[tick],v)
    assert report['camera']==s.camera.y
    assert s.deaths>0 and s.respawns>0,(s.deaths,s.respawns)
    report.update(trace_fields=len(cameras)*25,deaths=s.deaths,respawns=s.respawns)
