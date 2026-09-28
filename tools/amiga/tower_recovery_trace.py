"""Reference replay for the native camera-only recovery fixture."""
import ctypes as C
import subprocess
import struct
from test_tower_camera import ROOT,OUT

def read_trace(path):
    data=path.read_bytes()
    matches=[]
    for offset in range(0,len(data)-16,2):
        if data[offset:offset+8]!=b'V6CT\0\0\0\1':continue
        count,capacity=struct.unpack_from('>II',data,offset+8)
        if capacity!=128 or count!=128:continue
        end=offset+16+count*26
        if end<=len(data):
            matches.append(list(struct.iter_unpack('>13h',data[offset+16:end])))
    assert len(matches)==1, ('Expected one completed native camera trace',len(matches))
    return matches[0]


def verify(report,ram_path):
    # These tests compile the original desktop source blocks into reference libs.
    for name in ('test_tower_camera.py','test_tower_camera_recovery.py'):
        subprocess.run(['python3',str(ROOT/'tools/amiga'/name)],check=True)
    early=C.CDLL(str(OUT/'reference.so')).reference
    recovery=C.CDLL(str(OUT/'recovery.so')).reference
    early.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*5
    recovery.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*3
    trace=read_trace(ram_path)
    state=(C.c_int*10)();life=delay=calls=0
    assert report['logic_ticks']>=len(trace),report
    for tick in range(report['logic_ticks']):
        if tick==70:life=5
        early(state,300,1,1,0,0)
        r=(C.c_int*6)(state[2],state[4],delay,state[9],0,life)
        recovery(r,life,life-1,30 if 60<=tick<70 else -1)
        state[2],state[4],delay,state[9],count,life=r
        calls+=count
        if tick<len(trace):
            expected=tuple(state)+(life,delay,calls)
            assert trace[tick]==expected, ('native camera tick',tick,trace[tick],expected)
    expected=dict(camera=state[0],camera_mode=state[2],recovery_seek_frames=state[4],
                  recovery_delay=delay,recovery_calls=calls,recovery_life=life)
    for key,value in expected.items():
        assert report[key]==value,(key,report[key],value)
    assert calls==5 and life==0,expected
    report['native_trace_ticks']=len(trace)
    report['native_trace_fields']=13
    report['reference_recovery_ticks']=report['logic_ticks']
