#!/usr/bin/env python3
"""Native map DMA across resident rooms and streamed tower cameras."""
import argparse,ctypes as C,shlex,struct,subprocess
from pathlib import Path
from test_map_draw import libraries,arrays
from test_player import ROOT

SCENES=[(0,c) for c in (0,166,249,255,5368)]+[(i,0) for i in range(1,10)]
ROOMS=[(109,109,'The Tower'),(109,104,'The Tower'),(108,109,"I'm Sorry..."),
       (110,104,'Seeing Red'),(111,104,'Building Apport'),(110,105,'Energize'),
       (111,105,'Frown Upside Down'),(111,106,'Shenanigan'),
       (111,107,'Prize for the Reckless'),(112,107,'V Stitch'),
       (112,106,'Stop and Reflect'),(112,105,'The Yes Men'),(112,104,'Gantry and Dolly'),(112,103,'Security Sweep')]

def main():
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True)
 g.add_argument('--make-command-log',type=Path);g.add_argument('--cppflags')
 p.add_argument('--scene',type=int);p.add_argument('--start-scene',type=int,default=0);p.add_argument('--north',action='store_true');a=p.parse_args()
 source=libraries();assets=ROOT/'build/amiga-feasibility'
 bp=C.POINTER(C.c_uint8)
 source.v6_map_draw_row.argtypes=[bp,C.c_uint,bp,bp,bp,bp,bp,bp,C.c_char_p]
 def bytes_array(path,name):return (C.c_uint8*len(v))(*v) if (v:=arrays(assets/path,name)) else None
 font=bytes_array('dialogue_font.h','dialogue_font');border=bytes_array('pickup_assets.h','pickup_border')
 minimap=bytes_array('map_assets.h','map_minimap');fog=bytes_array('map_assets.h','map_covered');colours=bytes_array('map_assets.h','map_ui_colours')
 if a.cppflags is not None:
  base=ROOT/'build/amiga-menu-slide-native'
  command=['make',f'BUILD={base}',f'CPPFLAGS={a.cppflags}',str(base/'tower.adf')]
 else:
  line=[l for l in a.make_command_log.read_text().splitlines() if l.startswith('/Library/Developer/CommandLineTools/usr/bin/make BUILD=') and 'build/amiga-menu-slide-native ' in l][-1]
  command=shlex.split(line)
 tested=0
 if a.north:command=[v+' -DV6_NORTH_ROUTE' if v.startswith('CPPFLAGS=') else v for v in command]
 for scene,camera in SCENES+([(i,0) for i in range(10,14)] if a.north else []):
  if scene<a.start_scene:continue
  if a.scene is not None and scene!=a.scene:continue
  build=ROOT/f'build/amiga-menu-scene-{scene}-{camera}'
  args=[v.replace('amiga-menu-slide-native',build.name) for v in command]
  args=[v+f' -DV6_MENU_SCENE_CAPTURE={scene} -DV6_MENU_CAMERA_CAPTURE={camera}' if v.startswith('CPPFLAGS=') else v for v in args]
  with (ROOT/'build/menu-scene-build.log').open('w') as log:subprocess.run(args,cwd=ROOT/'amiga_version',stdout=log,stderr=subprocess.STDOUT,check=True)
  subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_slide.py'),'--build',str(build),'--page','0'],check=True)
  rx,ry,title=ROOMS[scene];explored=(C.c_uint8*50)();bit=(ry-100)*20+rx-100;explored[bit//8]=1<<(bit%8)
  bitmap=bytearray(48000);row=(C.c_uint8*200)()
  for y in range(240):
   assert source.v6_map_draw_row(row,y,explored,minimap,fog,font,border,colours,title.encode())
   for plane in range(5):bitmap[plane*9600+y*40:plane*9600+y*40+40]=bytes(row[plane*40:plane*40+40])
  chip=(build/'ui-slide-full.bin').read_bytes();at=chip.find(bitmap);assert at>=0,(scene,camera,'source bitmap')
  search=0;lists=0
  while True:
   pos=chip.find(bytes.fromhex('2c01fffe01005200'),search)
   if pos<0:break
   search=pos+2;words=struct.unpack_from('>138H',chip,pos-64);regs=dict(zip(words[::2],words[1::2]))
   if (regs[0xe0]<<16|regs[0xe2])!=at:continue
   ptr=regs[0x120]<<16|regs[0x122];head=struct.unpack_from('>2H',chip,ptr)
   if head!=(0,0):
    mode=1 if regs[0x1a2]==0xfff else 2;height=180 if rx==109 else 9;x=148 if rx==109 else 40+(rx-100)*12;y=21 if rx==109 else 21+(ry-100)*9
    start=52+y;stop=start+height;h=128+x
    assert head==(((start&255)<<8)|(h>>1),((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(h&1))
    for yy in range(height):
     bits=sum((int(mode==1 and (yy in (0,height-1) or xx in (0,11))) or int(mode and 2<=yy<height-2 and 2<=xx<10 and (yy in (2,height-3) or xx in (2,9))))<<(15-xx) for xx in range(12))
     assert struct.unpack_from('>2H',chip,ptr+4+yy*4)==(bits,0),(scene,camera,yy)
    assert chip[ptr+4+height*4:ptr+8+height*4]==bytes(4)
   lists+=1
  assert lists==2,(scene,camera,lists)
  tested+=1;print('PASS native scene',scene,'camera',camera,': 48000 source map bytes and both cursor DMA banks',flush=True)
 print('PASS resident menu scenes:',tested,'rooms/cameras')
if __name__=='__main__':main()
