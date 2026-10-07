#!/usr/bin/env python3
"""Teleporter masks and six-channel DMA against source alpha pixels."""
import ctypes as C
import subprocess
from pathlib import Path
from test_player import ROOT, BUILD
ASSETS=ROOT/'build/amiga-feasibility'
Row=C.c_uint16*6
Frame=Row*96

def masks():
    dimensions,rgba=subprocess.check_output([str(ASSETS/'png_rgba'),str(ASSETS/'teleporter.png')]).split(b'\n',1)
    assert dimensions==b'960 96'
    return [[[(rgba[(y*960+f*96+x)*4+3]!=0) for x in range(96)] for y in range(96)] for f in range(10)]

def main():
    frames=masks();converted=[]
    for pixels in frames:
        converted.append(Frame(*[Row(*[sum(pixels[y][c*16+x]<<(15-x) for x in range(16)) for c in range(6)]) for y in range(96)]))
    # Use the converter's generated C data independently of the source masks.
    path=BUILD/'teleporter_draw_fixture.c';path.write_text('#include <stdint.h>\n#include "teleporter_assets.h"\nconst void *asset(unsigned f){return teleporter_masks[f];}\n')
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ASSETS),
        str(ROOT/'amiga_version/teleporter_draw.c'),str(path),'-o',str(BUILD/'teleporter_draw.so')],check=True)
    core=C.CDLL(str(BUILD/'teleporter_draw.so'));core.asset.restype=C.POINTER(Frame)
    core.v6_teleporter_draw.argtypes=[C.POINTER(C.c_uint16),C.POINTER(Row),C.POINTER(Row),C.c_int,C.c_int]
    for f in range(10): assert bytes(core.asset(f).contents)==bytes(converted[f])
    cases=0
    for f in range(1,10):
        for x in (-96,-95,-17,-16,-15,-1,0,112,225,305,319,320):
            for y in (-96,-80,-79,0,15,16,48,121,215,216):
                storage=(C.c_uint16*(6*196+2))(*([0xdead]*(6*196+2)))
                dma=C.cast(C.byref(storage,2),C.POINTER(C.c_uint16))
                assert core.v6_teleporter_draw(dma,core.asset(0).contents,core.asset(f).contents,x,y)
                assert storage[0]==storage[-1]==0xdead
                actual={}
                for c in range(6):
                    d=dma[c*196:(c+1)*196]
                    if d[:2]==[0,0]:continue
                    start=(d[0]>>8)|((d[1]&4)<<6);stop=(d[1]>>8)|((d[1]&2)<<7)
                    left=((d[0]&255)<<1)|(d[1]&1);left-=128
                    for row in range(stop-start):
                        a,b=d[2+row*2:4+row*2]
                        for bit in range(16):
                            colour=((a>>(15-bit))&1)|(((b>>(15-bit))&1)<<1)
                            if colour:actual[left+bit,start-52+row]=colour
                    assert d[2+(stop-start)*2:4+(stop-start)*2]==[0,0]
                expected={(x+sx,y+sy):2 if frames[f][sy][sx] else 1
                    for sy in range(96) for sx in range(96)
                    if 0<=x+sx<320 and 16<=y+sy<216 and (frames[f][sy][sx] or frames[0][sy][sx])}
                assert actual==expected,(f,x,y)
                cases+=1
    dma=(C.c_uint16*(6*196))(*([0xdead]*(6*196)))
    for x,y in ((32768,0),(-32769,0),(0,32768),(0,-32769)):
        assert not core.v6_teleporter_draw(dma,converted[0],converted[1],x,y)
        assert set(dma)=={0xdead}
    print(f'PASS teleporter draw: 10 source masks, {cases} clipping/DMA compositions, guard words and invalid-input preservation')
if __name__=='__main__':main()
