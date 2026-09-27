#!/usr/bin/env python3
"""Host trace of the native synthetic disappearing-platform scene adapter."""
import json
import subprocess
from test_player import ROOT,BUILD


def main():
    native=(ROOT/'amiga_version/prototype.c').read_text()
    start=native.index('#ifdef V6_PLATFORM_SCENE\nstatic V6Platform')
    end=native.index('static UWORD saved_dma',start)
    source=r'''
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include "slice.h"
#include "platform.h"
#include "disappearing.h"
#include "disappearing_fixture.h"
#define V6_PLATFORM_SCENE
#define V6_DISAPPEAR_SCENE
#define ULONG unsigned long
static V6Slice slice;
static struct {unsigned error;} diagnostics;
static uint16_t tiles[1200];
static V6Terrain terrain;
static V6Room current_room={tiles,0,0,&terrain,0,0};
'''+native[start:end]+r'''
int main(void) {
    unsigned tick,states=0;
    disappearing_fixture_tiles(tiles);v6_terrain_build(&terrain,&current_room);
    v6_slice_init_world(&slice,room_setups,1,0);
    v6_player_init(&slice.player,108,70,0);reset_platforms();
    puts("[");
    for(tick=1;tick<=240;++tick) {
        unsigned events;
        if(slice.death_timer>=0) update_disappearing(1);
        events=v6_slice_step_movement(&slice,&current_room,0,0,platform_movement,0);
        if(events&V6_EVENT_RESPAWN) {
            platform_motion=(V6PlayerMotion){0,slice.player.y};
            platform_push=(V6PlatformPush){slice.player.y,0,0};
        }
        states|=1u<<disappearing[0].state;
        assert(!diagnostics.error && !slice.exits && disappearing[0].walking_frame>=0 && disappearing[0].walking_frame<5);
        printf("%s{\"ticks\":%u,\"player_x\":%d,\"player_y\":%d,\"player_vx\":%d,\"player_vy\":%d,"
               "\"gravity\":%d,\"death_timer\":%d,\"deaths\":%d,\"respawns\":%d,\"checkpoint\":%d,"
               "\"enemy_x\":%d,\"enemy_y\":%d,\"enemy_ticks\":%lu,\"enemy_hits\":%lu}",
               tick==1?"":",\n",tick,slice.player.x,slice.player.y,slice.player.vx,slice.player.vy,
               slice.player.gravity,slice.death_timer,slice.deaths,slice.respawns,slice.checkpoint_active,
               disappearing[0].state,disappearing[0].walking_frame,platform_ticks,platform_pushes);
    }
    puts("\n]");
    assert(states==63 && slice.deaths==1 && slice.respawns==1 && platform_pushes==1);
    return 0;
}
'''
    path=BUILD/'disappearing_replay.c';path.write_text(source)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(path),
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','slice.c','terrain.c','platform.c','enemy.c','blocks.c','disappearing.c')],
        '-o',str(BUILD/'disappearing_replay')],check=True)
    trace=json.loads(subprocess.check_output([str(BUILD/'disappearing_replay')]))
    (BUILD/'disappearing-replay-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    print('PASS: 240-tick native scene host trace; all six lifecycle states, one collapse and respawn')


if __name__=='__main__':main()
