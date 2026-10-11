#!/usr/bin/env python3
"""Bounded north entry with Prize already saved; input-only puzzle and pickup."""
import ctypes as C
from test_prize_input import expected as north_expected,ROOT
from tower_gameplay_data import shenanigan_room,prize_room
COUNT=180

def expected():
    north=north_expected()
    # Entry coordinates/gravity come from the separately retained north replay.
    assert north[125][1:4]==(10,6,0)
    core=C.CDLL(str(ROOT/'build/amiga-prize-input-host/core.so'))
    core.prize_collection_fixture.argtypes=[C.POINTER(C.c_uint16)]*2+[C.POINTER(C.c_int32),C.c_uint]
    rooms=[(C.c_uint16*1200)(*r()['tiles']) for r in (shenanigan_room,prize_room)]
    trace=(C.c_int32*(COUNT*24))()
    assert core.prize_collection_fixture(*rooms,trace,COUNT)
    rows=[tuple(trace[i*24:(i+1)*24]) for i in range(COUNT)]
    assert all(r[0]==8 and r[5:11]==(443490,236,134,1,111,107) for r in rows)
    assert [i+1 for i,r in enumerate(rows) if r[4]==30]==[67]
    assert rows[30][20:23]==(3,0,0) and rows[48][20:23]==(3,3,0)
    assert rows[64][20:23]==(3,3,3)
    assert rows[67][13]==rows[66][13]==236 and rows[67][16]==1 and rows[67][19]==59
    assert rows[96][:5]==(8,236,134,1,-1) and rows[96][23]==1
    assert rows[114][1:4]==(246,78,1) # Caught underneath the moving platform.
    assert rows[124][1:4]==(196,78,1) # Carried over the alcove.
    assert rows[129][1:4]==(192,124,0) and rows[129][15:19]==(1,1,1,0)
    assert all(r[15:19]==(1,1,1,0) and r[23]==1 for r in rows[129:])
    assert rows[-1][1:5]==(192,129,0,-1)
    return rows

if __name__=='__main__':
    expected()
    print('PASS Prize collection: 180 world ticks, three collapses, one source spike death, local checkpoint respawn, platform catch/carry, flip into alcove and single pickup; pre-saved checkpoint/shaft entry, campaign return connection excluded')
