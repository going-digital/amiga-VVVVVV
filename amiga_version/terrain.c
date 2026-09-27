#include "player.h"
void v6_terrain_build(V6Terrain *out, const V6Room *room)
{
    int x,y,height=29+room->extra_row;
    out->directional=0;
    for(y=0;y<height;++y) for(x=0;x<40;++x) {
        unsigned tile=room->tiles[y*40+x];
        if(tile>=14 && tile<=17) out->directional=1;
    }
    for(y=0;y<32;++y) for(x=0;x<64;++x) {
        int sx=x-1,sy=y-1,solid=0;
        if(sx==-1) sx=0;
        if(sx==40) sx=39;
        if(sy==-1) sy=0;
        if(sy==height) sy=height-1;
        if(sx>=0 && sx<40 && sy>=0 && sy<height) {
            unsigned tile=room->tiles[sy*40+sx];
            solid=room->tileset==2 ? tile>=12 && tile<=27 :
                tile==1 || (tile>=80 && tile<680) ||
                (tile==59 && room->tileset==0) || (tile==740 && room->tileset==1);
        }
        out->solid[y][x]=(uint8_t)solid;
    }
}

int v6_terrain_set_tile(V6Terrain *out,uint16_t *tiles,int tileset,int extra_row,
                        int x,int y,uint16_t tile)
{
    V6Room room;
    if((unsigned)x>=40 || (unsigned)y>=30 || (unsigned)tileset>2 ||
       (unsigned)extra_row>1) return -1;
    if(tiles[y*40+x]==tile) return 0;
    tiles[y*40+x]=tile;
    room.tiles=tiles;room.tileset=tileset;room.extra_row=extra_row;
    room.terrain=0;room.blocks=0;room.block_count=0;
    /* Changes can remove the final directional tile or affect duplicated
     * border cells. Rebuild all classifications, not just one cached byte. */
    v6_terrain_build(out,&room);
    return 1;
}
