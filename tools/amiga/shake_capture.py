"""Validate native fixed-tick shake records independently of gameplay RNG."""
import struct

def verify(report,dump,build):
    data=dump.read_bytes();at=data.index(b'V6SH\0\0\0\1')
    count=struct.unpack_from('>I',data,at+8)[0]
    records=[struct.unpack_from('>3i',data,at+12+12*i) for i in range(count)]
    dep_at=data.index(b'V6DR\0\0\0\1');arr_at=data.index(b'V6AR\0\0\0\1')
    seed=19
    for tick,(timer,x,y) in enumerate(records):
        dep=struct.unpack_from('>8i',data,dep_at+12+tick*32)
        arr=struct.unpack_from('>14i',data,arr_at+12+tick*56)
        assert timer==(dep[4] if dep[0] else arr[4]),(tick,timer,dep,arr)
        if timer:
            offsets=[]
            for _ in range(2):
                seed^=(seed<<13)&0xffffffff;seed^=seed>>17;seed^=(seed<<5)&0xffffffff
                numerator=(seed>>16)*7-262144
                offsets.append(abs(numerator)//65536*(-1 if numerator<0 else 1))
            assert (x,y)==tuple(offsets),(timer,x,y,offsets)
        else:assert (x,y)==(0,0)
    assert count==report['display']['logic_ticks']
    assert any(r[0] for r in records)
    at=data.index(b'V6PF\0\0\0\1')
    profile=struct.unpack_from('>8I',data,at)
    report['profile']=dict(zip(('max_logic','max_render','peak_logic','peak_render','peak_tick','peak_rows'),profile[2:]))
    assert profile[4]+profile[5]==report['display']['max_work_lines']
    report['shake_records']=records
    report['scope']='Native register-based staged teleporter shake'+(' with reserved two-voice Paula audio' if 'audio_channels' in report else '')+'; gameplay, fixed-tick effects and independent RNG verified; persistence and explored menu destinations pending'
