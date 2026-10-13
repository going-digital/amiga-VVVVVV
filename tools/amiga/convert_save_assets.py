#!/usr/bin/env python3
"""Private source Save prompt/failure bitmaps, three planes and lossless RLE."""
import argparse,ctypes as C,json,subprocess
from pathlib import Path
from test_map_draw import arrays
ROOT=Path(__file__).resolve().parents[2]
def build(out):
 out.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/map_draw.c'),str(ROOT/'amiga_version/save_page.c'),'-o',str(out/'.save_packer.so')],check=True)
 lib=C.CDLL(str(out/'.save_packer.so'))
 class Page(C.Structure):_fields_=[(n,C.c_uint) for n in ('state','autosave_note','last_summary')]
 bp=C.POINTER(C.c_uint8)
 lib.v6_save_draw_row.argtypes=[bp,C.c_uint,C.POINTER(Page),bp,bp,bp,C.c_char_p,C.c_char_p]
 font=(C.c_uint8*1024)(*arrays(out/'dialogue_font.h','dialogue_font'));border=(C.c_uint8*64)(*arrays(out/'pickup_assets.h','pickup_border'))
 mp=arrays(out/'map_assets.h','map_palette');mc=arrays(out/'map_assets.h','map_ui_colours');palette=[mp[i] for i in mc]+[0xfff,0x99b]+[0]*24
 text='/* Private generated source Save assets. */\nstatic const uint16_t save_palette[32]={'+','.join(hex(v) for v in palette)+'};\n';sizes={}
 for name,page in [('prompt',Page(0,1,0)),('failure',Page(6,0,0))]:
  bitmap=bytearray(28800);row=(C.c_uint8*200)();semantics=(C.c_uint8*8)(*range(8))
  for y in range(240):
   assert lib.v6_save_draw_row(row,y,C.byref(page),font,border,semantics,b'V Stitch',b'Space')
   assert not any(row[120:])
   for p in range(3):bitmap[p*9600+y*40:p*9600+(y+1)*40]=row[p*40:(p+1)*40]
  runs=[];i=0
  while i<len(bitmap):
   n=1
   while n<255 and i+n<len(bitmap) and bitmap[i+n]==bitmap[i]:n+=1
   runs.extend((n,bitmap[i]));i+=n
  (out/('save-'+name+'.bin')).write_bytes(bitmap)
  text+='static const uint8_t save_'+name+'_rle['+str(len(runs))+']={'+','.join(map(str,runs))+'};\n';sizes[name]=len(runs)
 (out/'save_assets.h').write_text(text);(out/'save-assets.json').write_text(json.dumps(dict(palette=palette,packed=sizes,bitmap_bytes=28800))+'\n')
 print('Save assets:',sizes,'two 28800-byte three-plane bitmaps')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);build(p.parse_args().out)
