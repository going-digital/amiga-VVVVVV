#!/usr/bin/env python3
"""Filesystem fault injection and source checkpoint restart validation."""
import ctypes as C
from pathlib import Path
import subprocess
from test_campaign_save import Checkpoint,Story,values
from tower_gameplay_data import checkpoints,hallway_rooms
ROOT=Path(__file__).resolve().parents[2]
Handle=C.c_ssize_t
Exists=C.CFUNCTYPE(C.c_int,C.c_char_p)
Open=C.CFUNCTYPE(Handle,C.c_char_p,C.c_int)
Read=C.CFUNCTYPE(C.c_int,Handle,C.c_void_p,C.c_uint)
Write=Read
Close=C.CFUNCTYPE(C.c_int,Handle)
Rename=C.CFUNCTYPE(C.c_int,C.c_char_p,C.c_char_p)
class IO(C.Structure):
    _fields_=[('exists',Exists),('open',Open),('read',Read),('write',Write),('close',Close),('rename',Rename),('remove',Exists)]
class Bank(C.Structure):
    _fields_=[(n,C.c_int) for n in 'x y tile id active pending'.split()]
class Files:
    def __init__(self,fault=''):
        self.files={};self.handles={};self.fault=fault;self.next=0;self.calls=[]
        self.io=IO(Exists(self.exists),Open(self.open),Read(self.read),Write(self.write),Close(self.close),Rename(self.rename),Exists(self.remove))
    def exists(self,p):return -1 if self.fault=='exists' else int(p in self.files)
    def open(self,p,w):
        self.calls.append(('open',p,w))
        if self.fault==('open-write' if w else 'open-read') or (not w and p not in self.files):return 0
        if w:self.files[p]=b''
        self.next+=1;self.handles[self.next]=[p,0,w];return self.next
    def read(self,h,p,n):
        self.calls.append(('read',n));name,pos,_=self.handles[h]
        if self.fault=='read' or (self.fault=='tail' and n==1):return -1
        data=self.files[name][pos:pos+n];C.memmove(p,data,len(data));self.handles[h][1]+=len(data);return len(data)
    def write(self,h,p,n):
        self.calls.append(('write',n));name,_,_=self.handles[h]
        data=C.string_at(p,n)
        if self.fault=='short-write':data=data[:-1]
        if self.fault=='write':return -1
        if self.fault=='corrupt':data=b'!'+data[1:]
        self.files[name]=data;return len(data)
    def close(self,h):
        _,_,w=self.handles.pop(h);self.calls.append(('close',w))
        return int(self.fault!=('close-write' if w else 'close-read'))
    def rename(self,a,b):
        self.calls.append(('rename',a,b))
        if self.fault=='rename' or b in self.files:return 0
        self.files[b]=self.files.pop(a);return 1
    def remove(self,p):
        if self.fault=='cleanup':return 0
        self.files.pop(p,None);return 1
def main():
    out=ROOT/'build/amiga-campaign-save';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/campaign_save.c'),str(ROOT/'amiga_version/campaign_file.c'),'-o',str(out/'file.so')],check=True)
    lib=C.CDLL(str(out/'file.so'))
    lib.v6_campaign_write_new.argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.v6_campaign_read.argtypes=[C.POINTER(IO),C.c_char_p,C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.v6_campaign_checkpoint_valid.argtypes=[C.POINTER(Checkpoint),C.POINTER(Bank),C.c_uint]
    c=Checkpoint(140,1822,1,1,109,109,505147);s=Story(0,0,9,1,1)
    def save(fs,a=b'save',b=b'temp'):return lib.v6_campaign_write_new(C.byref(fs.io),a,b,C.byref(c),C.byref(s))
    fs=Files();assert save(fs)==0 and len(fs.files[b'save'])==44 and b'temp' not in fs.files
    assert not fs.handles
    a=Checkpoint();b=Story();assert lib.v6_campaign_read(C.byref(fs.io),b'save',C.byref(a),C.byref(b))==0
    assert values(a)==values(c) and values(b)==values(s)
    for path in (b'save',b'temp'):
        f=Files();f.files[path]=b'precious';assert save(f)==2 and f.files=={path:b'precious'} and not f.calls
    f=Files();assert save(f,b'same',b'same')==1 and not f.calls
    faults=('exists','open-write','write','short-write','close-write','open-read','read','tail','close-read','corrupt','rename')
    for fault in faults:
        f=Files(fault);assert save(f)!=0,(fault,f.calls)
        assert b'save' not in f.files and not f.handles,(fault,f.files,f.handles)
    f=Files('short-write');failed_remove=Exists(lambda p:0);f.io.remove=failed_remove
    assert save(f)==3 and b'temp' in f.files and b'save' not in f.files
    f.fault='';assert save(f)==2  # retained temp is not overwritten on retry
    data=fs.files[b'save']
    for fault,payload in [(v,data) for v in ('open-read','read','tail','close-read')]+[('',data[:-1]),('',data+b'x'),('',b'!'+data[1:])]:
        f=Files(fault);f.files[b'save']=payload;a=Checkpoint(*([77]*7));b=Story(*([88]*5));before=bytes(a),bytes(b)
        assert lib.v6_campaign_read(C.byref(f.io),b'save',C.byref(a),C.byref(b))!=0
        assert (bytes(a),bytes(b))==before and not f.handles
    total=0
    for row in checkpoints()+[r['checkpoint'] for r in hallway_rooms()]:
        x,y,tile,ident=row;bank=Bank(x,y,tile,ident,0,0)
        for direction in (0,1):
            a=Checkpoint(x-4,y-(2 if tile==20 else 7),tile==20,direction,109,109,ident)
            assert lib.v6_campaign_checkpoint_valid(C.byref(a),C.byref(bank),1)
            for field in ('x','y','gravity','id','dir'):
                bad=Checkpoint(*values(a));setattr(bad,field,getattr(bad,field)+2)
                assert not lib.v6_campaign_checkpoint_valid(C.byref(bad),C.byref(bank),1)
            total+=1
    print(f'PASS campaign file: verified new save, existing-file preservation, {len(faults)} I/O faults, 7 transactional read failures, {total} source checkpoint spawns and 200 invalid variants')
if __name__=='__main__':main()
