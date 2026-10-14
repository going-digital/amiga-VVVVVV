#!/usr/bin/env python3
"""Shared portal pixels plus translated heads equal both resident source draws."""
import ctypes as C,subprocess
from pathlib import Path
from test_map_draw import arrays
ROOT=Path(__file__).resolve().parents[2]
def main():
 out=ROOT/'build/amiga-menu';libpath=out/'portal-cache.so'
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/teleporter_draw.c'),str(ROOT/'amiga_version/screen_shake_dma.c'),'-o',str(libpath)],check=True)
 lib=C.CDLL(str(libpath));word=C.c_uint16;ptr=C.POINTER(word)
 lib.v6_teleporter_draw.argtypes=[ptr,ptr,ptr,C.c_int,C.c_int];lib.v6_screen_shake_heads.argtypes=[ptr,ptr,C.c_uint,C.c_int,C.c_int]
 source=arrays(ROOT/'build/amiga-feasibility/teleporter_assets.h','teleporter_masks');masks=(word*len(source))(*source);base=C.cast(masks,ptr)
 prepared=(word*1176)();actual=(word*1176)();gold=(word*1176)();count=0
 for frame in range(1,10):
  mask=C.cast(C.byref(masks,frame*1152),ptr);assert lib.v6_teleporter_draw(prepared,base,mask,112,48)
  for x,y in ((112,48),(36,68)):
   for dx in range(-4,5):
    for dy in range(-4,5):
     C.memmove(actual,prepared,C.sizeof(actual));lib.v6_screen_shake_heads(actual,prepared,196,x-112+dx,y-48+dy)
     assert lib.v6_teleporter_draw(gold,base,mask,x+dx,y+dy)
     assert bytes(actual)==bytes(gold),(frame,x,y,dx,dy);count+=1
 print('PASS shared portal cache:',count,'full DMA comparisons; 23520 BSS bytes saved')
if __name__=='__main__':main()
