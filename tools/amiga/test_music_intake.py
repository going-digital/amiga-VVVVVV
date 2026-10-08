#!/usr/bin/env python3
"""Independent MOD byte fixtures for music intake bounds and channel conflicts."""
from audit_music import audit,catalogue

def fixture():
    data=bytearray(1084+2048+16)
    data[1080:1084]=b'M.K.';data[950]=2;data[953]=1
    data[42:44]=(8).to_bytes(2,'big');data[45]=64
    # Pattern 0, row 0, channel 0: instrument 1, period 428.
    data[1084:1088]=bytes((1,172,16,0))
    # Pattern 1, row 0, channel 3: effect-only volume 32.
    data[1084+1024+12:1084+1024+16]=bytes((0,0,12,32))
    return data

def main():
    tracks=catalogue()['tracks']
    assert [t['id'] for t in tracks]==list(range(16))
    assert [t['id'] for t in tracks if not t['loop']]==[0,7]
    assert tracks[9]['source_file']=='music/9positiveforcereversed.ogg'
    data=fixture();r=audit(data,12)
    assert (r['sample_bytes'],r['pattern_bytes'],r['active_mask'])==(16,2048,9)
    assert r['channel_event_counts']==[1,0,0,1] and r['conflicting_channels']==[3]
    assert r['instruments_used']==[1] and r['effect_commands']==[12]
    data[950]=1;r=audit(data,12)
    assert r['stored_patterns']==2 and r['active_mask']==1 and not r['conflicting_channels']
    assert audit(data+b'abc')['trailing_bytes']==3
    rejected=0
    for at,value in ((1080,ord('X')),(950,0),(950,129),(952,128),
        (44,16),(45,65),(48,1),(1084,240)):
        bad=fixture();bad[at]=value
        try:audit(bad)
        except ValueError:rejected+=1
        else:raise AssertionError((at,value))
    for end in (0,1083,1084,1084+2048+15):
        try:audit(fixture()[:end])
        except ValueError:rejected+=1
        else:raise AssertionError(end)
    for mask in (-1,16):
        try:audit(fixture(),mask)
        except ValueError:rejected+=1
        else:raise AssertionError(mask)
    print(f'PASS music intake: 16 source IDs, loop policy, sample/pattern sizes, effect-only channel conflicts, {rejected} invalid fixtures')
if __name__=='__main__':main()
