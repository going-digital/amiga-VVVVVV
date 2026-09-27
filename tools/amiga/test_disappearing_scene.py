#!/usr/bin/env python3
"""Exercise the native multi-platform adapter, without claiming campaign replay."""
import subprocess
from test_player import ROOT, BUILD


def main():
    native = (ROOT / 'amiga_version/prototype.c').read_text()
    start = native.index('#ifdef V6_PLATFORM_SCENE\nstatic V6Platform')
    end = native.index('static UWORD saved_dma', start)
    source = r'''
#include <assert.h>
#include <stdint.h>
#include "slice.h"
#include "platform.h"
#include "disappearing.h"
#define V6_PLATFORM_SCENE
#define V6_DISAPPEAR_SCENE
#define PLATFORM_COUNT 3
#define ULONG unsigned long
/* Positions from What Lies Beneath?; terrain is deliberately empty here. */
static const int platform_setup[3][2]={{120,72},{248,72},{184,200}};
static V6Slice slice;
static struct {unsigned error;} diagnostics;
static uint16_t tiles[1200];
static V6Room current_room={tiles,0,0,0,0,0};
''' + native[start:end] + r'''
int main(void)
{
    unsigned i,j,t;
    reset_platforms();
    /* Each actual movement callback must contact only the selected platform. */
    for(i=0;i<PLATFORM_COUNT;++i) {
        reset_platforms();
        v6_player_init(&slice.player,platform_setup[i][0],platform_setup[i][1]-23,0);
        platform_motion=(V6PlayerMotion){0,slice.player.y};
        platform_movement(&slice.player,&current_room,0,0,0);
        for(j=0;j<PLATFORM_COUNT;++j) assert(disappearing[j].state==(i==j?1:0));
        update_disappearing(0);
        assert(disappearing[i].state==2 && disappearing_sound);
        for(t=0;t<12;++t) update_disappearing(0);
        assert(disappearing[i].invisible);
        for(j=0;j<PLATFORM_COUNT;++j) assert(platform_blocks[j].w==(i==j?0:32));
    }
    /* Simultaneous collapse then death: reverse entity updates repopulate
     * slots in reverse order. Repeating catches accidental index ownership. */
    reset_platforms();platform_pushes=0;
    for(t=0;t<32;++t) {
        for(i=0;i<PLATFORM_COUNT;++i) v6_disappearing_contact(&disappearing[i],1);
        disappearing_sound=0;update_disappearing(0);
        assert(disappearing_sound && platform_pushes==(t+1)*3);
        for(j=0;j<12;++j) update_disappearing(0);
        for(i=0;i<PLATFORM_COUNT;++i) {
            assert(disappearing[i].state==3 && disappearing[i].invisible);
            assert(platform_blocks[i].w==0 && platform_blocks[i].h==0);
        }
        update_disappearing(1);
        for(i=0;i<PLATFORM_COUNT;++i) assert(disappearing[i].state==4);
        update_disappearing(0);
        for(i=0;i<PLATFORM_COUNT;++i) {
            assert(disappearing[i].state==5 && !disappearing[i].invisible);
            assert(platform_blocks[i].x==platform_setup[2-i][0]);
            assert(platform_blocks[i].y==platform_setup[2-i][1]);
            assert(platform_blocks[i].w==32 && platform_blocks[i].h==8);
        }
        for(j=0;j<4;++j) update_disappearing(0);
        for(i=0;i<PLATFORM_COUNT;++i)
            assert(disappearing[i].state==0 && disappearing[i].walking_frame==0);
        assert(current_room.block_count==3 && disappearing_count==3 && !diagnostics.error);
    }
    /* Recontact during recharge is legal and advances beyond the ordinary
     * five-frame range. Do not silently reset the desktop walking frame. */
    reset_platforms();
    for(t=0;t<16;++t) {
        v6_disappearing_contact(&disappearing[0],1);
        update_disappearing(0);
        for(j=0;j<12;++j) update_disappearing(0);
        update_disappearing(1);
        update_disappearing(0);
        assert(disappearing[0].state==5 && disappearing[0].walking_frame==(int)(3*(t+1)));
        assert(!diagnostics.error && current_room.block_count==3);
    }
    assert(disappearing[0].walking_frame==48);
    return 0;
}
'''
    BUILD.mkdir(parents=True, exist_ok=True)
    path = BUILD / 'disappearing_scene.c'
    path.write_text(source)
    executable = BUILD / 'disappearing_scene'
    subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
        '-fsanitize=undefined', '-fno-sanitize-recover=all',
        '-I' + str(ROOT / 'amiga_version'), str(path),
        *[str(ROOT / 'amiga_version' / f) for f in
          ('player.c', 'terrain.c', 'platform.c', 'enemy.c', 'blocks.c', 'disappearing.c')],
        '-o', str(executable)], check=True)
    subprocess.run([str(executable)], check=True)
    print('PASS: native adapter; three independent contacts and 32 shared-bank collapse/death/recharge cycles; 16 recharge retriggers through frame 48 (UBSan)')


if __name__ == '__main__':
    main()
