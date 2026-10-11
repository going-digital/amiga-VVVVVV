#!/usr/bin/env python3
"""Independent exploration save vectors and transactional migration guards."""
import ctypes as C
import struct
import subprocess
import zlib
from test_campaign_save import ROOT, Checkpoint, Story, values

class Exploration(C.Structure):
    _fields_=[('rooms',C.c_uint8*50)]

def main():
    out=ROOT/'build/amiga-campaign-state';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/campaign_save.c'),
        '-o',str(out/'state.so')],check=True)
    lib=C.CDLL(str(out/'state.so'))
    lib.v6_campaign_state_encode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Checkpoint),C.POINTER(Story),C.POINTER(Exploration)]
    lib.v6_campaign_state_decode.argtypes=[C.POINTER(Checkpoint),C.POINTER(Story),C.POINTER(Exploration),C.c_void_p,C.c_size_t]
    lib.v6_campaign_decode.argtypes=[C.POINTER(Checkpoint),C.POINTER(Story),C.c_void_p,C.c_size_t]
    def decode(data,expected=None):
        c=Checkpoint(*([77]*7));s=Story(*([88]*5));e=Exploration((C.c_uint8*50)(*([99]*50)))
        before=bytes(c),bytes(s),bytes(e)
        raw=(C.c_uint8*len(data)).from_buffer_copy(data)
        ok=lib.v6_campaign_state_decode(C.byref(c),C.byref(s),C.byref(e),raw,len(data))
        if expected is None:
            assert not ok and (bytes(c),bytes(s),bytes(e))==before
        else:
            assert ok and (values(c),values(s),bytes(e))==expected
    def encode(c,s,e):
        buf=(C.c_uint8*96)(*([165]*96))
        assert lib.v6_campaign_state_encode(buf,96,C.byref(c),C.byref(s),C.byref(e))
        expected=struct.pack('>4sHH7iI',b'V6CS',2,96,*values(c),s.rescue_triggered|s.red_rescued<<1|(s.companion==9)<<2)+bytes(e)+b'\0\0'
        expected+=struct.pack('>I',zlib.crc32(expected))
        assert bytes(buf)==expected
        decode(expected,(values(c),values(s),bytes(e)))
        return expected
    s=Story(0,0,0,0,0);c=Checkpoint(156,92,0,0,111,104,0)
    # Every map bit independently survives; unsupported rooms do not become residents.
    room=(104-100)*20+111-100
    for bit in range(400):
        e=Exploration();e.rooms[room>>3]|=1<<(room&7);e.rooms[bit>>3]|=1<<(bit&7)
        blob=encode(c,s,e)
    e=Exploration((C.c_uint8*50)(*([255]*50)));blob=encode(c,s,e)
    for bit in range(768):
        bad=bytearray(blob);bad[bit//8]^=1<<(bit%8);decode(bad)
    for n in range(96):decode(blob[:n])
    decode(blob+b'\0')
    # Checksum-valid corruption still cannot bypass semantic or reserved-field guards.
    for offset,value in ((0,0),(4,1),(5,1),(6,1),(7,95),(90,1),(91,1),(40+(room>>3),255^(1<<(room&7)))):
        bad=bytearray(blob);bad[offset]=value;struct.pack_into('>I',bad,92,zlib.crc32(bad[:92]));decode(bad)
    for offset,value in ((8,321),(16,2),(20,2),(24,107),(32,0xfffffffe),(36,8)):
        bad=bytearray(blob);struct.pack_into('>I',bad,offset,value);struct.pack_into('>I',bad,92,zlib.crc32(bad[:92]));decode(bad)
    # Legacy migration marks only the saved room, for every supported route bank.
    for rx,ry in ((109,109),(109,104),(108,109),(110,104),(111,104),(110,105)):
        c=Checkpoint(140,100,0,1,rx,ry,0)
        legacy=struct.pack('>4sHH7iI',b'V6CS',1,44,*values(c),0)
        legacy+=struct.pack('>I',zlib.crc32(legacy))
        e=Exploration();bit=(ry-100)*20+rx-100;e.rooms[bit>>3]=1<<(bit&7)
        decode(legacy,(values(c),values(s),bytes(e)))
        encode(c,s,e)
    # Encoding failures retain the entire destination buffer.
    buf=(C.c_uint8*96)(*([165]*96));before=bytes(buf);empty=Exploration()
    for n in (0,44,95,96,97):
        assert not lib.v6_campaign_state_encode(buf,n,C.byref(c),C.byref(s),C.byref(empty))
        assert bytes(buf)==before
    assert not lib.v6_campaign_state_encode(None,96,C.byref(c),C.byref(s),C.byref(e))
    raw=(C.c_uint8*96).from_buffer_copy(blob)
    assert not lib.v6_campaign_decode(C.byref(c),C.byref(s),raw,96)
    for missing in range(3):
        args=[C.byref(c),C.byref(s),C.byref(e),raw,96];args[missing]=None
        assert not lib.v6_campaign_state_decode(*args)
    print('PASS exploration codec: 400 map-bit round trips, 768 bit corruptions, 97 length guards, six legacy migrations; independent BE/CRC vectors')
if __name__=='__main__':main()
