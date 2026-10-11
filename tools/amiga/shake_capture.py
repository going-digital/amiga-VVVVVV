"""Validate native fixed-tick shake records independently of gameplay RNG."""
import struct

def verify(report,dump,build):
    data=dump.read_bytes();at=data.index(b'V6SH\0\0\0\1')
    count=struct.unpack_from('>I',data,at+8)[0]
    records=[struct.unpack_from('>3i',data,at+12+12*i) for i in range(count)]
    seed=19
    for timer,x,y in records:
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
    report['scope']='Native register-based staged teleporter shake; gameplay and independent effect RNG verified; persistence and explored menu destinations pending'
