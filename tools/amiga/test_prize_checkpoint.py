#!/usr/bin/env python3
"""Input-only V Stitch lower passage -> Prize checkpoint -> local respawn."""
import ctypes as C
from test_prize_input import expected as north_expected,ROOT
from tower_gameplay_data import shenanigan_room,prize_room,vstitch_room
COUNT=302

def expected():
    north_expected() # Build the shared host oracle and retain the north-route regression.
    core=C.CDLL(str(ROOT/'build/amiga-prize-input-host/core.so'))
    core.prize_checkpoint_fixture.argtypes=[C.POINTER(C.c_uint16)]*3+[C.POINTER(C.c_int32),C.c_uint]
    rooms=[(C.c_uint16*1200)(*r()['tiles']) for r in (shenanigan_room,prize_room,vstitch_room)]
    trace=(C.c_int32*(COUNT*24))()
    assert core.prize_checkpoint_fixture(*rooms,trace,COUNT)
    rows=[tuple(trace[i*24:(i+1)*24]) for i in range(COUNT)]
    assert [i+1 for i,r in enumerate(rows) if i and r[0]!=rows[i-1][0]]==[173]
    assert rows[172][:5]==(8,303,185,0,-1)
    assert all(r[0]==9 and r[2]>=112 for r in rows[:172]) # Upper intro trigger never touched.
    activations=[i+1 for i,r in enumerate(rows) if r[5]==443490]
    assert activations[0]==195
    assert sum(a[3]!=b[3] for a,b in zip(rows[:172],rows[1:172]))==8
    assert rows[activations[0]-1][5:11]==(443490,236,134,1,111,107)
    assert [i+1 for i,r in enumerate(rows) if r[4]==30]==[224]
    assert rows[224][13]==152 and rows[253][:5]==(8,236,134,1,-1)
    assert all(r[23]==1 and r[5:11]==(443490,236,134,1,111,107) for r in rows[253:])
    assert all(r[15]==r[17]==r[16]==0 for r in rows)
    return rows

if __name__=='__main__':
    rows=expected()
    print(f'PASS Prize checkpoint: {len(rows)} input-only ticks, eight lower-passage flips, west crossing, checkpoint activation, source spike death and local respawn; upper intro and pickup excluded')
