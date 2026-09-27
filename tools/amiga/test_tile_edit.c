/* Tile mutation/cache regression, including the disappearing-platform patch. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "player.h"
#include "disappearing.h"
static uint16_t tiles[1200];
static V6Terrain cache,reference;
int main(void)
{
    V6Room room={tiles,0,0,&cache,0,0};
    unsigned checks=0;
    const uint16_t ids[]={0,1,14,17,59,80,679,680,740};
    for(int set=0;set<3;++set) for(int extra=0;extra<2;++extra) {
        room.tileset=set;room.extra_row=extra;
        memset(tiles,0,sizeof tiles);v6_terrain_build(&cache,&room);
        for(int y=0;y<30;++y) for(int x=0;x<40;++x) {
            for(unsigned i=0;i<sizeof(ids)/sizeof(ids[0]);++i) {
                int changed=tiles[y*40+x]!=ids[i];
                assert(v6_terrain_set_tile(&cache,tiles,set,extra,x,y,ids[i])==changed);
                v6_terrain_build(&reference,&room);
                assert(memcmp(&cache,&reference,sizeof cache)==0);
                assert(v6_terrain_set_tile(&cache,tiles,set,extra,x,y,ids[i])==0);
                ++checks;
            }
            assert(v6_terrain_set_tile(&cache,tiles,set,extra,x,y,0)==1);
            assert(cache.directional==0);
        }
    }
    memset(tiles,0,sizeof tiles);room.tileset=room.extra_row=0;
    v6_terrain_build(&cache,&room);
    V6Disappearing platform={3,0,4,0,1};
    V6Block blocks[1]={{120,72,0,0,V6_BLOCK,0}};
    unsigned count=1;
    unsigned event=v6_disappearing_update_room(&platform,120,72,blocks,&count,1,1,111,107,0);
    assert(event==V6_DISAPPEAR_DEATH_TILE && platform.state==4);
    assert(count==1 && blocks[0].w==0 && blocks[0].h==0);
    assert(!v6_terrain_solid(&cache,18,9));
    assert(v6_terrain_set_tile(&cache,tiles,0,0,18,9,59)==1);
    assert(tiles[9*40+18]==59 && v6_terrain_solid(&cache,18,9));
    assert(v6_terrain_set_tile(&cache,tiles,0,0,18,9,59)==0);
    assert(v6_disappearing_update_room(&platform,120,72,blocks,&count,1,1,111,107,0)==0);
    assert(v6_disappearing_update_room(&platform,120,72,blocks,&count,1,0,111,107,0)==V6_DISAPPEAR_CREATE);
    assert(count==1 && blocks[0].x==120 && blocks[0].y==72 && blocks[0].w==32 && blocks[0].h==8);
    assert(tiles[9*40+18]==59 && v6_terrain_solid(&cache,18,9));
    reference=cache;
    assert(v6_terrain_set_tile(&cache,tiles,0,0,-1,9,0)==-1);
    assert(v6_terrain_set_tile(&cache,tiles,0,0,40,9,0)==-1);
    assert(v6_terrain_set_tile(&cache,tiles,0,0,18,-1,0)==-1);
    assert(v6_terrain_set_tile(&cache,tiles,0,0,18,30,0)==-1);
    assert(v6_terrain_set_tile(&cache,tiles,3,0,18,9,0)==-1);
    assert(v6_terrain_set_tile(&cache,tiles,0,2,18,9,0)==-1);
    assert(memcmp(&cache,&reference,sizeof cache)==0 && tiles[9*40+18]==59);
    printf("PASS: %u tile edits, border/directional cache rebuilds, death patch and invalid edits\n",checks);
    return 0;
}
