#!/usr/bin/env python3
"""Campaign Prize atlas and actors against independently decoded source PNGs."""
import re,subprocess,json
from tower_gameplay_data import ROOT,prize_room
from test_energize_graphics import main as test_ring

def main():
    test_ring('prize',prize_room,(59,))
    out=ROOT/'build/amiga-feasibility'
    header=(out/'prize_assets.h').read_text()
    def matrix(name):
        raw=re.search(name+r'\[\d+\]\[\d+\]=\{(.*?)\};',header,re.S)[1]
        return [[int(v) for v in row.split(',')] for row in re.findall(r'\{([^}]+)\}',raw)]
    planes=matrix('prize_gate_planes');masks=matrix('prize_gate_masks')
    assert len(planes)==len(masks)==453
    metadata=json.loads((out/'prize-graphics.json').read_text())
    palette=[((c>>8)&15,(c>>4)&15,c&15) for c in metadata['palette']]
    dimensions,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'prize-tiles.png')]).split(b'\n',1)
    w,h=map(int,dimensions.split());checks=0
    for frame,tile in enumerate(range(747,1200)):
        ox=tile%(w//8)*8;oy=tile//(w//8)*8
        for y in range(8):
            for x in range(8):
                r,g,b,a=rgba[((oy+y)*w+ox+x)*4:((oy+y)*w+ox+x)*4+4]
                colour=tuple(round(v/17) for v in (r,g,b)) if a else (0,0,0)
                expected=min(range(4),key=lambda i:sum((palette[i][j]-colour[j])**2 for j in range(3)))
                actual=sum(((planes[frame][p*8+y]>>(7-x))&1)<<p for p in range(2))
                assert actual==expected and ((masks[frame][y]>>(7-x))&1)==bool(a)
                checks+=1
    waiting=[int(v.strip().removesuffix('UL'),0) for v in
             re.search(r'prize_waiting_rows\[32\]=\{([^}]+)\}',header)[1].split(',')]
    ox=747%(w//8)*8;oy=747//(w//8)*8
    for y in range(8):
        mask=sum((rgba[((oy+y)*w+ox+x)*4+3]!=0 and
                  max(rgba[((oy+y)*w+ox+x)*4:((oy+y)*w+ox+x)*4+3])>0)<<(7-x) for x in range(8))
        assert waiting[y]==mask*0x01010101
    assert not any(waiting[8:])
    death=[int(v) for v in re.search(r'prize_death_tile\[16\]=\{([^}]+)\}',header)[1].split(',')]
    atlas=(out/'prize-atlas.bin').read_bytes();at=metadata['source_ids'].index(59)*16
    assert bytes(death)==atlas[at:at+16]
    # The route must retain the mutable source view instead of a fresh decode.
    collision=(out/'prize_collision.h').read_text()
    assert 'static uint16_t prize_tiles[1200]' in collision
    tiles=[int(v) for v in re.search(r'prize_tiles\[1200\]=\{([^}]+)\}',collision)[1].split(',')]
    assert tiles==prize_room()['tiles'] and tiles[9*40+18]==0
    assert '443490' in collision
    # Trinket frame 22 is a 16x16 crop, exported without disturbing frames 0..21.
    sprites=(out/'tower_player_assets.h').read_text()
    raw=re.search(r'tower_player_rows\[23\]\[32\]=\{(.*?)\};',sprites,re.S)[1]
    frames=[[int(v.strip().removesuffix('UL'),0) for v in row.split(',')]
            for row in re.findall(r'\{([^}]+)\}',raw)]
    dimensions,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'tower_sprites.png')]).split(b'\n',1)
    w,h=map(int,dimensions.split());ox=22%(w//32)*32;oy=22//(w//32)*32
    for y in range(32):
        expected=sum((rgba[((oy+y)*w+ox+x)*4+3]>127 and
                      max(rgba[((oy+y)*w+ox+x)*4:((oy+y)*w+ox+x)*4+3])>0)<<(31-x) for x in range(32))
        assert frames[22][y]==expected and not(expected&0xffff)
        assert y<16 or expected==0
    print(f'PASS Prize campaign actors: {checks} gate pixels, repeated waiting mask, death tile, mutable terrain and trinket crop')
if __name__=='__main__':main()
