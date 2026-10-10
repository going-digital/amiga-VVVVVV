#!/usr/bin/env python3
"""Map.cpp main/final/custom room music dispatch against extracted source."""
import ctypes as C
import itertools
from test_music_control import libraries,State,Plan,FIELDS

def main():
    core,ref=libraries();s=State();expected=State();p=Plan();count=0
    core.v6_music_entry_track.argtypes=[C.c_int]*7+[C.POINTER(C.c_int)]
    core.v6_music_enter_room.argtypes=[C.POINTER(State)]+[C.c_int]*7+[C.POINTER(Plan)]
    def compare():
        nonlocal count
        ref.reference_snapshot(C.byref(expected))
        assert bytes(s)==bytes(expected),[(n,getattr(s,n),getattr(expected,n)) for n in FIELDS if getattr(s,n)!=getattr(expected,n)]
        count+=1
    # Cartesian main-map boundaries, final trigger neighbors and extreme values.
    coords=( -2147483648,45,46,47,53,54,55,99,100,109,110,111,119,120,2147483647 )
    for flags in itertools.product(range(2),repeat=5):
        for x,y in itertools.product(coords,repeat=2):
            assert core.v6_music_init(C.byref(s),65535);ref.reference_init(65535)
            ref.reference_room(x,y,*flags);ref.reference_snapshot(C.byref(expected))
            track=C.c_int(99)
            assert core.v6_music_entry_track(x,y,*flags,C.byref(track))
            assert track.value==expected.queued,(x,y,flags,track.value,expected.queued)
            assert core.v6_music_enter_room(C.byref(s),x,y,*flags,C.byref(p));compare()
    # Source final trigger ignores script-running, and final wins over custom.
    track=C.c_int()
    assert core.v6_music_entry_track(46,54,1,1,1,0,1,C.byref(track)) and track.value==15
    # Stateful traversal across main map, final trigger and custom exclusions.
    for _ in range(10):
        for args in ((111,104,0,0,0,0,0),(110,105,0,0,0,0,0),
            (46,54,1,0,1,0,1),(46,54,1,0,0,0,0),(100,100,0,1,0,0,0),
            (109,109,0,0,0,1,0),(120,99,0,0,0,0,0)):
            assert core.v6_music_enter_room(C.byref(s),*args,C.byref(p));ref.reference_room(*args);compare()
            for _ in range(100):
                assert core.v6_music_tick(C.byref(s),34,C.byref(p));ref.reference_tick(34);compare()
    for i in range(5):
        args=[111,104,0,0,0,0,0];args[i+2]=2;before=(bytes(s),bytes(p))
        track=C.c_int(99)
        assert not core.v6_music_entry_track(*args,C.byref(track)) and track.value==99
        assert not core.v6_music_enter_room(C.byref(s),*args,C.byref(p))
        assert before==(bytes(s),bytes(p))
    assert not core.v6_music_enter_room(None,111,104,0,0,0,0,0,C.byref(p))
    assert not core.v6_music_entry_track(111,104,0,0,0,0,0,None)
    print(f'PASS music entry: {count} extracted Map.cpp/control comparisons; wrapping, mode precedence, final time trial, script ownership, custom exclusions and invalid flags')
if __name__=='__main__':main()
