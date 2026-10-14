#!/usr/bin/env python3
"""Original north-room declarations and source actor scheduling."""
import ctypes as C
import subprocess
from test_player import ROOT,BUILD,Player,Room,Terrain,DynamicBlock
from test_enemy import Enemy
from test_carry import Push
from test_disappearing import State as Gate
from test_platform_loop import reference_source
from tower_gameplay_data import north_route_room

class Bank(C.Structure):
    _fields_=[('platforms',Enemy*3),('enemies',Enemy*5),('gates',Gate*3),
              ('blocks',DynamicBlock*4),('push',Push),
              *[(n,C.c_uint) for n in ('room_y','platform_count','enemy_count','gate_count','block_count','flags')]]

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=reference_source()+r'''
extern "C" void north_enemy(const uint16_t *tiles,V6Enemy *a,unsigned n) {
    V6Player dummy={};reference_init(&dummy,tiles,0,0);obj.entities.resize(n+1);
    for(unsigned i=0;i<n;++i) {
        entclass& e=obj.entities[i+1];const V6Enemy& v=a[i];
        e.type=EntityType_MOVING;e.rule=1;e.gravity=false;
        e.xp=v.x;e.yp=v.y;e.oldxp=v.old_x;e.oldyp=v.old_y;e.vx=v.vx;e.vy=v.vy;
        e.cx=v.cx;e.cy=v.cy;e.w=v.w;e.h=v.h;e.x1=v.x1;e.y1=v.y1;e.x2=v.x2;e.y2=v.y2;
        e.behave=v.behavior;e.para=v.speed;e.state=v.state;e.onwall=v.onwall;
    }
    for(unsigned i=n;i>0;--i) {
        obj.updateentities(i);obj.updateentitylogic(i);obj.entitymapcollision(i);
        const entclass& e=obj.entities[i];V6Enemy& v=a[i-1];
        v.x=e.xp;v.y=e.yp;v.old_x=e.oldxp;v.old_y=e.oldyp;
        v.vx=e.vx;v.vy=e.vy;v.state=e.state;v.onwall=e.onwall;
    }
}
'''
    path=BUILD/'north_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'north_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/(n+'.c')) for n in ('north_route','player','platform','enemy','terrain','blocks','disappearing')],
        '-o',str(BUILD/'north_route.so')],check=True)
    core=C.CDLL(str(BUILD/'north_route.so'));ref=C.CDLL(str(BUILD/'north_reference.so'))
    bp=C.POINTER(Bank);rp=C.POINTER(Room);pp=C.POINTER(Player);ep=C.POINTER(Enemy);dp=C.POINTER(DynamicBlock)
    core.v6_north_init.argtypes=[bp,rp,C.c_int,C.c_int,C.c_int]
    core.v6_north_entities.argtypes=[bp,rp,C.c_int]
    core.v6_north_platforms.argtypes=[bp,rp,pp,C.c_int,C.c_int]
    ref.north_enemy.argtypes=[C.POINTER(C.c_uint16),ep,C.c_uint]
    ref.loop_init.argtypes=[pp,C.POINTER(C.c_uint16),C.c_int,C.c_int,dp,C.c_uint,ep,C.c_uint]
    ref.loop_step.argtypes=[C.c_uint,C.c_uint,C.c_int,ep,C.c_uint,dp,C.c_uint,C.POINTER(Push)]
    ticks=0
    for name in ('reflect','yesmen','gantry'):
        data=north_route_room(name);tiles=(C.c_uint16*1200)(*data['tiles']);room=Room(tiles,0,0);bank=Bank();p=Player()
        assert core.v6_north_init(C.byref(bank),C.byref(room),data['x'],data['y'],0)
        assert len(data['checkpoints'])==(2 if name!='reflect' else 1)
        if name=='yesmen':
            wanted=(Enemy*5).from_buffer_copy(bank.enemies)
            for tick in range(2048):
                ref.north_enemy(tiles,wanted,5)
                core.v6_north_entities(C.byref(bank),C.byref(room),0)
                assert bytes(bank.enemies)==bytes(wanted),(name,tick)
                if tick%17==0:
                    old=bytes(bank.enemies);core.v6_north_entities(C.byref(bank),C.byref(room),1)
                    assert bytes(bank.enemies)==old
                ticks+=5
        else:
            # Keep the player outside the world; compare transport's moving
            # actor and block pass, including its death-time freeze rules.
            p.x=-64;p.y=0
            n=bank.platform_count;wanted=(Enemy*n).from_buffer_copy(bank.platforms)
            blocks=(DynamicBlock*bank.block_count).from_buffer_copy(bank.blocks)
            ref.loop_init(C.byref(p),tiles,0,0,blocks,bank.block_count,wanted,n)
            push=Push(0,0,0)
            for tick in range(1024):
                life=9 if tick%31==0 else 0
                ref.loop_step(0,bank.flags,life,wanted,n,blocks,bank.block_count,C.byref(push))
                core.v6_north_platforms(C.byref(bank),C.byref(room),C.byref(p),life,0)
                assert bytes(bank.platforms)[:n*C.sizeof(Enemy)]==bytes(wanted),(name,tick,'platform')
                assert bytes(bank.blocks)[:bank.block_count*C.sizeof(DynamicBlock)]==bytes(blocks),(name,tick,'blocks')
                ticks+=n
    print('PASS original north-route declarations and',ticks,'source actor updates; death-time enemy freeze')

if __name__=='__main__':main()
