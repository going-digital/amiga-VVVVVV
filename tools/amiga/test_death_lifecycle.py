#!/usr/bin/env python3
"""Compare ordinary same-room death timing/reset with extracted desktop methods."""
import ctypes as C
import hashlib
import json
import subprocess
from test_player import ROOT, BUILD, Player, DynamicBlock, block
from test_enemy import Enemy


def reference_source():
    game=(ROOT/'desktop_version/src/Game.cpp').read_text()
    maps=(ROOT/'desktop_version/src/Map.cpp').read_text()
    logic=(ROOT/'desktop_version/src/Logic.cpp').read_text()
    methods=[block(game,game.index('void Game::'+name+'(void)'))
             for name in ('deathsequence',)]
    methods.append(block(maps,maps.index('void mapclass::resetplayer(const bool player_died)')))
    start=logic.index('        game.deathsequence();')
    end=logic.index('        if (game.deathseq <= 0)',start)
    timer=logic[start:end]+block(logic,end)
    # Unsupported branches abort instead of silently providing alternate behavior.
    shim=r'''
#include <cstdlib>
#include <cmath>
#include "player.h"
#include <cstring>
#include <vector>
#include "Ent.h"
#define INBOUNDS_VEC(i,v) ((i)>=0 && static_cast<size_t>(i)<(v).size())
enum { EntityColour_DEAD = 1 }; // Graphics.h, no rendering dependency.
enum { Sound_CRY, SWN_SUPERGRAVITRON, FADE_NONE, FADE_START_FADEOUT, FADE_FULLY_BLACK, Glitchrunner2_2 };
namespace Menu { enum { gameover }; }
bool GlitchrunnerMode_less_than_or_equal(int) { return false; }
void setbgobjlerp(int) { std::abort(); }
struct Music {
    bool nicefade;int currentsong;
    void playef(int) {} // Audio output has no simulation state.
    void fadeout() { std::abort(); }
    void fadeMusicVolumeIn(int) { std::abort(); }
} music;
struct Graphics {
    int fademode,towerbg;bool showcutscenebars;
    void textboxremove() {} // No textboxes in this fixture.
} graphics;
struct Script { bool running; } script;
struct Game {
    int deathseq,lifeseq,deathcounts,gravitycontrol,savegc,gameoverdelay;
    int roomx,roomy,saverx,savery,savex,savey,savedir,savecolour,currentroomdeaths;
    int swngame,swntimer,swnmessage,swnrank,state,scmprogress;
    bool supercrewmate,scmhurt,nodeathmode,noflashingmode,swnmode,hascontrol,completestop,advancetext;
    void deathsequence();
    void invalidate_ndm_trophy() {} // Achievement only.
    void gethardestroom() {} // Statistics only.
    void copyndmresults() { std::abort(); }
    void quittomenu() { std::abort(); }
    void createmenu(int) { std::abort(); }
} game;
struct mapclass {
    bool finalmode,towermode;int roomdeaths[400],roomdeathsfinal[400],ypos,oldypos;
    void resetplayer(bool);
    void gotoroom(int,int) { std::abort(); }
    void twoframedelayfix() { std::abort(); }
} map;
struct Entity {
    std::vector<entclass> entities;
    int getplayer() { return 0; }
    int getscm() { std::abort(); }
} obj;
entclass::entclass() { std::memset(this,0,sizeof(*this)); }
extern "C" void death_init(const V6Player *p,int x,int y,int gravity,int dir) {
    std::memset(&game,0,sizeof(game));std::memset(&map,0,sizeof(map));
    obj.entities.clear();obj.entities.resize(1);
    game.deathseq=30;game.roomx=game.saverx=110;game.roomy=game.savery=110;
    game.savex=x;game.savey=y;game.savedir=dir;game.savegc=gravity;
    music.currentsong=-1;game.gravitycontrol=p->gravity;
    obj.entities[0].xp=p->x;obj.entities[0].yp=p->y;obj.entities[0].dir=p->dir;
    obj.entities[0].vx=p->vx/float(V6_ONE);obj.entities[0].vy=p->vy/float(V6_ONE);
}
extern "C" void death_read(int *s) {
    const entclass& e=obj.entities[0];
    s[0]=game.deathseq;s[1]=game.lifeseq;s[2]=game.deathcounts;
    s[3]=e.xp;s[4]=e.yp;s[5]=std::lround(e.vx*double(V6_ONE));s[6]=std::lround(e.vy*double(V6_ONE));
    s[7]=game.gravitycontrol;s[8]=e.dir;
    s[9]=e.invis;s[10]=map.roomdeaths[210];
}
'''
    return shim+'\n'.join(methods)+'''
extern "C" void death_tick() {
    if(game.nodeathmode || game.swnmode || game.supercrewmate || map.towermode ||
       game.roomx!=game.saverx || game.roomy!=game.savery || script.running ||
       game.completestop) std::abort();
'''+timer+'\n}\n'


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    source=reference_source();path=BUILD/'death_reference.cpp';path.write_text(source)
    subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC',
        '-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),
        '-I'+str(ROOT/'amiga_version'),str(path),
        '-o',str(BUILD/'death_reference.so')],check=True)
    # Build independently, so this test does not require a previous host-suite run.
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/f) for f in
          ('player.c','platform.c','enemy.c','blocks.c','terrain.c','slice.c')],
        str(ROOT/'tools/amiga/crush_session.c'),'-o',str(BUILD/'death_session.so')],check=True)
    ref=C.CDLL(str(BUILD/'death_reference.so'));core=C.CDLL(str(BUILD/'death_session.so'))
    ref.death_init.argtypes=[C.POINTER(Player)]+[C.c_int]*4;ref.death_read.argtypes=[C.POINTER(C.c_int)]
    core.crush_session_init.argtypes=[C.c_int]*6
    core.crush_session_read.argtypes=[C.POINTER(Player),C.POINTER(Enemy),C.POINTER(DynamicBlock),C.POINTER(C.c_int)]
    cases=ticks=0
    for tileset in (0,1):
        for down in (0,1):
            for tile in (6,7,8,9,49,50):
                for speed in (1,2,3,6):
                    for x in (103,108,115):
                        for cached in (0,1):
                            core.crush_session_init(tileset,down,tile,speed,x,cached)
                            p=Player();e=Enemy();b=DynamicBlock();state=(C.c_int*6)();original=(C.c_int*11)()
                            for live in range(16):
                                core.crush_session_step()
                                core.crush_session_read(C.byref(p),C.byref(e),C.byref(b),state)
                                if state[0]==30:break
                            else:raise AssertionError('Fixture did not reach damage')
                            ref.death_init(C.byref(p),x,97 if down else 70,down,1)
                            for delay in range(30):
                                ref.death_tick();core.crush_session_step()
                                ref.death_read(original)
                                core.crush_session_read(C.byref(p),C.byref(e),C.byref(b),state)
                                assert list(state[:3])==list(original[:3]),(cases,delay,list(state),list(original))
                                assert original[10]==state[2],(cases,delay,'room deaths')
                                assert [p.x,p.y,p.vx,p.vy,p.gravity,p.dir]==list(original[3:9]),(cases,delay,'player')
                                if delay==29:
                                    assert state[3]==1 and state[5]&8
                                ticks+=1
                            cases+=1
    report=dict(cases=cases,death_ticks=ticks,reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
        scope='Extracted Game::deathsequence and Map::resetplayer plus Logic.cpp countdown/reset branch; ordinary same-room death only. Compare timer, life timer and death count each tick; player position, velocity, gravity and direction through freeze and respawn. Excludes input/contact retention, rendering, other rooms, scripts, towers and special modes.')
    (BUILD/'death-lifecycle-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
