#!/usr/bin/env python3
"""Full normal Crew/Stats/Save content against original renderer statements."""
import ctypes as C,re,subprocess
from pathlib import Path
from test_save_draw import main as save_draw
from test_music_control import method
from test_map_draw import arrays
from convert_ui_assets import build
from test_save_summary import Clock,Summary
ROOT=Path(__file__).resolve().parents[2]
class State(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('page','saved','failed','crew_mask','crew_frame')]+[('deaths',C.c_uint32),('trinkets',C.c_uint),('clock',Clock),('last',Summary)]+[(n,C.c_char_p) for n in ('roomname','area','last_area','action')]
class Icon(C.Structure):_fields_=[('x',C.c_int),('y',C.c_int),('tile',C.c_uint),('colour',C.c_uint)]
def prepare():
 save_draw();assets=ROOT/'build/amiga-feasibility';build(assets)
 out=ROOT/'build/amiga-ui-menu';out.mkdir(parents=True,exist_ok=True)
 original=(ROOT/'desktop_version/src/Render.cpp').read_text();gfx=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
 shim=(ROOT/'build/amiga-save-draw/reference.cpp').read_text().replace('uint8_t pixels[320*240]','uint16_t pixels[320*240]')
 start=shim.index('unsigned colour(');end=shim.index('void put(',start)
 shim=shim[:start]+'unsigned colour(int r,int g,int b){return ((r+8)/17<<8)|((g+8)/17<<4)|((b+8)/17);}\n'+shim[end:]
 shim=shim.replace('pixels[y*320+x]=(uint8_t)c','pixels[y*320+x]=(uint16_t)c')
 shim=shim.replace('pixels[y*320+x]=c','pixels[y*320+x]=(uint16_t)c')
 shim=shim.replace('struct Game {','struct Game {const char *customleveltitle="";bool crewstats[6];int deathcounts;const char *savetime;int savetrinkets;int trinkets(){return savetrinkets;}')
 shim=shim.replace('const char *currentarea(int,int){return "Space Station";}','const char *currentarea(int,int);')
 shim=shim.replace('struct Graphics {','struct Graphics {int crewframe=0;unsigned col_crewcyan,col_crewpurple,col_crewyellow,col_crewred,col_crewgreen,col_crewblue,col_crewinactive,col_clock,col_trinket;\n void draw_sprite(int,int,int,unsigned);void draw_flipsprite(int,int,int,unsigned){}\n void drawcrewman(int,int,int,bool,bool=false);void printcrewname(int,int,int);void printcrewnamedark(int,int,int);void printcrewnamestatus(int,int,int,bool);')
 shim=shim.replace('namespace loc {Lang *','namespace loc {const char *gettext_case(const char *s,char){return s;} Lang *')
 start=shim.index('namespace font {int height');end=shim.index('\nvoid Graphics::drawpixeltextbox',start)
 shim=shim[:start]+'''const int PR_RIGHT=128,PR_CJK_HIGH=256,FLIP_PR_CJK_HIGH=256,FLIP_PR_CJK_LOW=2;
namespace font {int height(int){return 8;}void print(int f,int x,int y,const char *s,int r,int g,int b){int n=std::strlen(s);if(f&PR_CEN){if(x==-1)x=160;x-=n*4;}else if(f&PR_RIGHT)x-=n*8;unsigned c=colour(r,g,b);for(int i=0;i<n;++i)for(int yy=0;yy<8;++yy)for(int xx=0;xx<8;++xx)if(dialogue_font[(unsigned char)s[i]][yy]&(128>>xx))put(x+i*8+xx,y+yy,c);}}
'''+shim[end:]
 shim=shim.replace('\nvoid Graphics::drawpixeltextbox','\nnamespace font {void print(int f,int x,int y,const std::string& s,int r,int g,int b){print(f,x,y,s.c_str(),r,g,b);}}\nvoid Graphics::drawpixeltextbox',1)
 # Existing formatter handles tab/prompt strings; add exact default-English numeric cases.
 shim=shim.replace('std::string t=std::strstr(f,"Press")?','std::string t=std::strstr(f,"{area}")?std::string(s):std::strstr(f,"Press")?')
 shim=shim.replace('void vformat_buf(char*,size_t,const char*,const char*,const char*,const char*){}','''void vformat_buf(char *b,size_t n,const char*,const char*,const char *s,const char *t){std::snprintf(b,n,"%s, %s",s,t);}
void vformat_buf(char *b,size_t n,const char*,const char*,int v){std::snprintf(b,n,"%d",v);}
void vformat_buf(char *b,size_t n,const char*,const char*,int v,int max){std::snprintf(b,n,"%d out of %d",v,max);}
struct {int numtrinkets(){return 20;}} cl;
''')
 shim=shim.replace('#include <cassert>','#include <cassert>\n#include <cstdio>\n#include "ui_menu.h"\n#include "ui_assets.h"\n#define SDL_arraysize(a) (sizeof(a)/sizeof(a[0]))')
 # Compile only the original palette branches used by normal menu portraits.
 cases=[];getcol=method(gfx,'SDL_Color Graphics::getcol(')
 for key in (0,13,14,15,16,18,19,20):
  start=getcol.index('    case '+str(key)+':');end=getcol.find('    case ',start+9)
  cases.append(getcol[start:end].replace('getRGB(','colour(').replace('GETCOL_RANDOM','0.5'))
 shim+='\nunsigned source_portrait_colour(int t){switch(t){'+''.join(cases)+'default:return 0;}}\n'
 shim+='''static const V6UIState *current;
const char *Map::currentarea(int,int){return current->last_area;}
void Graphics::draw_sprite(int x,int y,int tile,unsigned c){const uint32_t *r=tile==0?ui_portrait[0]:tile==1?ui_portrait[1]:tile==12?ui_portrait[2]:tile==50?ui_icons[0]:ui_icons[1];for(int yy=0;yy<32;++yy)for(int xx=0;xx<32;++xx)if(r[yy]&(1UL<<(31-xx)))put(x+xx,y+yy,c);}
'''
 for name in ('void Graphics::printcrewname(','void Graphics::printcrewnamedark(','void Graphics::printcrewnamestatus(','void Graphics::drawcrewman('):shim+='\n'+method(gfx,name)
 # Normal (unflipped) crew branch from the original renderer.
 start=original.index('                for (int i = 0; i < 3; i++)',original.index('else\n            {\n                for (int i = 0; i < 3',original.index('case 1:\n        if (game.insecretlab)')))
 brace=original.index('{',start);depth=1;end=brace+1
 while depth:
  depth+=(original[end]=='{')-(original[end]=='}');end+=1
 crew=original[start:end]
 start=original.index('        int max_trinkets;',end);end=original.index('    case 3:',start);stats=original[start:end].rsplit('    }',1)[0]
 start=original.index('        if (game.inintermission || game.translator_exploring)',end);end=original.index('    case 10:',start);save=original[start:end].rsplit('    }',1)[0]
 shim+='''extern "C" void ui_reference(const V6UIState *s,uint16_t *out){
 current=s;game.menupage=s->page;game.gamesaved=s->saved;game.gamesavefailed=s->failed;game.deathcounts=s->deaths;
 game.savetrinkets=s->trinkets;game.inintermission=game.translator_exploring=game.nodeathmode=game.intimetrial=game.insecretlab=false;
 map.custommode=false;game.last_quicksave.exists=s->last.exists;game.last_quicksave.hours=s->last.clock.hours;game.last_quicksave.minutes=s->last.clock.minutes;game.last_quicksave.seconds=s->last.clock.seconds;
 static char time[12];if(s->last.clock.hours)std::snprintf(time,sizeof(time),"%u:%02u:%02u",s->last.clock.hours,s->last.clock.minutes,s->last.clock.seconds);else std::snprintf(time,sizeof(time),"%u:%02u",s->last.clock.minutes,s->last.clock.seconds);
 game.savetime=time;action_label=s->action;map.roomname=s->roomname;graphics.crewframe=s->crew_frame;
 for(unsigned i=0;i<6;++i)game.crewstats[i]=s->crew_mask&(1<<i);
 graphics.col_crewcyan=source_portrait_colour(0);graphics.col_crewpurple=source_portrait_colour(20);graphics.col_crewyellow=source_portrait_colour(14);
 graphics.col_crewred=source_portrait_colour(15);graphics.col_crewgreen=source_portrait_colour(13);graphics.col_crewblue=source_portrait_colour(16);
 graphics.col_crewinactive=source_portrait_colour(19);graphics.col_clock=graphics.col_trinket=source_portrait_colour(18);
 maprender();do {switch(s->page){case 1:{'''+crew+'''}break;case 2:{'''+stats+'''}break;case 3:{'''+save+'''}}}while(false);
 std::memcpy(out,pixels,sizeof(pixels));}
'''
 # Source Game::timestring uses current time; its existing helper returns source formatting.
 shim=shim.replace('std::string giventimestring(int,int,int){return "0:00";}','''std::string giventimestring(int h,int m,int s){char b[12];if(h)std::snprintf(b,sizeof(b),"%d:%02d:%02d",h,m,s);else std::snprintf(b,sizeof(b),"%d:%02d",m,s);return b;}
 std::string timestring(){return giventimestring(hours,minutes,seconds);}
 int hours=0,minutes=0,seconds=0;
''')
 shim=shim.replace('game.savetrinkets=s->trinkets;','game.savetrinkets=s->trinkets;game.hours=s->clock.hours;game.minutes=s->clock.minutes;game.seconds=s->clock.seconds;')
 shim=shim.replace('struct Help {int glow=0;} help;','struct Help {int glow=0;const char *String(int n){static char b[12];std::snprintf(b,sizeof(b),"%d",n);return b;}} help;')
 shim+='''
extern "C" int ui_cpu_fill(void *context,int x,int y,unsigned w,unsigned h,unsigned c){
 uint8_t *out=(uint8_t*)context;for(int yy=y;yy<y+(int)h;++yy)for(int xx=x;xx<x+(int)w;++xx)if(xx>=0&&xx<320&&yy>=0&&yy<240)for(unsigned p=0;p<4;++p){unsigned at=p*9600+yy*40+xx/8,mask=1<<(7-xx%8);if(c&(1<<p))out[at]|=mask;else out[at]&=~mask;}return 1;}
'''
 (out/'reference.cpp').write_text(shim)
 flags=['-O2','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),'-I'+str(assets)]
 subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror','-c',str(ROOT/'amiga_version/ui_menu.c'),'-o',str(out/'ui.o')],check=True)
 subprocess.run(['cc','-std=c99',*flags,'-c',str(ROOT/'amiga_version/save_summary.c'),'-o',str(out/'summary.o')],check=True)
 subprocess.run(['c++','-std=c++11',*flags,'-shared',str(out/'reference.cpp'),str(ROOT/'build/amiga-map-draw/core.o'),str(out/'ui.o'),str(out/'summary.o'),'-o',str(out/'ui.so')],check=True)
 return C.CDLL(str(out/'ui.so')),assets

def main():
 lib,assets=prepare();bp=C.POINTER(C.c_uint8);sp=C.POINTER(State)
 Fill=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_int,C.c_int,C.c_uint,C.c_uint,C.c_uint)
 lib.v6_ui_draw.argtypes=[bp,sp,bp,bp,C.POINTER(C.c_uint32),Fill,C.c_void_p]
 lib.ui_reference.argtypes=[sp,C.POINTER(C.c_uint16)];lib.v6_ui_colour.argtypes=[C.c_uint,C.c_uint,sp]
 lib.v6_ui_icons.argtypes=[C.POINTER(Icon),sp]
 font=(C.c_uint8*1024)(*arrays(assets/'dialogue_font.h','dialogue_font'));border=(C.c_uint8*64)(*arrays(assets/'pickup_assets.h','pickup_border'));icons=(C.c_uint32*64)(*arrays(assets/'ui_assets.h','ui_icons'));portrait=arrays(assets/'ui_assets.h','ui_portrait')
 bitmap=(C.c_uint8*38400)();gold=(C.c_uint16*76800)();shapes=(Icon*8)()
 callback=Fill(('ui_cpu_fill',lib));count=0
 cases=[(1,0,0,mask,frame,0,0) for mask in range(64) for frame in range(2)]
 cases += [(2,0,0,5,0,n,d) for n,d in [(0,0),(1,10),(20,2147483647),(100,42)]]
 cases += [(3,s,f,mask,frame,n,0) for s,f in [(0,0),(1,0),(0,1)] for mask in (1,5,63) for frame in (0,1) for n in (0,20)]
 for page,saved,failed,mask,frame,n,deaths in cases:
  last=Summary(Clock(1,2,3,4),112,107,n,mask,1)
  state=State(page,saved,failed,mask,frame,deaths,n,Clock(1,2,3,4),last,b'V Stitch',b'Space Station',b'Space Station',b'Space')
  assert lib.v6_ui_draw(bitmap,C.byref(state),font,border,icons,callback,C.cast(bitmap,C.c_void_p))
  lib.ui_reference(C.byref(state),gold)
  palette=[[lib.v6_ui_colour(c,y,C.byref(state)) for c in range(16)] for y in range(240)]
  actual=[palette[y][sum(((bitmap[p*9600+y*40+x//8]>>(7-x%8))&1)<<p for p in range(4))] for y in range(240) for x in range(320)]
  amount=lib.v6_ui_icons(shapes,C.byref(state))
  for i in range(min(6,amount)):
   shape=shapes[i];idx=0 if shape.tile==0 else 1 if shape.tile==1 else 2
   for y in range(32):
    for x in range(32):
     if portrait[idx*32+y]&(1<<(31-x)) and 0<=shape.x+x<320 and 0<=shape.y+y<240:actual[(shape.y+y)*320+shape.x+x]=shape.colour
  for at,(a,b) in enumerate(zip(actual,gold)):
   assert a==b,(page,saved,failed,mask,frame,n,at%320,at//320,hex(a),hex(b))
  count+=1
 print(f'PASS full menu: {count} Crew/Stats/Save states, {count*76800} source RGB12 pixels, both portrait frames and all crew masks')
if __name__=='__main__':main()
