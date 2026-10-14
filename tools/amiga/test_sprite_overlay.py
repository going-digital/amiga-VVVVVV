#!/usr/bin/env python3
"""Third-foreground-plane actor bands and sprite palette timeline parity."""
import ctypes as C,subprocess
from test_sprite_mux import Actor,Plan
from test_player import ROOT,BUILD
from test_menu_slide import events
def main():
 BUILD.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-shared','-fPIC',str(ROOT/'amiga_version/sprite_mux.c'),'-o',str(BUILD/'sprite_overlay.so')],check=True)
 class Overlay(C.Structure):_fields_=[('bitmap',C.c_uint32),('blank',C.c_uint32),('start',C.c_uint16),('stop',C.c_uint16),('colour',C.c_uint16)]
 m=C.CDLL(str(BUILD/'sprite_overlay.so'));w=C.POINTER(C.c_uint16);p=C.POINTER(Plan);a=C.POINTER(Actor);o=C.POINTER(Overlay)
 m.v6_sprite_mux_plan.argtypes=[p,a,C.c_uint]
 m.v6_sprite_mux_overlay_copper.argtypes=[w,w,C.c_uint,p,a,o]
 m.v6_sprite_mux_append_overlay.argtypes=[w,C.c_uint,p,a,o]
 rows=(C.c_uint32*32)(*[0xffff0000]*32);actors=(Actor*3)(Actor(rows,60,73,6,16,32,0x6ff),Actor(rows,80,134,6,16,32,0xff4),Actor(rows,194,204,0,16,20,0xff4));plan=Plan();assert m.v6_sprite_mux_plan(C.byref(plan),actors,3)
 base=(C.c_uint16*6)(0x2c01,0xfffe,0x100,0x3600,0xffff,0xfffe);cases=0
 for start in range(68,268):
  for h in range(1,min(32,268-start)+1):
   overlay=Overlay(0x20000,0x30000,start,start+h,0xff4);out=(C.c_uint16*512)();direct=(C.c_uint16*512)();direct[:6]=base[:]
   n=m.v6_sprite_mux_overlay_copper(out,base,6,C.byref(plan),actors,C.byref(overlay));assert n
   assert m.v6_sprite_mux_append_overlay(direct,6,C.byref(plan),actors,C.byref(overlay))==n and bytes(out)==bytes(direct)
   trace=events(list(out[:n]));assert [(line,val) for line,reg,val in trace if reg==0x100]==[(44,0x3600),(start-1,0x5600),(start+h-1,0x3600)]
   assert [(line,reg,val) for line,reg,val in trace if reg in (0xec,0xee,0xf0,0xf2)]==[(start-1,0xec,3),(start-1,0xee,0),(start-1,0xf0,2),(start-1,0xf2,0)]
   assert all((start-1,0x180+i*2,0xff4) in trace for i in range(4,8));cases+=1
 print('PASS',cases,'overlay bands, register epochs, palette/pointer order and direct/general compositor parity')

if __name__=='__main__':main()
