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
 text+='static const uint16_t ui_portrait_bits[3][32]={'+','.join('{'+','.join(hex((v>>10)&65535) for v in frame)+'}' for frame in masks[:3])+'};\n'
 portrait_data=[]
 for frame in masks[:3]:
  parity=[]
  for odd in (False,True):
   words=[]
   for row in frame:
    bits=(row>>10)&65535;words.extend((bits,bits if odd else 0))
   parity.append('{'+','.join(hex(v) for v in words)+'}')
  portrait_data.append('{'+','.join(parity)+'}')
 text+='static const uint16_t ui_portrait_data[3][2][64]={'+','.join(portrait_data)+'};\n'
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
 note="(Note: The game is autosaved at every";alpha=[0]*320;left=160-len(note)*4
 for i,c in enumerate(note):
  for y in range(8):
   for x in range(8):
    if font[ord(c)*8+y]&(128>>x):
     xx=left+i*8+x;alpha[y*40+xx//8]|=128>>(xx%8)
 text+='static const uint8_t ui_note_mask[320]={'+','.join(map(str,alpha))+'};\n'
 tab_masks=[]
 for column,label in enumerate(('MAP','CREW','STATS','SAVE')):
  for selected in (False,True):
   label_text='['+label+']' if selected else label;alpha=[0]*320;left=40+column*80-len(label_text)*4
   for i,c in enumerate(label_text):
    for y in range(8):
     for x in range(8):
      if font[ord(c)*8+y]&(128>>x):
       xx=left+i*8+x;alpha[y*40+xx//8]|=128>>(xx%8)
   tab_masks.extend(alpha)
 text+='static const uint8_t ui_tab_masks[2560]={'+','.join(map(str,tab_masks))+'};\n'
 prompt="[Press Space to save your game]";alpha=[0]*320;left=160-len(prompt)*4
 for i,c in enumerate(prompt):
  for y in range(8):
   for x in range(8):
    if font[ord(c)*8+y]&(128>>x):
     xx=left+i*8+x;alpha[y*40+xx//8]|=128>>(xx%8)
 text+='static const uint8_t ui_prompt_mask[320]={'+','.join(map(str,alpha))+'};\n'
 icon_masks=[]
 for shape,left in zip(masks[3:],(34,270)):
  alpha=[0]*1280
  for y,row in enumerate(shape):
   for x in range(32):
    if row&(1<<(31-x)):
     xx=left+x;alpha[y*40+xx//8]|=128>>(xx%8)
  first=(left//16)*2;height=17 if left==34 else 16
  icon_masks.extend(alpha[y*40+first+byte] for y in range(height) for byte in range(4))
 text+='static const uint8_t ui_icon_masks[132]={'+','.join(map(str,icon_masks))+'};\n'
 crew_texts=[('Viridian',44),('Violet',44),('Vitellary',44),('Vermilion',204),('Verdigris',204),('Victoria',204),("(that's you!)",44),('Rescued!',44),('Rescued!',204),('Missing...',44),('Missing...',204)]
 text+='static const char *const ui_crew_texts[11]={'+','.join('"'+s+'"' for s,x in crew_texts)+'};\n'
 text+='static const uint16_t ui_crew_text_x[11]={'+','.join(str(x) for s,x in crew_texts)+'};\n'
 crew_masks=[]
 for label,left in crew_texts:
  alpha=[0]*320
  for i,c in enumerate(label):
   for y in range(8):
    for x in range(8):
     if font[ord(c)*8+y]&(128>>x):
      xx=left+i*8+x;alpha[y*40+xx//8]|=128>>(xx%8)
  crew_masks.extend(alpha)
 text+='static const uint8_t ui_crew_text_masks[3520]={'+','.join(map(str,crew_masks))+'};\n'
 static_texts=['[Trinkets found]','[Number of Deaths]','[Time Taken]','The Tower',"I'm Sorry...",'Seeing Red','Building Apport','Energize','Frown Upside Down','Shenanigan','Prize for the Reckless','V Stitch','A Deception','Down Under','Stop and Reflect','The Yes Men','Gantry and Dolly']
 text+='static const char *const ui_static_texts['+str(len(static_texts))+']={'+','.join('"'+s+'"' for s in static_texts)+'};\n'
 static_masks=[]
 for label in static_texts:
  alpha=[0]*320;left=160-len(label)*4
  for i,c in enumerate(label):
   for y in range(8):
    for x in range(8):
     if font[ord(c)*8+y]&(128>>x):
      xx=left+i*8+x;alpha[y*40+xx//8]|=128>>(xx%8)
  static_masks.extend(alpha)
 text+='static const uint8_t ui_static_text_masks['+str(len(static_masks))+']={'+','.join(map(str,static_masks))+'};\n'
 (out/'ui_assets.h').write_text(text);print('UI assets: original five sprite masks and all 400 room areas')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
