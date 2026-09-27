#!/usr/bin/env python3
"""C row drawing and alternating display rings against a pixel/atlas reference."""
import ctypes as C
import json
import subprocess
from pack_rooms import ROOT
from probe_feasibility import tower_probe
from test_tower_stream import Stream

class Draw(C.Structure):
    _fields_=[('valid',C.c_uint32),('tags',C.c_int16*32)]


def main():
    out=ROOT/'build/amiga-feasibility';out.mkdir(parents=True,exist_ok=True)
    tower_probe(out)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('tower_draw.c','tower_stream.c','room_codec.c')],
        '-o',str(out/'tower_draw.so')],check=True)
    core=C.CDLL(str(out/'tower_draw.so'))
    bp=C.POINTER(C.c_uint8);wp=C.POINTER(C.c_uint16);up=C.POINTER(C.c_uint)
    core.v6_tower_open.argtypes=[C.POINTER(Stream),C.c_char_p,C.c_size_t]
    core.v6_tower_row.argtypes=[C.POINTER(Stream),C.c_int,up];core.v6_tower_row.restype=wp
    core.v6_tower_draw_row.argtypes=[bp,C.c_int,wp,bp,C.c_uint]
    core.v6_tower_draw_prepare.argtypes=[C.POINTER(Draw),bp,C.POINTER(Stream),C.c_int,bp,C.c_uint,up,up]
    # Distinct plane, scanline and tile patterns catch bit order/stride mistakes.
    atlas=bytes((tile*37+plane*113+y*19)&255 for tile in range(256) for plane in range(2) for y in range(8))
    native_atlas=(C.c_uint8*len(atlas)).from_buffer_copy(atlas)
    rows_checked=0;frames=0;peak_drawn=0
    for name in ('loadmap','loadbackground','loadminitower1','loadminitower2'):
        blob=(out/(name+'.v6tr')).read_bytes();stream=Stream()
        assert core.v6_tower_open(C.byref(stream),blob,len(blob))
        buffers=[(C.c_uint8*20482)(*([0xa5]*20482)) for _ in range(2)]
        draws=[Draw(),Draw()];decoded=C.c_uint();drawn=C.c_uint()
        # Alternate buffers through forward, reverse, map wrap and cache wrap.
        positions=list(range(-35,stream.height+35))+list(range(stream.height+34,-36,-1))
        for frame,top in enumerate(positions):
            index=frame&1;buf=buffers[index];dst=C.cast(C.byref(buf,1),bp)
            assert core.v6_tower_draw_prepare(C.byref(draws[index]),dst,C.byref(stream),top,native_atlas,256,C.byref(decoded),C.byref(drawn))
            if frame>1:assert drawn.value<=2
            peak_drawn=max(peak_drawn,drawn.value);frames+=1
            output=bytes(buf)
            assert output[0]==output[-1]==0xa5
            for row in range(top,top+31):
                tiles=list(core.v6_tower_row(C.byref(stream),row,None)[:40])
                for plane in range(2):
                    for y in range(8):
                        expected=bytes(atlas[t*16+plane*8+y] for t in tiles)
                        offset=1+plane*10240+(row&31)*320+y*40
                        assert output[offset:offset+40]==expected,(name,frame,row,plane,y)
                rows_checked+=1
            assert core.v6_tower_draw_prepare(C.byref(draws[index]),dst,C.byref(stream),top,native_atlas,256,C.byref(decoded),C.byref(drawn))
            assert decoded.value==drawn.value==0
        before=bytes(buffers[0]);tiles=(C.c_uint16*40)(*([0]*39+[256]))
        assert not core.v6_tower_draw_row(C.cast(C.byref(buffers[0],1),bp),0,tiles,native_atlas,256)
        assert bytes(buffers[0])==before
        assert not core.v6_tower_draw_prepare(C.byref(draws[0]),C.cast(C.byref(buffers[0],1),bp),C.byref(stream),32738,native_atlas,256,C.byref(decoded),C.byref(drawn))
        assert bytes(buffers[0])==before and drawn.value==decoded.value==0
    report=dict(frames=frames,rows_checked=rows_checked,initial_max_rows_drawn=peak_drawn,
        ring_bytes_each=20480,scope='Native C two-plane drawing using synthetic atlas and original packed maps; host memory only, no Copper/DMA or target timing')
    (out/'tower-draw-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
