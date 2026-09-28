"""Reference replay for the native camera-only recovery fixture."""
import ctypes as C
import subprocess
import struct
from test_tower_camera import ROOT,OUT

def read_trace(path):
    data=path.read_bytes()
    matches=[]
    for offset in range(0,len(data)-16,2):
        if data[offset:offset+8]!=b'V6CT\0\0\0\2':continue
        count,capacity=struct.unpack_from('>II',data,offset+8)
        if capacity!=128 or count!=128:continue
        end=offset+16+128*26+count*48
        if end<=len(data):
            matches.append((list(struct.iter_unpack('>13h',data[offset+16:offset+16+count*26])),
                            list(struct.iter_unpack('>12i',data[offset+16+128*26:end]))))
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
    trace,players=read_trace(ram_path)
    # Compile the actual Game::lifesequence body, including visibility and gravity.
    source=(ROOT/'desktop_version/src/Game.cpp').read_text()
    start=source.index('void Game::lifesequence(void)');opening=source.index('{',start)
    end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    wrapper='''#define INBOUNDS_VEC(i,v) ((i)==0)
struct Obj { struct { bool invis; } entities[1]; int getplayer() { return 0; } } obj;
struct Game { int lifeseq,gravitycontrol,savegc; bool noflashingmode; void lifesequence(); };
'''+source[start:end]+'''
extern "C" void life_reference(int *v) {
Game game={v[0],v[1],1,false};obj.entities[0].invis=v[2];game.lifesequence();
v[0]=game.lifeseq;v[1]=game.gravitycontrol;v[2]=obj.entities[0].invis;
}
'''
    (OUT/'real-life.cpp').write_text(wrapper)
    subprocess.run(['c++','-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all',
        str(OUT/'real-life.cpp'),'-o',str(OUT/'real-life.so')],check=True)
    advance=C.CDLL(str(OUT/'real-life.so')).life_reference
    advance.argtypes=[C.POINTER(C.c_int)]
    player=[80,450,16777216,-16777216,0,0,-1,0,0,0,79,451]
    state=(C.c_int*10)();life=delay=calls=0
    assert report['logic_ticks']>=len(trace),report
    for tick in range(report['logic_ticks']):
        if tick==60:player[6]=30
        early(state,player[1],1,1,0,0)
        r=(C.c_int*6)(state[2],state[4],delay,state[9],0,life)
        recovery(r,life,life-1,player[6])
        state[2],state[4],delay,state[9],count,life=r
        if count:
            values=(C.c_int*3)(life+1,player[4],player[7])
            advance(values)
            assert values[0]==life
            player[4],player[7]=values[1],values[2]
        calls+=count
        if player[6]!=-1:
            if player[6]==30:player[8]+=1
            player[6]-=1
            if player[6]<=0:
                player[0:6]=[144,300,0,0,1,0]
                player[6]=-1;player[7]=1;player[9]+=1;life=10
        if tick<len(trace):
            expected=tuple(state)+(life,delay,calls)
            assert trace[tick]==expected, ('native camera tick',tick,trace[tick],expected)
            assert players[tick]==tuple(player),('native player tick',tick,players[tick],player)
    expected=dict(camera=state[0],camera_mode=state[2],recovery_seek_frames=state[4],
                  recovery_delay=delay,recovery_calls=calls,recovery_life=life)
    for key,value in expected.items():
        assert report[key]==value,(key,report[key],value)
    assert calls==10 and life==0 and player[9]==1,expected
    report['native_trace_ticks']=len(trace)
    report['native_trace_fields']=25
    report['verified_player_respawns']=player[9]
    report['reference_recovery_ticks']=report['logic_ticks']
