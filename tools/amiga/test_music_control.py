#!/usr/bin/env python3
"""Portable music state against extracted desktop Music.cpp methods."""
import ctypes as C
import random
import subprocess
from pathlib import Path
from test_audio import ROOT
from export_music_area import export

FIELDS='current halted_song queued nice quick safe fade_in fade_out volume present paused available start end duration elapsed'.split()
class State(C.Structure):
    _fields_=[(name,C.c_int32) for name in FIELDS]
class Op(C.Structure):
    _fields_=[('kind',C.c_int32),('track',C.c_int32),('value',C.c_int32)]
class Plan(C.Structure):
    _fields_=[('count',C.c_int32),('ops',Op*4)]

def method(source,signature):
    start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

def libraries():
    out=ROOT/'build/amiga-music';out.mkdir(parents=True,exist_ok=True)
    export(out)
    source=(ROOT/'desktop_version/src/Music.cpp').read_text()
    helpers=source[source.index('struct FadeState'):source.index('void musicclass::fadeMusicVolumeIn')]
    signatures=['bool musicclass::play(int t)','void musicclass::resume(void)',
        'void musicclass::resumefade(const int fadein_ms)','void musicclass::pause(void)',
        'void musicclass::haltdasmusik(const bool from_fade)','void musicclass::silencedasmusik(void)',
        'void musicclass::fadeMusicVolumeIn(int ms)','void musicclass::fadeMusicVolumeOut(const int fadeout_ms)',
        'void musicclass::fadeout(const bool quick_fade_','void musicclass::processmusicfadein(void)',
        'void musicclass::processmusicfadeout(void)','void musicclass::processmusic(void)',
        'void musicclass::niceplay(int t)','bool musicclass::halted(void)',
        'void musicclass::changemusicarea(int x, int y)']
    code='''#include <stdint.h>
#include <assert.h>
#include "music_control.h"
#define SDL_assert assert
#define musicroom(x,y) ((x)+(y)*20)
#define INBOUNDS_ARR(i,a) ((i)>=0 && (i)<400)
#define VVV_MAX_VOLUME 128
#define Music_PATHCOMPLETE 0
#define Music_PLENARY 7
#define Music_PREDESTINEDFATEREMIX 15
#define INBOUNDS_VEC(t,v) ((t)>=0 && (t)<16)
#define vlog_error(...) ((void)0)
static unsigned available;static bool present,paused;static int timestep;
struct {bool custommode;} map;
struct {int get_timestep(){return timestep;} bool intimetrial;int roomx,roomy,currentroomdeaths;} game;
static bool finalmode,custommode;
static int roomdeaths[400],roomdeathsfinal[400];
struct {int mapwidth=20,mapheight=20;} cl;
struct {bool running;} script;
struct {bool setflipmode;} graphics;
struct MusicTrack {
 int id;
 bool Play(bool){if(!(available&(1U<<id)))return false;present=true;paused=false;return true;}
 static void Pause(){if(present)paused=true;}
 static void Resume(){if(present)paused=false;}
 static bool IsPaused(){return paused || !present;}
};
static MusicTrack musicTracks[16];
struct musicclass {
 int currentsong,haltedsong,nicechange,controlVolume,num_mmmmmm_tracks,num_pppppp_tracks;
 bool safeToProcessMusic,m_doFadeInVol,m_doFadeOutVol,nicefade,quick_fade,mmmmmm,usingmmmmmm;
 void set_music_volume(int){}
 bool play(int);void resume();void resumefade(int);void pause();void haltdasmusik(bool);
 void silencedasmusik();void fadeMusicVolumeIn(int);void fadeMusicVolumeOut(int);
 void fadeout(bool);void processmusicfadein();void processmusicfadeout();void processmusic();
 void niceplay(int);bool halted();void changemusicarea(int,int);
};
'''+helpers+'\n'+source[source.index('static const int areamap'):source.index('SDL_COMPILE_TIME_ASSERT(areamap')]+'\n'+'\n'.join(method(source,s) for s in signatures)+'''
static musicclass m;
extern "C" void reference_init(unsigned mask) {
 m={};m.currentsong=m.haltedsong=m.nicechange=-1;m.quick_fade=true;
 m.num_pppppp_tracks=16;available=mask;present=false;paused=true;fade={};
 for(int i=0;i<16;++i)musicTracks[i].id=i;
}
extern "C" void reference_command(unsigned c,int arg) {
 switch(c){
 case 0:m.play(arg);break;case 1:m.niceplay(arg);break;case 2:m.pause();break;
 case 3:m.haltdasmusik(false);break;case 4:m.resume();break;case 5:m.resumefade(arg);break;
 case 6:m.fadeout(arg!=0);break;case 7:m.fadeMusicVolumeIn(arg);break;
 case 8:m.silencedasmusik();break;
 }
}
extern "C" void reference_tick(unsigned ms){timestep=ms;m.processmusic();}
extern "C" void reference_area(int x,int y,int running,int flip,int trial){
 script.running=running;graphics.setflipmode=flip;game.intimetrial=trial;m.changemusicarea(x,y);
}
extern "C" void reference_snapshot(V6MusicControl *s){
 *s={m.currentsong,m.haltedsong,m.nicechange,m.nicefade,m.quick_fade,m.safeToProcessMusic,
 m.m_doFadeInVol,m.m_doFadeOutVol,m.controlVolume,present,paused,(int)available,
 fade.start_volume,fade.end_volume,fade.duration_ms,fade.step_ms};
}
'''
    dispatch_source=(ROOT/'desktop_version/src/Map.cpp').read_text()
    begin=dispatch_source.index('    if (finalmode)\n    {\n        //Ok, what way')
    dispatch=dispatch_source[begin:dispatch_source.index('    loadlevel(game.roomx, game.roomy);',begin)]
    code+='\nextern "C" void reference_room(int rx,int ry,int final_,int custom_,int running,int flip,int trial){\n'
    code+='finalmode=final_;custommode=custom_;script.running=running;graphics.setflipmode=flip;game.intimetrial=trial;\n'
    code+=dispatch.replace('music.', 'm.')+'\n}\n'
    path=out/'music-control-reference.cpp';path.write_text(code)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
        '-I'+str(ROOT/'amiga_version'),'-I'+str(out)]
    subprocess.run(['c++','-std=c++11',*flags,str(path),'-o',str(out/'music-reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/music_control.c'),str(ROOT/'amiga_version/music_area.c'),'-o',str(out/'music-control.so')],check=True)
    core=C.CDLL(str(out/'music-control.so'));ref=C.CDLL(str(out/'music-reference.so'))
    core.v6_music_init.argtypes=[C.POINTER(State),C.c_uint]
    core.v6_music_command.argtypes=[C.POINTER(State),C.c_uint,C.c_int,C.POINTER(Plan)]
    core.v6_music_tick.argtypes=[C.POINTER(State),C.c_uint,C.POINTER(Plan)]
    ref.reference_snapshot.argtypes=[C.POINTER(State)]
    return core,ref

def main():
    core,ref=libraries();s=State();expected=State();p=Plan();checks=0
    def init(mask=65535):
        assert core.v6_music_init(C.byref(s),mask);ref.reference_init(mask);check()
    def check():
        nonlocal checks
        ref.reference_snapshot(C.byref(expected))
        assert bytes(s)==bytes(expected),[(n,getattr(s,n),getattr(expected,n)) for n in FIELDS if getattr(s,n)!=getattr(expected,n)]
        assert 0<=p.count<=4
        for op in p.ops[:p.count]:
            assert 1<=op.kind<=4
            if op.kind==1:assert 0<=op.track<=15 and op.value==(op.track not in (0,7))
            if op.kind==4:assert 0<=op.value<=128
        checks+=1
    def command(c,arg=0):
        assert core.v6_music_command(C.byref(s),c,arg,C.byref(p));ref.reference_command(c,arg);check()
    def tick(ms=34):
        assert core.v6_music_tick(C.byref(s),ms,C.byref(p));ref.reference_tick(ms);check()
    # Every base ID, full fade completion and same-track no-restart.
    for track in range(16):
        init();command(0,track)
        assert [(o.kind,o.track,o.value) for o in p.ops[:p.count]]==[(1,track,int(track not in (0,7))),(4,-1,128 if track in (0,7) else 0)]
        command(0,track);assert not p.count
        for _ in range(92):tick()
        command(6,0)
        for _ in range(61):tick()
        assert s.current==-1 and s.halted_song==track and s.paused
        command(5,3000)
        assert [(o.kind,o.value) for o in p.ops[:p.count]]==[(3,0),(4,0)]
    # Queued change, repeated requests, one-shot during fade, explicit cancellation.
    for target in range(16):
        init();command(0,2)
        for _ in range(31):tick()
        command(1,target);command(1,target)
        for _ in range(170):tick()
        command(6,1);command(0,7);tick();command(3);command(4)
    # At fade completion, adapter gain/pause/start/gain order is significant.
    init();command(0,2)
    for _ in range(92):tick()
    command(1,3);transition=False
    for _ in range(61):
        tick()
        if any(op.kind==1 for op in p.ops[:p.count]):
            assert [(op.kind,op.track,op.value) for op in p.ops[:p.count]]==[(4,-1,0),(2,-1,0),(1,3,1),(4,-1,0)]
            transition=True
    assert transition
    # Zero duration, fractional fade-out duration and backend-start failure.
    for mask in (0,1,128,512,65535):
        init(mask)
        for c,arg in ((0,9),(7,0),(6,1),(1,2),(3,0),(5,0),(0,0)):
            command(c,arg);tick()
    rng=random.Random(34)
    for _ in range(40):
        init(rng.choice((0,0xffff,0x0281)))
        for _ in range(600):
            if rng.randrange(3):tick(rng.choice((0,1,17,34,100,1000)))
            else:
                c=rng.randrange(9)
                arg=rng.randrange(16) if c in (0,1) else rng.randrange(2) if c==6 else rng.choice((0,1,500,2000,3000,60000)) if c in (5,7) else 0
                command(c,arg)
    init();command(0,-1);tick()
    for c,arg in ((9,0),(0,-2),(0,16),(1,-1),(6,2),(5,-1),(7,60001)):
        before=(bytes(s),bytes(p));assert not core.v6_music_command(C.byref(s),c,arg,C.byref(p));assert before==(bytes(s),bytes(p))
    before=(bytes(s),bytes(p));assert not core.v6_music_tick(C.byref(s),1001,C.byref(p));assert before==(bytes(s),bytes(p))
    assert not core.v6_music_command(None,0,0,C.byref(p))
    assert not core.v6_music_tick(C.byref(s),34,None)
    assert not core.v6_music_init(C.byref(s),65536) and before[0]==bytes(s)
    for field,value in (('volume',129),('current',16),('duration',60001),('elapsed',61001),('fade_in',2)):
        init();setattr(s,field,value);before=(bytes(s),bytes(p))
        assert not core.v6_music_tick(C.byref(s),34,C.byref(p))
        assert not core.v6_music_command(C.byref(s),0,2,C.byref(p))
        assert before==(bytes(s),bytes(p))
    print(f'PASS music control: {checks} extracted desktop state comparisons; base IDs, one-shots, fades, queued changes, pause/resume, unavailable starts and input guards')
if __name__=='__main__':main()
