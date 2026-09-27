#!/usr/bin/env python3
"""Host trace of the native synthetic disappearing-platform scene adapter."""
import argparse
import json
import subprocess
from test_player import ROOT,BUILD


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--retrigger",action="store_true")
    args=parser.parse_args()
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
        assert(!diagnostics.error && !slice.exits && disappearing[0].walking_frame>=0 && disappearing[0].walking_frame<1198);
        printf("%s{\"ticks\":%u,\"player_x\":%d,\"player_y\":%d,\"player_vx\":%d,\"player_vy\":%d,"
               "\"gravity\":%d,\"death_timer\":%d,\"deaths\":%d,\"respawns\":%d,\"checkpoint\":%d,"
               "\"enemy_x\":%d,\"enemy_y\":%d,\"enemy_ticks\":%lu,\"enemy_hits\":%lu}",
               tick==1?"":",\n",tick,slice.player.x,slice.player.y,slice.player.vx,slice.player.vy,
               slice.player.gravity,slice.death_timer,slice.deaths,slice.respawns,slice.checkpoint_active,
               disappearing[0].state,disappearing[0].walking_frame,platform_ticks,platform_pushes);
    }
    puts("\n]");
#ifdef V6_RETRIGGER_REPLAY
    assert((states&30)==30);
    assert(slice.deaths>=3 && slice.respawns>=3 && platform_pushes>=4);
    assert(disappearing[0].walking_frame>4);
#else
    assert(states==63 && slice.deaths==1 && slice.respawns==1 && platform_pushes==1);
#endif
    return 0;
}
'''
    if args.retrigger: source='#define V6_RETRIGGER_REPLAY\n'+source
    stem='retrigger' if args.retrigger else 'disappearing'
    path=BUILD/(stem+'_replay.c');path.write_text(source)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(path),
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','slice.c','terrain.c','platform.c','enemy.c','blocks.c','disappearing.c')],
        '-o',str(BUILD/(stem+'_replay'))],check=True)
    trace=json.loads(subprocess.check_output([str(BUILD/(stem+'_replay'))]))
    (BUILD/(stem+'-replay-trace.json')).write_text(json.dumps(trace,indent=2)+'\n')
    if args.retrigger:
        assert any(row['enemy_y']>4 and row['enemy_x']==2 for row in trace)
        print('PASS: 240-tick recharge-contact host trace; repeated collapses and frames beyond four')
        return
    print('PASS: 240-tick native scene host trace; all six lifecycle states, one collapse and respawn')


if __name__=='__main__':main()
