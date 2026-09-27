#!/usr/bin/env python3
"""Compare normal-world boundaries against extracted Logic.cpp/Map.cpp code."""
import hashlib
import json
import subprocess
from pack_rooms import ROOT
from test_player import block

build = ROOT / 'build/amiga'
logic = (ROOT / 'desktop_version/src/Logic.cpp').read_text()
maps = (ROOT / 'desktop_version/src/Map.cpp').read_text()
vertical = block(logic, logic.index('if (!map.warpy && !map.towermode)'))
horizontal = block(logic, logic.index('if (!map.warpx && !map.towermode)'))
a = maps.index('if (game.roomx < 100) game.roomx = 119;')
b = maps.index('game.currentroomdeaths', a)
wrap = maps[a:b]
source = r'''
#include <cassert>
#include <cstdio>
extern "C" {
#include "slice.h"
}
struct { int roomx, roomy; } game;
struct { bool warpy, warpx, towermode; } map = {false,false,false};
struct Entity { int xp,yp; };
struct { Entity entities[1]; int getplayer() { return 0; } } obj;
int changes;
#define INBOUNDS_VEC(i,v) ((i)==0)
void gotoroom(int rx,int ry) { game.roomx=rx; game.roomy=ry; ++changes;
''' + wrap + r'''
}
#define GOTOROOM(x,y) gotoroom(x,y)
void reference() {
''' + vertical + '\n' + horizontal + r'''
}
int main() {
    V6RoomSetup rooms[400];
    for (int i=0;i<400;++i) rooms[i] = {100+i%20,100+i/20,80,80,21,i};
    const int xs[] = {-24,-15,-14,-13,0,307,308,309,318};
    const int ys[] = {-12,-3,-2,-1,0,237,238,239,248};
    int cases=0;
    for (int i=0;i<400;++i) for (int x:xs) for (int y:ys) {
        V6Slice s;
        v6_slice_init_world(&s,rooms,400,i);
        s.player.x=x; s.player.y=y; s.player.vx=-12345678; s.player.vy=98765432;
        s.player.held=1; s.player.buffer=3; s.player.gravity=1;
        game.roomx=rooms[i].x; game.roomy=rooms[i].y;
        obj.entities[0]={x,y}; changes=0;
        reference();
        unsigned event=v6_slice_transition(&s);
        assert(s.player.x==obj.entities[0].xp && s.player.y==obj.entities[0].yp);
        assert(rooms[s.room_index].x==game.roomx && rooms[s.room_index].y==game.roomy);
        assert(s.transitions==changes && !!(event & V6_EVENT_ROOM)==!!changes);
        assert(s.player.vx==-12345678 && s.player.vy==98765432);
        assert(s.player.gravity==1 && s.player.held==1 && s.player.buffer==3);
        if (changes) assert(s.player.old_x==s.player.x && s.player.old_y==s.player.y);
        assert(s.deaths==0 && s.respawns==0 && s.exits==0);
        ++cases;
    }
    printf("PASS: %d normal-world boundary/reference cases\n",cases);
}
'''
path = build / 'transition_reference.cpp'
path.write_text(source)
for name in ('slice', 'player'):
    subprocess.run(['cc', '-std=c99', '-fsanitize=undefined', '-I'+str(ROOT/'amiga_version'),
                    '-c', str(ROOT/f'amiga_version/{name}.c'), '-o', str(build/f'{name}_host.o')], check=True)
subprocess.run(['c++', '-std=c++11', '-fsanitize=undefined', '-I'+str(ROOT/'amiga_version'),
                str(path), str(build/'slice_host.o'), str(build/'player_host.o'),
                '-o', str(build/'test_transitions')], check=True)
subprocess.run([str(build/'test_transitions')], check=True)
(build/'transition-test-report.json').write_text(json.dumps(dict(cases=32400,
    reference_sha256=hashlib.sha256((vertical+horizontal+wrap).encode()).hexdigest(),
    scope='Normal main-world boundary coordinates/order and retained player state; excludes special rooms and full loadlevel side effects.'), indent=2)+'\n')
