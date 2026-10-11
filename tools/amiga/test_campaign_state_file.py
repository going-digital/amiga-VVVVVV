#!/usr/bin/env python3
"""Full-state replacement/recovery faults retain a coherent checkpoint and map."""
import ctypes as C
import struct
import zlib
from test_campaign_save import ROOT, Checkpoint, Story, values
from test_campaign_state import Exploration
from test_campaign_file import Files, IO, main as build_file
from test_campaign_replace import Operations

def main():
    build_file()
    lib=C.CDLL(str(ROOT/'build/amiga-campaign-save/file.so'))
    ptrs=[C.POINTER(Checkpoint),C.POINTER(Story),C.POINTER(Exploration)]
    for name in ('replace','recover'):
        getattr(lib,'v6_campaign_state_'+name).argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p]+ptrs
    lib.v6_campaign_state_read.argtypes=[C.POINTER(IO),C.c_char_p]+ptrs
    lib.v6_campaign_state_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs
    lib.v6_campaign_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs[:2]
    lib.v6_campaign_replace.argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p]+ptrs[:2]
    old=Checkpoint(156,92,0,0,111,104,0);new=Checkpoint(80,112,0,1,110,105,0);story=Story()
    oldmap=Exploration();oldmap.rooms[91>>3]|=1<<(91&7)
    newmap=Exploration.from_buffer_copy(bytes(oldmap));newmap.rooms[110>>3]|=1<<(110&7)
    def encode(c,e,legacy=False):
        raw=(C.c_uint8*(44 if legacy else 96))()
        args=[raw,len(raw),C.byref(c),C.byref(story)]
        assert (lib.v6_campaign_encode(*args) if legacy else lib.v6_campaign_state_encode(*args,C.byref(e)))
        return bytes(raw)
    updated=encode(new,newmap)
    def replace(io):
        return lib.v6_campaign_state_replace(C.byref(io),b'save',b'temp',b'backup',C.byref(new),C.byref(story),C.byref(newmap))
    def recover(fs,io=None):
        c=Checkpoint(*([77]*7));s=Story(*([88]*5));e=Exploration.from_buffer_copy(bytes([99]*50));before=bytes(c),bytes(s),bytes(e)
        result=lib.v6_campaign_state_recover(C.byref(io or fs.io),b'save',b'temp',b'backup',C.byref(c),C.byref(s),C.byref(e))
        if result:assert (bytes(c),bytes(s),bytes(e))==before
        else:
            assert values(s)==values(story)
            assert (values(c),bytes(e)) in ((values(old),bytes(oldmap)),(values(new),bytes(newmap)))
        return result
    snapshots=faults=0
    for legacy in (False,True):
        original=encode(old,oldmap,legacy)
        f=Files();f.files[b'save']=original;ops=Operations(f);assert replace(ops.io)==0 and f.files=={b'save':updated}
        for image in ops.snapshots:
            fs=Files();fs.files=image.copy();assert recover(fs)==0
            assert fs.files[b'save'] in (original,updated) and set(fs.files)=={b'save'}
            assert recover(fs)==0;snapshots+=1
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
                    clean=Files();clean.files=fs.files.copy();assert recover(clean)==0;faults+=1
    for image in ({b'save':b'bad',b'backup':updated},{b'save':updated,b'backup':b'bad'},{b'backup':b'bad',b'temp':updated},{b'temp':updated}):
        fs=Files();fs.files=image.copy();assert recover(fs)!=0 and fs.files==image
    # A different but checksum-valid readback must never be promoted.
    class Altered(Files):
        def write(self,h,p,n):
            result=super().write(h,p,n);name=self.handles[h][0]
            data=bytearray(self.files[name]);data[40]^=1
            struct.pack_into('>I',data,92,zlib.crc32(data[:92]));self.files[name]=bytes(data)
            return result
    for image in ({},{b'save':encode(old,oldmap)}):
        fs=Altered();fs.files=image.copy();assert replace(fs.io)==4 and fs.files==image
    # The legacy writer cannot destroy a full-state save.
    fs=Files();fs.files[b'save']=updated
    assert lib.v6_campaign_replace(C.byref(fs.io),b'save',b'temp',b'backup',C.byref(old),C.byref(story))==4
    assert fs.files=={b'save':updated}
    # Read faults and malformed lengths retain all outputs.
    for fault,payload in [(v,updated) for v in ('read','tail','close-read')]+[('',updated[:n]) for n in range(96)]+[('',updated+b'x')]:
        fs=Files(fault);fs.files[b'save']=payload
        c=Checkpoint(*([77]*7));s=Story(*([88]*5));e=Exploration.from_buffer_copy(bytes([99]*50));before=bytes(c),bytes(s),bytes(e)
        assert lib.v6_campaign_state_read(C.byref(fs.io),b'save',C.byref(c),C.byref(s),C.byref(e))!=0
        assert (bytes(c),bytes(s),bytes(e))==before and not fs.handles
    print(f'PASS full-state disk: {snapshots} interruption snapshots, {faults} operation faults, legacy upgrades, map/checkpoint coherence and transactional read failures')
if __name__=='__main__':main()
