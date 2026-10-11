#!/usr/bin/env python3
"""Actual generated yellow programs, original handlers, four-line caption pixels."""
import ctypes as C
import json
import subprocess
from test_player import ROOT,block
from test_rescue_script import VM,Program,Signals,Op,Speech,NAMES
from test_station_trigger import Story
from station_scripts import export

def main():
    out=ROOT/'build/amiga-station-rescue';out.mkdir(parents=True,exist_ok=True);compiled=export(out)
    (out/'programs.c').write_text('''#include "station_rescue_programs.h"
const V6RescueProgram *program(int skip){return skip?&v6_skipyellow_program:&v6_rescueyellow_program;}
''')
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror','-I'+str(ROOT/'amiga_version'),
        '-I'+str(out),str(out/'programs.c'),str(ROOT/'amiga_version/rescue_script.c'),str(ROOT/'amiga_version/dialogue.c'),'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));core.program.argtypes=[C.c_int];core.program.restype=C.POINTER(Program)
    core.v6_rescue_start.argtypes=[C.POINTER(VM),C.POINTER(Program),C.POINTER(Program),C.c_int]
    core.v6_station_rescue_tick.argtypes=[C.POINTER(VM),C.POINTER(Story),C.POINTER(Signals)]
    core.v6_dialogue_draw.argtypes=[C.c_void_p,C.c_void_p,C.POINTER(Speech)]
    normal,skip=core.program(0),core.program(1)
    # Inspect the compiled C artifact, not just Python compiler dictionaries.
    for program,name in ((normal,'rescueyellow'),(skip,'skipyellow')):
        desc=compiled[name];assert program.contents.count==len(desc['ops'])
        for op,want in zip(program.contents.ops[:program.contents.count],desc['ops']):
            assert (NAMES[op.op],op.value)==(want['op'],want['value'])
            if want['speech'] is not None:
                speech=op.speech.contents;data=desc['speeches'][want['speech']]
                assert speech.index==want['speech'] and speech.speaker==int(data['speaker']=='player')
                assert [speech.lines[i].decode() for i in range(speech.count)]==data['lines']
    source=(ROOT/'desktop_version/src/Script.cpp').read_text()
    commands=('changeai','changetile','rescued','companion','delay','untilbars','untilfade')
    handlers=[block(source,source.index('if (words[0] == "'+name+'")')) for name in commands]
    shim='''#include <string>
#include <vector>
#include <cstdlib>
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
#define FADEMODE_IS_FADING(x) ((x)!=0)
struct Ent {int tile,state,para,dir;};
struct Obj {std::vector<Ent> entities;int getplayer(){return 0;}} obj;
struct Game {int crewstats[6],companion;} game;
struct Graphics {int showcutscenebars,cutscenebarspos,fademode;} graphics;
int ss_toi(const std::string&s){return std::atoi(s.c_str());}
int getcrewmanfromname(const std::string&){return 0;}
extern "C" void reference(const char *command,const char *arg1,const char *arg2,int ready,int *out){
std::string words[4]={command,arg1,arg2,"0"};int i=0,position=1,scriptdelay=0;
obj.entities={{150,0,0,1}};game={};graphics={1,ready?361:0,ready?0:1};
'''+ '\n'.join(handlers)+'''
out[0]=obj.entities[0].tile;out[1]=obj.entities[0].state==10;
out[2]=game.crewstats[2];out[3]=game.crewstats[3];out[4]=game.companion;
out[5]=scriptdelay?scriptdelay-1:0;out[6]=position;
}
'''
    (out/'reference.cpp').write_text(shim)
    subprocess.run(['c++',*flags,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
    reference=C.CDLL(str(out/'reference.so')).reference
    reference.argtypes=[C.c_char_p,C.c_char_p,C.c_char_p,C.c_int,C.POINTER(C.c_int)]
    cases=0
    tests=(('changeai','yellow','followplayer','FOLLOW',0),('changetile','yellow','6','TILE',6),
        ('rescued','yellow','','RESCUED',0),('companion','7','','COMPANION',7),
        ('delay','30','','DELAY',30),('untilbars','','','WAIT_BARS',0),('untilfade','','','WAIT_FADE',0))
    for command,a,b,op,value in tests:
        for ready in (0,1):
            for roof in (0,2):
                ops=(Op*1)(Op(NAMES.index(op),value,None));program=Program(ops,1);v=VM();s=Story();sig=Signals(ready,ready,roof,0)
                assert core.v6_rescue_start(C.byref(v),C.byref(program),skip,0)
                core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
                want=(C.c_int*7)();reference(command.encode(),a.encode(),b.encode(),ready,want)
                if op=='FOLLOW':assert v.following==want[1]
                if op=='TILE':assert v.tile==want[0] and v.tile_serial==1
                if op=='RESCUED':assert s.yellow_rescued==want[2] and want[3]==0
                if op=='COMPANION':assert s.companion==want[4]
                if op=='DELAY':assert v.delay==want[5]
                if op.startswith('WAIT'):assert v.pc==want[6] and bool(v.active)==(not ready)
                assert not v.error and not v.flips;cases+=1
    v=VM();s=Story(0,0,0,1,0);sig=Signals(0,0,2,0)
    assert core.v6_rescue_start(C.byref(v),normal,skip,0)
    for tick in range(10):core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
    assert v.bars and v.following and v.tile==6 and v.tile_serial==1 and not s.yellow_rescued and not v.flips
    sig.bars_ready=sig.fade_ready=1;shown=[];delay_ticks=0
    for tick in range(400):
        sig.advance=0;core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
        if v.waiting:
            shown.append(v.speech.contents.index);before=v.pc
            for hold in range(5):
                core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(sig));assert v.pc==before
            sig.advance=1;core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
        if v.delay:delay_ticks+=1
        if not v.active:break
    assert shown==list(range(11)) and delay_ticks==29,(shown,delay_ticks)
    assert s.yellow_rescued and s.companion==7 and s.rescue_triggered and not v.bars and not v.speech and v.control
    assert not v.error and not v.flips and v.following and v.tile==6 and v.tile_serial==1 and v.cues==11
    assert core.v6_rescue_start(C.byref(v),normal,skip,1)
    s=Story(0,0,0,1,0);core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(Signals()))
    assert not v.active and not v.error and s.yellow_rescued and s.companion==7 and v.following
    assert not v.speech and v.cues==1 and v.tile==6 and v.tile_serial==1 and not v.flips
    assert core.v6_rescue_start(C.byref(v),normal,skip,0)
    before=bytes(v),bytes(s)
    core.v6_station_rescue_tick(C.byref(v),None,C.byref(sig))
    core.v6_station_rescue_tick(C.byref(v),C.byref(s),None)
    core.v6_station_rescue_tick(None,C.byref(s),C.byref(sig))
    assert (bytes(v),bytes(s))==before
    # The four-line source speech fits the existing 48-row caption allocation.
    speech=normal.contents.ops[[i for i,op in enumerate(compiled['rescueyellow']['ops']) if op['speech']==6][0]].speech
    font=(C.c_uint8*1024)(*(c^(y*17) for c in range(128) for y in range(8)))
    guard=(C.c_uint8*3842)(*([165]*3842));assert core.v6_dialogue_draw(C.byref(guard,1),font,speech)
    expected=bytearray([255]*1920+[0]*1920)
    for x in range(1,39):expected[1920+4*40+x]=expected[1920+43*40+x]=255
    for y in range(5,43):expected[1920+y*40+1]=128;expected[1920+y*40+38]=1
    for line in range(4):
        text=speech.contents.lines[line];x=(40-len(text))//2
        for i,ch in enumerate(text):
            for y in range(8):expected[1920+(8+line*8+y)*40+x+i]=font[ch*8+y]
    assert bytes(guard)[1:-1]==expected and guard[0]==guard[-1]==165
    missing=Speech(0,0,4,(C.c_char_p*4)(b"a",b"b",b"c",None));before=bytes(guard)
    assert not core.v6_dialogue_draw(C.byref(guard,1),font,C.byref(missing)) and bytes(guard)==before
    for count in (0,5):
        bad=Speech();bad.count=count;before=bytes(guard)
        assert not core.v6_dialogue_draw(C.byref(guard,1),font,C.byref(bad)) and bytes(guard)==before
    for value in (-1,256):
        ops=(Op*1)(Op(NAMES.index('TILE'),value,None));program=Program(ops,1)
        assert core.v6_rescue_start(C.byref(v),C.byref(program),skip,0)
        core.v6_station_rescue_tick(C.byref(v),C.byref(s),C.byref(Signals()))
        assert v.error and not v.active and v.control and not v.tile_serial
    report=dict(source_handler_cases=cases,speech_order=shown,delay_wait_ticks=delay_ticks,
        normal_and_skip_complete=True,caption_bytes_compared=3840,scope='Yellow script core and caption; native yellow crew/persistence not admitted')
    (out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS yellow rescue:',report)
if __name__=='__main__':main()
