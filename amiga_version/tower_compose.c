#include "tower_compose.h"
#include "tower_draw.h"
int v6_tower_mask_row(uint8_t *ring,int row,const uint16_t *tiles,
    const uint8_t *masks,unsigned count)
{
    unsigned x,y;
    if(row< -32768 || row>32767) return 0;
    for(x=0;x<40;++x) if(tiles[x]>=count) return 0;
    ring+=((unsigned)row&31)*320;
    for(x=0;x<40;++x)
        for(y=0;y<8;++y) ring[y*40+x]=masks[(uint32_t)tiles[x]*8+y];
    return 1;
}
int v6_tower_compose(uint8_t *out,const uint8_t *fg,const uint8_t *bg,
    const uint8_t *opacity,unsigned fg_offset,unsigned bg_offset)
{
    unsigned y,x;
    if(fg_offset>255 || bg_offset>255) return 0;
    for(y=0;y<240;++y) {
        unsigned f=((fg_offset+y)&255)*40,b=((bg_offset+y)&255)*40;
        for(x=0;x<40;++x) {
            unsigned mask=opacity[f+x];
            out[x]=(fg[f+x]&mask)|(bg[b+x]&~mask);
            out[9600+x]=(fg[V6_TOWER_PLANE_BYTES+f+x]&mask)|
                (bg[V6_TOWER_PLANE_BYTES+b+x]&~mask);
        }
        out+=40;
    }
    return 1;
}
