#!/usr/bin/env python3
"""English hint geometry, border pixels, fade palette and Copper DMA schedule."""
import ctypes as C
import random,subprocess
from test_player import ROOT
from test_music_control import method

def main():
    out=ROOT/'build/amiga-vstitch-hint-draw';out.mkdir(parents=True,exist_ok=True)
    graphics=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    textbox=(ROOT/'desktop_version/src/Textbox.cpp').read_text()
    fonts=(ROOT/'desktop_version/src/Font.cpp').read_text()
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    assert 'textbox_colours["gray"] = graphics.getRGB(174, 174, 174)' in (ROOT/'desktop_version/src/Script.cpp').read_text()
    source=r'''
#include <SDL3/SDL.h>
#include <algorithm>
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#define SCREEN_WIDTH_CHARS 40
struct Lang {bool autowordwrap=true;} lang;
namespace loc {Lang *get_langmeta(){return &lang;}const char *gettext(const char *s){return s;}}
uint32_t UTF8_peek_next(const char *s,uint8_t *n){*n=1;assert((unsigned char)*s<128);return (unsigned char)*s;}
namespace font {
struct Font {} f;struct PrintFlags {Font *font_sel=&f;};
PrintFlags decode_print_flags(uint32_t){return {};}
int get_advance(Font*,uint32_t){return 8;}
int len(int,const char *s){return std::strlen(s)*8;}int height(int){return 8;}
bool is_rtl(int){return false;}void glyph_dimensions(int,uint8_t *w,uint8_t*){*w=8;}
NEXT
std::string string_wordwrap(uint32_t,const std::string&,int,short *lines=NULL);
WRAPSTRING
BALANCED
}
struct textboxclass {
 std::vector<std::string> lines;int w=0,h=0,linegap=1,print_flags=0;
 void resize();void pad(size_t,size_t);void padtowidth(size_t);void centertext();void wrap(int);
 void addline(const std::string& s){lines.push_back(s);resize();}
};
RESIZE
PAD
PADWIDTH
CENTER
WRAPBOX
const char *vformat_button(int,int){return "ENTER";}
void vformat_buf(char *out,size_t size,const char*,const char*,const char*){SDL_strlcpy(out,"Press ENTER to view map and quicksave",size);}
enum {ActionSet_InGame,Action_InGame_Map};
MAPTEXT
uint8_t pixels[320*240],glyphs[128][8],tiles[8][8];
struct Graphics {
 void fill_rect(int x,int y,int w,int h,int,int,int){for(int yy=y;yy<y+h;++yy)for(int xx=x;xx<x+w;++xx)pixels[yy*320+xx]=4;}
 void drawcoloredtile(int x,int y,int tile,int,int,int){for(int yy=0;yy<8;++yy)for(int xx=0;xx<8;++xx)if(tiles[tile-40][yy]&(128>>xx))pixels[(y+yy)*320+x+xx]=5;}
 void drawpixeltextbox(int,int,int,int,int,int,int);
} graphics;
BOX
extern "C" void render(const uint8_t *font,const uint8_t *border,uint8_t *out,int *geometry){
std::memcpy(glyphs,font,1024);std::memcpy(tiles,border,64);std::memset(pixels,0,sizeof(pixels));
textboxclass box;map_textbox(&box);int x=160-box.w/2;geometry[0]=x;geometry[1]=box.w;geometry[2]=box.h;
graphics.drawpixeltextbox(x,155,box.w,box.h,174,174,174);
for(size_t line=0;line<box.lines.size();++line)for(size_t ch=0;ch<box.lines[line].size();++ch)
 for(int y=0;y<8;++y)for(int xx=0;xx<8;++xx)if(glyphs[(unsigned char)box.lines[line][ch]][y]&(128>>xx))
  pixels[(155+8+line*9+y)*320+x+8+ch*8+xx]=5;
std::memcpy(out,pixels,sizeof(pixels));
}
'''
    replacements={'NEXT':method(fonts,'static bool next_wrap('),
        'WRAPSTRING':method(fonts,'std::string string_wordwrap('),'BALANCED':method(fonts,'std::string string_wordwrap_balanced('),
        'RESIZE':method(textbox,'void textboxclass::resize('),'PAD':method(textbox,'void textboxclass::pad('),
        'PADWIDTH':method(textbox,'void textboxclass::padtowidth('),'CENTER':method(textbox,'void textboxclass::centertext('),
        'WRAPBOX':method(textbox,'void textboxclass::wrap('),'MAPTEXT':method(game,'static void map_textbox('),
        'BOX':method(graphics,'void Graphics::drawpixeltextbox(')}
    source='\n'.join(replacements.get(line,line) for line in source.splitlines())
    # Only log calls on unreachable malformed empty-text paths need stubbing.
    source='#define vlog_error(...) ((void)0)\n'+source
    (out/'reference.cpp').write_text(source)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++',*flags,'-I/opt/homebrew/include',str(out/'reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',str(ROOT/'amiga_version/vstitch_hint_draw.c'),str(ROOT/'amiga_version/vstitch_hint_copper.c'),'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));ref=C.CDLL(str(out/'reference.so'));bp=C.POINTER(C.c_uint8)
    core.v6_vstitch_hint_row.argtypes=[C.c_uint,bp,bp,bp,bp]
    core.v6_vstitch_hint_colours.argtypes=[C.c_uint]*3;core.v6_vstitch_hint_colours.restype=C.c_uint32
    ref.render.argtypes=[bp,bp,bp,C.POINTER(C.c_int)]
    rng=random.Random(443501);pixels=(C.c_uint8*(320*240))();geometry=(C.c_int*3)()
    for case in range(32):
        font=(C.c_uint8*1024)(*(0 if i//8==32 else rng.randrange(256) for i in range(1024)))
        border=(C.c_uint8*64)(*(rng.randrange(256) for _ in range(64)))
        ref.render(font,border,pixels,geometry);assert tuple(geometry)==(60,200,33),tuple(geometry)
        for row in range(33):
            mask=(C.c_uint8*40)();ink=(C.c_uint8*40)()
            assert core.v6_vstitch_hint_row(row,mask,ink,font,border)
            for x in range(320):
                got=(4 if mask[x//8]&(128>>(x&7)) else 0)+(1 if ink[x//8]&(128>>(x&7)) else 0)
                assert got==pixels[(155+row)*320+x],(case,row,x,got,pixels[(155+row)*320+x])
        before=bytes(mask),bytes(ink)
        assert not core.v6_vstitch_hint_row(33,mask,ink,font,border) and before==(bytes(mask),bytes(ink))
    fades=0
    for previous in range(5,11):
        for level in range(max(5,previous-1),min(10,previous+1)+1):
            for phase in list(range(0,34001,17))+[34000,40000]:
                grey=int(174*(previous+(level-previous)*min(phase,34000)/34000)/10+1e-9)
                fill=(grey//6+8)//17;ink=(grey+8)//17
                assert core.v6_vstitch_hint_colours(previous,level,phase)==((fill*0x111)<<16)|(ink*0x111),(previous,level,phase)
                fades+=1
    for previous,level in ((0,5),(5,11),(5,7),(10,5)):assert not core.v6_vstitch_hint_colours(previous,level,100)
    wp=C.POINTER(C.c_uint16);core.v6_vstitch_hint_copper.argtypes=[wp]+[C.c_uint32]*8
    def schedule(fo,bo):
        buf=(C.c_uint16*104)(*([0xbeef]*104));n=core.v6_vstitch_hint_copper(C.cast(C.byref(buf,2),wp),0x10000,0x20000,fo,bo,0x30000,0x40000,0x111,0xaaa)
        assert 0<n<=100 and buf[0]==buf[n+1]==0xbeef
        events={};line=0;epoch=0
        for i in range(1,n+1,2):
            a,b=buf[i],buf[i+1]
            if a&1:
                if a==0xffff:break
                if a==0xffdf:line=255;epoch=256
                else:line=(a>>8)+epoch
            else:events.setdefault(line+1,[]).append((a,b))
        registers={0x100:0x3600,0x104:0x24};pointers={}
        for physical in range(45,292):
            for a,b in events.get(physical,[]):
                registers[a]=b
                if 0xe0<=a<=0xf2:
                    r=a&~3;pointers[r]=(registers.get(r,0)<<16)|registers.get(r+2,0)
            if physical<52:continue
            y=physical-52;hint=155<=y<188
            assert registers[0x100]==(0x5600 if hint else 0x3600),(fo,bo,y)
            assert pointers[0xe4]==0x20000+((bo+y)&255)*40,(fo,bo,y,'bg')
            if hint:
                for r,p in ((0xe0,0),(0xe8,1),(0xf0,2)):
                    assert pointers[r]==0x30000+p*3040+(y-155)*40,(fo,bo,y,r)
                assert pointers[0xec]==0x40000+(y-155)*40
            else:
                for r,p in ((0xe0,0),(0xe8,1)):assert pointers[r]==0x10000+p*10240+((fo+y)&255)*40,(fo,bo,y,r)
            active=(0xe0,0xe4,0xe8,0xec,0xf0) if hint else (0xe0,0xe4,0xe8)
            for r in active:pointers[r]+=40
    edges=(0,16,17,51,68,69,100,101,102,155,156,188,189,255)
    cases=set((f,b) for f in edges for b in edges)|set((f,0) for f in range(256))|set((0,b) for b in range(256))
    for fo,bo in cases:schedule(fo,bo)
    buf=(C.c_uint16*104)(*([0xbeef]*104));before=bytes(buf)
    for fg,bg,fo,bo,bank,zero,fill,ink in ((1,0x20000,0,0,0x30000,0x40000,0,0),(0x10000,0x20000,256,0,0x30000,0x40000,0,0),(0x10000,0x20000,0,0,0x30000,0xffffff,0,0),(0x10000,0x20000,0,0,0x30000,0x40000,0x1000,0)):
        assert not core.v6_vstitch_hint_copper(buf,fg,bg,fo,bo,bank,zero,fill,ink) and bytes(buf)==before
    print(f'PASS V Stitch hint drawing: {32*33*320} source box/font pixels, {fades} source-grey fade palettes, {len(cases)} complete DMA schedules and invalid-input immutability')
if __name__=='__main__':main()
