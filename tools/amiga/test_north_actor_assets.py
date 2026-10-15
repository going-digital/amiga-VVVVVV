#!/usr/bin/env python3
"""Native MOVEM-ready actor data against original visible/red-channel PNGs."""
import subprocess
from test_map_draw import arrays
from test_player import ROOT

def main():
 p=ROOT/'build/amiga-feasibility';path=p/'north_actor_assets.h'
 h,rgba=subprocess.check_output([str(p/'png_rgba'),str(p/'tower_sprites.png')]).split(b'\n',1);width,height=map(int,h.split())
 checks=0
 for name,tiles,crops,widths,rows in [('north_enemy_dma',range(40,44),(0,16),(16,4),20),
                                  ('north_drone_dma',range(36,40),(0,),(16,),32),
                                  ('north_linear_dma',range(32,36),(0,16),(16,16),32),
                                  ('north_terminal_dma',(16,17),(0,),(16,),16),
                                  ('north_player_dma',range(16),(6,),(16,),32),
                                  ('north_checkpoint_dma',(20,21),(0,),(16,),16),
                                  ('north_crew_dma',(150,),(6,),(16,),32)]:
  data=arrays(path,name);at=0
  for tile in tiles:
   ox=tile%(width//32)*32;oy=tile//(width//32)*32
   for crop,w in zip(crops,widths):
    for parity in (0,1):
     for y in range(rows):
      bits=sum((rgba[((oy+y)*width+ox+crop+x)*4+3]>127 and max(rgba[((oy+y)*width+ox+crop+x)*4:((oy+y)*width+ox+crop+x)*4+3])>0)<<(15-x) for x in range(w))
      assert data[at:at+2]==[bits,bits if parity else 0],(name,tile,crop,y);at+=2;checks+=w
  assert at==len(data)
 # A crewmate's transparent outer rows need no sprite/bitplane bandwidth.
 for name,frames in [('north_player_dma',16),('north_crew_dma',1)]:
  v=arrays(path,name)
  for frame in range(frames):
   for parity in range(2):
    body=v[(frame*2+parity)*64:(frame*2+parity+1)*64]
    assert not any(body[:4]) and not any(body[46:]),('crew visible bounds',name,frame,parity)
 for name,red,tiles in [('north_enemy_visible',False,range(40,44)),('north_enemy_collision',True,range(40,44)),
                        ('north_drone_visible',False,range(36,40)),('north_drone_collision',True,range(36,40)),
                        ('north_linear_visible',False,range(32,36)),('north_linear_collision',True,range(32,36)),
                        ('north_terminal_visible',False,(16,17))]:
  masks=arrays(path,name)
  for frame,tile in enumerate(tiles):
   ox=tile%(width//32)*32;oy=tile//(width//32)*32
   for y in range(32):
    expected=0
    for x in range(32):
     pixel=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
     if (pixel[0]!=0) if red else (pixel[3]>127 and max(pixel[:3])>0):expected|=1<<(31-x)
    assert masks[frame*32+y]==expected;checks+=32
 h,pixels=subprocess.check_output([str(p/'png_rgba'),str(p/'reflect-tiles.png')]).split(b'\n',1);width,height=map(int,h.split())
 data=arrays(path,'north_platform_dma');colours=arrays(path,'north_platform_colours');at=0
 for frame,tile in enumerate((*range(10,14),616)):
  ox=tile%(width//8)*8;oy=tile//(width//8)*8
  for part in range(2):
   for parity in (0,1):
    for y in range(8):
     bits=0
     for x in range(16):
      pixel=pixels[((oy+y)*width+ox+x%8)*4:((oy+y)*width+ox+x%8)*4+4]
      if pixel[3]:
       colour=((pixel[0]+8)//17<<8)|((pixel[1]+8)//17<<4)|((pixel[2]+8)//17)
       assert colour==colours[frame];bits|=1<<(15-x)
     assert data[at:at+2]==[bits,bits if parity else 0];at+=2;checks+=16
 assert at==len(data)
 print('PASS north actor assets:',checks,'original PNG pixel/parity/collision checks; exact RGB12 platform colours')
if __name__=='__main__':main()
