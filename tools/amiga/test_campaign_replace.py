#!/usr/bin/env python3
"""Save replacement operation failures and interruption snapshots."""
import ctypes as C
from pathlib import Path
from test_campaign_file import Files,IO,Exists,Open,Read,Write,Close,Rename
from test_campaign_save import Checkpoint,Story,values
ROOT=Path(__file__).resolve().parents[2]
class Operations:
    def __init__(self,fs,fail=None,after=False):
        self.count=0;self.snapshots=[]
        def wrap(name,fn,failure):
            def call(*args):
                self.count+=1
                failing=self.count==fail
                if failing and not after and name!='close':return failure
                result=fn(*args);self.snapshots.append(dict(fs.files))
                return failure if failing else result
            return call
        self.io=IO(Exists(wrap('exists',fs.exists,-1)),Open(wrap('open',fs.open,0)),Read(wrap('read',fs.read,-1)),Write(wrap('write',fs.write,-1)),Close(wrap('close',fs.close,0)),Rename(wrap('rename',fs.rename,0)),Exists(wrap('remove',fs.remove,0)))
def main():
    lib=C.CDLL(str(ROOT/'build/amiga-campaign-save/file.so'))
    signature=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.c_char_p]
    lib.v6_campaign_replace.argtypes=signature+[C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.v6_campaign_recover.argtypes=signature+[C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.v6_campaign_write_new.argtypes=[C.POINTER(IO),C.c_char_p,C.c_char_p,C.POINTER(Checkpoint),C.POINTER(Story)]
    old=Checkpoint(140,1822,1,1,109,109,505147);new=Checkpoint(*values(old));new.dir=0
    story=Story(0,0,9,1,1)
    f=Files();assert lib.v6_campaign_write_new(C.byref(f.io),b'save',b'temp',C.byref(old),C.byref(story))==0
    original=f.files[b'save']
    def replace(io):return lib.v6_campaign_replace(C.byref(io),b'save',b'temp',b'backup',C.byref(new),C.byref(story))
    def recover(fs):
        a=Checkpoint(*([77]*7));b=Story(*([88]*5));before=bytes(a),bytes(b)
        result=lib.v6_campaign_recover(C.byref(fs.io),b'save',b'temp',b'backup',C.byref(a),C.byref(b))
        if result:assert (bytes(a),bytes(b))==before
        else:assert values(a) in (values(old),values(new)) and values(b)==values(story)
        return result,a
    f=Files();f.files[b'save']=original;ops=Operations(f);assert replace(ops.io)==0
    updated=f.files[b'save'];assert updated!=original and set(f.files)=={b'save'}
    snapshots=ops.snapshots;steps=ops.count
    for image in snapshots:
        fs=Files();fs.files=dict(image);result,a=recover(fs);assert result==0,(image,result)
        assert fs.files[b'save'] in (original,updated) and set(fs.files)=={b'save'}
        assert recover(fs)[0]==0  # idempotent
    for after in (False,True):
        for step in range(1,steps+1):
            fs=Files();fs.files[b'save']=original;ops=Operations(fs,step,after)
            result=replace(ops.io);assert result!=0,(step,after)
            # Every interrupted replacement leaves a complete old or new record.
            assert original in fs.files.values() or updated in fs.files.values(),(step,after,fs.files)
            clean=Files();clean.files=dict(fs.files);assert recover(clean)[0]==0,(step,after,fs.files)
    for names in ((b'save',b'SAVE',b'backup'),(b'save',b'temp',b'TEMP')):
        fs=Files();assert lib.v6_campaign_replace(C.byref(fs.io),*names,C.byref(new),C.byref(story))==1 and not fs.calls
    recovery_faults=0
    states=[{b'backup':original,b'temp':updated},{b'save':updated,b'backup':original},{b'save':original,b'temp':b'partial'},{b'save':original,b'backup':original,b'temp':updated}]
    for image in states:
        fs=Files();fs.files=image.copy();ops=Operations(fs);a=Checkpoint();b=Story()
        assert lib.v6_campaign_recover(C.byref(ops.io),b'save',b'temp',b'backup',C.byref(a),C.byref(b))==0
        for after in (False,True):
            for step in range(1,ops.count+1):
                fs=Files();fs.files=image.copy();bad=Operations(fs,step,after);a=Checkpoint(*([77]*7));b=Story(*([88]*5));before=bytes(a),bytes(b)
                recovery_faults+=1
                result=lib.v6_campaign_recover(C.byref(bad.io),b'save',b'temp',b'backup',C.byref(a),C.byref(b))
                assert result!=0 and (bytes(a),bytes(b))==before
                clean=Files();clean.files=dict(fs.files);assert recover(clean)[0]==0
    for image in ({b'save':b'bad',b'backup':original},{b'backup':b'bad',b'temp':updated},{b'save':original,b'backup':b'bad'},{b'temp':updated}):
        fs=Files();fs.files=image.copy();assert recover(fs)[0]!=0 and fs.files==image
    print(f'PASS replacement: {len(snapshots)} interruption snapshots, {steps*2} replacement faults, {recovery_faults} recovery faults, corruption preservation and idempotence')
if __name__=='__main__':main()
