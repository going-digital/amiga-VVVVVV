#!/usr/bin/env python3
"""Original Conundrum trigger rectangles, flag guards and nonblocking timed hint."""
import ctypes as C
import subprocess
from test_player import ROOT,Player
from tower_gameplay_data import north_route_room

class Trigger(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('active','pending','contacts','removed','visible','timer','level','mode','hints')]

def main():
 room=north_route_room('conundrum')
 assert room['blocks']==[(1,10,0,60,240,22),(1,280,0,320,240,21)] and not room['entities']
 source=(ROOT/'desktop_version/src/Game.cpp').read_text()
 for state,flag in ((21,2),(22,3)):
  body=source.split(f'case {state}:',1)[1].split('break;',1)[0]
  assert f'!obj.flags[{flag}]' in body and f'obj.flags[{flag}] = true;' in body and f'obj.removetrigger({state})' in body
 assert 'graphics.textboxtimer(60);' in source.split('case 22:',1)[1].split('break;',1)[0]
 out=ROOT/'build/amiga-conundrum-host';out.mkdir(exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/station_trigger.c'),'-o',str(out/'core.so')],check=True)
 lib=C.CDLL(str(out/'core.so'));ptr=C.POINTER(Trigger)
 lib.v6_conundrum_enter.argtypes=[ptr,C.c_int,C.c_int,C.c_int]
 lib.v6_conundrum_contact.argtypes=[ptr,C.POINTER(Player)]
 lib.v6_conundrum_dispatch.argtypes=[ptr,C.POINTER(C.c_uint16)]
 lib.v6_conundrum_tick.argtypes=[ptr]
 cases=0
 for initial in range(8):
  for x in (-100,-8,-7,0,63,64,262,263,290,593,594,1000):
   for y in (-100,-23,-22,97,237,238,1000):
    for enabled in (0,1):
     t=Trigger();flags=C.c_uint16(initial);p=Player();p.x=x;p.y=y
     before=bytes(p);lib.v6_conundrum_enter(C.byref(t),114,105,not enabled)
     assert not lib.v6_conundrum_dispatch(C.byref(t),C.byref(flags))
     for i in range(3):lib.v6_conundrum_contact(C.byref(t),C.byref(p))
     hit=(1 if 262<x<594 else 2 if -8<x<64 else 0) if enabled and -23<y<238 else 0
     assert t.pending==hit and t.contacts==bool(hit)
     fresh=lib.v6_conundrum_dispatch(C.byref(t),C.byref(flags))
     expected=hit if hit and not(initial&(2 if hit==1 else 4)) else 0
     assert fresh==expected and flags.value==initial|(2 if hit==1 else 4 if hit==2 else 0)
     assert t.visible==bool(expected==2) and t.hints==bool(expected==2) and t.removed==bool(hit)
     for i in range(3):lib.v6_conundrum_contact(C.byref(t),C.byref(p))
     assert not lib.v6_conundrum_dispatch(C.byref(t),C.byref(flags)) and bytes(p)==before
     if t.visible:
      levels=[]
      for i in range(65):lib.v6_conundrum_tick(C.byref(t));levels.append((t.visible,t.timer,t.level,t.mode))
      assert levels[3]==(1,56,9,0) and levels[4]==(1,55,10,1)
      assert levels[59]==(1,0,10,2) and levels[64]==(0,0,5,2)
     cases+=1
 # Right-side removal suppresses an existing textbox only on its first contact.
 for seen in (0,2):
  t=Trigger(3,1,0,0,1,30,10,1,1);flags=C.c_uint16(seen)
  lib.v6_conundrum_dispatch(C.byref(t),C.byref(flags));assert t.visible and t.mode==(1 if seen else 2)
  if not seen:
   for i in range(5):lib.v6_conundrum_tick(C.byref(t))
   assert not t.visible and t.level==5
 for x,y in ((115,105),(114,104),(113,105)):
  t=Trigger();lib.v6_conundrum_enter(C.byref(t),x,y,0);assert not t.active
 print('PASS Conundrum:',cases,'source trigger/flag/boundary cases; source timed fade; repeated and wrong-room contacts; player unchanged')
if __name__=='__main__':main()
