#!/usr/bin/env python3
"""Independent V4 vectors, migration and interrupted collection-save recovery."""
import ctypes as C
import struct
import zlib
from test_campaign_save import ROOT, Checkpoint, Story, values
from test_campaign_state import Exploration
from test_station_trigger import Story as Yellow
from test_campaign_file import Files, IO, Read, main as build_file
from test_campaign_replace import Operations

class Collect(C.Structure):
    _fields_=[('bits',C.c_uint8*13)]

def main():
    build_file()
    lib=C.CDLL(str(ROOT/'build/amiga-campaign-save/file.so'))
    types=(Checkpoint,Story,Yellow,Exploration,Collect)
    ptrs=[C.POINTER(t) for t in types]
    lib.v6_campaign_collection_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs
    lib.v6_campaign_collection_decode.argtypes=ptrs+[C.c_void_p,C.c_size_t]
    lib.v6_campaign_collection_read.argtypes=[C.POINTER(IO),C.c_char_p]+ptrs
    lib.v6_campaign_collection_write_new.argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p]+ptrs
    for name in ('recover','replace'):
        getattr(lib,'v6_campaign_collection_'+name).argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p]+ptrs
    oldc=Checkpoint(156,92,0,0,111,104,0)
    c=Checkpoint(20,110,1,1,111,106,442491)
    r=Story();y=Yellow(0,0,7,1,1);e=Exploration();e.rooms[131>>3]=1<<(131&7)
    def refs(items):return [C.byref(x) for x in items]
    def snapshot(items):return tuple(bytes(x) for x in items)
    def outputs():
        return [t.from_buffer_copy(bytes([37+i]*C.sizeof(t))) for i,t in enumerate(types)]
    def vector(state,version=4):
        c,r,y,e,b=state
        flags=r.rescue_triggered|r.red_rescued<<1|(r.companion==9)<<2|y.rescue_triggered<<3|y.yellow_rescued<<4|(y.companion==7)<<5
        body=struct.pack('>4sHH7iI',b'V6CS',version,112 if version==4 else 44 if version==1 else 96,*values(c),flags)
        if version!=1:body+=bytes(e)
        if version==4:body+=bytes(b)+bytes(5)
        elif version!=1:body+=bytes(2)
        return body+struct.pack('>I',zlib.crc32(body))
    def encode(state):
        raw=(C.c_uint8*112)(*([165]*112))
        assert lib.v6_campaign_collection_encode(raw,112,*refs(state))
        assert bytes(raw)==vector(state)
        return bytes(raw)
    def decode(blob,expected=None):
        out=outputs();before=snapshot(out)
        raw=(C.c_uint8*len(blob)).from_buffer_copy(blob)
        ok=lib.v6_campaign_collection_decode(*refs(out),raw,len(blob))
        assert bool(ok)==(expected is not None)
        assert snapshot(out)==(snapshot(expected) if ok else before)
    bank=Collect();state=[c,r,y,e,bank]
    for bit in range(100):
        bank.bits[bit>>3]|=1<<(bit&7)
        decode(encode(state),state)
    updated=encode(state)
    for bit in range(896):
        bad=bytearray(updated);bad[bit>>3]^=1<<(bit&7);decode(bad)
    for n in range(112):decode(updated[:n])
    decode(updated+b'x')
    def resign(blob):
        struct.pack_into('>I',blob,108,zlib.crc32(blob[:108]));return blob
    for offset in (0,4,5,6,7,103,104,105,106,107):
        bad=bytearray(updated);bad[offset]^=1;decode(resign(bad))
    for spare in range(16,256):
        bad=bytearray(updated);bad[102]=spare;decode(resign(bad))
    for offset,value in ((8,321),(12,241),(16,2),(20,2),(24,112),(28,107),(32,0xfffffffe),(36,64),(36,8),(36,32),(36,63)):
        bad=bytearray(updated);struct.pack_into('>I',bad,offset,value);decode(resign(bad))
    bad=bytearray(updated);bad[40+(131>>3)]=0;decode(resign(bad))
    # Legacy readers/writers must refuse V4, leaving outputs and files intact.
    for name,ts in (('v6_campaign_decode',types[:2]),('v6_campaign_state_decode',(Checkpoint,Story,Exploration)),('v6_campaign_progress_decode',types[:4])):
        fn=getattr(lib,name);fn.argtypes=[C.POINTER(t) for t in ts]+[C.c_void_p,C.c_size_t]
        out=[t.from_buffer_copy(bytes([77]*C.sizeof(t))) for t in ts];before=snapshot(out)
        raw=(C.c_uint8*112).from_buffer_copy(updated)
        assert not fn(*refs(out),raw,112) and snapshot(out)==before
    oldmap=Exploration();oldmap.rooms[91>>3]=1<<(91&7)
    oldstate=[oldc,r,Yellow(),oldmap,Collect()]
    originals=[vector(oldstate,v) for v in (1,2,3)]+[encode(oldstate)]
    for blob in originals:decode(blob,oldstate)
    # V4 alone admits the reviewed Prize checkpoint and its actual map bit.
    prize_map=Exploration();prize_map.rooms[151>>3]=1<<(151&7)
    prize=Checkpoint(236,134,1,1,111,107,443490)
    prize_state=[prize,r,y,prize_map,bank]
    prize_blob=encode(prize_state);decode(prize_blob,prize_state)
    for offset,value in ((8,235),(12,135),(16,0),(20,2),(24,112),(28,108),(32,443491)):
        bad=bytearray(prize_blob);struct.pack_into('>I',bad,offset,value);decode(resign(bad))
    bad=bytearray(prize_blob);bad[40+(151>>3)]=0;decode(resign(bad))
    prize.dir=0;decode(encode(prize_state),prize_state);prize.dir=1
    for version in (1,2,3):decode(vector(prize_state,version))
    legacy=(C.c_uint8*96)(*([165]*96))
    lib.v6_campaign_progress_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs[:4]
    assert not lib.v6_campaign_progress_encode(legacy,96,*refs(prize_state[:4]))
    assert bytes(legacy)==bytes([165]*96)
    # Exercise every transaction fault against the newly admitted room, too.
    state=prize_state;updated=prize_blob
    def replace(io):return lib.v6_campaign_collection_replace(C.byref(io),b'save',b'temp',b'backup',*refs(state))
    def recover(fs,io=None):
        out=outputs();before=snapshot(out)
        result=lib.v6_campaign_collection_recover(C.byref(io or fs.io),b'save',b'temp',b'backup',*refs(out))
        if result:assert snapshot(out)==before
        else:assert snapshot(out) in (snapshot(oldstate),snapshot(state))
        return result
    snapshots=faults=recovery_faults=0
    for original in originals:
        fs=Files();fs.files[b'save']=original;ops=Operations(fs)
        assert replace(ops.io)==0 and fs.files=={b'save':updated}
        for image in ops.snapshots:
            clean=Files();clean.files=image.copy();assert recover(clean)==0
            assert recover(clean)==0;snapshots+=1
        for after in (False,True):
            for step in range(1,ops.count+1):
                fs=Files();fs.files[b'save']=original;bad=Operations(fs,step,after)
                assert replace(bad.io)!=0
                assert original in fs.files.values() or updated in fs.files.values()
                clean=Files();clean.files=fs.files.copy();assert recover(clean)==0;faults+=1
        for image in ({b'backup':original,b'temp':updated},{b'save':updated,b'backup':original},{b'save':original,b'temp':b'partial'}):
            fs=Files();fs.files=image.copy();ops=Operations(fs);assert recover(fs,ops.io)==0
            for after in (False,True):
                for step in range(1,ops.count+1):
                    fs=Files();fs.files=image.copy();bad=Operations(fs,step,after)
                    assert recover(fs,bad.io)!=0
                    clean=Files();clean.files=fs.files.copy();assert recover(clean)==0;recovery_faults+=1
    for fault in ('exists','open-write','write','short-write','close-write','open-read','read','tail','close-read','corrupt','rename'):
        fs=Files(fault)
        assert lib.v6_campaign_collection_write_new(C.byref(fs.io),b'save',b'temp',*refs(state))!=0
        assert b'save' not in fs.files and not fs.handles
    for names in ((b'save',b'SAVE',b'backup'),(b'save',b'temp',b'TEMP')):
        fs=Files();assert lib.v6_campaign_collection_replace(C.byref(fs.io),*names,*refs(state))==1 and not fs.calls
    # Existing V1/V2/V3 replacement entry points cannot discard a V4 bank.
    for name,legacy_state in (('v6_campaign_replace',oldstate[:2]),
            ('v6_campaign_state_replace',[oldc,r,oldmap]),
            ('v6_campaign_progress_replace',oldstate[:4])):
        fn=getattr(lib,name)
        fn.argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p]+[C.POINTER(type(x)) for x in legacy_state]
        fs=Files();fs.files[b'save']=updated
        assert fn(C.byref(fs.io),b'save',b'temp',b'backup',*refs(legacy_state))!=0
        assert fs.files=={b'save':updated}
    for image in ({b'save':b'bad',b'backup':updated},{b'backup':b'bad',b'temp':updated},{b'save':updated,b'backup':b'bad'},{b'temp':updated}):
        fs=Files();fs.files=image.copy();assert recover(fs)!=0 and fs.files==image
    for fault,payload in [(v,updated) for v in ('open-read','read','tail','close-read')]+[('',updated[:-1]),('',updated+b'x')]:
        fs=Files(fault);fs.files[b'save']=payload;out=outputs();before=snapshot(out)
        assert lib.v6_campaign_collection_read(C.byref(fs.io),b'save',*refs(out))!=0
        assert snapshot(out)==before and not fs.handles
    # Valid CRC but altered collection readback must never be promoted.
    fs=Files();real_read=fs.read
    def altered_read(h,p,n):
        got=real_read(h,p,n)
        if got==112:
            blob=bytearray(C.string_at(p,112));blob[90]^=1
            C.memmove(p,bytes(resign(blob)),112)
        return got
    callback=Read(altered_read);fs.io.read=callback
    assert lib.v6_campaign_collection_write_new(C.byref(fs.io),b'save',b'temp',*refs(state))!=0
    assert b'save' not in fs.files
    # Invalid encoder input never writes partial output or opens files.
    bank.bits[12]=16;raw=(C.c_uint8*112)(*([165]*112))
    assert not lib.v6_campaign_collection_encode(raw,112,*refs(state)) and bytes(raw)==bytes([165]*112)
    fs=Files();assert replace(fs.io)==1 and not fs.calls
    bank.bits[12]=15
    for n in (0,44,96,111,113):
        assert not lib.v6_campaign_collection_encode(raw,n,*refs(state))
        assert bytes(raw)==bytes([165]*112)
    for i in range(5):
        arguments=refs(state);arguments[i]=None
        assert not lib.v6_campaign_collection_encode(raw,112,*arguments)
        out=outputs();arguments=refs(out);arguments[i]=None;before=snapshot(out)
        source=(C.c_uint8*112).from_buffer_copy(updated)
        assert not lib.v6_campaign_collection_decode(*arguments,source,112)
        assert snapshot(out)==before
    print(f'PASS collection saves: 100 bank vectors, 896 corruptions, canonical V4 Prize guards, V1..V3 migrations, {snapshots} interruption snapshots, {faults} replacement faults, {recovery_faults} recovery faults')

if __name__=='__main__':main()
