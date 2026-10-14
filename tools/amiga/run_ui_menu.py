#!/usr/bin/env python3
"""Compare native complete-menu Chip bitmaps with source-certified page drawing."""
import argparse,ctypes as C,os,struct,subprocess
from pathlib import Path
from test_ui_menu import State,Clock,Summary,Icon,prepare,arrays
from run_interactive_save import config
from run_map_input import capture
from run_tower_probe import EMU
from save_disk import read_record

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();build=a.build.resolve()
 lib,assets=prepare();Fill=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_uint)
 lib.v6_ui_draw.argtypes=[C.POINTER(C.c_uint8),C.POINTER(State),C.POINTER(C.c_uint8),C.POINTER(C.c_uint8),C.POINTER(C.c_uint32),Fill,C.c_void_p]
 callback=Fill(('ui_cpu_fill',lib));font=(C.c_uint8*1024)(*arrays(assets/'dialogue_font.h','dialogue_font'));border=(C.c_uint8*64)(*arrays(assets/'pickup_assets.h','pickup_border'));icons=(C.c_uint32*64)(*arrays(assets/'ui_assets.h','ui_icons'))
 disk=build/'map-display-save.adf';record=read_record(disk);assert len(record)==144 and record[5]==6
 last=Summary(Clock(*struct.unpack_from('>4H',record,122)),*struct.unpack_from('>2h',record,130),*struct.unpack_from('>2H',record,134),record[121])
 bitmap=(C.c_uint8*38400)();cfg=config(build,disk)
 for page in (1,2,3):
  capture_time=80 if page==3 else 74
  dump=build/f'ui-page-{page}-chip.bin';inputs=['--key-after','62','0x44','1000']
  if page==3:inputs+=['--key-after','65','0x4f','500','--key-after','66','0x40','500']
  else:
   inputs+=['--key-after','65','0x4e','400']
   if page==2:inputs+=['--key-after','66','0x4e','400']
  env=dict(os.environ,COPPERLINE_DBG_AFTER=str(capture_time),COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
  with (build/f'ui-page-{page}.log').open('w') as log:
   subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,'--screenshot-after',str(capture_time+.01),str(build/f'ui-page-{page}.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  if page==3:
   record=read_record(disk);last=Summary(Clock(*struct.unpack_from('>4H',record,122)),*struct.unpack_from('>2h',record,130),*struct.unpack_from('>2H',record,134),record[121])
  chip=dump.read_bytes();matches=[]
  # Stats advances its source clock while the menu is open. Search the bounded
  # capture interval; all other bytes must still match the exact source page.
  for seconds in (range(60) if page==2 else (0,)):
   state=State(page,int(page==3),0,record[120],0,struct.unpack_from('>I',record,116)[0],last.trinkets,Clock(0,0,seconds,0),last,b'V Stitch',b'Space Station',b'Space Station',b'Space')
   assert lib.v6_ui_draw(bitmap,C.byref(state),font,border,icons,callback,C.cast(bitmap,C.c_void_p))
   at=chip.find(bytes(bitmap))
   if at>=0:matches.append((at,seconds))
  assert 1<=len(matches)<=2,(page,matches)
  # Validate DMA portraits and their exact source positions/monochrome colours
  # independently of the bitplane comparison.
  lib.v6_ui_icons.argtypes=[C.POINTER(Icon),C.POINTER(State)];shapes=(Icon*8)()
  lib.v6_ui_icons(shapes,C.byref(state));portraits=arrays(assets/'ui_assets.h','ui_portrait')
  prefix=bytes.fromhex('2c01fffe01004200');seen=0;search=0
  while True:
   pos=chip.find(prefix,search)
   if pos<0:break
   search=pos+1;start=pos-64
   if start<0:continue
   words=struct.unpack_from('>384H',chip,start);regs={}
   for r,v in zip(words[::2],words[1::2]):
    if r==65535:break
    if not(r&1):regs[r]=v
   base=(regs.get(0xe0,0)<<16)|regs.get(0xe2,0)
   if base not in {at for at,seconds in matches}:continue
   frames=set()
   for i in range(8):
    address=(regs[0x120+i*4]<<16)|regs[0x122+i*4]
    if page==2 or i>=6:
     assert chip[address:address+4]==bytes(4);continue
    shape=shapes[i];x=128+shape.x+6;first=52+shape.y;stop=first+32
    control=((first&255)<<8)|(x>>1),((stop&255)<<8)|((first&256)>>6)|((stop&256)>>7)|(x&1)
    dma=struct.unpack_from('>68H',chip,address);assert dma[:2]==control,(page,i,dma[:2],control)
    allowed=(0,1) if state.crew_mask&(1<<i) else (2,);found=[]
    for frame in allowed:
     expected=[]
     for row in portraits[frame*32:(frame+1)*32]:
      bits=(row>>10)&65535;expected.extend((bits,bits if i&1 else 0))
     if dma[2:66]==tuple(expected):found.append(frame)
    assert len(found)==1 and dma[66:]==(0,0),(page,i,found)
    if found[0]!=2:frames.add(found[0])
    assert regs[0x180+2*(17+(i//2)*4+(i&1)*2)]==shape.colour
   assert len(frames)<=1;seen+=1
  assert seen==2,(page,seen)
  timed=capture(build,disk,f'ui-page-{page}-timing',inputs,end=capture_time);d=timed['display']
  assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
  print('PASS native UI bitmap',page,'38400 source-certified bytes',matches,'work lines',d['max_work_lines'],flush=True)
if __name__=='__main__':main()
