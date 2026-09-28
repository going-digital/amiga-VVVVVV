#include "tower_draw.h"
/* Fixed tile height: constant displacements avoid eight loop iterations and
 * repeated row-address arithmetic per tile on a 68000. Byte accesses retain
 * the atlas/ring alignment contract. */
static void tile_column(uint8_t *dst,const uint8_t *src)
{
    dst[0]=src[0];dst[40]=src[1];dst[80]=src[2];dst[120]=src[3];
    dst[160]=src[4];dst[200]=src[5];dst[240]=src[6];dst[280]=src[7];
}
void v6_tower_draw_reset(V6TowerDraw *d) { d->valid=0; }
int v6_tower_draw_row(uint8_t *ring,int row,const uint16_t *tiles,
                      const uint8_t *atlas,unsigned count)
{
    unsigned x,plane;
    unsigned offset;
    if(row< -32768 || row>32767) return 0;
    for(x=0;x<40;++x) if(tiles[x]>=count) return 0;
    offset=((unsigned)row&31)*320;
    for(plane=0;plane<2;++plane) {
        uint8_t *dst=ring+plane*V6_TOWER_PLANE_BYTES+offset;
        for(x=0;x<40;++x) {
            const uint8_t *src=atlas+(uint32_t)tiles[x]*16+plane*8;
            tile_column(dst+x,src);
        }
    }
    return 1;
}
int v6_tower_draw_prepare(V6TowerDraw *d,uint8_t *ring,V6TowerStream *stream,int top,
    const uint8_t *atlas,unsigned count,unsigned *decoded,unsigned *drawn)
{
    int row;
    if(decoded) *decoded=0;
    if(drawn) *drawn=0;
    if(top< -32768 || top>32737) return 0;
    for(row=top;row<top+31;++row) {
        unsigned slot=(unsigned)row&31,loaded;
        uint32_t bit=(uint32_t)1<<slot;
        const uint16_t *tiles;
        if((d->valid&bit) && d->tags[slot]==row) continue;
        tiles=v6_tower_row(stream,row,&loaded);
        if(decoded) *decoded+=loaded;
        if(!tiles || !v6_tower_draw_row(ring,row,tiles,atlas,count)) return 0;
        d->tags[slot]=(int16_t)row;d->valid|=bit;
        if(drawn) ++*drawn;
    }
    return 1;
}

int v6_tower_draw_mono_prepare(V6TowerDraw *d,uint8_t *ring,V6TowerStream *stream,
    int top,const uint8_t *atlas,unsigned count,unsigned *drawn)
{
    int row;
    if(drawn) *drawn=0;
    if(top< -32768 || top>32737) return 0;
    for(row=top;row<top+31;++row) {
        unsigned slot=(unsigned)row&31,x;
        uint32_t bit=(uint32_t)1<<slot;
        const uint16_t *tiles;
        uint8_t *dst;
        if((d->valid&bit) && d->tags[slot]==row) continue;
        tiles=v6_tower_row(stream,row,0);
        if(!tiles) return 0;
        for(x=0;x<40;++x) if(tiles[x]>=count) return 0;
        dst=ring+slot*320;
        for(x=0;x<40;++x)
            tile_column(dst+x,atlas+(uint32_t)tiles[x]*8);
        d->tags[slot]=(int16_t)row;d->valid|=bit;
        if(drawn) ++*drawn;
    }
    return 1;
}
