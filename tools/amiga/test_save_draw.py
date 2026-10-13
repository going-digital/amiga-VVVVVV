#!/usr/bin/env python3
"""Save prompt/failure pixels against original renderer and Font.cpp wrapping."""
import ctypes as C
from pathlib import Path
import subprocess
from test_map_draw import libraries,arrays
from test_music_control import method
ROOT=Path(__file__).resolve().parents[2]
def main():
 libraries() # Generate the existing original-map rendering/font shim.
 out=ROOT/'build/amiga-save-draw';out.mkdir(parents=True,exist_ok=True)
 shim=(ROOT/'build/amiga-map-draw/reference.cpp').read_text()
 assets=ROOT/'build/amiga-feasibility'
 colours=arrays(assets/'map_assets.h','map_ui_colours')
 palette=arrays(assets/'map_assets.h','map_palette')
 rgb=[palette[i] for i in colours]+[0xfff,0x99b]
 begin=shim.index('unsigned colour(');end=shim.index('void put(',begin)
 shim=shim[:begin]+'unsigned colour(int r,int g,int b){unsigned c=((r+8)/17<<8)|((g+8)/17<<4)|((b+8)/17);const unsigned values[8]={'+','.join(map(str,rgb))+'};for(unsigned i=0;i<8;++i)if(values[i]==c)return i;assert(false);return 0;}\n'+shim[end:]
 shim=shim.replace('struct Lang {','struct Lang {bool autowordwrap=true;')
 begin=shim.index('struct Game {');end=shim.index('struct Script',begin)
 policy=(ROOT/'build/amiga-save-page/reference.cpp').read_text()
 game=policy[policy.index('struct Game {'):policy.index('struct Map {')]
 game=game.replace('struct Game {','struct Game {bool noflashingmode=false;int roomx=112,roomy=107,menupage=3;')
 shim=shim[:begin]+game+shim[end:]
 shim=shim.replace('MapRenderData get_render_data()', 'const char *currentarea(int,int){return "Space Station";} MapRenderData get_render_data()')
 shim=shim.replace('std::string t="["+std::string(s)+"]";', 'std::string t="["+std::string(s)+"]";')
 # Replace the formatter with prompt-aware original English placeholder handling.
 begin=shim.index('void vformat_buf(');end=shim.index('uint8_t pixels',begin)
 shim=shim[:begin]+'''const char *action_label;
const int ActionSet_InGame=0,Action_InGame_ACTION=0;
const char *vformat_button(int,int){return action_label;}
void vformat_buf(char *b,size_t n,const char *f,const char*,const char *s){
 std::string t=std::strstr(f,"Press")?"[Press "+std::string(s)+" to save your game]":"["+std::string(s)+"]";
 assert(t.size()+1<=n);std::strcpy(b,t.c_str());}
void vformat_buf(char*,size_t,const char*,const char*,const char*,const char*){}
#define FLIP(y,h) (y)
#define SDL_FALLTHROUGH
struct Font {};
uint32_t UTF8_peek_next(const char *s,uint8_t *n){*n=1;return (unsigned char)*s;}
int get_advance(Font*,uint32_t){return 8;}
'''+shim[end:]
 next_wrap=method((ROOT/'desktop_version/src/Font.cpp').read_text(),'static bool next_wrap(')
 shim+='\n'+next_wrap+'''
namespace font {void print_wrap(int f,int x,int y,const char *s,int r,int g,int b,int spacing=10){
 Font font;size_t start=0,len=0;
 while(true){size_t previous=start;if(!next_wrap(&font,&start,&len,s+previous,304))break;
 std::string line(s+previous,len);print(f,x,y,line.c_str(),r,g,b);y+=spacing;}
}}
'''
 render=(ROOT/'desktop_version/src/Render.cpp').read_text();start=render.index('        if (game.inintermission || game.translator_exploring)')
 body=render[start:render.index('        graphics.drawpixeltextbox(17, 65, 286, 90',start)]
 shim+='''extern "C" void save_pixels(unsigned flags,const char *label,uint8_t *out){
 game.inintermission=flags&1;game.translator_exploring=flags&2;game.nodeathmode=flags&4;
 game.intimetrial=flags&8;game.insecretlab=flags&16;game.gamesavefailed=flags&32;
 game.gamesaved=flags&64;map.custommode=flags&128;game.last_quicksave.exists=flags&256;
 action_label=label;game.menupage=3;maprender();do {
'''+body+'''
 }while(false);std::memcpy(out,pixels,sizeof(pixels));}
'''
 (out/'reference.cpp').write_text(shim)
 flags=['-O2','-fPIC','-shared','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),'-I'+str(assets)]
 subprocess.run(['cc','-std=c99',*[f for f in flags if f!='-shared'],'-c',str(ROOT/'amiga_version/save_page.c'),'-o',str(out/'page.o')],check=True)
 subprocess.run(['c++','-std=c++11',*flags,str(out/'reference.cpp'),str(ROOT/'build/amiga-map-draw/core.o'),str(out/'page.o'),'-o',str(out/'draw.so')],check=True)
 lib=C.CDLL(str(out/'draw.so'));bp=C.POINTER(C.c_uint8)
 class Page(C.Structure):_fields_=[(n,C.c_uint) for n in ('state','autosave_note','last_summary')]
 lib.v6_save_page.argtypes=[C.c_uint];lib.v6_save_page.restype=Page
 lib.save_pixels.argtypes=[C.c_uint,C.c_char_p,bp]
 lib.v6_save_draw_row.argtypes=[bp,C.c_uint,C.POINTER(Page),bp,bp,bp,C.c_char_p,C.c_char_p]
 font=(C.c_uint8*1024)(*arrays(assets/'dialogue_font.h','dialogue_font'))
 border=(C.c_uint8*64)(*arrays(assets/'pickup_assets.h','pickup_border'))
 semantics=(C.c_uint8*8)(*range(8));pixels=(C.c_uint8*76800)();row=(C.c_uint8*200)();cases=0;seen=set()
 for bits in range(512):
  page=lib.v6_save_page(bits)
  if page.state not in (0,6) or page.last_summary or bytes(page) in seen:continue
  seen.add(bytes(page))
  for label in (b'Space',b'Fire',b'12345678'):
   lib.save_pixels(bits,label,pixels)
   for y in range(240):
    assert lib.v6_save_draw_row(row,y,C.byref(page),font,border,semantics,b'V Stitch',label)
    for x in range(320):
     actual=sum(((row[p*40+x//8]>>(7-x%8))&1)<<p for p in range(5))
     assert actual==pixels[y*320+x],(bits,label,x,y,actual,pixels[y*320+x])
   cases+=1
 for page,label,y in [(Page(1,1,0),b'Space',0),(Page(0,1,1),b'Space',0),(Page(0,1,0),b'',0),(Page(0,1,0),b'123456789',0),(Page(0,1,0),b'Space',240)]:
  before=bytes(row);assert not lib.v6_save_draw_row(row,y,C.byref(page),font,border,semantics,b'V Stitch',label) and bytes(row)==before
 print(f'PASS Save drawing: {cases} source pages, {cases*76800} source pixels, original Font.cpp wrapping; rejected unadmitted receipt/summary and invalid inputs')
if __name__=='__main__':main()
