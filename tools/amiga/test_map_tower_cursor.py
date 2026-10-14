#!/usr/bin/env python3
"""Tower map column against the unmodified original cursor renderer."""
import ctypes as C
from test_map_draw import libraries

def main():
    source=libraries()
    # libraries() compiles map_draw.c into its source comparison library.
    rows=(C.c_uint32*180)();pixels=(C.c_uint8*76800)();x=C.c_int();y=C.c_int()
    source.v6_map_tower_cursor_rows.argtypes=[C.POINTER(C.c_uint32),C.c_uint,C.POINTER(C.c_int),C.POINTER(C.c_int)]
    source.cursor_pixels.argtypes=[C.c_int,C.c_int,C.c_uint,C.c_uint,C.POINTER(C.c_uint8)]
    source.v6_map_cursor_mode.argtypes=[C.c_uint,C.c_uint,C.c_int]
    count=0
    for room_y in (100,104,109,119):
        for state in range(3):
            for delay in range(60):
                mode=source.v6_map_cursor_mode(state,delay,0)
                assert source.v6_map_tower_cursor_rows(rows,mode,C.byref(x),C.byref(y))
                source.cursor_pixels(109,room_y,state,delay,pixels)
                for yy in range(240):
                    for xx in range(320):
                        ink=x.value<=xx<x.value+12 and y.value<=yy<y.value+180 and rows[yy-y.value]&(1<<(31-xx+x.value))
                        assert pixels[yy*320+xx]==(17 if ink else 0),(room_y,state,delay,xx,yy)
                count+=1
    before=bytes(rows);assert not source.v6_map_tower_cursor_rows(rows,3,C.byref(x),C.byref(y)) and bytes(rows)==before
    print('PASS original tower cursor:',count,'states, 55296000 source pixels; invalid output preserved')
if __name__=='__main__':main()
