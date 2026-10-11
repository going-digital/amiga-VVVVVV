#!/usr/bin/env python3
"""Source simple-loop animation, private masks and pixel damage comparisons."""
import ctypes as C
import re,random,subprocess
from test_player import ROOT,Player,block
from test_prize_return_actors import Bank
class Animation(C.Structure):
    _fields_=[(n,C.c_int) for n in ('delay','walk','frame')]

def main():
    out=ROOT/'build/amiga-feasibility'
    header=(out/'prize_return_sprite_assets.h').read_text()
    def masks(name):
        raw=re.search(name+r'\[\d+\]\[32\]=\{(.*?)\};',header,re.S)[1]
        return [[int(v.removesuffix('UL'),16) for v in row.split(',')] for row in re.findall(r'\{([^}]+)\}',raw)]
    player=masks('return_player_collision');enemy=masks('return_enemy_collision');visible=masks('return_enemy_visible')
    assert len(player)==16 and len(enemy)==len(visible)==4
    assert all(len(row)==32 for row in player+enemy+visible)
    assert all(not (row&65535) for frame in visible for row in frame)
    assert all(not row for frame in visible for row in frame[16:])
    dimensions,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'tower_sprites.png')]).split(b'\n',1)
    width,height=map(int,dimensions.split());pixels=0
    for tiles,rows,collision in ((range(16),player,True),(range(92,96),enemy,True),(range(92,96),visible,False)):
        for tile,mask in zip(tiles,rows):
            ox=tile%(width//32)*32;oy=tile//(width//32)*32
            for y in range(32):
                for x in range(32):
                    pixel=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                    expected=bool(pixel[0]) if collision else pixel[3]>127 and max(pixel[:3])>0
                    assert bool(mask[y] & (1<<(31-x)))==expected,(tile,x,y,collision)
                    pixels+=1
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    start=entity.index('            case 1:',entity.index('void entityclass::animateentities('))
    animation=entity[start:entity.index('            case 2:',start)]
    graphics=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    hit=block(graphics,graphics.index('bool Graphics::Hitest('))
    source=r'''#include <SDL3/SDL.h>
#include <vector>
struct Ent {int framedelay=0,walkingframe=0,drawframe=0,tile=92;};
std::vector<Ent> entities(1);int _i=0;
extern "C" void animate(int stopped,int *out) {
if(!stopped)switch(1) {
'''+animation+r'''}
out[0]=entities[0].framedelay;out[1]=entities[0].walkingframe;
out[2]=entities[0].drawframe ? entities[0].drawframe-92 : -1;
}
struct Help {bool intersects(SDL_Rect a,SDL_Rect b){return SDL_HasRectIntersection(&a,&b);}} help;
struct MaskSurface {int w=32,h=32;const uint32_t *rows;};
#define SDL_Surface MaskSurface
struct Graphics {
SDL_Color ReadPixel(MaskSurface *s,int x,int y) {return {static_cast<Uint8>((s->rows[y]>>(31-x))&1),0,0,0};}
bool Hitest(SDL_Surface*,SDL_Point,SDL_Surface*,SDL_Point);
};
'''+hit+r'''
extern "C" int hurt(const uint32_t *a,int ax,int ay,const uint32_t *b,int bx,int by) {
SDL_Rect player={ax+6,ay+2,12,21},enemy={bx,by,16,16};
if(!SDL_HasRectIntersection(&player,&enemy))return 0;
MaskSurface aa,bb;aa.rows=a;bb.rows=b;Graphics g;
return g.Hitest(&aa,{ax,ay},&bb,{bx,by});
}
'''
    path=out/'return_sprite_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-I/opt/homebrew/include',str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(out/'return_sprite_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/(n+'.c')) for n in ('prize_return_sprite','player','pixel_collision','blocks','terrain')],
        '-o',str(out/'return_sprite.so')],check=True)
    core=C.CDLL(str(out/'return_sprite.so'));ref=C.CDLL(str(out/'return_sprite_reference.so'))
    core.v6_return_enemy_animation_init.argtypes=[C.POINTER(Animation)]
    core.v6_return_enemy_animation_tick.argtypes=[C.POINTER(Animation),C.c_int]
    wp=C.POINTER(C.c_uint32)
    core.v6_prize_return_pixel_hurt.argtypes=[C.POINTER(Bank),C.POINTER(Player),wp,wp,wp]
    ref.hurt.argtypes=[wp,C.c_int,C.c_int,wp,C.c_int,C.c_int]
    ref.animate.argtypes=[C.c_int,C.POINTER(C.c_int)]
    rng=random.Random(443480);anim=Animation();core.v6_return_enemy_animation_init(C.byref(anim))
    for tick in range(4096):
        stopped=tick<3 or rng.randrange(5)==0
        wanted=(C.c_int*3)();ref.animate(stopped,wanted)
        core.v6_return_enemy_animation_tick(C.byref(anim),stopped)
        assert (anim.delay,anim.walk,anim.frame)==tuple(wanted),(tick,anim.delay,anim.walk,anim.frame,tuple(wanted))
    bank=Bank();bank.enemy_count=2
    for i in range(2):
        bank.enemies[i].x=80+i*24;bank.enemies[i].y=80
        bank.enemies[i].w=bank.enemies[i].h=16
    p=Player();comparisons=box_only=hits=0
    for frame in range(16):
        a=(C.c_uint32*32)(*player[frame])
        for ef in range(4):
            b=(C.c_uint32*32)(*enemy[ef]);c=(C.c_uint32*32)(*enemy[(ef+1)&3])
            for x in range(58,123):
                for y in range(54,100):
                    p.x=x;p.y=y
                    wanted=ref.hurt(a,x,y,b,80,80) or ref.hurt(a,x,y,c,104,80)
                    actual=core.v6_prize_return_pixel_hurt(C.byref(bank),C.byref(p),a,b,c)
                    assert bool(actual)==bool(wanted),(frame,ef,x,y)
                    broad=(x>-18+80 and x<16-6+80 and y>-23+80 and y<16-2+80) or (x>-18+104 and x<16-6+104 and y>-23+80 and y<16-2+80)
                    box_only+=bool(broad and not actual);hits+=bool(actual);comparisons+=1
    assert box_only and hits
    print(f'PASS return sprites: {pixels} original PNG mask pixels, 4096 extracted animation ticks, {comparisons} source Hitest damage comparisons; {box_only} bounding-box-only contacts correctly harmless')
if __name__=='__main__':main()
