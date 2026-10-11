#!/usr/bin/env python3
"""Candidate west actor composition and source-extracted platform scheduling."""
import ctypes as C
import random,subprocess
from test_player import ROOT,BUILD,Player,Room,Terrain,DynamicBlock,block
from test_enemy import Enemy
from test_carry import Motion,Push
from test_platform_loop import reference_source
from tower_gameplay_data import prize_return_room
class Bank(C.Structure):
    _fields_=[('platforms',Enemy*6),('enemies',Enemy*2),('blocks',DynamicBlock*6),
              ('push',Push),('platform_count',C.c_uint),('enemy_count',C.c_uint),('flags',C.c_uint)]

def main():
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
    ent=(ROOT/'desktop_version/src/Ent.cpp').read_text()
    start=ent.index('case rn(10, 7):')
    appearance=ent[start:ent.index('case rn(',start+5)]
    assert all(line in appearance for line in ('tile = 92;', 'animate = 1;', 'w = 16;', 'h = 16;'))
    creation=entity[entity.index('case 2: //A moving platform'):entity.index('case 3: //Disappearing platforms')]
    assert all(line in creation for line in ('meta1 >= 10  && meta1 <= 11','entity.w = 64;', 'meta1 -= 2;', 'createblock(0, xp, yp, 32, 8);'))
    overload=block(entity,entity.index('void entityclass::createentity(int xp, int yp, int t, int meta1, int meta2, int p1, int p2)'))
    assert 'createentity(xp, yp, t, meta1, meta2, p1, p2, 320, 240);' in overload
    source=reference_source()+r'''
extern "C" void bank_enemy_step(const uint16_t *tiles,V6Enemy *actors,unsigned count,
                               const V6Block *blocks,unsigned block_count) {
    V6Player dummy={};reference_init(&dummy,tiles,0,0);
    obj.entities.resize(count+1);
    for(unsigned i=0;i<count;++i) {
        const V6Enemy& a=actors[i];entclass& e=obj.entities[i+1];
        e.type=EntityType_MOVING;e.rule=1;e.gravity=false;
        e.xp=a.x;e.yp=a.y;e.oldxp=a.old_x;e.oldyp=a.old_y;e.vx=a.vx;e.vy=a.vy;
        e.cx=a.cx;e.cy=a.cy;e.w=a.w;e.h=a.h;
        e.x1=a.x1;e.y1=a.y1;e.x2=a.x2;e.y2=a.y2;
        e.behave=a.behavior;e.para=a.speed;e.state=a.state;e.onwall=a.onwall;
    }
    for(unsigned i=0;i<block_count;++i) {
        blockclass b={};b.type=BLOCK;b.trigger=0;
        b.rect={blocks[i].x,blocks[i].y,blocks[i].w,blocks[i].h};obj.blocks.push_back(b);
    }
    for(unsigned i=count;i>0;--i) {
        obj.updateentities(i);obj.updateentitylogic(i);obj.entitymapcollision(i);
        const entclass& e=obj.entities[i];V6Enemy& a=actors[i-1];
        a.x=e.xp;a.y=e.yp;a.old_x=e.oldxp;a.old_y=e.oldyp;
        a.vx=e.vx;a.vy=e.vy;a.state=e.state;a.onwall=e.onwall;
    }
}
extern "C" unsigned bank_candidates(const V6Player *p,const V6Enemy *a,unsigned count) {
    SDL_Rect player={p->x+6,p->y+2,12,21};unsigned hits=0;
    for(unsigned i=0;i<count;++i) {
        SDL_Rect enemy={a[i].x+a[i].cx,a[i].y+a[i].cy,a[i].w,a[i].h};
        if(SDL_HasRectIntersection(&player,&enemy))hits|=1U<<i;
    }
    return hits;
}
''';path=BUILD/'prize_return_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-fno-fast-math','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),str(path),
        '-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'prize_return_reference.so')],check=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/(n+'.c')) for n in
          ('prize_return','player','platform','enemy','terrain','blocks')],
        '-o',str(BUILD/'prize_return.so')],check=True)
    core=C.CDLL(str(BUILD/'prize_return.so'));ref=C.CDLL(str(BUILD/'prize_return_reference.so'))
    pp=C.POINTER(Player);rp=C.POINTER(Room);bp=C.POINTER(Bank);ep=C.POINTER(Enemy);dp=C.POINTER(DynamicBlock)
    core.v6_prize_return_init.argtypes=[bp,rp,C.c_int,C.c_int,C.c_int]
    core.v6_prize_return_platforms.argtypes=[bp,rp,pp,C.c_int,C.c_int]
    core.v6_prize_return_contacts.argtypes=[bp,pp]
    core.v6_prize_return_entities.argtypes=[bp,rp]
    ref.bank_enemy_step.argtypes=[C.POINTER(C.c_uint16),ep,C.c_uint,dp,C.c_uint]
    ref.bank_candidates.argtypes=[pp,ep,C.c_uint]
    core.v6_player_init.argtypes=[pp,C.c_int,C.c_int,C.c_int]
    core.v6_player_input.argtypes=[pp,C.c_uint,C.POINTER(Motion)]
    core.v6_player_physics.argtypes=[pp,rp,C.POINTER(Motion),C.c_void_p,C.c_void_p]
    core.v6_player_unstick.argtypes=[pp,rp]
    core.v6_terrain_build.argtypes=[C.POINTER(Terrain),rp]
    ref.loop_init.argtypes=[pp,C.POINTER(C.c_uint16),C.c_int,C.c_int,dp,C.c_uint,ep,C.c_uint]
    ref.loop_step.argtypes=[C.c_uint,C.c_uint,C.c_int,ep,C.c_uint,dp,C.c_uint,C.POINTER(Push)]
    ref.reference_read.argtypes=[pp]
    rng=random.Random(443480);ticks=0
    for name in ('deception','downunder'):
        data=prize_return_room(name);tiles=(C.c_uint16*1200)(*data['tiles'])
        for scenario in range(32):
            room=Room(tiles,0,0);bank=Bank();p=Player()
            core.v6_player_init(C.byref(p),40+scenario*7,65+scenario%4*24,scenario%2)
            assert core.v6_prize_return_init(C.byref(bank),C.byref(room),data['x'],data['y'],p.y)
            calls=[r for r in data['entities'] if r[2]==2]
            assert bank.platform_count==len(calls) and bank.enemy_count==(2 if name=='deception' else 0)
            for i,call in enumerate(calls):
                a=bank.platforms[i];x,y,_,behavior,speed,*bounds=call
                assert (a.x,a.y,a.behavior,a.speed,a.w)==(x,y,behavior-2 if behavior>=10 else behavior,speed,64 if behavior>=10 else 32)
                assert (bank.blocks[i].x,bank.blocks[i].y,bank.blocks[i].w,bank.blocks[i].h)==(x,y,32,8)
                assert (a.x1,a.y1,a.x2,a.y2)==tuple(bounds or [-64,-64,384,304])
            expected_a=(Enemy*bank.platform_count).from_buffer_copy(bank.platforms)
            expected_b=(DynamicBlock*bank.platform_count).from_buffer_copy(bank.blocks)
            ref.loop_init(C.byref(p),tiles,0,0,bank.blocks,bank.platform_count,bank.platforms,bank.platform_count)
            terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
            if scenario%2:room.terrain=C.pointer(terrain)
            motion=Motion(0,p.y);push=Push(p.y,0,0)
            for tick in range(240):
                buttons=rng.choice((0,0,1,2,4,5,6));life=max(0,10-tick)
                if life>5:buttons|=8
                ref.loop_step(buttons,bank.flags,life,expected_a,bank.platform_count,expected_b,bank.platform_count,C.byref(push))
                wanted=Player();ref.reference_read(C.byref(wanted))
                core.v6_player_input(C.byref(p),buttons,C.byref(motion))
                core.v6_prize_return_platforms(C.byref(bank),C.byref(room),C.byref(p),life,motion.pending_y)
                core.v6_player_physics(C.byref(p),C.byref(room),C.byref(motion),None,None)
                core.v6_prize_return_contacts(C.byref(bank),C.byref(p))
                core.v6_player_unstick(C.byref(p),C.byref(room))
                assert bytes(p)==bytes(wanted),(name,scenario,tick,'player')
                for i in range(bank.platform_count):
                    assert bytes(bank.platforms[i])==bytes(expected_a[i]),(name,scenario,tick,i)
                    assert bytes(bank.blocks[i])==bytes(expected_b[i]),(name,scenario,tick,i,'block')
                assert motion.pending_y==ref.reference_pending()
                assert (bank.push.visual_ground,bank.push.visual_roof)==(push.visual_ground,push.visual_roof)
                ticks+=1
    data=prize_return_room('deception');tiles=(C.c_uint16*1200)(*data['tiles'])
    room=Room(tiles,0,0);bank=Bank()
    assert core.v6_prize_return_init(C.byref(bank),C.byref(room),110,107,0)
    assert [(a.x,a.y,a.behavior,a.speed,a.w,a.h) for a in bank.enemies]==[(272,120,2,8,16,16),(32,96,3,8,16,16)]
    terrain=Terrain();core.v6_terrain_build(C.byref(terrain),C.byref(room))
    wanted_a=(Enemy*2).from_buffer_copy(bank.enemies);enemy_ticks=0
    p=Player();core.v6_player_init(C.byref(p),0,0,0)
    for tick in range(2048):
        if tick%2:room.terrain=C.pointer(terrain)
        else:room.terrain=C.POINTER(Terrain)()
        # Include initial 32-wide blocks and expanded conveyors, plus disabled
        # blocks left by the contact pass. Their changing geometry is supplied
        # identically to both independent implementations.
        for i in range(6):bank.blocks[i].w=0 if tick%7==0 else bank.platforms[i].w
        ref.bank_enemy_step(tiles,wanted_a,2,bank.blocks,6)
        core.v6_prize_return_entities(C.byref(bank),C.byref(room))
        assert bytes(bank.enemies)==bytes(wanted_a),(tick,'enemy')
        for i in range(2):
            e=bank.enemies[i]
            for dx,dy in ((-18,0),(-17,0),(9,0),(10,0),(0,-23),(0,-22),(0,13),(0,14),(0,0)):
                p.x=e.x+dx;p.y=e.y+dy
                assert core.v6_prize_return_contacts(C.byref(bank),C.byref(p))==ref.bank_candidates(C.byref(p),bank.enemies,2)
        enemy_ticks+=2
    # Filtering must also retain colliding blocks and exact vertical edges.
    for tick in range(1024):
        for i in range(6):
            b=bank.blocks[i];e=bank.enemies[i%2]
            b.x=e.x+rng.randrange(-24,25);b.y=e.y+rng.choice((-9,-8,-1,0,15,16,17))
            b.w=rng.choice((0,8,32,64));b.h=rng.choice((0,8,16))
        ref.bank_enemy_step(tiles,wanted_a,2,bank.blocks,6)
        core.v6_prize_return_entities(C.byref(bank),C.byref(room))
        assert bytes(bank.enemies)==bytes(wanted_a),(tick,'filtered enemy blocks')
        enemy_ticks+=2
    # Invalid rooms must leave both bank and binding unchanged.
    before=bytes(bank),bytes(room)
    assert not core.v6_prize_return_init(C.byref(bank),C.byref(room),111,107,0)
    assert before==(bytes(bank),bytes(room))
    print(f'PASS Prize return actors: {ticks} source-extracted platform/player ticks in both candidate rooms, cached/plain terrain; {enemy_ticks} enemy ticks and 36864 broad-phase edge checks; ordered source setup and invalid-room immutability')
if __name__=='__main__':main()
