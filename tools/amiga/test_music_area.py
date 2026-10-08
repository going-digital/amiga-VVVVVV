#!/usr/bin/env python3
"""Room-selection/controller coupling against desktop changemusicarea body."""
import ctypes as C
import itertools
from test_music_control import libraries,State,Plan,FIELDS

def main():
    core,ref=libraries();s=State();expected=State();p=Plan();count=0
    core.v6_music_area_track.argtypes=[C.c_int,C.c_int,C.c_int,C.c_int,C.c_int,C.POINTER(C.c_int)]
    core.v6_music_change_area.argtypes=[C.POINTER(State),C.c_int,C.c_int,C.c_int,C.c_int,C.c_int,C.POINTER(Plan)]
    def init():
        assert core.v6_music_init(C.byref(s),65535);ref.reference_init(65535)
    def check():
        nonlocal count
        ref.reference_snapshot(C.byref(expected))
        assert bytes(s)==bytes(expected),[(n,getattr(s,n),getattr(expected,n)) for n in FIELDS if getattr(s,n)!=getattr(expected,n)]
        count+=1
    # Fresh state exposes the selected source ID through nicechange. Script and
    # no-change rooms leave it at -1, so no hand-copied reference map is used.
    selections=0
    for running,flip,trial in itertools.product(range(2),repeat=3):
        for y,x in itertools.product(range(20),repeat=2):
            init();track=C.c_int(99)
            ref.reference_area(x,y,running,flip,trial);ref.reference_snapshot(C.byref(expected))
            assert core.v6_music_area_track(x,y,running,flip,trial,C.byref(track))
            assert track.value==expected.queued,(x,y,running,flip,trial,track.value,expected.queued)
            assert core.v6_music_change_area(C.byref(s),x,y,running,flip,trial,C.byref(p));check()
            assert p.count==0 # niceplay queues, it does not start the player.
            selections+=1
    # Complete route sweeps while transitions/fades are already in flight.
    # A script-owned entry must preserve a queued request and its fade envelope.
    for flip,trial in itertools.product(range(2),repeat=2):
        init();assert core.v6_music_command(C.byref(s),0,2,C.byref(p));ref.reference_command(0,2)
        for y,x in itertools.product(range(20),repeat=2):
            for running in (0,1):
                before=bytes(s)
                assert core.v6_music_change_area(C.byref(s),x,y,running,flip,trial,C.byref(p))
                ref.reference_area(x,y,running,flip,trial);check()
                if running:assert bytes(s)==before and not p.count
                for _ in range(5):
                    assert core.v6_music_tick(C.byref(s),34,C.byref(p));ref.reference_tick(34);check()
    for args in ((-1,0,0,0,0),(20,0,0,0,0),(0,-1,0,0,0),(0,20,0,0,0),
        (2147483647,2147483647,0,0,0),(0,0,2,0,0),(0,0,0,-1,0),(0,0,0,0,2)):
        track=C.c_int(99);before=(bytes(s),bytes(p))
        assert not core.v6_music_area_track(*args,C.byref(track)) and track.value==99
        assert not core.v6_music_change_area(C.byref(s),*args,C.byref(p))
        assert before==(bytes(s),bytes(p))
    assert not core.v6_music_area_track(0,0,0,0,0,None)
    assert not core.v6_music_change_area(None,0,0,0,0,0,C.byref(p))
    assert not core.v6_music_change_area(C.byref(s),0,0,0,0,0,None)
    s.volume=129;before=(bytes(s),bytes(p))
    # Even script/no-change paths validate the controller transactionally.
    assert not core.v6_music_change_area(C.byref(s),0,0,1,0,0,C.byref(p))
    assert before==(bytes(s),bytes(p))
    print(f'PASS music area: {selections} exhaustive room/flag selections, {count} extracted desktop state comparisons; scripted ownership, tower flip, time trial, pending fades and invalid-input preservation')
if __name__=='__main__':main()
