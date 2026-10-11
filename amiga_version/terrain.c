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
    int height,old,sx,sy,x0,x1,y0,y1,solid;
    if((unsigned)x>=40 || (unsigned)y>=30 || (unsigned)tileset>2 ||
       (unsigned)extra_row>1) return -1;
    height=29+extra_row;
    if(tiles[y*40+x]==tile) return 0;
    old=tiles[y*40+x];
    tiles[y*40+x]=tile;
    /* Row 29 is excluded in ordinary rooms. Preserve duplicated edge cells
     * without rebuilding 2048 classifications during a death-time tile edit. */
    if(y>=height)return 1;
    solid=tileset==2 ? tile>=12 && tile<=27 :
        tile==1 || (tile>=80 && tile<680) ||
        (tile==59 && tileset==0) || (tile==740 && tileset==1);
    x0=x==0?0:x+1;x1=x==39?41:x+1;
    y0=y==0?0:y+1;y1=y==height-1?height+1:y+1;
    for(sy=y0;sy<=y1;++sy)for(sx=x0;sx<=x1;++sx)out->solid[sy][sx]=(uint8_t)solid;
    if(tile>=14 && tile<=17)out->directional=1;
    else if(old>=14 && old<=17) {
        out->directional=0;
        /* Removing a directional tile may remove the last one. */
        for(sy=0;sy<height;++sy)for(sx=0;sx<40;++sx) {
            unsigned other=tiles[sy*40+sx];
            if(other>=14 && other<=17) {out->directional=1;return 1;}
        }
    }
    return 1;
}
