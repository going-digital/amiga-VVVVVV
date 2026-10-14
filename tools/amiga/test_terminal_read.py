#!/usr/bin/env python3
"""Station-terminal flow, textbox geometry/fades, and original border/font pixels."""
import ctypes as C
import subprocess
from test_player import ROOT,block
from test_map_draw import libraries,arrays
from terminal_scripts import export
class Page(C.Structure):
 _fields_=[('x',C.c_int),('y',C.c_int),('flip',C.c_uint),('count',C.c_uint),('lines',C.c_char_p*6)]
class Program(C.Structure):_fields_=[('pages',C.POINTER(Page)),('count',C.c_uint)]
class Box(C.Structure):
 _fields_=[('page',C.POINTER(Page)),*[(n,C.c_int) for n in 'x y w h'.split()],*[(n,C.c_uint) for n in 'visible mode step'.split()],('opacity',C.c_uint32),('previous_opacity',C.c_uint32)]
class VM(C.Structure):
 _fields_=[('program',C.POINTER(Program)),('boxes',Box*2),*[(n,C.c_uint) for n in 'active phase bars control waiting cues serial'.split()]]
class Signals(C.Structure):_fields_=[('bars_position',C.c_int),('advance',C.c_int)]

def main():
 out=ROOT/'build/amiga-terminal-read';data=export(out);libraries()
 source=(ROOT/'desktop_version/src/Script.cpp').read_text()
 handlers=[block(source,source.index('if (words[0] == "'+n+'")')) for n in ('cutscene','endcutscene','untilbars','backgroundtext','flipme','endtext')]
 speak=block(source,source.index('if (!game.backgroundtext)',source.index('else if (words[0] == "speak_active"')))
 shim=(ROOT/'build/amiga-map-draw/reference.cpp').read_text()
 shim=shim.replace('#include <string>','#include <string>\n#include <vector>\nextern "C" {\n#include "terminal_read.h"\n}\n')
 a=shim.index('unsigned colour(');b=shim.index('void put(',a)
 shim=shim[:a]+'unsigned colour(int r,int,int){return r==174?3:1;}\n'+shim[b:]
 shim=shim.replace('struct Script {bool running=false;} script;','struct Script {bool running=false;} script;')
 textbox='''namespace font {int len(int,const char*);int height(int);bool is_rtl(int){return false;}}
struct textboxclass {std::vector<std::string> lines;int xp=0,yp=0,w=0,h=0,linegap=1,tm=0,timer=0,r=0,g=0,b=0,print_flags=0;float tl=0.5f,prev_tl=0.0f;bool flipme=false,fill_buttons=false;
 void resize();void centerx();void centery();void adjust();void initcol(int,int,int);void update();void remove();};
const int PR_RIGHT=128;const int SCREEN_HEIGHT_PIXELS=240;
#define PR_BRIGHTNESS(x) 0
float lerp(float,float b){return b;}
'''
 shim=shim.replace('struct Graphics {',textbox+'struct Graphics {std::vector<textboxclass> textboxes;int showcutscenebars=0,cutscenebarspos=0;void terminal_gui();void textboxremove(){for(auto& t:textboxes)t.remove();}')
 shim=shim.replace('namespace font {int height(int)', 'namespace font {int len(int,const char*s){return std::strlen(s)*8;}int height(int)')
 shim=shim.replace('void print(int,int x','void print(int flags,int x').replace('if(x==-1)x=160;x-=n*4;','if(flags&PR_CEN){if(x==-1)x=160;x-=n*4;}')
 a=source.index('if (!game.backgroundtext)',source.index('else if (words[0] == "speak_active"'))
 text=(ROOT/'desktop_version/src/Textbox.cpp').read_text()
 shim+='\n'+'\n'.join(block(text,text.index('void textboxclass::'+n+'(')) for n in ('resize','centerx','centery','adjust','initcol','update','remove'))
 gfx=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
 a=gfx.index('        int font_height =',gfx.index('void Graphics::drawgui(void)'));b=gfx.index('        const bool transparent',a)
 layout=gfx[a:b]
 a=gfx.index('        else\n        {\n            const float tl_lerp',b);opaque=block(gfx,a)[len('        else'):]
 shim+='''const char *textbox_line(char*,size_t,size_t i,size_t j){return graphics.textboxes[i].lines[j].c_str();}
void Graphics::terminal_gui(){int text_sign=flipmode?-1:1;for(size_t i=0;i<textboxes.size();++i){int text_yoff,yp;
'''+layout+opaque+'''}}
static textboxclass make_box(const V6TerminalPage& p){textboxclass t;for(unsigned i=0;i<p.count;++i)t.lines.push_back(p.lines[i]);t.xp=p.x;t.yp=p.y;t.flipme=p.flip;
 t.resize();if(p.x==-500)t.centerx();if(p.y==-500)t.centery();t.adjust();t.initcol(174,174,174);return t;}
extern "C" void terminal_geometry(const V6TerminalPage *p,int *o){auto t=make_box(*p);o[0]=t.xp;o[1]=t.yp;o[2]=t.w;o[3]=t.h;}
extern "C" void terminal_fade(unsigned n,int removal,unsigned *o){textboxclass t;t.initcol(174,174,174);if(removal)t.remove();for(unsigned i=0;i<n;++i)t.update();o[0]=(unsigned)(t.tl*16777216.0f);o[1]=(int)(174*t.tl);o[2]=t.tm;o[3]=(unsigned)(t.prev_tl*16777216.0f);}
extern "C" void terminal_pixels(const V6TerminalPage *p,unsigned mask,int flip,uint8_t *o){graphics.textboxes.clear();graphics.flipmode=flip;std::memset(pixels,0,sizeof(pixels));
 for(unsigned i=0;i<2;++i)if(mask&(1U<<i)){auto t=make_box(p[i]);t.tl=t.prev_tl=1;graphics.textboxes.push_back(t);}
 graphics.terminal_gui();std::memcpy(o,pixels,sizeof(pixels));}
struct ReadGame {bool backgroundtext,hascontrol,pausescript,advancetext,jumpheld;};
struct Key {bool isDown(int){return false;}} key;
const int KEYBOARD_UP=1,KEYBOARD_DOWN=2;
extern "C" void terminal_handler(const char *command,int *o){
 ReadGame game={(bool)o[0],(bool)o[2],(bool)o[3],(bool)o[4],false};
 graphics.showcutscenebars=o[5];graphics.cutscenebarspos=o[9];
 bool textflipme=o[1];int position=1,scriptdelay=0;
 std::string words[1]={command};
'''+ '\n'.join(handlers)+'''if(words[0]=="speak") {'''+speak+'''game.backgroundtext=false;}
 o[0]=game.backgroundtext;o[1]=textflipme;o[2]=game.hascontrol;o[3]=game.pausescript;o[4]=game.advancetext;o[5]=graphics.showcutscenebars;o[6]=position;o[7]=scriptdelay;
}
'''
 (out/'reference.cpp').write_text(shim)
 api=out/'program_api.c';api.write_text('#include "terminal_station_program.h"\nconst V6TerminalReadProgram *station_program(void){return &v6_station_terminal_program;}\n')
 flags=['-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'build/amiga-feasibility')]
 subprocess.run(['c++','-std=c++11',*flags,str(out/'reference.cpp'),str(ROOT/'build/amiga-map-draw/core.o'),'-o',str(out/'reference.so')],check=True)
 subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',str(ROOT/'amiga_version/terminal_read.c'),'-I'+str(out),str(api),'-o',str(out/'core.so')],check=True)
 core=C.CDLL(str(out/'core.so'));ref=C.CDLL(str(out/'reference.so'))
 core.v6_terminal_read_start.argtypes=[C.POINTER(VM),C.POINTER(Program)];core.v6_terminal_read_start.restype=C.c_int
 core.v6_terminal_read_tick.argtypes=[C.POINTER(VM),C.POINTER(Signals)];core.v6_terminal_read_animate.argtypes=[C.POINTER(VM)]
 core.v6_terminal_box_gray.argtypes=[C.POINTER(Box)];core.v6_terminal_box_gray.restype=C.c_uint
 bp=C.POINTER(C.c_uint8);core.v6_terminal_read_row.argtypes=[bp,C.c_uint,C.POINTER(VM),bp,bp,C.c_int]
 ref.terminal_geometry.argtypes=[C.POINTER(Page),C.POINTER(C.c_int)];ref.terminal_fade.argtypes=[C.c_uint,C.c_int,C.POINTER(C.c_uint)]
 ref.terminal_pixels.argtypes=[C.POINTER(Page),C.c_uint,C.c_int,bp];ref.terminal_handler.argtypes=[C.c_char_p,C.POINTER(C.c_int)]
 pages=(Page*2)();keep=[]
 for i,p in enumerate(data['pages']):
  lines=[s.encode() for s in p['lines']];keep+=lines;pages[i]=Page(p['x'],p['y'],p['flip'],len(lines),(C.c_char_p*6)(*lines))
 core.station_program.restype=C.POINTER(Program)
 compiled=core.station_program().contents;assert compiled.count==2
 for i in range(2):
  a,b=compiled.pages[i],pages[i]
  assert (a.x,a.y,a.flip,a.count,list(a.lines))==(b.x,b.y,b.flip,b.count,list(b.lines))
 program=Program(pages,2);v=VM();assert core.v6_terminal_read_start(C.byref(v),C.byref(program))
 for i in range(2):
  expected=(C.c_int*4)();ref.terminal_geometry(C.byref(pages[i]),expected)
  assert [getattr(v.boxes[i],n) for n in 'x y w h'.split()]==list(expected)
 assert v.boxes[1].h==69
 # Independent interpreter of the literal source command stream, with original
 # C++ handlers for the bars, background/pause and removal side effects.
 traces=0
 for opening in (0,1,7):
  for pause in (0,1,8):
   for closing in (0,1,9):
    v=VM();assert core.v6_terminal_read_start(C.byref(v),C.byref(program))
    state=(C.c_int*10)(0,0,1,0,0,0,0,0,0,0);pc=0;cues=0;created=0;running=True;old_wait=False
    for tick in range(80):
     barspos=0 if tick>=opening+pause+2+closing else 360 if tick>=opening else 359
     advance=int(tick>=opening+pause+1)
     if old_wait and advance:state[2]=1;state[3]=0
     state[9]=barspos
     while running and not state[3]:
      if pc==len(data['commands']):running=False;break
      cmd=data['commands'][pc];name=cmd.split('(')[0]
      if name=='text':pc+=int(cmd.rsplit(',',1)[1][:-1])+1;continue
      if name=='position':pc+=1;continue
      if name=='squeak':cues+=1;pc+=1;continue
      if name=='speak':created+=1
      if name=='endtext':created=0
      ref.terminal_handler(name.encode(),state)
      if name=='speak':state[1]=0
      if state[7]:break
      pc+=1
     old_wait=bool(state[3])
     core.v6_terminal_read_tick(C.byref(v),C.byref(Signals(barspos,advance)))
     assert (v.active,v.bars,v.control,v.waiting,v.cues)==(running,state[5],state[2],state[3],cues),(opening,pause,closing,tick,pc)
     if v.phase==1:assert created==2 and all(b.visible for b in v.boxes)
     traces+=1
     if not running:break
 # Source binary32 fade values and removal, including advancing before the
 # appearance finishes (remove() resets opacity to 1 in the original).
 fades=0
 for appearance in range(8):
  for removal in range(7):
   v=VM();assert core.v6_terminal_read_start(C.byref(v),C.byref(program));core.v6_terminal_read_tick(C.byref(v),C.byref(Signals(360,0)))
   for _ in range(appearance):core.v6_terminal_read_animate(C.byref(v))
   expected=(C.c_uint*4)();ref.terminal_fade(appearance,0,expected)
   assert v.boxes[0].opacity==expected[0] and core.v6_terminal_box_gray(C.byref(v.boxes[0]))==expected[1]
   assert v.boxes[0].previous_opacity==expected[3]
   core.v6_terminal_read_tick(C.byref(v),C.byref(Signals(360,1)))
   for _ in range(removal):core.v6_terminal_read_animate(C.byref(v))
   ref.terminal_fade(removal,1,expected)
   assert v.boxes[0].opacity==expected[0] and core.v6_terminal_box_gray(C.byref(v.boxes[0]))==expected[1]
   if 0<removal<=5:assert v.boxes[0].previous_opacity==expected[3]
   assert bool(v.boxes[0].visible)==(removal<5)
   assert v.serial==(3 if removal>=5 else 2);fades+=1
 font=(C.c_uint8*1024)(*arrays(ROOT/'build/amiga-feasibility/dialogue_font.h','dialogue_font'))
 border=(C.c_uint8*64)(*arrays(ROOT/'build/amiga-feasibility/pickup_assets.h','pickup_border'));pixels=0
 for flip in (0,1):
  for shift,mask in [(None,m) for m in range(4)]+[(s,3) for s in range(8)]:
   render_pages=(Page*2).from_buffer_copy(pages)
   if shift is not None:
    for p in render_pages:p.x=10+shift
    render_pages[0].y=60+shift
   render_program=Program(render_pages,2)
   v=VM();assert core.v6_terminal_read_start(C.byref(v),C.byref(render_program))
   for i in range(2):v.boxes[i].visible=bool(mask&(1<<i))
   expected=(C.c_uint8*76800)();ref.terminal_pixels(render_pages,mask,flip,expected)
   row=(C.c_uint8*80)()
   for y in range(240):
    assert core.v6_terminal_read_row(row,y,C.byref(v),font,border,flip)
    for x in range(320):
     bit=128>>(x&7);actual=int(bool(row[x//8]&bit))+2*int(bool(row[40+x//8]&bit))
     assert actual==expected[y*320+x],(mask,flip,shift,x,y,actual,expected[y*320+x]);pixels+=1
 # Failed starts and invalid draw requests preserve every byte.
 v=VM();assert core.v6_terminal_read_start(C.byref(v),C.byref(program));before=bytes(v)
 assert not core.v6_terminal_read_start(C.byref(v),C.byref(program)) and bytes(v)==before
 row=(C.c_uint8*80)(*([0xa5]*80));assert not core.v6_terminal_read_row(row,240,C.byref(v),font,border,0);assert bytes(row)==bytes([0xa5]*80)
 bad_cases=0
 for name,value in [('count',0),('count',7),('flip',2),('x',-1),('x',321),('y',-1),('y',241)]:
  bad_pages=(Page*2).from_buffer_copy(pages);setattr(bad_pages[1],name,value);bad=Program(bad_pages,2);v=VM();before=bytes(v)
  assert not core.v6_terminal_read_start(C.byref(v),C.byref(bad)) and bytes(v)==before;bad_cases+=1
 for text in (None,b'x'*37,b'\x80'):
  bad_pages=(Page*2).from_buffer_copy(pages);bad_pages[1].lines[0]=text;bad=Program(bad_pages,2);v=VM();before=bytes(v)
  assert not core.v6_terminal_read_start(C.byref(v),C.byref(bad)) and bytes(v)==before;bad_cases+=1
 v=VM();assert core.v6_terminal_read_start(C.byref(v),C.byref(program));v.boxes[1].visible=1;v.boxes[1].h+=1
 assert not core.v6_terminal_read_row(row,100,C.byref(v),font,border,0) and bytes(row)==bytes([0xa5]*80)
 print('PASS terminal read:',traces,'source script ticks,',fades,'binary32 fade schedules,',pixels,'original textbox/font/border pixels;',bad_cases,'invalid descriptors preserved; six-line log and flip mode')

if __name__=='__main__':main()
