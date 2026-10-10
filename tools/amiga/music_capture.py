"""Trace-only native music controller against desktop room/fade methods."""
import ctypes as C
import struct
from test_music_control import libraries,State,Plan

def verify(report,ram):
    core,ref=libraries();s=State();expected=State();p=Plan();data=ram.read_bytes()
    at=data.index(b'V6MU\0\0\0\1');count,entries=struct.unpack_from('>2I',data,at+8)
    assert (count,entries)==(128,3),(count,entries)
    rows=[struct.unpack_from('>32i',data,at+16+128*i) for i in range(count)]
    core.v6_music_enter_room.argtypes=[C.POINTER(State)]+[C.c_int]*7+[C.POINTER(Plan)]
    assert core.v6_music_init(C.byref(s),65535);ref.reference_init(65535)
    assert core.v6_music_command(C.byref(s),0,4,C.byref(p));ref.reference_command(0,4)
    starts=[]
    for tick,row in enumerate(rows,1):
        room=(111,104) if tick<22 or tick>=86 else (110,105)
        entry=tick in (1,22,86)
        assert row[29:32]==(*room,int(entry)),(tick,row[29:32],room)
        if entry:
            assert core.v6_music_enter_room(C.byref(s),*room,0,0,0,0,0,C.byref(p))
            ref.reference_room(*room,0,0,0,0,0)
        p=Plan()
        assert core.v6_music_tick(C.byref(s),34,C.byref(p));ref.reference_tick(34)
        ref.reference_snapshot(C.byref(expected))
        wanted=tuple(getattr(expected,name) for name,_ in State._fields_)
        assert row[:16]==wanted,(tick,row[:16],wanted)
        plan=(p.count,*[v for op in p.ops for v in (op.kind,op.track,op.value)])
        assert row[16:29]==plan,(tick,row[16:29],plan)
        for op in p.ops[:p.count]:
            if op.kind==1:starts.append((tick,op.track,op.value))
    assert starts==[(1,2,1),(35,1,1),(119,2,1)],starts
    report.update(music_trace_fields=count*32,music_entries=entries,music_starts=starts,
        music_final_track=rows[-1][0],music_final_gain=rows[-1][8],
        scope='Native trace-only source music dispatch/fades and staged round trip; virtual backend, no tracker playback or Paula music writes')
