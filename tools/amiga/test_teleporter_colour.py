#!/usr/bin/env python3
"""Integer OCS flashing colour against actual Graphics.cpp colour 102."""
import ctypes as C
import random
import subprocess
from test_player import ROOT,BUILD

def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
    begin=source.index('    case 102: // Teleporter in action!')
    case=source[begin:source.index('\n    }\n\n    return getRGB',begin)]
    code='''#include <stdint.h>
struct RGB {uint8_t r,g,b;};
RGB getRGB(uint8_t r,uint8_t g,uint8_t b){return {r,g,b};}
struct {bool noflashingmode;} game;
const uint16_t *samples;unsigned at;
double next(){return samples[at++]/65536.0;}
#define GETCOL_RANDOM (game.noflashingmode?0.5:next())
RGB colour(){switch(102){
'''+case+'''
}return {255,255,255};}
extern "C" unsigned reference(const uint16_t *r,int noflash) {
samples=r;at=0;game.noflashingmode=noflash;RGB c=colour();
return ((c.r>>4)<<8)|((c.g>>4)<<4)|(c.b>>4);
}
'''
    path=BUILD/'teleporter-colour-reference.cpp';path.write_text(code)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined',
        '-fno-sanitize-recover=all']
    subprocess.run(['c++','-std=c++11',*flags,str(path),'-o',str(BUILD/'teleporter-colour-reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-I'+str(ROOT/'amiga_version'),
        str(ROOT/'amiga_version/teleporter_colour.c'),'-o',str(BUILD/'teleporter-colour.so')],check=True)
    core=C.CDLL(str(BUILD/'teleporter-colour.so'));ref=C.CDLL(str(BUILD/'teleporter-colour-reference.so'))
    core.v6_teleporter_flash_colour.argtypes=ref.reference.argtypes=[C.POINTER(C.c_uint16),C.c_int]
    core.v6_teleporter_flash_colour.restype=C.c_uint16
    return core,ref

def main():
    core,ref=libraries();cases=0;r=(C.c_uint16*4)()
    def check():
        assert core.v6_teleporter_flash_colour(r,0)==ref.reference(r,0),tuple(r)
    # Every branch threshold and channel rounding input, then mixed samples.
    for i in range(65536):
        r[:]=[i,0,32768,65535];check();cases+=1
    for branch in (0,20000,35000,65535):
        for i in range(65536):
            r[:]=[branch,i,i,i];check();cases+=1
    rng=random.Random(102)
    for i in range(10000):
        r[:]=[rng.randrange(65536) for _ in range(4)];check();cases+=1
        assert core.v6_teleporter_flash_colour(r,1)==ref.reference(r,1)==0xccd
    assert core.v6_teleporter_flash_colour(None,0)==0xccd
    assert core.v6_teleporter_flash_colour(None,1)==0xccd
    print(f'PASS teleporter colour: {cases} extracted source/OCS comparisons, all branch/channel thresholds, fixed noflashing colour and NULL fallback')
if __name__=='__main__':main()
