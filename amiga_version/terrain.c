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
