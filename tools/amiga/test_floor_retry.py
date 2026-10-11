#!/usr/bin/env python3
"""Cached downward retry fast path against original recursive testwallsy."""
import ctypes as C
from test_player import build_libraries,Player,Terrain,Room,DynamicBlock

def main():
    core,ref,_=build_libraries()
    core.v6_player_test_y.argtypes=[C.POINTER(Player),C.POINTER(Room),C.POINTER(C.c_int)]
    ref.reference_vertical.argtypes=[C.POINTER(C.c_int)]
    count=0
    for tileset,tile in ((0,80),(1,80),(2,12),(0,14),(0,15),(2,14)):
        for floor in (1,9,26,28,29):
            for pattern in ('row','single','gap'):
                scene=[0]*1200
                for x in range(40):
                    if pattern=='row' or (pattern=='single' and x==10) or (pattern=='gap' and x!=10):
                        scene[floor*40+x]=tile
                tiles=(C.c_uint16*1200)(*scene);room=Room(tiles,tileset,0)
                terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room));room.terrain=C.pointer(terrain)
                for x in (-17,-8,-1,0,*range(62,84),302,308,319):
                    for offset in range(-8,3):
                        for quarter in range(1,45):
                            p=Player();core.v6_player_init(C.byref(p),x,floor*8-23+offset,0)
                            p.vy=quarter*(16777216//4)
                            for target_offset in (0,1):
                                actual=Player.from_buffer_copy(p);expected=Player()
                                target=C.c_int(int(p.y+p.vy/16777216)+target_offset)
                                wanted=C.c_int(target.value)
                                ref.reference_init(C.byref(p),tiles,tileset,0)
                                result=ref.reference_vertical(C.byref(wanted))
                                ref.reference_read(C.byref(expected))
                                allowed=core.v6_player_test_y(C.byref(actual),C.byref(room),C.byref(target))
                                assert (allowed,target.value,actual.vy)==(result,wanted.value,expected.vy),(
                                    tileset,tile,floor,pattern,x,offset,quarter,target_offset,
                                    (allowed,target.value,actual.vy),(result,wanted.value,expected.vy))
                                count+=1
    ref.reference_vertical_blocks.argtypes=[C.POINTER(DynamicBlock),C.c_uint]
    dynamic=0
    for width,height,kind,trigger in ((32,8,0,0),(16,1,0,0),(0,8,0,0),(32,0,0,0),
                                     (32,8,1,0),(32,8,2,0),(32,8,2,1),(32,8,2,3)):
        for floor in (72,152,208):
            for nearer in (False,True):
                blocks=(DynamicBlock*3)(DynamicBlock(80,floor,width,height,kind,trigger),
                    DynamicBlock(80,floor-3,32 if nearer else 0,1,0,0),
                    DynamicBlock(80,floor,32,8,0,0))
                tiles=(C.c_uint16*1200)();room=Room(tiles,0,0,None,blocks,3)
                terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room));room.terrain=C.pointer(terrain)
                for x in (62,63,64,73,80,94,105,106,112):
                    for offset in range(-8,3):
                        for quarter in range(1,45):
                            p=Player();core.v6_player_init(C.byref(p),x,floor-23+offset,0)
                            p.vy=quarter*(16777216//4);p.ground=2
                            actual=Player.from_buffer_copy(p);expected=Player()
                            target=C.c_int(int(p.y+p.vy/16777216));wanted=C.c_int(target.value)
                            ref.reference_init(C.byref(p),tiles,0,0)
                            ref.reference_vertical_blocks(blocks,3)
                            result=ref.reference_vertical(C.byref(wanted));ref.reference_read(C.byref(expected))
                            allowed=core.v6_player_test_y(C.byref(actual),C.byref(room),C.byref(target))
                            assert (allowed,target.value,actual.vy)==(result,wanted.value,expected.vy),(
                                width,height,kind,trigger,floor,nearer,x,offset,quarter,
                                (allowed,target.value,actual.vy),(result,wanted.value,expected.vy))
                            count+=1;dynamic+=1
    print(f'PASS floor retries: {count} original C++ comparisons; allowed move, pending Y and exact velocity; fractions, embedded/edge starts, interior-only tiles, directional tiles, row exclusion and non-motion targets; {dynamic} dynamic-floor cases')
if __name__=='__main__':main()
