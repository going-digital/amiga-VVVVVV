#!/usr/bin/env python3
"""Check software parallax against direct desktop-map pixel composition."""
import ctypes as C
import json
import re
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'build/amiga-feasibility'


def main():
    subprocess.run(['python3',str(ROOT/'tools/amiga/convert_tower_assets.py')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('tower_compose.c','tower_draw.c','tower_stream.c','room_codec.c')],
        '-o',str(OUT/'tower_compose.so')],check=True)
    lib=C.CDLL(str(OUT/'tower_compose.so'));bp=C.POINTER(C.c_uint8);wp=C.POINTER(C.c_uint16)
    lib.v6_tower_draw_row.argtypes=[bp,C.c_int,wp,bp,C.c_uint]
    lib.v6_tower_mask_row.argtypes=[bp,C.c_int,wp,bp,C.c_uint]
    lib.v6_tower_compose.argtypes=[bp,bp,bp,bp,C.c_uint,C.c_uint]
    atlas=(OUT/'tower_tiles.bin').read_bytes();masks=(OUT/'tower_masks.bin').read_bytes()
    native_atlas=(C.c_uint8*480).from_buffer_copy(atlas)
    native_masks=(C.c_uint8*240).from_buffer_copy(masks)
    # Verify opacity directly against source alpha and the desktop tile-zero skip.
    header,rgba=subprocess.check_output([str(OUT/'png_rgba'),str(OUT/'tiles3.png')]).split(b'\n',1)
    width,height=map(int,header.split())
    for t in range(30):
        for y in range(8):
            for x in range(8):
                alpha=rgba[((t//(width//8)*8+y)*width+t%(width//8)*8+x)*4+3]
                assert ((masks[t*8+y]>>(7-x))&1)==int(t!=0 and alpha==255)
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text()
    maps=[]
    for name,h in [('loadmap',700),('loadbackground',120)]:
        body=source[source.index('void towerclass::'+name+'('):]
        body=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
        body=re.sub(r'//[^\n]*|/\*.*?\*/','',body,flags=re.S)
        assert re.fullmatch(r'[\s\d,]+',body)
        tiles=[int(v) for v in body.split(',') if v.strip()];assert len(tiles)==40*h
        maps.append([tiles[y*40:y*40+40] for y in range(h)])
    rings=[(C.c_uint8*20480)() for _ in range(2)];mask=(C.c_uint8*10240)()
    guarded=(C.c_uint8*19202)(*([0xa5]*19202));dst=C.cast(C.byref(guarded,1),bp)
    cameras=(0,1,7,8,16,17,52,53,254,255,256,1919,1920,5599,5600,5601)
    checks=0
    for camera in cameras:
        positions=(camera,camera//2)
        for n,position in enumerate(positions):
            for row in range(position//8,position//8+32):
                tiles=(C.c_uint16*40)(*maps[n][row%len(maps[n])])
                assert lib.v6_tower_draw_row(rings[n],row,tiles,native_atlas,30)
                if n==0:assert lib.v6_tower_mask_row(mask,row,tiles,native_masks,30)
        assert lib.v6_tower_compose(dst,*rings,mask,camera&255,(camera//2)&255)
        assert guarded[0]==guarded[-1]==0xa5
        for y in range(240):
            fy=camera+y;by=camera//2+y
            for x in range(320):
                ft=maps[0][(fy//8)%700][x//8];bt=maps[1][(by//8)%120][x//8]
                bit=7-x%8;use_fg=(masks[ft*8+fy%8]>>bit)&1
                tile,ty=(ft,fy) if use_fg else (bt,by)
                for plane in range(2):
                    expected=(atlas[tile*16+plane*8+ty%8]>>bit)&1
                    actual=(guarded[1+plane*9600+y*40+x//8]>>bit)&1
                    assert actual==expected,(camera,x,y,plane)
                checks+=1
    before=bytes(guarded)
    for f,b in [(256,0),(0,256),(0xffffffff,0)]:
        assert not lib.v6_tower_compose(dst,*rings,mask,f,b)
        assert bytes(guarded)==before
    before=bytes(mask);bad=(C.c_uint16*40)(*([0]*39+[30]))
    assert not lib.v6_tower_mask_row(mask,0,bad,native_masks,30)
    assert bytes(mask)==before
    report=dict(cameras=cameras,pixel_checks=checks,opacity_bytes=len(masks),
        scope='Host C two-plane composition; half-speed positive cameras, source alpha masks and desktop maps; no native DMA integration or timing')
    (OUT/'tower-compose-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
