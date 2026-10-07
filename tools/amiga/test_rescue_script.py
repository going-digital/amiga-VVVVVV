#!/usr/bin/env python3
"""Bounded rescue runner state changes, waits, complete normal/skip flow."""
import ctypes as C
import json
import subprocess
from test_player import ROOT,block
from test_hallway_crew import Story
from hallway_scripts import compile_script,scripts,export
NAMES='IF_SKIP BARS FLOOR MOOD WAIT_BARS RESCUED CUE TEXT POSITION SHOW HIDE FADE WAIT_FADE DELAY COMPANION FOLLOW'.split()
class Speech(C.Structure):
    _fields_=[('index',C.c_uint),('speaker',C.c_uint),('count',C.c_uint),('lines',C.c_char_p*3)]
class Op(C.Structure):
    _fields_=[('op',C.c_uint),('value',C.c_int),('speech',C.POINTER(Speech))]
class Program(C.Structure):
    _fields_=[('ops',C.POINTER(Op)),('count',C.c_uint)]
class Signals(C.Structure):
    _fields_=[(name,C.c_int) for name in ('bars_ready','fade_ready','onroof','advance')]
class VM(C.Structure):
    _fields_=[(name,C.POINTER(Program)) for name in ('normal','skip','program')]+[(name,C.POINTER(Speech)) for name in ('draft','speech')]+[(name,C.c_uint) for name in ('pc','active','error','delay','waiting','bars','control','mood','following','skip_enabled','ui_serial','cues','flips')]+[(name,C.c_int) for name in ('fade','position','cue_speaker')]
def programs():
    keep=[];result=[]
    for name in ('rescuered','skipred'):
        data=compile_script(scripts()[name]['lines']);speeches=(Speech*len(data['speeches']))()
        for index,desc in enumerate(data['speeches']):
            text=[line.encode() for line in desc['lines']];keep+=text
            speeches[index]=Speech(index,desc['speaker']=='player',len(text),(C.c_char_p*3)(*(text+[None]*(3-len(text)))))
        ops=(Op*len(data['ops']))()
        for index,desc in enumerate(data['ops']):
            ptr=C.pointer(speeches[desc['speech']]) if desc['speech'] is not None else None
            ops[index]=Op(NAMES.index(desc['op']),desc['value'],ptr)
        result.append(Program(ops,len(ops)));keep.extend((ops,speeches))
    return result,keep

def main():
    out=ROOT/'build/amiga-rescue-script';out.mkdir(parents=True,exist_ok=True);export(out)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',*[str(ROOT/'amiga_version'/name) for name in ('rescue_script.c','dialogue.c','tower_copper.c')],'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));core.v6_rescue_start.argtypes=[C.POINTER(VM),C.POINTER(Program),C.POINTER(Program),C.c_int]
    core.v6_rescue_tick.argtypes=[C.POINTER(VM),C.POINTER(Story),C.POINTER(Signals)]
    # Compile the actual Script.cpp state handlers, independently of the new
    # compiler/runner. Presentation-only calls are checked by the pixel gate.
    source=(ROOT/'desktop_version/src/Script.cpp').read_text();handlers=[]
    commands=('cutscene','endcutscene','tofloor','changemood','untilbars','rescued','delay','companion','changeai','fadein','fadeout','untilfade')
    for command in commands:
        start=source.index('if (words[0] == "'+command+'")')
        handlers.append(block(source,start))
    wrapper='''#include <string>
#include <vector>
#include <cstdlib>
#define INBOUNDS_VEC(i,v) ((i)>=0 && (unsigned)(i)<(v).size())
#define FADE_START_FADEIN -1
#define FADE_START_FADEOUT 1
#define FADEMODE_IS_FADING(x) ((x)!=0)
struct Ent {int tile,state,para,dir,onroof;};
struct Obj {std::vector<Ent> entities;int getplayer(){return 0;}} obj;
struct Game {int crewstats[6],companion,press_action;} game;
struct Graphics {int showcutscenebars,cutscenebarspos,fademode;} graphics;
int ss_toi(const std::string &s){return std::atoi(s.c_str());}
int getcrewmanfromname(const std::string&){return 0;}
extern "C" void reference(const char *command,const char *arg1,const char *arg2,int ready,int roof,int *out) {
std::string words[4]={command,arg1,arg2,"0"};int i=0,position=1,scriptdelay=0;
obj.entities={{144,17,0,0,roof}};game={};graphics={1,ready?361:0,ready?0:1};
'''+ '\n'.join(handlers)+'''
out[0]=graphics.showcutscenebars;out[1]=obj.entities[0].tile!=0;
out[2]=game.crewstats[3];out[3]=game.companion;out[4]=obj.entities[0].state==10;
out[5]=graphics.fademode;out[6]=scriptdelay?scriptdelay-1:0;out[7]=position;out[8]=game.press_action;
}
'''
    (out/'reference.cpp').write_text(wrapper)
    subprocess.run(['c++',*flags,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
    reference=C.CDLL(str(out/'reference.so')).reference
    reference.argtypes=[C.c_char_p,C.c_char_p,C.c_char_p,C.c_int,C.c_int,C.POINTER(C.c_int)]
    cases=0;dummy_ops=(Op*1)(Op(NAMES.index('MOOD'),0,None));dummy=Program(dummy_ops,1)
    tests=[('cutscene','','','BARS',1),('endcutscene','','','BARS',0),('changemood','red','0','MOOD',0),('rescued','red','','RESCUED',0),('companion','9','','COMPANION',9),('changeai','red','followplayer','FOLLOW',0),('fadeout','','','FADE',1),('fadein','','','FADE',-1),('delay','30','','DELAY',30),('untilbars','','','WAIT_BARS',0),('untilfade','','','WAIT_FADE',0),('tofloor','','','FLOOR',0)]
    for command,arg1,arg2,op,value in tests:
        for ready in (0,1):
            for roof in (0,2):
                ops=(Op*1)(Op(NAMES.index(op),value,None));program=Program(ops,1);v=VM();s=Story();sig=Signals(ready,ready,roof,0)
                assert core.v6_rescue_start(C.byref(v),C.byref(program),C.byref(dummy),0)
                core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(sig));expected=(C.c_int*9)()
                reference(command.encode(),arg1.encode(),arg2.encode(),ready,roof,expected)
                if op=='BARS':assert v.bars==expected[0]
                if op=='MOOD':assert v.mood==expected[1]
                if op=='RESCUED':assert s.red_rescued==expected[2]
                if op=='COMPANION':assert s.companion==expected[3]
                if op=='FOLLOW':assert v.following==expected[4]
                if op=='FADE':assert v.fade==expected[5]
                if op=='DELAY':assert v.delay==expected[6]
                if op in ('WAIT_BARS','WAIT_FADE'):assert v.pc==expected[7] and bool(v.active)==(not ready)
                if op=='FLOOR':assert v.flips==expected[8]
                assert not v.error;cases+=1
    (normal,skip),keep=programs();v=VM();s=Story();sig=Signals(0,0,0,0)
    assert core.v6_rescue_start(C.byref(v),C.byref(normal),C.byref(skip),0)
    for tick in range(10):core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
    assert v.bars and not s.red_rescued and not v.mood and not v.speech
    sig.bars_ready=1;sig.fade_ready=1;shown=[];wait=0
    for tick in range(300):
        sig.advance=0
        core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
        if v.waiting:
            speech=v.speech.contents;shown.append(speech.index)
            before=v.pc
            for hold in range(5):core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(sig));assert v.pc==before
            sig.advance=1;core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(sig))
            # The next speech can be shown in the same tick. Record it on
            # the next loop before advancing again.
        if v.delay:wait+=1
        if not v.active:break
    assert shown==list(range(6)),shown
    assert s.red_rescued and s.companion==9 and v.following and not v.bars and not v.speech and v.control and not v.error
    assert wait==29,wait
    assert core.v6_rescue_start(C.byref(v),C.byref(normal),C.byref(skip),1)
    s=Story();core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(Signals()))
    assert not v.active and not v.error and s.red_rescued and s.companion==9 and v.following and not v.speech and v.cues==1
    # An unsupported opcode and a self-jumping skip program fail boundedly.
    bad_ops=(Op*1)(Op(999,0,None));bad=Program(bad_ops,1)
    assert core.v6_rescue_start(C.byref(v),C.byref(bad),C.byref(skip),0)
    core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(Signals()));assert v.error and not v.active and v.control
    cycle_ops=(Op*1)(Op(0,0,None));cycle=Program(cycle_ops,1)
    assert core.v6_rescue_start(C.byref(v),C.byref(cycle),C.byref(cycle),1)
    core.v6_rescue_tick(C.byref(v),C.byref(s),C.byref(Signals()));assert v.error and not v.active
    # Caption guards and Copper ring-wrap restoration across every offset pair.
    core.v6_tower_caption_copper.argtypes=[C.POINTER(C.c_uint16),C.c_uint32,C.c_uint32,C.c_uint,C.c_uint,C.c_uint32,C.c_uint,C.c_uint,C.c_uint]
    maximum=0
    for fo in range(256):
        for bo in range(256):
            buf=(C.c_uint16*82)(*([0xaaaa]*82))
            n=core.v6_tower_caption_copper(buf,0x10000,0x20000,fo,bo,0x30000,0xf44,0xf56,0x733)
            assert 0<n<=80 and buf[80]==buf[81]==0xaaaa
            maximum=max(maximum,n)
            pairs=list(zip(buf[:n:2],buf[1:n:2]));resume=pairs.index((0x100,0x3600))
            regs=dict(pairs[resume:])
            # Later ring wraps may overwrite the last register value. Check
            # the immediate resume writes, before any subsequent wait.
            regs={}
            for reg,value in pairs[resume:]:
                if reg&1:break
                regs[reg]=value
            assert (regs[0xe0]<<16|regs[0xe2])==0x10000+((fo+64)&255)*40
            assert (regs[0xe4]<<16|regs[0xe6])==0x20000+((bo+64)&255)*40
            assert regs[0x182]==0xf56 and regs[0x186]==0x733
    buf=(C.c_uint16*82)(*([0xaaaa]*82))
    assert not core.v6_tower_caption_copper(buf,0x10001,0x20000,0,0,0x30000,0xf44,0xf56,0x733)
    assert all(value==0xaaaa for value in buf)
    core.v6_dialogue_draw.argtypes=[C.c_void_p,C.c_void_p,C.POINTER(Speech)]
    guard=(C.c_ubyte*3842)(*([0xaa]*3842));font=(C.c_ubyte*1024)()
    invalid=Speech(0,0,1,(C.c_char_p*3)(b'x'*37,None,None))
    assert not core.v6_dialogue_draw(C.byref(guard,1),font,C.byref(invalid))
    assert all(value==0xaa for value in guard)
    valid=Speech(0,0,1,(C.c_char_p*3)(b'Captain!',None,None))
    assert core.v6_dialogue_draw(C.byref(guard,1),font,C.byref(valid))
    assert guard[0]==guard[3841]==0xaa
    report=dict(source_handler_cases=cases,copper_offset_pairs=65536,maximum_caption_words=maximum,speech_order=shown,delay_wait_ticks=wait,normal_and_skip_complete=True,scope='Compiled source rescue/skip scripts and actual Script.cpp state/wait handlers; captions verified separately')
    (out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
