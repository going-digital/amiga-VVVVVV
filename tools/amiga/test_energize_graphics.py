#!/usr/bin/env python3
"""Compact tile remapping and paired ring pixels against source PNG/palette."""
import ctypes as C
import json
import re
import subprocess
from pathlib import Path
from test_tower_draw import Draw
from test_tower_stream import Stream
from tower_gameplay_data import ROOT,energize_room

def main(name="energize",room_fn=energize_room,extra_ids=()):
    out=ROOT/'build/amiga-feasibility';meta=json.loads((out/(name+'-graphics.json')).read_text())
    header=(out/(name+'_assets.h')).read_text()
    def vals(name):return [int(v) for v in re.search(name+r'\[\]=\{([^}]+)\}',header)[1].split(',')]
    source=room_fn()['tiles'];ids=sorted(set(source)|set(extra_ids));assert ids==meta['source_ids']
    if name=='energize':assert len(ids)==16
    mapping={tile:i for i,tile in enumerate(ids)}
    assert meta['display_tiles']==[mapping[tile] for tile in source]
    assert vals(name+'_palette')==meta['palette']
    palette=[((c>>8)&15,(c>>4)&15,c&15) for c in meta['palette']]
    dimensions,rgba=subprocess.check_output([str(out/'png_rgba'),str(out/(name+'-tiles.png'))]).split(b'\n',1)
    width,height=map(int,dimensions.split());pixels=[]
    for tile in ids:
        ox=tile%(width//8)*8;oy=tile//(width//8)*8;row=[]
        for y in range(8):
            for x in range(8):
                rgb=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                colour=tuple(round(v*rgb[3]/255/17) for v in rgb[:3]) if tile else (0,0,0)
                row.append(min(range(4),key=lambda i:sum((palette[i][j]-colour[j])**2 for j in range(3))))
        pixels.append(row)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('tower_draw.c','tower_stream.c','room_codec.c')],
        '-o',str(out/(name+'-draw.so'))],check=True)
    core=C.CDLL(str(out/(name+'-draw.so')));bp=C.POINTER(C.c_uint8);wp=C.POINTER(C.c_uint16)
    core.v6_tower_open.argtypes=[C.POINTER(Stream),C.c_char_p,C.c_size_t]
    core.v6_tower_pairs_validate.argtypes=[C.POINTER(Stream),wp,C.c_uint,C.c_uint,C.c_uint]
    core.v6_tower_draw_pair_prepare.argtypes=[C.POINTER(Draw),bp,C.POINTER(Stream),C.c_int,wp,wp,C.c_uint,C.c_uint,C.c_uint,C.POINTER(C.c_uint)]
    blob=(out/(name+'.v6tr')).read_bytes();stream=Stream()
    assert core.v6_tower_open(C.byref(stream),blob,len(blob))
    offset_values=vals(name+'_pair_offsets');assert len(offset_values)==len(ids)*32
    offsets=(C.c_uint16*len(offset_values))(*offset_values);raw=vals(name+'_pairs')
    pairs=(C.c_uint16*len(raw))(*raw)
    assert core.v6_tower_pairs_validate(C.byref(stream),offsets,len(raw),len(ids),2)
    ring=(C.c_uint8*20480)();draw=Draw();rows=C.c_uint()
    assert core.v6_tower_draw_pair_prepare(C.byref(draw),ring,C.byref(stream),0,offsets,pairs,len(raw),len(ids),2,C.byref(rows))
    assert rows.value==31
    for y in range(248):
        for x in range(320):
            tile=mapping[source[((y//8)%30)*40+x//8]]
            expected=pixels[tile][(y%8)*8+x%8]
            actual=sum(((ring[p*10240+y*40+x//8]>>(7-x%8))&1)<<p for p in range(2))
            assert actual==expected,(x,y,actual,expected)
    print(f'PASS {name} graphics: {len(ids)} source IDs, {len(raw)//16} pairs, 79360 paired ring pixels against source PNG and frozen four-colour palette')
if __name__=='__main__':main()
