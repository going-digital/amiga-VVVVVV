#!/usr/bin/env python3
"""Independent V5 hint vectors, migration, admission and transaction faults."""
import ctypes as C
import struct,zlib
from test_campaign_save import ROOT,Checkpoint,Story,values
from test_campaign_state import Exploration
from test_station_trigger import Story as Yellow
from test_campaign_collection import Collect
from test_campaign_file import Files,IO,main as build_file
from test_campaign_replace import Operations
class Hints(C.Structure):
    _fields_=[('map_hint_seen',C.c_int)]
def main():
    build_file();lib=C.CDLL(str(ROOT/'build/amiga-campaign-save/file.so'))
    types=(Checkpoint,Story,Yellow,Exploration,Collect,Hints);ptrs=[C.POINTER(t) for t in types]
    lib.v6_campaign_hint_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs
    lib.v6_campaign_hint_decode.argtypes=ptrs+[C.c_void_p,C.c_size_t]
    for name in ('read','write_new','recover','replace'):
        paths=1 if name=='read' else 2 if name=='write_new' else 3
        getattr(lib,'v6_campaign_hint_'+name).argtypes=[C.POINTER(IO)]+[C.c_char_p]*paths+ptrs
    def refs(state):return [C.byref(x) for x in state]
    def snapshot(state):return tuple(bytes(x) for x in state)
    def outputs():return [t.from_buffer_copy(bytes([37+i]*C.sizeof(t))) for i,t in enumerate(types)]
    def vector(state,version=5):
        c,r,y,e,b,h=state
        flags=r.rescue_triggered|r.red_rescued<<1|(r.companion==9)<<2|y.rescue_triggered<<3|y.yellow_rescued<<4|(y.companion==7)<<5
        if version==5:flags|=h.map_hint_seen<<6
        n=44 if version==1 else 96 if version<4 else 112
        body=struct.pack('>4sHH7iI',b'V6CS',version,n,*values(c),flags)
        if version>1:body+=bytes(e)
        if version>=4:body+=bytes(b)+bytes(5)
        elif version>1:body+=bytes(2)
        return body+struct.pack('>I',zlib.crc32(body))
    def encode(state):
        raw=(C.c_uint8*112)(*([165]*112));assert lib.v6_campaign_hint_encode(raw,112,*refs(state))
        assert bytes(raw)==vector(state);return bytes(raw)
    def decode(blob,expected=None):
        out=outputs();before=snapshot(out);raw=(C.c_uint8*len(blob)).from_buffer_copy(blob)
        ok=lib.v6_campaign_hint_decode(*refs(out),raw,len(blob))
        assert bool(ok)==(expected is not None),(len(blob),expected)
        assert snapshot(out)==(snapshot(expected) if ok else before)
    def resign(blob):struct.pack_into('>I',blob,108,zlib.crc32(blob[:108]));return blob
    e=Exploration();e.rooms[152>>3]=1<<(152&7)
    bank=Collect();state=[Checkpoint(60,73,0,1,112,107,443501),Story(),Yellow(0,0,7,1,1),e,bank,Hints(1)]
    for checkpoint in ((60,73,443501),(276,185,443500)):
        state[0].x,state[0].y,state[0].id=checkpoint
        for direction in (0,1):
            state[0].dir=direction
            for seen in (0,1):state[5].map_hint_seen=seen;decode(encode(state),state)
    state[0]=Checkpoint(60,73,0,1,112,107,443501);state[5].map_hint_seen=1
    for bit in range(100):bank.bits[bit>>3]|=1<<(bit&7);decode(encode(state),state)
    updated=encode(state)
    for bit in range(896):
        bad=bytearray(updated);bad[bit>>3]^=1<<(bit&7);decode(bad)
    for n in range(112):decode(updated[:n])
    decode(updated+b'x')
    for offset in (0,4,5,6,7,103,104,105,106,107):
        bad=bytearray(updated);bad[offset]^=1;decode(resign(bad))
    for offset,value in ((8,61),(12,74),(16,1),(20,2),(24,111),(28,106),(32,443500),(36,128),(36,127),(36,72)):
        bad=bytearray(updated);struct.pack_into('>I',bad,offset,value);decode(resign(bad))
    bad=bytearray(updated);bad[40+(152>>3)]=0;decode(resign(bad))
    for hint in (-1,2):
        state[5].map_hint_seen=hint;raw=(C.c_uint8*112)(*([165]*112))
        assert not lib.v6_campaign_hint_encode(raw,112,*refs(state)) and bytes(raw)==bytes([165]*112)
    state[5].map_hint_seen=1
    # Older readers retain all outputs and writers cannot replace a V5 record.
    for name,ts in (('decode',types[:2]),('state_decode',(Checkpoint,Story,Exploration)),('progress_decode',types[:4]),('collection_decode',types[:5])):
        fn=getattr(lib,'v6_campaign_'+name);fn.argtypes=[C.POINTER(t) for t in ts]+[C.c_void_p,C.c_size_t]
        out=[t.from_buffer_copy(bytes([77]*C.sizeof(t))) for t in ts];before=snapshot(out)
        assert not fn(*refs(out),(C.c_uint8*112).from_buffer_copy(updated),112) and snapshot(out)==before
    oldmap=Exploration();oldmap.rooms[91>>3]=1<<(91&7)
    oldstate=[Checkpoint(156,92,0,0,111,104,0),Story(),Yellow(),oldmap,Collect(),Hints()]
    originals=[vector(oldstate,v) for v in range(1,6)]
    for blob in originals:decode(blob,oldstate)
    # V4 migration retains an existing collection and yellow progress while
    # seeding only the newly introduced hint state.
    prize_map=Exploration();prize_map.rooms[151>>3]=1<<(151&7)
    migrated=[Checkpoint(236,134,1,1,111,107,443490),Story(),Yellow(0,0,7,1,1),prize_map,bank,Hints()]
    decode(vector(migrated,4),migrated)
    decode(encode(migrated),migrated)
    # V Stitch remains unsupported by all old codecs, even with a valid CRC.
    for version in (1,2,3,4):decode(vector(state,version))
    def replace(io):return lib.v6_campaign_hint_replace(C.byref(io),b'save',b'temp',b'backup',*refs(state))
    def recover(fs,io=None):
        out=outputs();before=snapshot(out)
        result=lib.v6_campaign_hint_recover(C.byref(io or fs.io),b'save',b'temp',b'backup',*refs(out))
        if result:assert snapshot(out)==before
        else:assert snapshot(out) in (snapshot(oldstate),snapshot(state))
        return result
    snapshots=faults=recovery_faults=0
    for original in originals:
        fs=Files();fs.files[b'save']=original;ops=Operations(fs)
        assert replace(ops.io)==0 and fs.files=={b'save':updated}
        for image in ops.snapshots:
            clean=Files();clean.files=image.copy();assert recover(clean)==0;snapshots+=1
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
    fs=Files();fs.files[b'save']=updated;before=fs.files.copy()
    lib.v6_campaign_collection_replace.argtypes=[C.POINTER(IO)]+[C.c_char_p]*3+ptrs[:5]
    assert lib.v6_campaign_collection_replace(C.byref(fs.io),b'save',b'temp',b'backup',*refs(oldstate[:5]))!=0 and fs.files==before
    print(f'PASS V5 hint saves: canonical V Stitch checkpoints, 100 bank vectors, 896 corruptions, V1..V4 migration, legacy refusal, {snapshots} interruption snapshots, {faults} replacement faults, {recovery_faults} recovery faults')
if __name__=='__main__':main()
