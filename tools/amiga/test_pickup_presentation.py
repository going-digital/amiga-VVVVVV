#!/usr/bin/env python3
"""Pickup geometry, alpha borders, words and bars against extracted source."""
import ctypes as C
import subprocess
from pathlib import Path
from test_music_control import method

ROOT=Path(__file__).resolve().parents[2]
class Draw(C.Structure):
    _fields_=[('bars',C.c_int),('old_bars',C.c_int)]+[(n,C.c_uint) for n in ('count','length','x','width')]+[('text',C.c_char*37)]

def main():
    out=ROOT/'build/amiga-pickup-presentation';out.mkdir(parents=True,exist_ok=True)
    graphics=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    textbox=(ROOT/'desktop_version/src/Textbox.cpp').read_text()
    utility=(ROOT/'desktop_version/src/UtilityClass.cpp').read_text()
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    source=r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#define SDL_min std::min
template<typename A,typename B>auto sdl_max(A a,B b)->decltype(a+b){
 using T=decltype(a+b);return std::max<T>((T)a,(T)b);}
#define SDL_max sdl_max
#define SCREEN_WIDTH_CHARS 40
#define INBOUNDS_VEC(i,v) ((i)>=0 && (size_t)(i)<(v).size())
namespace loc {std::string lang="en";const char *gettext(const char *s){return s;}
 std::string getnumber(int n,const char*){return std::to_string(n);}}
std::string String(int n){return std::to_string(n);}
namespace font {
 int len(int,const char *s){return std::strlen(s)*8;}int height(int){return 8;}
 bool is_rtl(int){return false;}
 void glyph_dimensions(int,uint8_t *w,uint8_t*){*w=8;}
}
struct UtilityClass {std::string number_words(int,const char*);};
NUMBER
UtilityClass help;
struct textboxclass {
 std::vector<std::string> lines;int w=0,h=0,linegap=1,print_flags=0,xp=0,yp=0,other_textbox_index=-1;
 void resize();void pad(size_t,size_t);void padtowidth(size_t);void centertext();
 void wrap(int){std::string s=lines[0];lines.clear();size_t start=0,end;
   do{end=s.find('\n',start);lines.push_back(s.substr(start,end-start));start=end+1;}
   while(end!=std::string::npos);
   for(auto &line:lines)assert(line.size()<=34);resize();}
};
RESIZE
PAD
PADWIDTH
CENTER
uint8_t pixels[320*240],glyphs[128][8],tiles[8][8];
struct Graphics {
 std::vector<textboxclass> textboxes;bool showcutscenebars=false;
 int cutscenebarspos=0,oldcutscenebarspos=0;
 void cutscenebarstimer();void cutscenebars();
 void fill_rect(int x,int y,int w,int h,int,int,int){
   for(int yy=std::max(y,0);yy<std::min(y+h,240);++yy)
     for(int xx=std::max(x,0);xx<std::min(x+w,320);++xx)pixels[yy*320+xx]=4;
 }
 void drawcoloredtile(int x,int y,int t,int,int,int){
   for(int yy=0;yy<8;++yy)for(int xx=0;xx<8;++xx)
     if(tiles[t-40][yy]&(128>>xx))pixels[(y+yy)*320+x+xx]=5;
 }
 void drawpixeltextbox(int,int,int,int,int,int,int);
} graphics;
int lerp(int,int b){return b;}
BOX
BARTIMER
BARS
struct Game {int count;int trinkets(){return count;}} game;
struct Map {bool custommode=false;} map;
struct Custom {int numtrinkets(){return 20;}} cl;
void vformat_buf(char *out,size_t capacity,const char*,const char*,int n,int max){
 std::string text=help.number_words(n,"wordy")+" out of "+help.number_words(max,"wordy");
 assert(text.size()<capacity);std::strcpy(out,text.c_str());
}
FIRST
SECOND
extern "C" {
 void setup(const uint8_t *f,const uint8_t *t){std::memcpy(glyphs,f,1024);std::memcpy(tiles,t,64);}
 void render(int count,uint8_t *out){
   std::fill(pixels,pixels+320*240,0);game.count=count;
   graphics.textboxes=std::vector<textboxclass>(2);
   foundtrinket_textbox1(&graphics.textboxes[0]);graphics.textboxes[0].yp=85;
   graphics.textboxes[1].other_textbox_index=0;foundtrinket_textbox2(&graphics.textboxes[1]);
   for(auto &b:graphics.textboxes){b.resize();b.xp=160-b.w/2;
     graphics.drawpixeltextbox(b.xp,b.yp,b.w,b.h,174,174,174);
     for(size_t line=0;line<b.lines.size();++line)for(size_t ch=0;ch<b.lines[line].size();++ch)
       for(int y=0;y<8;++y)for(int x=0;x<8;++x)
         if(glyphs[(unsigned char)b.lines[line][ch]][y]&(128>>x))
           pixels[(b.yp+8+line*9+y)*320+b.xp+8+ch*8+x]=5;
   }
   std::memcpy(out,pixels,sizeof(pixels));
 }
 const char *words(int count){static std::string s;s=help.number_words(count,"wordy")+" out of Twenty";return s.c_str();}
 void bar_reset(){graphics.cutscenebarspos=graphics.oldcutscenebarspos=0;}
 void bar_tick(int show,int *out){graphics.showcutscenebars=show;graphics.cutscenebarstimer();
   out[0]=graphics.cutscenebarspos;out[1]=graphics.oldcutscenebarspos;}
 void bar_pixels(int pos,uint8_t *out){std::fill(pixels,pixels+320*240,0);
   graphics.showcutscenebars=true;graphics.cutscenebarspos=pos;graphics.cutscenebars();
   std::memcpy(out,pixels,sizeof(pixels));}
}
'''
    replacements={
        'NUMBER':method(utility,'std::string UtilityClass::number_words('),
        'RESIZE':method(textbox,'void textboxclass::resize('),
        'PAD':method(textbox,'void textboxclass::pad('),
        'PADWIDTH':method(textbox,'void textboxclass::padtowidth('),
        'CENTER':method(textbox,'void textboxclass::centertext('),
        'BOX':method(graphics,'void Graphics::drawpixeltextbox('),
        'BARTIMER':method(graphics,'void Graphics::cutscenebarstimer('),
        'BARS':method(graphics,'void Graphics::cutscenebars('),
        'FIRST':method(game,'void foundtrinket_textbox1('),
        'SECOND':method(game,'void foundtrinket_textbox2(')}
    # Replace whole placeholder lines so tokens inside source methods remain literal.
    source='\n'.join(replacements.get(line,line) for line in source.splitlines())
    ref_path=out/'reference.cpp';ref_path.write_text(source)
    inc='-I'+str(ROOT/'amiga_version')
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',inc,
                    str(ref_path),'-o',str(out/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',inc,
                    str(ROOT/'amiga_version/pickup_draw.c'),str(ROOT/'amiga_version/pickup_copper.c'),
                    '-o',str(out/'core.so')],check=True)
    core,ref=C.CDLL(str(out/'core.so')),C.CDLL(str(out/'reference.so'))
    core.v6_pickup_draw_init.argtypes=[C.POINTER(Draw)]
    core.v6_pickup_draw_count.argtypes=[C.POINTER(Draw),C.c_uint]
    core.v6_pickup_draw_tick.argtypes=[C.POINTER(Draw),C.c_int]
    core.v6_pickup_text_row.argtypes=[C.POINTER(Draw),C.c_uint,*([C.c_void_p]*4)]
    core.v6_pickup_bar_row.argtypes=[C.c_void_p,C.c_uint,C.c_int]
    core.v6_pickup_compose_row.argtypes=[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
    ref.words.restype=C.c_char_p
    font=(C.c_uint8*1024)(*((i*73+19)&255 if i//8!=32 else 0 for i in range(1024)))
    border=(C.c_uint8*64)(*((i*91+31)&255 for i in range(64)))
    ref.setup(font,border)
    s=Draw();core.v6_pickup_draw_init(C.byref(s))
    mask,ink=(C.c_uint8*42)(),(C.c_uint8*42)();pixels=(C.c_uint8*(320*240))()
    fg=(C.c_uint16*40)(*((i*12373+51)&65535 for i in range(40)));composite=(C.c_uint16*60)()
    checks=0
    for count in range(101):
        assert core.v6_pickup_draw_count(C.byref(s),count)
        assert s.text==ref.words(count) and s.width==(len(s.text)+4)*8
        ref.render(count,pixels)
        for row in range(76):
            mask[:]=ink[:]=[0xaa]*42
            assert core.v6_pickup_text_row(C.byref(s),row,C.byref(mask,1),C.byref(ink,1),font,border)
            assert mask[0]==mask[41]==ink[0]==ink[41]==0xaa
            aligned_mask=(C.c_uint16*20).from_buffer_copy(bytes(mask[1:41]))
            aligned_ink=(C.c_uint16*20).from_buffer_copy(bytes(ink[1:41]))
            core.v6_pickup_compose_row(composite,20,fg,20,aligned_mask,aligned_ink)
            raw=C.string_at(composite,120);fg_raw=C.string_at(fg,80)
            for x in range(320):
                m=(mask[1+x//8]>>(7-x%8))&1;k=(ink[1+x//8]>>(7-x%8))&1
                assert (4+m*k if m else 0)==pixels[(85+row)*320+x]
                actual=sum(((raw[p*40+x//8]>>(7-x%8))&1)<<p for p in range(3))
                original=sum(((fg_raw[p*40+x//8]>>(7-x%8))&1)<<p for p in range(2))
                assert actual==(4+k if m else original)
                checks+=1
    before=bytes(s)
    assert not core.v6_pickup_draw_count(C.byref(s),101) and bytes(s)==before
    for pos in range(362):
        ref.bar_pixels(pos,pixels)
        for bottom in (0,1):
            assert core.v6_pickup_bar_row(mask,pos,bottom)
            for x in range(320):
                assert bool(mask[x//8]&(128>>(x%8)))==bool(pixels[(224 if bottom else 0)*320+x])
    ref.bar_reset();core.v6_pickup_draw_init(C.byref(s));expected=(C.c_int*2)()
    for show in [1]*22+[0]*22+[1]*7+[0]*22:
        ref.bar_tick(show,expected);core.v6_pickup_draw_tick(C.byref(s),show)
        assert (s.bars,s.old_bars)==tuple(expected)
    mask[:]=[0xaa]*42;ink[:]=[0xaa]*42
    assert not core.v6_pickup_text_row(C.byref(s),76,mask,ink,font,border)
    assert bytes(mask)==bytes(ink)==bytes([0xaa])*42
    assert not core.v6_pickup_bar_row(mask,362,0) and bytes(mask)==bytes([0xaa])*42
    core.v6_pickup_bar_column.argtypes=[C.c_void_p,C.c_void_p,C.c_uint16,C.c_uint]
    fg=(C.c_uint16*10240)(*[(i*73+19)&65535 for i in range(10240)])
    for y in range(256):
        for bits in (0,65535,0x8000,0x07ff):
            dest=(C.c_uint16*960)(*([0xaaaa]*960));expected=list(dest)
            x=y%20;rows=min(16,256-y)
            core.v6_pickup_bar_column(C.byref(dest,x*2),C.byref(fg,(y*20+x)*2),bits,rows)
            if rows<16:
                core.v6_pickup_bar_column(C.byref(dest,(rows*20+x)*2),C.byref(fg,x*2),bits,16-rows)
            for row in range(16):
                src=((y+row)&255)*20+x;at=row*20+x
                expected[at]=fg[src]&~bits;expected[320+at]=fg[5120+src]&~bits
                expected[640+at]=bits
            assert list(dest)==expected,(y,bits)
    maximum,copper_checks=check_copper(core)
    print(f'PASS pickup presentation: {checks} source textbox/composite pixels, 101 source English counts, 362 source bar widths, source bar timer, {copper_checks} Copper plans; maximum {maximum}/176 words')

def check_copper(core):
    core.v6_pickup_copper.argtypes=[C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint,C.c_uint,C.c_uint32,C.c_uint32,C.c_int,C.c_uint]
    buf=(C.c_uint16*178)();maximum=cases=0
    for fo in (0,17,239,255):
        for text in (0,1):
            cached={}
            for bars in range(362):
                n=core.v6_pickup_copper(buf,0x10000,0x20000,fo,255-fo,0x30000,0x40000,text,bars)
                key=(fo,255-fo,text,bars>0,bars>40);segment=tuple(buf[:n])
                if key in cached:assert cached[key]==segment,(key,bars)
                cached[key]=segment
    for fo in range(256):
        bo=(fo*73+29)&255
        for text in (0,1):
            for bars in (0,25,41,175,320,361):
                buf[:]=[0xaaaa]*178
                n=core.v6_pickup_copper(buf,0x10000,0x20000,fo,bo,0x30000,0x40000,text,bars)
                assert 0<n<=176 and list(buf[n-2:n])==[0xffff,0xfffe]
                assert list(buf[176:])==[0xaaaa]*2
                maximum=max(maximum,n);events=[];line=epoch=0
                for i in range(0,n-2,2):
                    r,v=buf[i:i+2]
                    if r&1:
                        if r==0xffdf:epoch=256;line=255
                        else:line=(r>>8)+epoch
                    else:events.append((line,r,v))
                regs={0x100:0x3600,0x104:0x24};at=0
                for y in range(240):
                    while at<len(events) and events[at][0]<52+y:
                        _,r,v=events[at];regs[r]=v;at+=1
                    strip=(0,16,0) if bars and y<16 else (85,76,1920) if text and 85<=y<161 else (224,16,11040) if bars>40 and y>=224 else None
                    expected={0xe4:0x20000+((bo+y)&255)*40}
                    if strip:
                        top,h,offset=strip;base=0x30000+offset+(y-top)*40
                        expected.update({0xe0:base,0xe8:base+h*40,0xf0:base+2*h*40,0xec:0x40000+(y-top)*40})
                        assert regs[0x100]==0x5600 and regs[0x104]==0x20
                        assert regs[0x188]==(0x222 if top==85 else 0) and regs[0x18a]==0xaaa
                    else:
                        expected.update({0xe0:0x10000+((fo+y)&255)*40,0xe8:0x12800+((fo+y)&255)*40})
                        assert regs[0x100]==0x3600 and regs[0x104]==0x24
                    for r,address in expected.items():assert (regs[r]<<16|regs[r+2])==address,(fo,bo,y,r,regs,address)
                    for r in ((0xe0,0xe4,0xe8,0xec,0xf0) if strip else (0xe0,0xe4,0xe8)):
                        address=(regs[r]<<16|regs[r+2])+40;regs[r]=address>>16;regs[r+2]=address&65535
                cases+=1
    for fg,bg,fo,bo,bank,zero,text,bars in ((1,0x20000,0,0,0x30000,0x40000,1,361),
        (0x10000,0x20000,256,0,0x30000,0x40000,1,361),
        (0x10000,0x20000,0,0,0x30001,0x40000,1,361),
        (0x10000,0x20000,0,0,0x30000,0x40001,1,361),
        (0x10000,0x20000,0,0,0x30000,0x40000,2,361),
        (0x10000,0x20000,0,0,0x30000,0x40000,1,362),
        (0x10000,0x20000,0,0,0x1000000-12958,0x40000,1,361)):
        buf[:]=[0xaaaa]*178
        assert not core.v6_pickup_copper(buf,fg,bg,fo,bo,bank,zero,text,bars)
        assert list(buf)==[0xaaaa]*178
    return maximum,cases

if __name__=='__main__':main()
