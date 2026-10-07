#!/usr/bin/env python3
"""Independent big-endian save vectors, corruption and transactional guards."""
import ctypes as C
from pathlib import Path
import struct
import subprocess
import zlib
ROOT=Path(__file__).resolve().parents[2]
class Checkpoint(C.Structure):
    _fields_=[(n,C.c_int) for n in 'x y gravity dir room_x room_y id'.split()]
class Story(C.Structure):
    _fields_=[(n,C.c_int) for n in 'time_trial translator_exploring companion rescue_triggered red_rescued'.split()]
def values(v):return tuple(getattr(v,n) for n,_ in v._fields_)
def main():
    out=ROOT/'build/amiga-campaign-save';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/campaign_save.c'),'-o',str(out/'save.so')],check=True)
    lib=C.CDLL(str(out/'save.so'));buf=(C.c_uint8*44)()
    lib.v6_campaign_encode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.v6_campaign_decode.argtypes=[C.POINTER(Checkpoint),C.POINTER(Story),C.c_void_p,C.c_size_t]
    c=Checkpoint(140,1822,1,1,109,109,-1);s=Story(0,0,9,1,1)
    def encode(c,s):
        assert lib.v6_campaign_encode(buf,44,C.byref(c),C.byref(s));return bytes(buf)
    def reject(data,n=None):
        a=Checkpoint(*([77]*7));b=Story(*([88]*5));before=bytes(a),bytes(b)
        raw=(C.c_uint8*len(data)).from_buffer_copy(data)
        assert not lib.v6_campaign_decode(C.byref(a),C.byref(b),raw,len(data) if n is None else n)
        assert (bytes(a),bytes(b))==before
    blob=encode(c,s)
    expected=struct.pack('>4sHH7iI',b'V6CS',1,44,*values(c),7)
    expected+=struct.pack('>I',zlib.crc32(expected))
    assert blob==expected
    cases=0
    for rx,ry,maxy in ((109,109,5600),(109,104,5600),(108,109,240),(110,104,240),(111,104,240),(110,105,240)):
        for x in (0,140,320):
            for y in (0,maxy):
                for gravity in (0,1):
                    for direction in (0,1):
                        for ident in (-1,0,505147,2147483647):
                            for companion,red in ((0,0),(0,1),(9,1)):
                                a=Checkpoint(x,y,gravity,direction,rx,ry,ident);b=Story(0,0,companion,red,red)
                                data=encode(a,b);aa=Checkpoint();bb=Story()
                                assert lib.v6_campaign_decode(C.byref(aa),C.byref(bb),(C.c_uint8*44).from_buffer_copy(data),44)
                                assert values(a)==values(aa) and values(b)==values(bb);cases+=1
    for bit in range(44*8):
        corrupt=bytearray(blob);corrupt[bit//8]^=1<<(bit%8);reject(corrupt)
    for n in range(44):reject(blob[:n])
    reject(blob+b'\0')
    # Recompute CRC after malformed fields: checksum alone is not validation.
    semantic=0
    for offset,vals in ((8,(321,0xffffffff)),(12,(5601,0xffffffff)),(16,(2,)),(20,(2,)),(24,(107,)),(28,(105,)),(32,(0xfffffffe,)),(36,(1,2,4,5,6,8,0xffffffff))):
        for value in vals:
            bad=bytearray(blob);struct.pack_into('>I',bad,offset,value);struct.pack_into('>I',bad,40,zlib.crc32(bad[:40]));reject(bad);semantic+=1
    for offset,value in ((0,0),(4,1),(5,2),(6,1),(7,43)):
        bad=bytearray(blob);bad[offset]=value;struct.pack_into('>I',bad,40,zlib.crc32(bad[:40]));reject(bad)
    for field,value in (('x',-1),('y',5601),('gravity',2),('dir',2),('room_x',107),('room_y',105),('id',-2)):
        bad=Checkpoint(*values(c));setattr(bad,field,value);before=bytes(buf)
        assert not lib.v6_campaign_encode(buf,44,C.byref(bad),C.byref(s));assert bytes(buf)==before
    for field,value in (('time_trial',1),('translator_exploring',1),('companion',8),('rescue_triggered',0),('red_rescued',0)):
        bad=Story(*values(s));setattr(bad,field,value);before=bytes(buf)
        assert not lib.v6_campaign_encode(buf,44,C.byref(c),C.byref(bad));assert bytes(buf)==before
    for n in (0,43,45):
        before=bytes(buf);assert not lib.v6_campaign_encode(buf,n,C.byref(c),C.byref(s));assert bytes(buf)==before
    assert not lib.v6_campaign_encode(None,44,C.byref(c),C.byref(s))
    assert not lib.v6_campaign_decode(None,C.byref(s),buf,44)
    print(f'PASS campaign save: {cases} round trips, 352 bit corruptions, 45 length guards, {semantic} checksum-valid semantic rejections; independent BE/CRC vector')
if __name__=='__main__':main()
