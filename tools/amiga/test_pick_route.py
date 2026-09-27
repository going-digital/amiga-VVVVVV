#!/usr/bin/env python3
"""Exercise the native scene adapter and lifecycle with normal recorded input.

This is an integration replay, not an independent desktop-loop comparison.
The component suites supply source-reference comparisons.
"""
import json
import subprocess
from pathlib import Path
from pack_rooms import ROOT,build
from test_player import BUILD


def main():
    out=ROOT/'build/amiga-pick-route-host'
    build(out,'pick')
    native=(ROOT/'amiga_version/prototype.c').read_text()
    start=native.index('#ifdef CHECKPOINT_COUNT\nstatic V6Checkpoint')
    end=native.index('static UWORD saved_dma',start)
    source=r'''
#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include "slice.h"
#include "platform.h"
#include "room_codec.h"
#include "prototype_room.h"
#include "pick_replay.h"
#define ULONG unsigned long
static V6Slice slice;
static uint16_t tiles[1200];
static V6Terrain terrain;
static V6Room current_room={tiles,0,0,&terrain,0,0};
'''+native[start:end]+r'''
int main(void) {
    unsigned tick,first_save=0,second_save=0;
    assert(v6_unpack_room(packed_room_0,sizeof(packed_room_0),tiles,1200));
    v6_terrain_build(&terrain,&current_room);
    v6_slice_init_world(&slice,room_setups,1,0);
    reset_checkpoints();reset_platforms();
    puts("[");
    for(tick=1;tick<=240;++tick) {
        unsigned input=tick<=sizeof(pick_replay)?pick_replay[tick-1]:0;
        unsigned events=v6_slice_step_entities(&slice,&current_room,input,tick==130,platform_movement,0);
        if(events&V6_EVENT_RESPAWN) {
            platform_motion=(V6PlayerMotion){0,slice.player.y};
            platform_push=(V6PlatformPush){slice.player.y,0,0};
            assert(slice.player.x==208 && slice.player.y==185 && !slice.player.gravity);
        }
        if(events&V6_EVENT_SAVE) {
            if(checkpoint_save.id==445550 && !first_save) first_save=tick;
            if(checkpoint_save.id==445551 && !second_save) second_save=tick;
        }
        assert(!slice.exits);
        if(tick<130) assert(!slice.deaths && slice.death_timer<0);
        if(tick==124) assert(checkpoints[1].active);
        printf("%s{\"ticks\":%u,\"player_x\":%d,\"player_y\":%d,\"player_vx\":%d,"
               "\"player_vy\":%d,\"gravity\":%d,\"death_timer\":%d,"
               "\"deaths\":%d,\"respawns\":%d,\"checkpoint\":%d,\"flips\":%d,"
               "\"enemy_x\":%d,\"enemy_y\":%d,\"enemy_ticks\":%lu,\"enemy_hits\":%lu}",
               tick==1?"":",\n",tick,slice.player.x,slice.player.y,slice.player.vx,slice.player.vy,
               slice.player.gravity,slice.death_timer,slice.deaths,slice.respawns,
               checkpoints[0].active|checkpoints[1].active<<1,slice.player.flips,
               platforms[0].x,platforms[0].y,platform_ticks,platform_pushes);
    }
    puts("\n]");
    assert(first_save==2 && second_save==124 && platform_pushes>=15);
    assert(slice.deaths==1 && slice.respawns==1 && checkpoints[1].active);
    fprintf(stderr,"Route: first save %u, second save %u, transport ticks %lu\n",first_save,second_save,platform_pushes);
}
'''
    path=out/'pick_route.c';path.write_text(source)
    exe=out/'pick_route'
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-DV6_PLATFORM_SCENE',
        '-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),'-I'+str(out),
        str(path),*[str(ROOT/'amiga_version'/f) for f in
        ('player.c','platform.c','enemy.c','blocks.c','terrain.c','checkpoints.c','slice.c','room_codec.c')],
        '-o',str(exe)],check=True)
    trace=json.loads(subprocess.check_output([str(exe)],text=True))
    BUILD.mkdir(parents=True,exist_ok=True)
    # Standalone invocation also refreshes the independent movement comparison.
    from test_platform_loop import main as compare_movement
    compare_movement()
    reference=json.loads((BUILD/'pick-movement-reference.json').read_text())
    for tick,expected in enumerate(reference):
        for field,value in expected.items():
            assert trace[tick][field]==value, (tick+1,field,trace[tick][field],value)
    (BUILD/'pick-route-trace.json').write_text(json.dumps(trace,indent=2)+chr(10))
    report=dict(ticks=len(trace),desktop_movement_ticks=len(reference),second_checkpoint_tick=next(r['ticks'] for r in trace if r['checkpoint']==2),
                transport_ticks=trace[-1]['enemy_hits'],
                scope='Native scene integration replay with normal input, then requested restart; not independent full desktop-loop equivalence.')
    (BUILD/'pick-route-test-report.json').write_text(json.dumps(report,indent=2)+chr(10))
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
