#!/usr/bin/env python3
"""Native row cache versus all original tower maps, with malformed-input checks."""
import ctypes as C
import json
import re
import struct
import subprocess
from probe_feasibility import tower_probe
from pack_rooms import ROOT

class Stream(C.Structure):
    _fields_=[('data',C.c_void_p),('size',C.c_size_t),('valid',C.c_uint32),
              ('height',C.c_uint16),('tags',C.c_int16*32),('tiles',(C.c_uint16*40)*32)]


def main():
    out=ROOT/'build/amiga-feasibility';out.mkdir(parents=True,exist_ok=True)
    tower_probe(out)
    lib=out/'tower_stream.so'
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        str(ROOT/'amiga_version/tower_stream.c'),str(ROOT/'amiga_version/room_codec.c'),'-o',str(lib)],check=True)
    core=C.CDLL(str(lib));core.v6_tower_open.argtypes=[C.POINTER(Stream),C.c_char_p,C.c_size_t]
    core.v6_tower_row.argtypes=[C.POINTER(Stream),C.c_int,C.POINTER(C.c_uint)]
    core.v6_tower_row.restype=C.POINTER(C.c_uint16)
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text();checks=0;refills=0
    for name in ('loadmap','loadbackground','loadminitower1','loadminitower2'):
        blob=(out/(name+'.v6tr')).read_bytes();s=Stream()
        assert core.v6_tower_open(C.byref(s),blob,len(blob))==1
        body=source[source.index('void towerclass::'+name+'('):]
        raw=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
        raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
        values=[int(v) for v in raw.split(',') if v.strip()]
        assert len(values)==s.height*40
        decoded=C.c_uint()
        # Cross every map boundary both ways, including negative coordinates.
        for step in (1,-1):
            camera= -s.height*8 if step==1 else s.height*8
            for tick in range(s.height*16):
                camera+=step
                loads=0
                for screen_row in range(31):
                    row=int((camera+screen_row*8)/8)
                    data=core.v6_tower_row(C.byref(s),row,C.byref(decoded))
                    assert data and list(data[:40])==values[(row%s.height)*40:(row%s.height+1)*40]
                    loads+=decoded.value;checks+=1
                if tick:assert loads<=1,(name,step,tick,loads)
                refills+=loads
        for row in (-32768,32767,0,s.height-1,s.height,s.height+31):
            data=core.v6_tower_row(C.byref(s),row,C.byref(decoded))
            assert data and list(data[:40])==values[(row%s.height)*40:(row%s.height+1)*40]
            assert core.v6_tower_row(C.byref(s),row,C.byref(decoded)) and decoded.value==0
        before=bytes(s)
        for row in (-32769,32768):
            assert not core.v6_tower_row(C.byref(s),row,C.byref(decoded)) and decoded.value==0
            assert bytes(s)==before
        for bad in (b'',blob[:9],b'BAD!'+blob[4:],blob[:4]+b'\0\2'+blob[6:],
                    blob[:8]+b'\0\0'+blob[10:],blob[:8]+b'\x02\xbd'+blob[10:],
                    blob[:10]+b'\xff'*4+blob[14:],blob[:14]+b'\0\0'+blob[16:],blob[:15]):
            assert not core.v6_tower_open(C.byref(s),bad,len(bad)) and bytes(s)==before
    # Non-power-of-two heights and signed extremes exercise the freestanding
    # remainder implementation independently of the campaign's map sizes.
    modulus_checks=0
    for height in (1,2,31,32,33,699,700):
        blob=struct.pack('>4sHHH',b'V6TR',1,40,height)
        blob+=b''.join(struct.pack('>IH',i*4,4) for i in range(height))
        blob+=b''.join(struct.pack('>HH',0x8028,i) for i in range(height))
        assert core.v6_tower_open(C.byref(s),blob,len(blob))
        for row in list(range(-32768,32768,97))+[32767,-1,0,1]:
            data=core.v6_tower_row(C.byref(s),row,C.byref(decoded))
            assert data and list(data[:40])==[row%height]*40
            modulus_checks+=1
    # Valid directory pointing to malformed RLE must fail on every access.
    bad=struct.pack('>4sHHHIH',b'V6TR',1,40,1,0,4)+b'\x80\x29\0\0'
    assert core.v6_tower_open(C.byref(s),bad,len(bad))
    for _ in range(2):
        assert not core.v6_tower_row(C.byref(s),0,C.byref(decoded)) and s.valid==0 and decoded.value==0
    report=dict(queries=checks,modulus_checks=modulus_checks,refills=refills,host_struct_bytes=C.sizeof(Stream),
                scope='Actual C tower directory reader/cache; all four source maps, bidirectional wrap, cache hits and malformed data; no target display timing')
    (out/'tower-stream-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
