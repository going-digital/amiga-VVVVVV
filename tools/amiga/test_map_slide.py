#!/usr/bin/env python3
"""Stationary room/menu Copper split and sprite clipping boundaries."""
import ctypes as C
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def main():
 out=ROOT/'build/amiga-map-slide';out.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/map_slide.c'),'-o',str(out/'slide.so')],check=True)
 lib=C.CDLL(str(out/'slide.so'));fn=lib.v6_map_slide_copper
 fn.argtypes=[C.POINTER(C.c_uint16),C.c_uint32,C.c_uint32,C.c_uint,C.c_uint32,C.POINTER(C.c_uint16),C.c_uint32,C.c_uint32,C.c_uint]
 lib.v6_map_slide_clip.argtypes=[C.POINTER(C.c_uint16),C.c_uint]
 palette=(C.c_uint16*32)(*range(32));buf=(C.c_uint16*160)();count=0
 for fg in (0,0x123400,0xffb000):
  for bg in (0,0x456700,0xffd800):
   for bitmap in (0,0x789000,0xff4480):
    for offset in range(1,240):
     n=fn(buf,fg,bg,200,bitmap,palette,0x1000,0x2000,offset);assert 0<n<=160
     words=list(buf[:n]);regs={};waits=[];epoch=0
     for r,v in zip(words[::2],words[1::2]):
      if r==0xffff:break
      if r&1:
       if r==0xffdf:epoch=256;waits.append(255)
       else:waits.append(epoch+(r>>8))
      else:regs[r]=v
     assert waits==([44]+([107] if 107<51+offset else [])+([255] if 51+offset>255 else [])+[51+offset]),waits
     assert regs[0x100]==0x5200 and regs[0x104]==0x20
     for p in range(5):assert regs[0xe0+4*p]*65536+regs[0xe2+4*p]==bitmap+p*9600
     for i in range(32):assert regs[0x180+i*2]==palette[i]
     for i in range(8):assert regs[0x120+i*4]*65536+regs[0x122+i*4]==(0x1000 if i else 0x2000)
     # Initial gameplay pointers precede the background ring wrap and map boundary.
     assert words[6:18]==[0xe0,fg>>16,0xe2,fg&65535,0xe4,(bg+8000)>>16,0xe6,(bg+8000)&65535,0xe8,(fg+10240)>>16,0xea,(fg+10240)&65535]
     count+=1
 # Every independent background offset, including resets after line 255.
 for bo in range(256):
  for offset in range(1,240):
   n=fn(buf,0x10000,0x20000,bo,0x30000,palette,0x1000,0x2000,offset)
   assert n
   events=([307-bo] if bo>16 and 307-bo<51+offset else [])+[51+offset]
   expected=[44];epoch=False
   for line in events:
    if line>=255 and not epoch:
     expected.append(255);epoch=True
    if line!=255:expected.append(line)
   actual=[];epoch=0
   for r,v in zip(buf[:n:2],buf[1:n:2]):
    if r==0xffff:break
    if r&1:
     if r==0xffdf:epoch=256;actual.append(255)
     else:actual.append(epoch+(r>>8))
   assert actual==expected,(bo,offset,actual,expected)
   count+=1
 # Invalid schedules must not touch output.
 for args in [(0,0,0,0x1000,0x2000,0),(0,0,0,0x1000,0x2000,240),(1,0,0,0x1000,0x2000,1),(0xffb002,0,0,0,0,1),(0,0,0xff4482,0,0,1)]:
  before=bytes(buf);assert fn(buf,*args[:2],200,args[2],palette,*args[3:])==0 and bytes(buf)==before
 palette[31]=0x1000;before=bytes(buf);assert not fn(buf,0,0,200,0,palette,0,0,1) and bytes(buf)==before
 clips=0
 for offset in range(1,240):
  for y in range(0,240):
   start=52+y;stop=min(292,start+32)
   sprite=(C.c_uint16*68)(*([0xaaaa]*68))
   sprite[0]=((start&255)<<8)|0x90
   sprite[1]=((stop&255)<<8)|((start>>6)&4)|((stop>>7)&2)
   before=bytes(sprite);lib.v6_map_slide_clip(sprite,offset)
   if y>=offset:assert list(sprite[:4])==[0]*4
   elif stop<=52+offset:assert bytes(sprite)==before
   else:
    actual=(sprite[1]>>8)|((sprite[1]&2)<<7)
    assert actual==52+offset and ((sprite[0]>>8)|((sprite[1]&4)<<6))==start
    assert sprite[2+(offset-y)*2]==sprite[3+(offset-y)*2]==0
   clips+=1
 lib.v6_map_slide_channel.argtypes=[C.POINTER(C.c_uint16),C.c_uint]
 lib.v6_map_slide_cursor.argtypes=[C.POINTER(C.c_uint16),C.POINTER(C.c_uint32),C.c_uint,C.c_uint]
 for channel in range(8):
  sprite=(C.c_uint16*68)(*range(68));original=list(sprite)
  lib.v6_map_slide_channel(sprite,channel)
  assert list(sprite[:2])==original[:2] and list(sprite[66:])==original[66:]
  for i in range(32):
   assert sprite[2+i*2]==original[2+i*2]
   assert sprite[3+i*2]==(original[2+i*2] if channel&1 else 0)
 rows=(C.c_uint32*32)(*[((i*317)&0xfff0)<<16 for i in range(32)])
 cursors=0
 for x in (0,1,184,307,308):
  for y in range(256):
   sprite=(C.c_uint16*68)(*([0xaaaa]*68))
   height=lib.v6_map_slide_cursor(sprite,rows,x,y)
   assert height==(min(9,240-y) if y<240 else 0)
   if not height:assert not any(sprite)
   else:
    assert (sprite[0]>>8)|((sprite[1]&4)<<6)==52+y
    assert (sprite[1]>>8)|((sprite[1]&2)<<7)==52+y+height
    assert ((sprite[0]&255)<<1)|(sprite[1]&1)==128+x
    for i in range(height):assert sprite[2+i*2]==(rows[i]>>16)&0xfff0 and sprite[3+i*2]==0
    assert not any(sprite[2+height*2:])
   cursors+=1
 print(f'PASS map slide: {count} Copper schedules, {clips} sprite clips, {cursors} full-viewport cursor positions, channel colour remapping, invalid-input immutability (UBSan)')
if __name__=='__main__':main()
