#!/usr/bin/env python3
"""Seeing Red crew presence versus the literal desktop room setup."""
import ctypes as C
import itertools
import json
import subprocess
from test_player import ROOT,block

class Story(C.Structure):
    _fields_=[(name,C.c_int) for name in ('time_trial','translator_exploring','companion','rescue_triggered','red_rescued')]

def main():
    out=ROOT/'build/amiga-hallway-crew';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Finalclass.cpp').read_text()
    start=source.index('case rn(110,104):');body=source[start:source.index('case rn(',start+5)]
    setup=block(body,body.index('if(!game.intimetrial'))
    wrapper='''struct Game { int intimetrial,translator_exploring,companion,crewstats[6]; } game;
struct Obj { int flags[64],made,values[7];
void createentity(int x,int y,int type,int colour,int mood,int state,int dir) {
int v[]={x,y,type,colour,mood,state,dir};for(int i=0;i<7;++i)values[i]=v[i];made=1;
}
void createblock(int,int,int,int,int,int) {}
} obj;
extern "C" int reference(int x,int y,const int *s,int *spawn) {
game.intimetrial=s[0];game.translator_exploring=s[1];game.companion=s[2];
obj.flags[8]=s[3];game.crewstats[3]=s[4];obj.made=0;
if(x==110 && y==104) {
'''+setup+'''\n}
if(obj.made)for(int i=0;i<7;++i)spawn[i]=obj.values[i];return obj.made;
}
'''
    (out/'reference.cpp').write_text(wrapper)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',str(ROOT/'amiga_version/hallway_crew.c'),'-o',str(out/'core.so')],check=True)
    reference=C.CDLL(str(out/'reference.so')).reference
    reference.argtypes=[C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int)]
    visible=C.CDLL(str(out/'core.so')).v6_hallway_crew_visible
    visible.argtypes=[C.c_int,C.c_int,C.POINTER(Story)]
    count=0
    for x,y in ((110,104),(108,109),(109,104),(110,109)):
        for trial,exploring,triggered,rescued in itertools.product((0,1),repeat=4):
            for companion in (-3,0,1,9):
                s=Story(trial,exploring,companion,triggered,rescued)
                values=(C.c_int*5)(trial,exploring,companion,triggered,rescued);spawn=(C.c_int*7)()
                expected=reference(x,y,values,spawn)
                assert visible(x,y,C.byref(s))==expected,(x,y,list(values))
                if expected:assert tuple(spawn)==(264,185,18,15,1,17,0)
                count+=1
    assert not visible(110,104,None)
    report=dict(source_setup_cases=count,spawn=(264,185,18,15,1,17,0),scope='Literal room entry conditions and stand-still sad crew setup; dialogue/following not integrated')
    (out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)

if __name__=='__main__':main()
