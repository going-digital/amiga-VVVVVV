#!/usr/bin/env python3
"""Station tile/crew masks against private source PNG pixels."""
import json
import re
import subprocess
from tower_gameplay_data import ROOT,frown_room,shenanigan_room
from test_energize_graphics import main as tile_test

def main():
    tile_test('frown',frown_room)
    tile_test('shenanigan',shenanigan_room)
    out=ROOT/'build/amiga-feasibility'
    # Independently quantize every opaque source conveyor pixel to the room palette.
    source=(out/'shenanigan_assets.h').read_text()
    raw=re.search(r'shenanigan_treads\[8\]\[16\]=\{(.*?)\};',source)[1]
    frames=[list(map(int,re.findall(r'\d+',row))) for row in re.findall(r'\{([^}]+)\}',raw)]
    colours=json.loads((out/'shenanigan-graphics.json').read_text())['palette']
    palette=[((c>>8)&15,(c>>4)&15,c&15) for c in colours]
    dimensions,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'shenanigan-tiles.png')]).split(b'\n',1)
    width,height=map(int,dimensions.split())
    for frame,tile in zip(frames,(*range(68,72),*range(28,32))):
        assert len(frame)==16
        for y in range(8):
            for x in range(8):
                offset=((tile//(width//8)*8+y)*width+tile%(width//8)*8+x)*4
                assert rgba[offset+3]==255
                rgb=tuple(round(v/17) for v in rgba[offset:offset+3])
                expected=min(range(4),key=lambda i:sum((palette[i][j]-rgb[j])**2 for j in range(3)))
                actual=sum(((frame[p*8+y]>>(7-x))&1)<<p for p in range(2))
                assert actual==expected,(tile,x,y)
    print('PASS Shenanigan treads: 512 independently quantized source pixels, both directions and all four frames')
    data=(out/'tower_player_assets.h').read_text()
    raw=re.search(r'station_crew_rows\[32\]=\{([^}]+)\}',data)[1]
    rows=[int(v.removesuffix('UL'),16) for v in raw.split(',')]
    header,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'tower_sprites.png')]).split(b'\n',1)
    width,height=map(int,header.split());ox=150%(width//32)*32;oy=150//(width//32)*32
    assert oy+32<=height
    for y in range(32):
        for x in range(32):
            at=((oy+y)*width+ox+x)*4
            assert (rows[y]>>(31-x))&1==int(rgba[at+3]>127 and max(rgba[at:at+3])>0)
    print('PASS yellow idle sprite: 1024 source alpha/ink pixels, full crop retained')
if __name__=='__main__':main()
