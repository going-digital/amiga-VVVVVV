#!/usr/bin/env python3
"""Map/fog/box/tabs/cursor against extracted desktop render statements."""
import ctypes as C,json,re,subprocess,random
from test_player import ROOT
from test_music_control import method
from convert_map_assets import build
from convert_assets import DEFAULT_DATA

def arrays(path,name):
    return [int(v,0) for v in re.findall(r'0x[0-9a-fA-F]+|\d+',re.search(name+r'\[[^;]+?=\{(.*?)\};',path.read_text(),re.S)[1])]
def libraries():
    assets=ROOT/'build/amiga-feasibility';build(DEFAULT_DATA,assets)
    out=ROOT/'build/amiga-map-draw';out.mkdir(parents=True,exist_ok=True)
    render=(ROOT/'desktop_version/src/Render.cpp').read_text();graphics=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    fixed=(ROOT/'desktop_version/src/RenderFixed.cpp').read_text()
    prefix=render[render.index('void maprender(void)'):render.index('    // Draw menu header',render.index('void maprender(void)'))]+'}\n'
    cursor=fixed[fixed.index('    if (map.cursorstate == 0){'):fixed.index('    map.updateroomnames();',fixed.index('    if (map.cursorstate == 0){'))]
    shim=r'''
#include <cassert>
#include <cstring>
#include <string>
#include <cstdint>
extern "C" {
#include "map_draw.h"
}
#include "map_assets.h"
#include "dialogue_font.h"
#include "pickup_assets.h"
#define SCREEN_WIDTH_CHARS 40
const int PR_CEN=1,PR_CJK_LOW=2,PR_RTL_XFLIP=4,PR_FONT_INTERFACE=8,PR_FONT_LEVEL=16,PR_FONT_8X8=32,PR_FULLBOR=64;
struct Lang {std::string menu_select_tight="[{label}]";} lang;
namespace loc {Lang *get_langmeta(){return &lang;}const char *gettext(const char *s){return s;}
const char *gettext_roomname_special(const char *s){return s;}
const char *gettext_roomname(bool,int,int,const char *s,bool){return s;}}
void vformat_buf(char *b,size_t n,const char*,const char*,const char *s){std::string t="["+std::string(s)+"]";assert(t.size()+1<=n);std::strcpy(b,t.c_str());}
uint8_t pixels[320*240];
unsigned colour(int r,int g,int b){unsigned c=((r+8)/17<<8)|((g+8)/17<<4)|((b+8)/17);for(unsigned i=0;i<32;++i)if(map_palette[i]==c)return i;assert(r==16 && g==245 && b==245);return 17;}
void put(int x,int y,unsigned c){if(x>=0&&x<320&&y>=0&&y<240)pixels[y*320+x]=c;}
struct MapRenderData {int width=20,height=20,startx=0,starty=0,zoom=1,xoff=0,yoff=0,pixelsx=240,pixelsy=180;};
struct Map {bool custommode=false,customshowmm=false,roomname_special=false;int currentregion=0,cursorstate=0,cursordelay=0;
 char hiddenname[1]={0};const char *roomname="V Stitch";uint8_t explored[50];
 MapRenderData get_render_data(){return {};}
 bool isexplored(int x,int y){int n=x+y*20;return explored[n/8]&(1<<(n%8));}
} map;
struct Game {bool insecretlab=false,noflashingmode=false;int menupage=0,roomx=112,roomy=107;} game;
struct Script {bool running=false;} script;
struct Obj {bool flags[100]={false};} obj;
struct Help {int glow=0;} help;
enum {IMAGE_MINIMAP,IMAGE_CUSTOMMINIMAP,IMAGE_COVERED};
struct Graphics {bool flipmode=false,minimap_mounted=false;void *customminimaps[1]={nullptr};int menuTexture;
 void set_render_target(int){}void clear(){std::memset(pixels,0,sizeof(pixels));}
 void fill_rect(int x,int y,int w,int h,int r,int g,int b){unsigned c=colour(r,g,b);for(int yy=y;yy<y+h;++yy)for(int xx=x;xx<x+w;++xx)put(xx,yy,c);}
 void drawcoloredtile(int x,int y,int t,int r,int g,int b){unsigned c=colour(r,g,b);for(int yy=0;yy<8;++yy)for(int xx=0;xx<8;++xx)if(pickup_border[t-40][yy]&(128>>xx))put(x+xx,y+yy,c);}
 void drawimage(int id,int x,int y,bool){int w=id==IMAGE_COVERED?12:240,h=id==IMAGE_COVERED?9:180;const uint8_t *s=id==IMAGE_COVERED?map_covered:map_minimap;for(int yy=0;yy<h;++yy)for(int xx=0;xx<w;++xx)put(x+xx,y+yy,s[yy*w+xx]);}
 void drawpartimage(int,int,int,int,int){}void draw_region_image(int,int,int,int,int){}
 void draw_rect(int x,int y,int w,int h,int r,int g,int b){unsigned c=colour(r,g,b);for(int i=0;i<w;++i){put(x+i,y,c);put(x+i,y+h-1,c);}for(int i=0;i<h;++i){put(x,y+i,c);put(x+w-1,y+i,c);}}
 void drawpixeltextbox(int,int,int,int,int,int,int);void map_tab(int,const char*,bool);
} graphics;
namespace font {int height(int){return 8;}void print(int,int x,int y,const char *s,int r,int g,int b){int n=std::strlen(s);if(x==-1)x=160;x-=n*4;unsigned c=colour(r,g,b);for(int i=0;i<n;++i)for(int yy=0;yy<8;++yy)for(int xx=0;xx<8;++xx)if(dialogue_font[(unsigned char)s[i]][yy]&(128>>xx))put(x+i*8+xx,y+yy,c);}}
'''+method(graphics,'void Graphics::drawpixeltextbox(')+method(graphics,'void Graphics::map_tab(')+method(render,'static void draw_roomname_menu(')+method(render,'static void rendermap(void)')+method(render,'static void rendermapfog(void)')+method(render,'static void rendermapcursor(')+prefix+r'''
extern "C" int compare(const uint8_t *exploration){
 std::memcpy(map.explored,exploration,50);maprender();rendermap();rendermapfog();
 V6Exploration e;std::memcpy(e.rooms,exploration,50);uint8_t row[200],packed[200],fast[200];
 for(unsigned y=0;y<240;++y){assert(v6_map_draw_row(row,y,&e,map_minimap,map_covered,dialogue_font,pickup_border,map_ui_colours,"V Stitch"));
  assert(v6_map_draw_row_rle(packed,y,&e,map_minimap_rle,sizeof(map_minimap_rle),map_minimap_offsets,map_covered,dialogue_font,pickup_border,map_ui_colours,"V Stitch"));assert(std::memcmp(row,packed,200)==0);
  assert(v6_map_draw_template_row(fast,y,&e,map_template_rle,sizeof(map_template_rle),map_template_offsets,map_fog_bits));assert(std::memcmp(row,fast,200)==0);
  for(unsigned x=0;x<320;++x){unsigned c=0;for(unsigned p=0;p<5;++p)c|=((row[p*40+x/8]>>(7-x%8))&1)<<p;if(c!=pixels[y*320+x])return y*320+x+1;}}
 return 0;
}
extern "C" void reference_pixels(const uint8_t *exploration,uint8_t *out){std::memcpy(map.explored,exploration,50);maprender();rendermap();rendermapfog();std::memcpy(out,pixels,sizeof(pixels));}
extern "C" void cursor_tick(unsigned *state,unsigned *delay){map.cursorstate=*state;map.cursordelay=*delay;
'''+cursor+r'''
 *state=map.cursorstate;*delay=map.cursordelay;
}
extern "C" void cursor_pixels(int rx,int ry,unsigned state,unsigned delay,uint8_t *out){graphics.clear();game.roomx=rx;game.roomy=ry;map.cursorstate=state;map.cursordelay=delay;rendermapcursor(true);std::memcpy(out,pixels,sizeof(pixels));}
'''
    (out/'reference.cpp').write_text(shim)
    flags=['-O2','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),'-I'+str(assets)]
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror','-c',str(ROOT/'amiga_version/map_draw.c'),'-o',str(out/'core.o')],check=True)
    subprocess.run(['c++','-std=c++11',*flags,'-shared',str(out/'reference.cpp'),str(out/'core.o'),'-o',str(out/'reference.so')],check=True)
    return C.CDLL(str(out/'reference.so'))
def main():
    lib=libraries();bp=C.POINTER(C.c_uint8);up=C.POINTER(C.c_uint)
    lib.compare.argtypes=[bp];lib.cursor_tick.argtypes=[up,up];lib.v6_map_cursor_tick.argtypes=[up,up]
    lib.cursor_pixels.argtypes=[C.c_int,C.c_int,C.c_uint,C.c_uint,bp]
    lib.v6_map_cursor_rows.argtypes=[C.POINTER(C.c_uint32),C.c_uint,C.c_int,C.c_int,C.POINTER(C.c_int),C.POINTER(C.c_int)]
    lib.v6_map_cursor_mode.argtypes=[C.c_uint,C.c_uint,C.c_int]
    rng=random.Random(443501);maps=[bytes(50),bytes([255]*50)]+[bytes((1<<(i%8)) if b==i//8 else 0 for b in range(50)) for i in range(400)]+[rng.randbytes(50) for _ in range(16)]
    for i,m in enumerate(maps):assert lib.compare((C.c_uint8*50).from_buffer_copy(m))==0,i
    s=C.c_uint();d=C.c_uint();a=C.c_uint();b=C.c_uint();pixels=(C.c_uint8*76800)();rows=(C.c_uint32*32)();x=C.c_int();y=C.c_int()
    for tick in range(2000):
        lib.cursor_tick(C.byref(s),C.byref(d));lib.v6_map_cursor_tick(C.byref(a),C.byref(b))
        assert s.value==a.value
        mode=lib.v6_map_cursor_mode(a,b,0)
        wanted=2 if s.value==2 and d.value//15%2==0 else 1 if s.value==1 and d.value//4%2==0 else 0
        assert mode==wanted
    cases=0
    for rx in range(100,120):
      if rx==109:continue
      for ry in range(100,120):
       for state,delay in ((0,0),(1,0),(1,4),(2,31),(2,45)):
        mode=lib.v6_map_cursor_mode(state,delay,0);lib.cursor_pixels(rx,ry,state,delay,pixels)
        assert lib.v6_map_cursor_rows(rows,mode,rx,ry,C.byref(x),C.byref(y))
        for yy in range(9):
         for xx in range(12):assert bool(rows[yy]&(1<<(31-xx)))==bool(pixels[(y.value+yy)*320+x.value+xx])
        cases+=1
    assets=ROOT/'build/amiga-feasibility'
    data=assets/'map_assets.h'
    mini=(C.c_uint8*43200)(*arrays(data,'map_minimap'));fog=(C.c_uint8*108)(*arrays(data,'map_covered'))
    font=(C.c_uint8*1024)(*arrays(assets/'dialogue_font.h','dialogue_font'));border=(C.c_uint8*64)(*arrays(assets/'pickup_assets.h','pickup_border'))
    colours=(C.c_uint8*6)(*arrays(data,'map_ui_colours'));palette=(C.c_uint16*32)(*arrays(data,'map_palette'))
    assert 17 not in mini and 17 not in fog and 17 not in colours
    lib.v6_map_draw_row.argtypes=[bp,C.c_uint,bp,bp,bp,bp,bp,bp,C.c_char_p]
    row=(C.c_uint8*200)(*([0xa5]*200));e=(C.c_uint8*50)()
    for invalid_row,name in ((240,b'V Stitch'),(2,b'x'*37),(2,b'\xff')):
        assert not lib.v6_map_draw_row(row,invalid_row,e,mini,fog,font,border,colours,name)
        assert bytes(row)==bytes([0xa5]*200)
    for i in range(6):
        old=colours[i];colours[i]=32
        assert not lib.v6_map_draw_row(row,0,e,mini,fog,font,border,colours,b'V Stitch')
        assert bytes(row)==bytes([0xa5]*200);colours[i]=old
    rle_values=arrays(data,'map_minimap_rle');rle=(C.c_uint8*len(rle_values))(*rle_values)
    offsets=(C.c_uint16*181)(*arrays(data,'map_minimap_offsets'))
    lib.v6_map_draw_row_rle.argtypes=[bp,C.c_uint,bp,bp,C.c_uint,C.POINTER(C.c_uint16),bp,bp,bp,bp,C.c_char_p]
    def reject_rle(size=len(rle_values)):
        assert not lib.v6_map_draw_row_rle(row,21,e,rle,size,offsets,fog,font,border,colours,b'V Stitch')
        assert bytes(row)==bytes([0xa5]*200)
    old=rle[0]
    for count in (0,241,old-1):rle[0]=count;reject_rle()
    rle[0]=old;old=rle[1];rle[1]=32;reject_rle();rle[1]=old
    old=offsets[1];offsets[1]+=1;reject_rle();offsets[1]=old
    reject_rle(0)
    template_values=arrays(data,'map_template_rle');template=(C.c_uint8*len(template_values))(*template_values)
    template_offsets=(C.c_uint16*241)(*arrays(data,'map_template_offsets'))
    fog_masks=(C.c_uint16*45)(*arrays(data,'map_fog_bits'))
    lib.v6_map_draw_template_row.argtypes=[bp,C.c_uint,bp,bp,C.c_uint,C.POINTER(C.c_uint16),C.POINTER(C.c_uint16)]
    def reject_template(size=len(template_values),yy=21):
        assert not lib.v6_map_draw_template_row(row,yy,e,template,size,template_offsets,fog_masks)
        assert bytes(row)==bytes([0xa5]*200)
    reject_template(0);reject_template(yy=240)
    at=template_offsets[21];old=template[at]
    for count in (0,201):template[at]=count;reject_template()
    template[at]=old;old=template_offsets[22];template_offsets[22]+=1;reject_template();template_offsets[22]=old
    old=fog_masks[0];fog_masks[0]|=1;reject_template();fog_masks[0]=old
    before=bytes(rows),x.value,y.value
    for mode,rx,ry in ((3,112,107),(1,109,107),(1,99,107),(1,120,107),(1,112,99),(1,112,120)):
        assert not lib.v6_map_cursor_rows(rows,mode,rx,ry,C.byref(x),C.byref(y))
        assert (bytes(rows),x.value,y.value)==before
    wp=C.POINTER(C.c_uint16);lib.v6_map_copper.argtypes=[wp,C.c_uint32,wp,C.c_uint32,C.c_uint32]
    copper=(C.c_uint16*140)(*([0xa5a5]*140));schedules=0
    for bitmap in (0,0x10000,0x1000000-48000):
      for blank in (0,0x20000,0xfffffc):
       for cursor in (0,0x21000,0x1000000-136):
        n=lib.v6_map_copper(copper,bitmap,palette,blank,cursor);assert n==138 and copper[138]==0xa5a5
        regs=dict(zip(copper[:n-2:2],copper[1:n-2:2]))
        assert regs[0x100]==0x5200 and regs[0x104]==0x20 and regs[0x108]==regs[0x10a]==0
        for plane in range(5):
            ptr=regs[0xe0+plane*4]<<16|regs[0xe2+plane*4]
            for yy in range(240):assert ptr+yy*40==bitmap+plane*9600+yy*40
        assert [regs[0x180+i*2] for i in range(32)]==list(palette)
        schedules+=1
    before=bytes(copper)
    for bitmap,blank,cursor in ((1,0,0),(0x1000000-47998,0,0),(0,1,0),(0,0xffffff,0),(0,0,1),(0,0,0x1000000-134)):
        assert not lib.v6_map_copper(copper,bitmap,palette,blank,cursor) and bytes(copper)==before
    old=palette[31];palette[31]=0x1000
    assert not lib.v6_map_copper(copper,0,palette,0,0) and bytes(copper)==before;palette[31]=old
    print(f'PASS map display: {len(maps)*76800} source pixels for raw/RLE/packed paths, 400 one-room fog masks, {cases} source cursor placements, 2,000 timer updates, {schedules} full DMA schedules and invalid-output preservation')
if __name__=='__main__':main()
