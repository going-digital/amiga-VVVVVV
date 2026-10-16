#!/usr/bin/env python3
"""Frozen gameplay camera/overlay prefix composed with every partial menu offset."""
import ctypes as C,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def events(words):
 epoch=0;line=0;result=[]
 for r,v in zip(words[::2],words[1::2]):
  if r==65535:break
  if r&1:
   if r==0xffdf:epoch=256;line=255
   else:line=epoch+(r>>8)
  else:result.append((line,r,v))
 return result

def main():
 out=ROOT/'build/amiga-menu-slide';out.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/menu_slide.c'),str(ROOT/'amiga_version/tower_copper.c'),'-o',str(out/'slide.so')],check=True)
 lib=C.CDLL(str(out/'slide.so'));fn=lib.v6_menu_slide_copper;short=C.POINTER(C.c_uint16)
 fn.argtypes=[short,short,C.c_uint,C.c_uint32,C.c_uint,short,C.POINTER(C.c_uint32),C.c_uint]
 owned=lib.v6_menu_slide_owned_copper;owned.argtypes=fn.argtypes;fast=(C.c_uint16*512)()
 lib.v6_tower_dual_copper.argtypes=[short,C.c_uint32,C.c_uint32,C.c_uint,C.c_uint]
 gamebuf=(C.c_uint16*512)();buf=(C.c_uint16*512)();pal=(C.c_uint16*32)(*range(32));sprites=(C.c_uint32*8)(*[0x60000+i*1024 for i in range(8)])
 count=0
 for fo in (0,1,16,17,52,166,8,95,254,255):
  for bo in (0,1,16,17,64,200,255):
   segment=(C.c_uint16*34)();n=lib.v6_tower_dual_copper(segment,0x10000,0x20000,fo,bo)
   game=[0x100,0x3600,0x102,0,0x104,0x24]+list(segment[:n])
   for i,v in enumerate(game):gamebuf[i]=v
   for offset in range(1,240):
    for planes in (4,5):
     n=fn(buf,gamebuf,len(game),0x30000,planes,pal,sprites,offset);assert 0<n<=384
     assert owned(fast,gamebuf,len(game),0x30000,planes,pal,sprites,offset)==n and list(fast[:n])==list(buf[:n])
     trace=events(list(buf[:n]));regs={};at=0;pointers={};boundary=51+offset
     assert all(r<0x120 or r>0x13e or t==0 for t,r,v in trace)
     for y in range(240):
      physical=52+y
      while at<len(trace) and trace[at][0]<physical:
       _,r,v=trace[at];regs[r]=v
       if r in range(0xe0,0xf4,4):pointers[(r-0xe0)//4]=(v<<16)|(pointers.get((r-0xe0)//4,0)&65535)
       elif r in range(0xe2,0xf6,4):pointers[(r-0xe2)//4]=(pointers.get((r-0xe2)//4,0)&0xffff0000)|v
       at+=1
      if y<offset:
       assert regs[0x100]==0x3600
       expected=[0x10000+((fo+y)%256)*40,0x20000+((bo+y)%256)*40,0x12800+((fo+y)%256)*40]
      else:
       assert regs[0x100]==(planes<<12)|0x200 and regs[0x104]==0x20
       expected=[0x30000+p*9600+(y-offset)*40 for p in range(planes)]
      for p,address in enumerate(expected):assert pointers[p]==address,(fo,bo,offset,planes,y,p,pointers,expected)
      for p in pointers:pointers[p]+=40
     for i in range(8):assert (regs[0x120+i*4]<<16)|regs[0x122+i*4]==sprites[i]
     assert all(regs[0x180+i*2]==pal[i] for i in range(32));count+=1
 # Invalid inputs preserve the entire inactive destination.
 for words,planes,offset,bitmap in [(1,4,1,0x30000),(384,3,1,0x30000),(len(game),4,0,0x30000),(len(game),5,240,0x30000),(len(game),4,10,1)]:
  for i in range(512):buf[i]=0xa55a
  assert fn(buf,gamebuf,words,bitmap,planes,pal,sprites,offset)==0 and all(v==0xa55a for v in buf)
 lib.v6_menu_slide_rearm.argtypes=[short,C.c_uint,C.POINTER(C.c_uint32),C.POINTER(C.c_uint16*2),C.c_uint]
 lib.v6_menu_slide_owned_rearm.argtypes=lib.v6_menu_slide_rearm.argtypes
 control=((C.c_uint16*2)*8)();rearmed=0
 for offset in range(1,240):
  n=fn(buf,gamebuf,len(game),0x30000,4,pal,sprites,offset);assert n
  for i in range(8):
   start=84+offset;stop=min(292,start+32)
   if start>=292:control[i][0]=control[i][1]=0
   else:
    control[i][0]=((start&255)<<8)|100;control[i][1]=((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)
  fast[:n]=buf[:n]
  end=lib.v6_menu_slide_rearm(buf,n,sprites,control,offset);assert end and end<=512
  assert lib.v6_menu_slide_owned_rearm(fast,n,sprites,control,offset)==end and list(fast[:end])==list(buf[:end])
  trace=events(list(buf[:end]));late=[(t,r,v) for t,r,v in trace if t>=52+offset]
  assert len(late)==32 and all(t==52+offset for t,r,v in late)
  assert all((0x140+i*8,control[i][0]) in [(r,v) for t,r,v in late] for i in range(8));rearmed+=1
 print('PASS sprite rearm:',rearmed,'boundaries, including PAL epoch crossing')
 print('PASS general menu slide:' ,count,'camera/plane/offset schedules and all 240 fetched rows; invalid output preserved')
if __name__=='__main__':main()
