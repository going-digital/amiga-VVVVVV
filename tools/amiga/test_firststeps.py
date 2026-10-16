#!/usr/bin/env python3
"""Original firststeps trigger boundaries, one-shot flow and source cue mapping."""
import ctypes as C
import subprocess
from test_player import ROOT,Player
from test_rescue_script import VM,Program,Op,Speech,Signals,NAMES
from test_station_trigger import Story
from firststeps_script import script

def main():
 out=ROOT/'build/amiga-firststeps';out.mkdir(exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',*[str(ROOT/'amiga_version'/p) for p in ('station_trigger.c','rescue_script.c')],'-o',str(out/'core.so')],check=True)
 lib=C.CDLL(str(out/'core.so'))
 class Trigger(C.Structure):_fields_=[('active',C.c_int),('pending',C.c_int),('requests',C.c_uint)]
 lib.v6_firststeps_enter.argtypes=[C.POINTER(Trigger),C.c_int,C.c_int,C.c_int]
 lib.v6_firststeps_contact.argtypes=[C.POINTER(Trigger),C.POINTER(Player)]
 lib.v6_firststeps_dispatch.argtypes=[C.POINTER(Trigger),C.c_uint]
 cases=0
 for seen in (0,1):
  for x in (-100,54,55,148,385,386,1000):
   for y in (-100,-23,-22,161,237,238,1000):
    for enabled in (0,1):
     t=Trigger();p=Player();p.x=x;p.y=y;lib.v6_firststeps_enter(C.byref(t),115,105,not enabled)
     assert not lib.v6_firststeps_dispatch(C.byref(t),seen)
     for i in range(3):lib.v6_firststeps_contact(C.byref(t),C.byref(p))
     expected=enabled and 54<x<386 and -23<y<238
     assert bool(t.pending)==expected
     assert lib.v6_firststeps_dispatch(C.byref(t),seen)==int(expected and not seen)
     assert not lib.v6_firststeps_dispatch(C.byref(t),seen)
     assert t.requests==int(expected and not seen);cases+=1
 data=script();speeches=(Speech*2)();keep=[]
 for i,lines in enumerate(data['speeches']):
  texts=[s.encode() for s in lines];keep+=texts;speeches[i]=Speech(i,1,2,(C.c_char_p*4)(*texts,None,None))
 ops=(Op*len(data['ops']))()
 for i,(op,value,speech) in enumerate(data['ops']):ops[i]=Op(NAMES.index(op),value,C.pointer(speeches[speech]) if speech is not None else None)
 program=Program(ops,len(ops));vm=VM();story=Story(0,0,7,1,1)
 lib.v6_rescue_start.argtypes=[C.POINTER(VM),C.POINTER(Program),C.POINTER(Program),C.c_int]
 lib.v6_station_rescue_tick.argtypes=[C.POINTER(VM),C.POINTER(Story),C.POINTER(Signals)]
 assert lib.v6_rescue_start(C.byref(vm),C.byref(program),C.byref(program),0);before=bytes(story)
 def tick(bars=1,advance=0):lib.v6_station_rescue_tick(C.byref(vm),C.byref(story),C.byref(Signals(bars,1,0,advance)))
 tick(0);assert vm.bars and not vm.speech
 tick(0);assert not vm.speech
 tick();assert vm.waiting and not vm.control and vm.speech.contents.index==0 and vm.cues==1 and vm.cue_speaker==1
 for i in range(20):tick();assert vm.speech.contents.index==0
 tick(advance=1);assert vm.waiting and vm.speech.contents.index==1 and vm.cues==2 and vm.cue_speaker==2
 for i in range(20):tick();assert vm.speech.contents.index==1
 tick(0,1);assert not vm.speech and not vm.bars and vm.active
 tick();assert not vm.active and not vm.error and vm.control and bytes(story)==before
 from convert_teleporter_audio import source_files
 assert source_files(('CRY',))==('hurt',)
 print('PASS firststeps:',cases,'trigger/flag vectors; exact two-page wait/control/cue sequence; source story unchanged; CRY maps to hurt.wav')
if __name__=='__main__':main()
