#!/usr/bin/env python3
"""Reference-check the late tower edge/death and spike-height phase."""
import ctypes as C
import json
import subprocess
from test_tower_camera import ROOT,OUT,Camera

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    start=source.index('            if(map.towermode && game.lifeseq==0)')
    opening=source.index('{',start);depth=1;end=opening+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    block=source[start:end]
    wrapper='''#define INBOUNDS_VEC(i,v) ((i)==0)
extern "C" unsigned reference(int *v,int py,int valid,int direction,int invincible,int life) {
struct { int ypos,spikeleveltop,spikelevelbottom; bool towermode,invincibility; } map={v[0],v[1],v[2],true,invincible!=0};
struct { int lifeseq,deathseq; } game={life,-1};
struct { struct { int scrolldir; bool tdrawback; } towerbg; } graphics={{direction,false}};
struct Obj { struct { int yp; } entities[1]; int index; int getplayer() { return index; } } obj={{{py}},valid?0:-1};
'''+block+'''
v[0]=map.ypos;v[1]=map.spikeleveltop;v[2]=map.spikelevelbottom;
return (game.deathseq==30?1:0)|(graphics.towerbg.tdrawback?2:0);
}
'''
    (OUT/'edges.cpp').write_text(wrapper)
    flags=['-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,str(OUT/'edges.cpp'),'-o',str(OUT/'edges.so')],check=True)
    subprocess.run(['cc',*flags,str(ROOT/'amiga_version/tower_camera.c'),'-o',str(OUT/'camera.so')],check=True)
    ref=C.CDLL(str(OUT/'edges.so')).reference
    port=C.CDLL(str(OUT/'camera.so')).v6_tower_camera_edges
    ref.argtypes=[C.POINTER(C.c_int)]+[C.c_int]*5
    port.argtypes=[C.POINTER(Camera)]+[C.c_int]*5
    checks=0
    for y in (0,568,3000,5368):
        for relative in (-12,-1,0,1,7,8,9,39,40,41,163,164,165,199,200,201,207,208,209,220):
            for flags in range(16):
                valid=flags&1;direction=(flags>>1)&1;invincible=(flags>>2)&1;life=(flags>>3)&1
                for top in (0,1,7,8):
                    for bottom in (0,1,7,8):
                        c=Camera(y,0,1,0,0,top,bottom,0,0,0);r=(C.c_int*3)(y,top,bottom)
                        args=(y+relative,valid,direction,invincible,life)
                        expected=ref(r,*args);actual=port(C.byref(c),*args)
                        assert actual==expected and [c.y,c.spike_top,c.spike_bottom]==list(r),(y,relative,flags,top,bottom)
                        assert c.mode==1 and c.old_y==0
                        checks+=1
    report=dict(cases=checks,scope='Extracted desktop late edge and spike phase; normal death vs invincibility corrections; no lifecycle or native loop integration')
    (OUT/'edge-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))
if __name__=='__main__':main()
