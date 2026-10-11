#!/usr/bin/env python3
"""Candidate moving-platform restoration and source tile/alpha pixels."""
import ctypes as C
import json,re,random,subprocess
from tower_gameplay_data import ROOT
from test_prize_return_actors import Bank

def main():
    out=ROOT/'build/amiga-feasibility';header=(out/'downunder_assets.h').read_text()
    def array(name):
        data=re.search(name+r'\[[^;]+?=\{(.*?)\};',header,re.S)[1]
        return [int(v) for v in re.findall(r'\d+',data)]
    atlas=array('downunder_atlas');tile=array('downunder_platform');mask=array('downunder_platform_mask')
    strips=array('downunder_strips');meta=json.loads((out/'downunder-graphics.json').read_text())
    base=bytearray(20480)
    for p in range(2):
        for y in range(248):
            for x in range(40):base[p*10240+y*40+x]=atlas[meta['display_tiles'][(y//8)%30*40+x]*16+p*8+y%8]
    # Independent original-PNG conversion of source platform tile 239 and alpha.
    dimensions,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/'downunder-tiles.png')]).split(b'\n',1)
    width,height=map(int,dimensions.split());palette=[((v>>8)&15,(v>>4)&15,v&15) for v in meta['palette']]
    colours=[];expected_mask=[];ox=239%(width//8)*8;oy=239//(width//8)*8
    for y in range(8):
        row=[];alpha=0
        for x in range(8):
            pixel=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
            rgb=tuple(round(v*pixel[3]/255/17) for v in pixel[:3])
            row.append(min(range(4),key=lambda i:sum((palette[i][j]-rgb[j])**2 for j in range(3))))
            alpha|=bool(pixel[3])<<(7-x)
        colours.append(row);expected_mask.append(alpha)
    expected_tile=[sum(((colours[y][x]>>p)&1)<<(7-x) for x in range(8)) for p in range(2) for y in range(8)]
    assert tile==expected_tile and mask==expected_mask
    # Conveyors use the same opaque source tiles and each room's own palette.
    tread_header=(out/'deception_assets.h').read_text()
    tread_data=re.search(r'deception_treads\[[^;]+?=\{(.*?)\};',tread_header,re.S)[1]
    treads=[int(v) for v in re.findall(r'\d+',tread_data)]
    tread_meta=json.loads((out/'deception-graphics.json').read_text())
    palette=[((v>>8)&15,(v>>4)&15,v&15) for v in tread_meta['palette']]
    wanted=[]
    for source in range(72,76):
        colours=[];ox=source%(width//8)*8;oy=source//(width//8)*8
        for y in range(8):
            row=[]
            for x in range(8):
                pixel=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                assert pixel[3]==255
                rgb=tuple(round(v/17) for v in pixel[:3])
                row.append(min(range(4),key=lambda i:sum((palette[i][j]-rgb[j])**2 for j in range(3))))
            colours.append(row)
        wanted.extend(sum(((colours[y][x]>>p)&1)<<(7-x) for x in range(8)) for p in range(2) for y in range(8))
    assert treads==wanted
    assert len(strips)==7680
    for i,x in enumerate((88,136,184,232)):
        for y in range(240):
            assert strips[i*1920+y*8:i*1920+y*8+8]==[base[p*10240+y*40+x//8+c] for p in range(2) for c in range(4)]
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/prize_return_draw.c'),
        '-o',str(out/'return_draw.so')],check=True)
    core=C.CDLL(str(out/'return_draw.so'));bp=C.POINTER(C.c_uint8)
    core.v6_prize_return_draw_platforms.argtypes=[bp,C.POINTER(Bank),bp,bp,bp,C.POINTER(C.c_int)]
    core.v6_prize_return_draw_conveyors.argtypes=[bp,bp]
    for phase in range(4):
        ring=(C.c_uint8*20480).from_buffer_copy(base);wanted=bytearray(base)
        bits=treads[phase*16:phase*16+16]
        core.v6_prize_return_draw_conveyors(ring,(C.c_uint8*16)(*bits))
        for i,x in enumerate((104,168,232,56,120,184)):
            y=80 if i<3 else 144;columns=4 if i%3==2 else 8
            for p in range(2):
                for row in range(8):
                    at=p*10240+(y+row)*40+x//8
                    wanted[at:at+columns]=bytes([bits[p*8+row]]*columns)
        assert bytes(ring)==wanted,('conveyor',phase)
    backgrounds=(C.c_uint8*7680)(*strips);tiles=(C.c_uint8*16)(*tile);alpha=(C.c_uint8*8)(*mask)
    rings=[(C.c_uint8*20480).from_buffer_copy(base) for _ in range(2)]
    last=[(C.c_int*4)(-1,-1,-1,-1) for _ in range(2)]
    bank=Bank();bank.platform_count=4;bank.flags=1;rng=random.Random(442480)
    for i in range(4):bank.platforms[i].x=88+i*48;bank.platforms[i].w=32;bank.platforms[i].h=8
    for tick in range(640):
        if tick==512:
            mask=[0,255,85,170,1,128,15,240]
            alpha=(C.c_uint8*8)(*mask)
            tile=[value & mask[row%8] for row,value in enumerate(tile)]
            tiles=(C.c_uint8*16)(*tile)
            rings=[(C.c_uint8*20480).from_buffer_copy(base) for _ in range(2)]
            last=[(C.c_int*4)(-1,-1,-1,-1) for _ in range(2)]
        for i in range(4):bank.platforms[i].y=(0,1,7,8,9,224,231,232)[(tick+i)%8] if tick<16 else rng.randrange(233)
        n=tick&1;assert core.v6_prize_return_draw_platforms(rings[n],C.byref(bank),backgrounds,tiles,alpha,last[n])
        wanted=bytearray(base)
        for i in range(4):
            a=bank.platforms[i]
            for p in range(2):
                for y in range(8):
                    for x in range(4):
                        at=p*10240+(a.y+y)*40+a.x//8+x
                        wanted[at]=(wanted[at]&(~mask[y]&255))|tile[p*8+y]
        assert bytes(rings[n])==wanted,(tick,n)
        assert list(last[n])==[a.y for a in bank.platforms[:4]]
    before=bytes(rings[0]),bytes(last[0]);bank.platforms[3].y=233
    assert not core.v6_prize_return_draw_platforms(rings[0],C.byref(bank),backgrounds,tiles,alpha,last[0])
    assert before==(bytes(rings[0]),bytes(last[0]))
    print('PASS Down Under drawing: source tile 239 planes/alpha, 7680 background bytes, 640 alternating opaque/partial-alpha full-ring restoration comparisons, clipping bounds and invalid-input immutability')
if __name__=='__main__':main()
