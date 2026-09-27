#!/usr/bin/env python3
"""Original-room normal-input route through the native adapter (host trace)."""
import json
import subprocess
from pack_rooms import build
from test_player import ROOT, BUILD


def main():
    out=BUILD/'beneath-trace'
    build(out,'beneath')
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
#include "room_codec.h"
#include "prototype_room.h"
#include "beneath_replay.h"
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
    assert(v6_unpack_room(packed_rooms[0],packed_sizes[0],tiles,1200));
    v6_terrain_build(&terrain,&current_room);
    v6_slice_init_world(&slice,room_setups,1,0);reset_platforms();
    puts("[");
    for(tick=1;tick<=240;++tick) {
        unsigned input=beneath_replay_input(tick);
        unsigned restart=0;
        unsigned events;
        if(slice.death_timer>=0 || restart) update_disappearing(1);
        events=v6_slice_step_movement(&slice,&current_room,input,restart,platform_movement,0);
        if(events&V6_EVENT_RESPAWN) {
            platform_motion=(V6PlayerMotion){0,slice.player.y};
            platform_push=(V6PlatformPush){slice.player.y,0,0};
        }
        states|=1u<<disappearing[0].state;
        assert(!diagnostics.error && !slice.exits);
        assert(disappearing[1].state==0 && disappearing[2].state==0);
        printf("%s{\"ticks\":%u,\"player_x\":%d,\"player_y\":%d,\"player_vx\":%d,\"player_vy\":%d,"
               "\"gravity\":%d,\"death_timer\":%d,\"deaths\":%d,\"respawns\":%d,\"checkpoint\":%d,"
               "\"enemy_x\":%d,\"enemy_y\":%d,\"enemy_ticks\":%lu,\"enemy_hits\":%lu,\"exits\":%d}",
               tick==1?"":",\n",tick,slice.player.x,slice.player.y,slice.player.vx,slice.player.vy,
               slice.player.gravity,slice.death_timer,slice.deaths,slice.respawns,slice.checkpoint_active,
               disappearing[0].state,disappearing[0].walking_frame,platform_ticks,platform_pushes,slice.exits);
    }
    puts("\n]");
    assert(states==63 && slice.deaths==1 && slice.respawns==1 && platform_pushes==1);
    assert(slice.player.flips==1 && slice.player.x==60 && slice.player.y==145);
    return 0;
}
'''
    path=out/'trace.c';path.write_text(source)
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),'-I'+str(out),'-I'+str(ROOT/'tools/amiga'),str(path),
        *[str(ROOT/'amiga_version'/f) for f in ('player.c','slice.c','terrain.c','platform.c','enemy.c','blocks.c','disappearing.c','room_codec.c')],
        '-o',str(out/'trace')],check=True)
    trace=json.loads(subprocess.check_output([str(out/'trace')]))
    (BUILD/'beneath-replay-trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    print('PASS: 240 original-room route ticks; one collapse, ceiling-spike death and respawn; all six lifecycle states (UBSan)')

if __name__=='__main__':main()
