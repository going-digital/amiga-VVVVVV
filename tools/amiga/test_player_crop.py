#!/usr/bin/env python3
"""Prepared Prize player crop preserves original sprite DMA and clipping."""
import ctypes as C
import re,subprocess
from test_player import ROOT
class Sprites(C.Structure):
    _fields_=[('dma',C.POINTER(C.c_uint16)),('colours',C.c_uint16*8),('count',C.c_uint)]
def main():
    out=ROOT/'build/amiga-feasibility'
    header=(out/'tower_player_assets.h').read_text()
    def rows(name):
        data=re.search(name+r'\[\d+\]\[32\]=\{(.*?)\};',header,re.S)[1]
        return [[int(v.removesuffix('UL'),16) for v in r.split(',')] for r in re.findall(r'\{([^}]+)\}',data)]
    original=rows('tower_player_rows');prepared=rows('tower_player_cropped_rows')
    assert len(original)==23 and len(prepared)==16
    for frame in range(16):assert prepared[frame]==[((v>>10)&65535)<<16 for v in original[frame]]
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
                    '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/sprites.c'),
                    '-o',str(out/'player-crop.so')],check=True)
    core=C.CDLL(str(out/'player-crop.so'))
    core.v6_sprites_begin.argtypes=[C.POINTER(Sprites),C.POINTER(C.c_uint16)]
    core.v6_sprites_add.argtypes=[C.POINTER(Sprites),C.POINTER(C.c_uint32),C.c_int,C.c_int,C.c_uint,C.c_uint]
    count=0
    for frame in range(16):
        a=(C.c_uint32*32)(*original[frame]);b=(C.c_uint32*32)(*prepared[frame])
        for x in (-30,-23,-22,-17,-16,-7,-6,-1,0,10,289,298,303,304,308,319,320):
            for y in (-20,-16,0,15,16,180,200,215,216,240):
                for channel in range(9):
                    dma1=(C.c_uint16*(8*68))();dma2=(C.c_uint16*(8*68))()
                    s1=Sprites();s2=Sprites();core.v6_sprites_begin(C.byref(s1),dma1);core.v6_sprites_begin(C.byref(s2),dma2)
                    s1.count=s2.count=channel
                    r1=core.v6_sprites_add(C.byref(s1),a,x,y,6,0x6ff)
                    r2=core.v6_sprites_add(C.byref(s2),b,x+6,y,0,0x6ff)
                    assert r1==r2 and s1.count==s2.count and bytes(dma1)==bytes(dma2) and bytes(s1.colours)==bytes(s2.colours),(frame,x,y,channel)
                    count+=1
    print(f'PASS prepared player crop: {count} identical DMA/colour/allocator results across 16 frames, viewport clipping and channel parity/full allocation')
if __name__=='__main__':main()
