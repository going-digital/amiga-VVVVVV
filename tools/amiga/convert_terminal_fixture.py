#!/usr/bin/env python3
"""Private native terminal fixture: reviewed Linear Collider scene and original cues."""
import argparse,ctypes as C,json,subprocess,zipfile
from pathlib import Path
from convert_assets import DEFAULT_DATA
from tower_gameplay_data import north_route_room
from energize_assets import export as export_graphics
from terminal_scripts import export as export_script
from convert_audio import convert,PERIOD
from test_map_draw import arrays
from test_player import ROOT

def build(data,out):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);assets=ROOT/'build/amiga-feasibility'
 room=north_route_room('linear');export_script(out)
 with zipfile.ZipFile(data) as z:
  export_graphics(z,out,assets/'png_rgba',room,'linear')
  sprites=out/'sprites.png';sprites.write_bytes(z.read('graphics/sprites.png'))
  header,rgba=subprocess.check_output([str(assets/'png_rgba'),str(sprites)]).split(b'\n',1);w,h=map(int,header.split())
  masks=[]
  for tile in (0,17,20,21,32,33,34,35):
   ox=tile%(w//32)*32;oy=tile//(w//32)*32
   masks.append([sum((rgba[((oy+y)*w+ox+x)*4+3]>127 and max(rgba[((oy+y)*w+ox+x)*4:((oy+y)*w+ox+x)*4+3])>0)<<(31-x) for x in range(32)) for y in range(32)])
  samples=[];meta=[]
  for name in ('terminal','blip2'):
   pcm,info=convert(z.read('sounds/'+name+'.wav'))
   if len(pcm)<1024:pcm+=bytes(1024-len(pcm))
   samples.append(pcm);info['dma_bytes']=len(pcm);info['name']=name;meta.append(info)
 libpath=out/'terminal-draw.so'
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC',str(ROOT/'amiga_version/terminal_read.c'),'-o',str(libpath)],check=True)
 # Use the tested compositor itself for immutable source-equivalent overlays.
 from test_terminal_read import Page,Program,VM
 pages=(Page*2)();strings=[];source=export_script(out)
 for i,p in enumerate(source['pages']):
  text=[v.encode() for v in p['lines']];strings+=text
  pages[i]=Page(p['x'],p['y'],p['flip'],len(text),(C.c_char_p*6)(*text))
 program=Program(pages,2);vm=VM();lib=C.CDLL(str(libpath));lib.v6_terminal_read_start.argtypes=[C.POINTER(VM),C.POINTER(Program)]
 assert lib.v6_terminal_read_start(C.byref(vm),C.byref(program))
 for b in vm.boxes:b.visible=1
 font=(C.c_uint8*1024)(*arrays(assets/'dialogue_font.h','dialogue_font'));border=(C.c_uint8*64)(*arrays(assets/'pickup_assets.h','pickup_border'));row=(C.c_uint8*80)()
 lib.v6_terminal_read_row.argtypes=[C.POINTER(C.c_uint8),C.c_uint,C.POINTER(VM),C.POINTER(C.c_uint8),C.POINTER(C.c_uint8),C.c_int]
 atlas=arrays(out/'linear_assets.h','linear_atlas');palette=arrays(out/'linear_assets.h','linear_palette');ids=sorted(set(room['tiles']));mapping={t:i for i,t in enumerate(ids)}
 base=bytearray(28800);reading=bytearray(28800);mask=bytearray(9600)
 for y in range(240):
  assert lib.v6_terminal_read_row(row,y,C.byref(vm),font,border,0)
  for xbyte in range(40):
   tile=mapping[room['tiles'][y//8*40+xbyte]]
   fg=[atlas[tile*16+p*8+y%8] for p in range(2)];m=row[xbyte];ink=row[40+xbyte];mask[y*40+xbyte]=m
   for p in range(2):base[p*9600+y*40+xbyte]=fg[p]
   reading[y*40+xbyte]=(fg[0]&~m)|m
   reading[9600+y*40+xbyte]=(fg[1]&~m)|ink
   reading[19200+y*40+xbyte]=m
 text='/* Private terminal hardware fixture; original game assets. */\n'
 for name,value in [('fixture_world',base),('fixture_read',reading),('fixture_cover',mask)]:
  text+='static const uint8_t '+name+'[] __attribute__((aligned(4)))={'+','.join(map(str,value))+'};\n'
 text+='static const uint16_t fixture_palette[8]={'+','.join(map(str,palette+[0xff4,0x222,0xff4,0xaaa]))+'};\n'
 text+='static const uint32_t fixture_masks[8][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in masks)+'};\n'
 text+='static const uint16_t fixture_tiles[1200]={'+','.join(map(str,room['tiles']))+'};\n'
 for i,pcm in enumerate(samples):text+='static const uint8_t fixture_sound'+str(i)+'[]={'+','.join(map(str,pcm))+'};\n'
 text+='#define FIXTURE_PERIOD '+str(PERIOD)+'\n#define FIXTURE_AUDIO_BYTES '+str(sum(map(len,samples))+2)+'\n'
 (out/'terminal_fixture_assets.h').write_text(text)
 (out/'terminal-fixture.json').write_text(json.dumps(dict(room={k:v for k,v in room.items() if k!='tiles'},audio=meta,scope='Read-only native terminal fixture; actor motion, terminal display and cues; no campaign admission'),indent=2)+'\n')
 print('PASS terminal fixture conversion:',len(ids),'source tiles;',sum(map(len,samples)),'PCM bytes')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--data',type=Path,default=DEFAULT_DATA);p.add_argument('--out',type=Path,default=ROOT/'build/amiga-terminal-native');a=p.parse_args();build(a.data,a.out)
