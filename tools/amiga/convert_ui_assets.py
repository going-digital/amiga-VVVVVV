#!/usr/bin/env python3
"""Original menu sprite masks, room areas and resident names; private header."""
import argparse,re,subprocess,ctypes as C
from test_map_draw import arrays
from test_save_summary import Clock,Summary
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def build(out):
 h,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'tower_sprites.png')]).split(b'\n',1);w,ht=map(int,h.split());masks=[]
 tiles=(0,1,12,50,22)
 for tile in tiles:
  ox=tile%(w//32)*32;oy=tile//(w//32)*32
  masks.append([sum((rgba[((oy+y)*w+ox+x)*4+3]>127 and max(rgba[((oy+y)*w+ox+x)*4:((oy+y)*w+ox+x)*4+3])>0)<<(31-x) for x in range(32)) for y in range(32)])
 # Portrait source columns 6..21 are sufficient, clock uses its full 17 columns.
 assert all(not(v&~0x03fffc00) for frame in masks[:3] for v in frame)
 source=(ROOT/'desktop_version/src/Map.cpp').read_text();body=re.search(r'const int mapclass::areamap\[\] = \{(.*?)\};',source,re.S)[1];areas=list(map(int,re.findall(r'\d+',body)));assert len(areas)==400
 text='/* Private original menu sprite masks and source world-area map. */\nstatic const uint32_t ui_portrait[3][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in frame)+'}' for frame in masks[:3])+'};\n'
 text+='static const uint32_t ui_icons[2][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in frame)+'}' for frame in masks[3:])+'};\n'
 text+='static const uint8_t ui_world_areas[400]={'+','.join(map(str,areas))+'};\n'
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/ui_menu.c'),str(ROOT/'amiga_version/save_summary.c'),'-o',str(out/'.ui_packer.so')],check=True)
 lib=C.CDLL(str(out/'.ui_packer.so'))
 class State(C.Structure):
  _fields_=[(n,C.c_uint) for n in ('page','saved','failed','crew_mask','crew_frame')]+[('deaths',C.c_uint32),('trinkets',C.c_uint),('clock',Clock),('last',Summary)]+[(n,C.c_char_p) for n in ('roomname','area','last_area','action')]
 Fill=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_uint)
 bitmap=(C.c_uint8*38400)()
 def fill(_,x,y,w,h,c):
  for yy in range(max(0,y),min(240,y+h)):
   for xx in range(max(0,x),min(320,x+w)):
    for p in range(4):
     at=p*9600+yy*40+xx//8;bit=1<<(7-xx%8)
     bitmap[at]=(bitmap[at]|bit) if c&(1<<p) else bitmap[at]&~bit
  return 1
 callback=Fill(fill);font=(C.c_uint8*1024)(*arrays(out/'dialogue_font.h','dialogue_font'));border=(C.c_uint8*64)(*arrays(out/'pickup_assets.h','pickup_border'));icons=(C.c_uint32*64)(*[v for f in masks[3:] for v in f])
 state=State(3,1,0,1,0,0,0,Clock(),Summary(Clock(),112,107,0,1,1),b'',b'',b'',b'Space')
 lib.v6_ui_draw.argtypes=[C.POINTER(C.c_uint8),C.POINTER(State),C.POINTER(C.c_uint8),C.POINTER(C.c_uint8),C.POINTER(C.c_uint32),Fill,C.c_void_p]
 assert lib.v6_ui_draw(bitmap,C.byref(state),font,border,icons,callback,None)
 for name,top,height in [('footer',212,24),('receipt',65,90)]:
  values=[]
  for y in range(top,top+height):
   for x in range(0,320,8):
    values.append(sum((sum(((bitmap[p*9600+y*40+(x+i)//8]>>(7-(x+i)%8))&1)<<p for p in range(4))==3)<<(7-i) for i in range(8)))
  text+='static const uint8_t ui_'+name+'_mask['+str(len(values))+']={'+','.join(map(str,values))+'};\n'
 (out/'ui_assets.h').write_text(text);print('UI assets: original five sprite masks and all 400 room areas')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
