#include <assert.h>
#include <stdio.h>
#include "player.h"
static uint16_t tiles[1200];
static V6Terrain cache;
int main(void)
{
    unsigned id,checks=0;
    int set,extra,x,y;
    V6Room room={tiles,0,0,0};
    for(set=0;set<3;++set) for(extra=0;extra<2;++extra) {
        room.tileset=set; room.extra_row=extra;
        for(id=0;id<1024;++id) {
            int expected=set==2?(id>=12 && id<=27):
                id==1 || (id>=80 && id<680) || (id==59 && set==0) || (id==740 && set==1);
            for(x=0;x<1200;++x) tiles[x]=id;
            v6_terrain_build(&cache,&room);
            assert(cache.directional==(id>=14 && id<=17));
            for(y=-2;y<=31;++y) for(x=-2;x<=41;++x) {
                int inside=x>=-1 && x<=40 && y>=-1 && y<=29+extra;
                assert(v6_terrain_solid(&cache,x,y)==(inside && expected));
                ++checks;
            }
        }
    }
    /* Mixed edge cells: check replication uses the adjacent tile, not a
     * blanket solid border, and rebuilding clears old classifications. */
    room.tileset=0; room.extra_row=1;
    for(x=0;x<1200;++x) tiles[x]=(x%3)?0:80;
    v6_terrain_build(&cache,&room);
    for(y=-1;y<=30;++y) for(x=-1;x<=40;++x) {
        int sx=x<0?0:x>39?39:x, sy=y<0?0:y>29?29:y;
        assert(v6_terrain_solid(&cache,x,y)==(tiles[sy*40+sx]==80)); ++checks;
    }
    assert(!cache.directional);
    printf("PASS: %u terrain classification and border queries\n",checks);
    return 0;
}
