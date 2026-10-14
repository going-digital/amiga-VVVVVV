#!/usr/bin/env python3
"""Private source Save bitmaps, unpacking and three-plane DMA schedules."""
import ctypes as C,subprocess
from pathlib import Path
from convert_save_assets import build
from test_map_draw import arrays
ROOT=Path(__file__).resolve().parents[2]
def main():
 assets=ROOT/'build/amiga-feasibility';build(assets)
 out=ROOT/'build/amiga-save-dma';out.mkdir(parents=True,exist_ok=True)
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(ROOT/'amiga_version/map_draw.c'),str(ROOT/'amiga_version/save_page.c'),'-o',str(out/'dma.so')],check=True)
 lib=C.CDLL(str(out/'dma.so'));reference=C.CDLL(str(ROOT/'build/amiga-save-draw/draw.so'))
 bp=C.POINTER(C.c_uint8);wp=C.POINTER(C.c_uint16)
 lib.v6_save_page_unpack.argtypes=[bp,bp,C.c_uint]
 lib.v6_menu_copper.argtypes=[wp,C.c_uint32,wp,C.c_uint32,C.c_uint32,C.c_uint]
 reference.save_pixels.argtypes=[C.c_uint,C.c_char_p,bp]
 pixels=(C.c_uint8*76800)();bitmap=(C.c_uint8*28800)()
 for name,flags in [('prompt',0),('failure',32)]:
  reference.save_pixels(flags,b'Space',pixels)
  golden=bytes(sum(((pixels[y*320+x*8+i]>>p)&1)<<(7-i) for i in range(8)) for p in range(3) for y in range(240) for x in range(40))
  runs=arrays(assets/'save_assets.h','save_'+name+'_rle');raw=(C.c_uint8*len(runs))(*runs)
  assert lib.v6_save_page_unpack(bitmap,raw,len(runs)) and bytes(bitmap)==golden
  assert (assets/('save-'+name+'.bin')).read_bytes()==golden
  for bad in [runs[:-1],runs[:-2],[0,0]+runs[2:],runs+[1,0],[]]:
   invalid=(C.c_uint8*len(bad))(*bad);before=bytes(bitmap)
   assert not lib.v6_save_page_unpack(bitmap,invalid,len(bad)) and bytes(bitmap)==before
 palette=(C.c_uint16*32)(*arrays(assets/'save_assets.h','save_palette'));out=(C.c_uint16*140)();count=0
 for address in (0,0x20000,0x1000000-28800):
  for blank in (0,0x40000,0xfffffc):
   assert lib.v6_menu_copper(out,address,palette,blank,0,3)==130
   r=dict(zip(out[:130:2],out[1:130:2]));assert r[0x100]==0x3200 and r[0x104]==0x20
   for p in range(3):assert r[0xe0+4*p]*65536+r[0xe2+4*p]==address+p*9600
   for i in range(32):assert r[0x180+i*2]==palette[i]
   count+=1
 for planes in (0,1,2,6,7):
  before=bytes(out);assert not lib.v6_menu_copper(out,0,palette,0,0,planes) and bytes(out)==before
 print(f'PASS Save DMA: 57600 source bitmap bytes, packed-data rejection, {count} three-plane DMA schedules, invalid-output preservation')
if __name__=='__main__':main()
