#!/usr/bin/env python3
"""Check recovery callback gating and subsequent death override against source."""
import ctypes as C
import json
import subprocess
from test_tower_camera import ROOT,OUT,Camera

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=source.index('        if (game.lifeseq > 0)',source.index('if (map.towermode)'))
    opening=source.index('{',start);end=opening+1;depth=1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    recovery=source[start:end]
    start=source.index('        if (map.towermode)',source.index('    if (game.deathseq != -1)',end))
    opening=source.index('{',start);end=source.index('}',opening)+1
    death=source[start:end]
    wrapper='''extern "C" void reference(int *v,int life,int next_life,int deathseq) {
struct { int cameramode,cameraseekframe,resumedelay,colsuperstate; bool towermode; } map={v[0],v[1],v[2],v[3],true};
struct Game { int lifeseq,next,calls; void lifesequence() { ++calls;lifeseq=next; } } game={life,next_life,0};
'''+recovery+'\nif(deathseq!=-1) {\n'+death+'''
}
v[0]=map.cameramode;v[1]=map.cameraseekframe;v[2]=map.resumedelay;
v[3]=map.colsuperstate;v[4]=game.calls;v[5]=game.lifeseq;
}
'''
    (OUT/'recovery.cpp').write_text(wrapper)
    flags=['-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,str(OUT/'recovery.cpp'),'-o',str(OUT/'recovery.so')],check=True)
    subprocess.run(['cc',*flags,str(ROOT/'amiga_version/tower_camera.c'),'-o',str(OUT/'camera.so')],check=True)
    ref=C.CDLL(str(OUT/'recovery.so')).reference
    lib=C.CDLL(str(OUT/'camera.so'))
    callback_type=C.CFUNCTYPE(C.c_int,C.c_void_p)
    lib.v6_tower_camera_recover.argtypes=[C.POINTER(Camera),C.POINTER(C.c_int16),C.c_int,callback_type,C.c_void_p]
    lib.v6_tower_camera_death.argtypes=[C.POINTER(Camera),C.c_int]
    ref.argtypes=[C.POINTER(C.c_int),C.c_int,C.c_int,C.c_int]
    calls=0;remaining=0
    @callback_type
    def advance(context):
        nonlocal calls,remaining
        assert context==1234
        calls+=1;remaining=next_life
        return remaining
    checks=0
    for mode in range(6):
        for seek in (-1,0,1,10,20):
            for delay in (-1,0,1,4):
                for life in (-1,0,1,8):
                    for next_life in (0,1,7):
                        for deathseq in (-1,0,1,30):
                            c=Camera(100,98,mode,0,seek,2,3,2,3,6)
                            d=C.c_int16(delay);r=(C.c_int*6)(mode,seek,delay,6,0,life)
                            calls=0;remaining=life
                            ref(r,life,next_life,deathseq)
                            lib.v6_tower_camera_recover(C.byref(c),C.byref(d),life,advance,1234)
                            lib.v6_tower_camera_death(C.byref(c),deathseq)
                            actual=[c.mode,c.seek_frames,d.value,c.colour_superstate,calls,remaining]
                            assert actual==list(r),(mode,seek,delay,life,next_life,deathseq,actual,list(r))
                            assert c.y==100 and c.old_y==98 and c.spike_top==2 and c.spike_bottom==3
                            checks+=1
    report=dict(cases=checks,scope='Extracted recovery gate and subsequent death camera override; lifecycle callback is a controlled stub, not player respawn integration')
    (OUT/'recovery-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))
if __name__=='__main__':main()
