#!/usr/bin/env python3
"""Independent V3 story/map vectors, migrations, guards and transactional faults."""
import ctypes as C
import itertools
import struct
import zlib
from test_campaign_save import ROOT,Checkpoint,Story,values
from test_campaign_state import Exploration
from test_station_trigger import Story as Yellow
from test_campaign_file import Files,IO,Bank,main as build_file
from test_campaign_replace import Operations

def main():
    build_file();lib=C.CDLL(str(ROOT/'build/amiga-campaign-save/file.so'))
    ptrs=[C.POINTER(Checkpoint),C.POINTER(Story),C.POINTER(Yellow),C.POINTER(Exploration)]
    lib.v6_campaign_progress_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs
    lib.v6_campaign_progress_decode.argtypes=ptrs+[C.c_void_p,C.c_size_t]
    lib.v6_campaign_progress_read.argtypes=[C.POINTER(IO),C.c_char_p]+ptrs
    for name in ('replace','recover'):
        getattr(lib,'v6_campaign_progress_'+name).argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p]+ptrs
    lib.v6_campaign_state_replace.argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p,C.POINTER(Checkpoint),C.POINTER(Story),C.POINTER(Exploration)]
    c=Checkpoint(188,86,1,0,111,105,441490);r=Story();y=Yellow(0,0,7,1,1);e=Exploration();e.rooms[111>>3]=1<<(111&7)
    def encode(c,r,y,e):
        out=(C.c_uint8*96)(*([165]*96));args=[C.byref(x) for x in (c,r,y,e)]
        assert lib.v6_campaign_progress_encode(out,96,*args)
        flags=r.rescue_triggered|r.red_rescued<<1|(r.companion==9)<<2|y.rescue_triggered<<3|y.yellow_rescued<<4|(y.companion==7)<<5
        body=struct.pack('>4sHH7iI',b'V6CS',3,96,*values(c),flags)+bytes(e)+b'\0\0'
        assert bytes(out)==body+struct.pack('>I',zlib.crc32(body))
        return bytes(out)
    def decode(blob,expected=None):
        out=[Checkpoint(*([77]*7)),Story(*([88]*5)),Yellow(*([99]*5)),Exploration.from_buffer_copy(bytes([55]*50))]
        before=tuple(bytes(x) for x in out);raw=(C.c_uint8*len(blob)).from_buffer_copy(blob)
        ok=lib.v6_campaign_progress_decode(*[C.byref(x) for x in out],raw,len(blob))
        assert bool(ok)==(expected is not None)
        assert tuple(bytes(x) for x in out)==(expected if ok else before)
    # All flag combinations checked against an independent semantic predicate.
    valid=0
    for rt,rr,rc,yt,yr,yc in itertools.product((0,1),repeat=6):
        red=Story(0,0,9 if rc else 0,rt,rr);yellow=Yellow(0,0,7 if yc else 0,yt,yr)
        legal=rt==rr and yt==yr and (not rc or rr) and (not yc or yr) and not(rc and yc)
        out=(C.c_uint8*96)(*([165]*96));ok=lib.v6_campaign_progress_encode(out,96,C.byref(c),C.byref(red),C.byref(yellow),C.byref(e))
        assert bool(ok)==legal
        if legal:decode(encode(c,red,yellow,e),tuple(bytes(x) for x in (c,red,yellow,e)));valid+=1
        else:assert bytes(out)==bytes([165]*96)
    for bit in range(400):
        m=Exploration.from_buffer_copy(bytes(e));m.rooms[bit>>3]|=1<<(bit&7)
        decode(encode(c,r,y,m),tuple(bytes(x) for x in (c,r,y,m)))
    # Room-specific admission checks the actual two-entry source bank.
    bank=(Bank*2)(Bank(144,168,21,442490,0,0),Bank(24,112,20,442491,0,0))
    lib.v6_campaign_checkpoint_valid.argtypes=[C.POINTER(Checkpoint),C.POINTER(Bank),C.c_uint]
    for px,py,g,identity in ((140,161,0,442490),(20,110,1,442491)):
        for direction in (0,1):
            checkpoint=Checkpoint(px,py,g,direction,111,106,identity)
            assert lib.v6_campaign_checkpoint_valid(C.byref(checkpoint),bank,2)
            for field in ('x','y','gravity','dir','id'):
                bad=Checkpoint(*values(checkpoint));setattr(bad,field,getattr(bad,field)+2)
                assert not lib.v6_campaign_checkpoint_valid(C.byref(bad),bank,2)
            for name,n in (('v6_campaign_encode',44),('v6_campaign_state_encode',96)):
                out=(C.c_uint8*n)(*([165]*n))
                args=[out,n,C.byref(checkpoint),C.byref(r)]
                if n==96:args.append(C.byref(e))
                assert not getattr(lib,name)(*args)
                assert bytes(out)==bytes([165]*n)
    # Independent V3 vectors for both Shenanigan source checkpoint orientations.
    for checkpoint in (Checkpoint(140,161,0,1,111,106,442490),Checkpoint(20,110,1,0,111,106,442491)):
        m=Exploration.from_buffer_copy(bytes(e));m.rooms[131>>3]|=1<<(131&7)
        decode(encode(checkpoint,r,y,m),tuple(bytes(x) for x in (checkpoint,r,y,m)))
    updated=encode(c,r,y,e)
    for bit in range(768):
        bad=bytearray(updated);bad[bit>>3]^=1<<(bit&7);decode(bad)
    for n in range(96):decode(updated[:n])
    decode(updated+b'x')
    for offset,value in ((8,321),(12,241),(16,2),(20,2),(24,112),(28,107),(32,0xfffffffe),(36,64),(36,8),(36,32),(36,63)):
        bad=bytearray(updated);struct.pack_into('>I',bad,offset,value);struct.pack_into('>I',bad,92,zlib.crc32(bad[:92]));decode(bad)
    for offset in (0,4,6,7,90,91,40+(111>>3)):
        bad=bytearray(updated);bad[offset]^=1 if offset!=40+(111>>3) else 1<<(111&7)
        struct.pack_into('>I',bad,92,zlib.crc32(bad[:92]));decode(bad)
    old=Checkpoint(156,92,0,0,111,104,0);oldmap=Exploration();oldmap.rooms[91>>3]=1<<(91&7)
    def older(version):
        body=struct.pack('>4sHH7iI',b'V6CS',version,44 if version==1 else 96,*values(old),0)
        if version==2:body+=bytes(oldmap)+b'\0\0'
        return body+struct.pack('>I',zlib.crc32(body))
    originals=[older(1),older(2),encode(old,r,Yellow(),oldmap)]
    for blob in originals:decode(blob,tuple(bytes(x) for x in (old,r,Yellow(),oldmap)))
    def replace(io):return lib.v6_campaign_progress_replace(C.byref(io),b'save',b'temp',b'backup',*[C.byref(x) for x in (c,r,y,e)])
    def recover(fs,io=None):
        out=[Checkpoint(*([77]*7)),Story(*([88]*5)),Yellow(*([99]*5)),Exploration.from_buffer_copy(bytes([55]*50))]
        before=tuple(bytes(x) for x in out)
        result=lib.v6_campaign_progress_recover(C.byref(io or fs.io),b'save',b'temp',b'backup',*[C.byref(x) for x in out])
        if result:assert tuple(bytes(x) for x in out)==before
        else:assert tuple(bytes(x) for x in out) in (tuple(bytes(x) for x in (old,r,Yellow(),oldmap)),tuple(bytes(x) for x in (c,r,y,e)))
        return result
    snapshots=faults=0
    for original in originals:
        fs=Files();fs.files[b'save']=original;ops=Operations(fs);assert replace(ops.io)==0 and fs.files=={b'save':updated}
        for image in ops.snapshots:
            clean=Files();clean.files=image.copy();assert recover(clean)==0;snapshots+=1
        for after in (False,True):
            for step in range(1,ops.count+1):
                fs=Files();fs.files[b'save']=original;bad=Operations(fs,step,after);assert replace(bad.io)!=0
                clean=Files();clean.files=fs.files.copy();assert recover(clean)==0;faults+=1
    # Old state writers reject V3 even if its yellow flags are zero.
    for blob in (updated,originals[2]):
        fs=Files();fs.files[b'save']=blob
        assert lib.v6_campaign_state_replace(C.byref(fs.io),b'save',b'temp',b'backup',C.byref(old),C.byref(r),C.byref(oldmap))==4
        assert fs.files=={b'save':blob}
    class Altered(Files):
        def write(self,h,p,n):
            result=super().write(h,p,n);name=self.handles[h][0];data=bytearray(self.files[name]);data[40]^=1
            struct.pack_into('>I',data,92,zlib.crc32(data[:92]));self.files[name]=bytes(data);return result
    fs=Altered();assert replace(fs.io)==4 and fs.files=={}
    # Invalid pointers/modes and read failures publish none of the four outputs.
    for missing in range(4):
        args=[C.byref(x) for x in (c,r,y,e)];args[missing]=None
        out=(C.c_uint8*96)(*([165]*96))
        assert not lib.v6_campaign_progress_encode(out,96,*args) and bytes(out)==bytes([165]*96)
    for mode in ('time_trial','translator_exploring'):
        bad=Yellow.from_buffer_copy(bytes(y));setattr(bad,mode,1)
        out=(C.c_uint8*96)(*([165]*96))
        assert not lib.v6_campaign_progress_encode(out,96,C.byref(c),C.byref(r),C.byref(bad),C.byref(e))
        assert bytes(out)==bytes([165]*96)
    for fault,payload in [(v,updated) for v in ('read','tail','close-read')]+[('',updated[:n]) for n in range(96)]+[('',updated+b'x')]:
        fs=Files(fault);fs.files[b'save']=payload
        out=[Checkpoint(*([77]*7)),Story(*([88]*5)),Yellow(*([99]*5)),Exploration.from_buffer_copy(bytes([55]*50))]
        before=tuple(bytes(x) for x in out)
        assert lib.v6_campaign_progress_read(C.byref(fs.io),b'save',*[C.byref(x) for x in out])!=0
        assert tuple(bytes(x) for x in out)==before and not fs.handles
    print(f'PASS progress save: 64 flag combinations ({valid} valid), 400 map bits, 768 corruptions, V1/V2 migration, {snapshots} interruption snapshots, {faults} replacement faults, older-writer and altered-readback guards')
if __name__=='__main__':main()
