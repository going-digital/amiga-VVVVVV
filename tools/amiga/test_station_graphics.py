#!/usr/bin/env python3
"""Station tile/crew masks against private source PNG pixels."""
import re
import subprocess
from tower_gameplay_data import ROOT,frown_room
from test_energize_graphics import main as tile_test

def main():
    tile_test('frown',frown_room)
    out=ROOT/'build/amiga-feasibility'
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
