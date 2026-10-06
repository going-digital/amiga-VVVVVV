#!/usr/bin/env python3
"""Paired word renderer versus direct source tiles and byte atlases."""
import ctypes as C
import json
import re
import subprocess
from test_player import ROOT
from test_tower_stream import Stream
from test_tower_draw import Draw
OUT=ROOT/'build/amiga-feasibility'
def values(path,name):
    text=path.read_text()
    return [int(v) for v in re.search(r'\b'+name+r'\[\d+\]\s*=\s*\{(.*?)\}',text,re.S)[1].split(',') if v.strip()]
def main():
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',*[str(ROOT/'amiga_version'/f) for f in
        ('tower_draw.c','tower_stream.c','room_codec.c')],'-o',str(OUT/'tower_pairs.so')],check=True)
    core=C.CDLL(str(OUT/'tower_pairs.so'));bp=C.POINTER(C.c_uint8);wp=C.POINTER(C.c_uint16)
    core.v6_tower_open.argtypes=[C.POINTER(Stream),C.c_char_p,C.c_size_t]
    core.v6_tower_pairs_validate.argtypes=[C.POINTER(Stream),wp,C.c_uint,C.c_uint,C.c_uint]
    for name in ('v6_tower_draw_pair_prepare','v6_tower_draw_pair_prepare_verified'):
        getattr(core,name).argtypes=[C.POINTER(Draw),bp,C.POINTER(Stream),C.c_int,wp,wp,C.c_uint,C.c_uint,C.c_uint,C.POINTER(C.c_uint)]
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text();frames=rows=0
    for name in ('loadmap','loadminitower1','loadminitower2','loadbackground'):
        planes=1 if name=='loadbackground' else 2;prefix='tower_background' if planes==1 else 'tower'
        offsets=values(OUT/(prefix+'_pairs.h'),prefix+'_pair_offsets')
        words=values(OUT/(prefix+'_pairs.h'),prefix+'_pairs')
        native_offsets=(C.c_uint16*1024)(*offsets);native_words=(C.c_uint16*len(words))(*words)
        raw=source[source.index('void towerclass::'+name+'('):]
        raw=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',raw,re.S)[1]
        raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
        tiles=[int(v) for v in raw.split(',') if v.strip()];height=len(tiles)//40
        atlas=(OUT/('tower_backdrop.bin' if planes==1 else 'tower_tiles.bin')).read_bytes()
        blob=(OUT/(name+'.v6tr')).read_bytes();stream=Stream()
        assert core.v6_tower_open(C.byref(stream),blob,len(blob))
        assert core.v6_tower_pairs_validate(C.byref(stream),native_offsets,len(words),30,planes)
        buffers=[(C.c_uint16*(planes*5120+2))(*([0xa5a5]*(planes*5120+2))) for _ in range(2)]
        draws=[Draw(),Draw()];drawn=C.c_uint()
        positions=list(range(-4,height+4))+list(range(height+3,-5,-1))+[0,0,31,-31,32737,-32768,0]
        for frame,top in enumerate(positions):
            i=frame&1;dst=C.cast(C.byref(buffers[i],2),bp)
            prepare=core.v6_tower_draw_pair_prepare_verified if i else core.v6_tower_draw_pair_prepare
            assert prepare(C.byref(draws[i]),dst,C.byref(stream),top,native_offsets,native_words,len(words),30,planes,C.byref(drawn))
            output=bytes(buffers[i]);assert output[:2]==output[-2:]==b'\xa5\xa5'
            for row in range(top,top+31):
                ids=tiles[(row%height)*40:(row%height+1)*40]
                for plane in range(planes):
                    for y in range(8):
                        expected=bytes(atlas[t*planes*8+plane*8+y] for t in ids)
                        offset=2+plane*10240+(row&31)*320+y*40
                        assert output[offset:offset+40]==expected,(name,frame,row,plane,y)
                rows+=1
            frames+=1
        # Reject unsupported pairs and short/unaligned destinations before
        # writing their row; repairs must validate again before verified use.
        bad=(C.c_uint16*1024)(*offsets);key=tiles[0]*32+tiles[1];bad[key]=65535
        assert not core.v6_tower_pairs_validate(C.byref(stream),bad,len(words),30,planes)
        empty=Draw();buf=(C.c_uint16*(planes*5120+2))(*([0xa5a5]*(planes*5120+2)));before=bytes(buf)
        dst=C.cast(C.byref(buf,2),bp)
        assert not core.v6_tower_draw_pair_prepare(C.byref(empty),dst,C.byref(stream),0,bad,native_words,len(words),30,planes,C.byref(drawn))
        assert bytes(buf)==before and drawn.value==0 and not empty.complete
        assert not core.v6_tower_draw_pair_prepare(C.byref(empty),C.cast(C.byref(buf,1),bp),C.byref(stream),0,native_offsets,native_words,len(words),30,planes,C.byref(drawn))
        assert bytes(buf)==before
        assert not core.v6_tower_pairs_validate(C.byref(stream),native_offsets,planes*8-1,30,planes)
    report=dict(frames=frames,rows=rows,scope='Checked and prevalidated paired-word rendering vs source maps/byte atlases; all four maps, alternating buffers, signed limits, unknown pairs and alignment failures')
    (OUT/'tower-pair-tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
