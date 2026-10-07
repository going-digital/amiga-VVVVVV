#!/usr/bin/env python3
"""Resident ordinary-room crossings against the desktop Logic.cpp blocks."""
import ctypes as C
import subprocess
from test_tower_route import ROOT, OUT, Route, RouteRoom, route_setup, libraries, block, encode

def reference():
    source=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    vertical=block(source,source.index('        if (!map.warpy && !map.towermode)'))
    horizontal=block(source,source.index('        if (!map.warpx && !map.towermode)'))
    source=(ROOT/'desktop_version/src/Map.cpp').read_text()
    history=block(source,source.index('    if (INBOUNDS_VEC(player_idx, obj.entities))',source.index('void mapclass::gotoroom(')))
    wrapper='''#include <vector>
#define INBOUNDS_VEC(i,v) ((i)==0)
struct entclass {int xp,yp,oldxp,oldyp,lerpoldxp,lerpoldyp,vx,vy;};
struct Obj {std::vector<entclass> entities;int getplayer(){return 0;}} obj;
struct Map {bool warpy,warpx,towermode;} map;
struct Game {int roomx,roomy;} game;
int calls;
void enter(int x,int y) {
game.roomx=x;game.roomy=y;++calls;
int player_idx=0;
'''+history+'''\n}
#define GOTOROOM(x,y) enter(x,y)
extern "C" void reference(int *v) {
obj.entities.resize(1);obj.entities[0]={v[0],v[1],-123,-456,0,0,3,-2};
game.roomx=108;game.roomy=109;calls=0;
'''+vertical+'\n'+horizontal+'''
v[0]=obj.entities[0].xp;v[1]=obj.entities[0].yp;
v[2]=obj.entities[0].oldxp;v[3]=obj.entities[0].oldyp;
v[4]=game.roomx;v[5]=game.roomy;v[6]=calls;
}
'''
    path=OUT/'boundary_reference.cpp';path.write_text(wrapper)
    binary=OUT/'boundary_reference.so'
    subprocess.run(['c++','-std=c++11','-shared','-fPIC','-O2','-fsanitize=undefined',
                    '-fno-sanitize-recover=all',str(path),'-o',str(binary)],check=True)
    fn=C.CDLL(str(binary)).reference;fn.argtypes=[C.POINTER(C.c_int)]
    return fn

def fixture(core):
    r,s,w,keep=route_setup(core)
    rooms=(RouteRoom*9)()
    desc=keep[2][2]
    for i in range(9):
        rooms[i]=RouteRoom(107+i%3,108+i//3,desc.packed,desc.bytes,None,0,None,None,2)
    r.rooms=rooms;r.count=9;r.index=4
    assert core.v6_tower_route_load(C.byref(r),108,109,0)
    return r,s,w,(keep,rooms)

def main():
    core,_=libraries();ref=reference()
    core.v6_tower_route_boundary.argtypes=[C.POINTER(Route)]
    cases=0
    for x in (-22,-15,-14,-13,0,140,306,307,308,309,320,326):
        for y in (-10,-3,-2,-1,0,120,236,237,238,246):
            for gravity in (0,1):
                for direction in (0,1):
                    r,s,w,keep=fixture(core)
                    s.player.x=x;s.player.y=y;s.player.old_x=-123;s.player.old_y=-456
                    s.player.gravity=gravity;s.player.dir=direction
                    s.player.vx=3*16777216;s.player.vy=-2*16777216
                    saved=bytes(w.save);transitions=r.transitions
                    expected=(C.c_int*7)(x,y,0,0,0,0,0);ref(expected)
                    assert core.v6_tower_route_boundary(C.byref(r))
                    here=r.rooms[r.index]
                    got=(s.player.x,s.player.y,s.player.old_x,s.player.old_y,
                         here.x,here.y,r.transitions-transitions)
                    assert got==tuple(expected),(x,y,got,tuple(expected))
                    assert not r.error and not s.camera.y and not s.camera.old_y
                    assert (s.player.vx,s.player.vy,s.player.gravity,s.player.dir)==(3*16777216,-2*16777216,gravity,direction)
                    assert bytes(w.save)==saved
                    cases+=1
    # Missing and malformed destinations retain the failed edge's coordinates
    # and live bank. Repeated calls stay rejected once the error is latched.
    failures=0
    for malformed in (False,True):
        for x,y in ((140,238),(140,-3),(-15,120),(308,120)):
            r,s,w,keep=fixture(core)
            s.player.x=x;s.player.y=y
            target=4+(3 if y>=238 else -3 if y< -2 else -1 if x< -14 else 1)
            bad=(C.c_uint8*4)(128,0,0,0)
            if malformed:
                keep[1][target].packed=bad;keep[1][target].bytes=4
            else: keep[1][target].x=999
            before=bytes(w),r.index,r.transitions,bytes(s)
            assert not core.v6_tower_route_boundary(C.byref(r)) and r.error
            assert (bytes(w),r.index,r.transitions,bytes(s))==before
            assert not core.v6_tower_route_boundary(C.byref(r))
            failures+=1
    # A diagonal crossing commits vertical first; missing horizontal destination
    # retains that new room and its correctly transformed history.
    r,s,w,keep=fixture(core);s.player.x=308;s.player.y=238
    keep[1][8].x=999
    assert not core.v6_tower_route_boundary(C.byref(r))
    assert r.index==7 and (s.player.x,s.player.y)==(308,-2)
    assert (s.player.old_x,s.player.old_y)==(308,-2)
    # Exercise the production gameplay call, with empty resident terrain so
    # all four edges are reachable without injecting a post-physics position.
    packed=encode([0]*1200);payload=(C.c_uint8*len(packed)).from_buffer_copy(packed)
    integrated=0
    for x,y,index in ((140,238,7),(140,-3,1),(-15,120,3),(308,120,5),(308,238,8)):
        r,s,w,keep=fixture(core)
        for room in keep[1]: room.packed=payload;room.bytes=len(packed)
        assert core.v6_tower_route_load(C.byref(r),108,109,0)
        s.player.x=x;s.player.y=y;s.player.vx=s.player.vy=s.player.ay=0
        s.player.gravity=1 if y< -2 else 0
        s.motion.ax=0;s.life_timer=0;s.death_timer=-1
        assert core.v6_tower_route_step(C.byref(r),0)
        assert r.index==index and not r.error,(x,y,r.index,s.player.x,s.player.y)
        integrated+=1
    print(f'PASS ordinary room boundaries: {cases} desktop-source cases, {failures} failed edges, diagonal partial-load preservation, {integrated} gameplay crossings')

if __name__=='__main__':main()
