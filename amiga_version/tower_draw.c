#include "tower_draw.h"
/* Fixed tile height: constant displacements avoid eight loop iterations and
 * repeated row-address arithmetic per tile on a 68000. Byte accesses retain
 * the atlas/ring alignment contract. */
static void tile_column(uint8_t *dst,const uint8_t *src)
{
    dst[0]=src[0];dst[40]=src[1];dst[80]=src[2];dst[120]=src[3];
    dst[160]=src[4];dst[200]=src[5];dst[240]=src[6];dst[280]=src[7];
}
static uint16_t be_word(uint16_t value)
{
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return (uint16_t)((value<<8)|(value>>8));
#else
    return value;
#endif
}
static void pair_column(uint16_t *dst,const uint16_t *src)
{
    dst[0]=be_word(src[0]);dst[20]=be_word(src[1]);
    dst[40]=be_word(src[2]);dst[60]=be_word(src[3]);
    dst[80]=be_word(src[4]);dst[100]=be_word(src[5]);
    dst[120]=be_word(src[6]);dst[140]=be_word(src[7]);
}
void v6_tower_draw_reset(V6TowerDraw *d) { d->valid=0;d->complete=0; }
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
    int row,first,end;
    uint32_t bit;
    if(decoded) *decoded=0;
    if(drawn) *drawn=0;
    if(top< -32768 || top>32737) return 0;
    v6_tower_draw_span(d,top,&first,&end);d->complete=0;
    for(row=first,bit=(uint32_t)1<<((unsigned)first&31);row<end;
        ++row,bit=(bit<<1)|(bit>>31)) {
        unsigned slot=(unsigned)row&31,loaded;
        const uint16_t *tiles;
        if((d->valid&bit) && d->tags[slot]==row) continue;
        tiles=v6_tower_row(stream,row,&loaded);
        if(decoded) *decoded+=loaded;
        if(!tiles || !v6_tower_draw_row(ring,row,tiles,atlas,count)) return 0;
        d->tags[slot]=(int16_t)row;d->valid|=bit;
        if(drawn) ++*drawn;
    }
    d->top=(int16_t)top;d->complete=1;
    return 1;
}

int v6_tower_draw_mono_prepare(V6TowerDraw *d,uint8_t *ring,V6TowerStream *stream,
    int top,const uint8_t *atlas,unsigned count,unsigned *drawn)
{
    int row,first,end;
    uint32_t bit;
    if(drawn) *drawn=0;
    if(top< -32768 || top>32737) return 0;
    v6_tower_draw_span(d,top,&first,&end);d->complete=0;
    for(row=first,bit=(uint32_t)1<<((unsigned)first&31);row<end;
        ++row,bit=(bit<<1)|(bit>>31)) {
        unsigned slot=(unsigned)row&31,x;
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
    d->top=(int16_t)top;d->complete=1;
    return 1;
}
static inline __attribute__((always_inline)) int pair_prepare(V6TowerDraw *d,uint8_t *ring,V6TowerStream *stream,
    int top,const uint16_t offsets[1024],const uint16_t *atlas,unsigned words,
    unsigned count,unsigned planes,unsigned *drawn,int verified,unsigned budget)
{
    int row,first,end;uint32_t bit;
    if(drawn) *drawn=0;
    if(top< -32768 || top>32737 || ((uintptr_t)ring&1) ||
       !count || count>32 || !planes || planes>2 || words<planes*8) return 0;
    v6_tower_draw_span(d,top,&first,&end);d->complete=0;
    for(row=first,bit=(uint32_t)1<<((unsigned)first&31);row<end;
        ++row,bit=(bit<<1)|(bit>>31)) {
        unsigned slot=(unsigned)row&31,x,plane;
        const uint16_t *tiles;
        const uint16_t *columns[20];
        if((d->valid&bit) && d->tags[slot]==row) continue;
        if(!budget) return 2;
        --budget;
        tiles=v6_tower_row(stream,row,0);
        if(!tiles) return 0;
        /* Validate the whole row before writing either plane. */
        for(x=0;x<40;x+=2) {
            unsigned offset;
            if(!verified && (tiles[x]>=count || tiles[x+1]>=count)) return 0;
            offset=offsets[tiles[x]*32+tiles[x+1]];
            if(!verified && (offset==0xffff || offset>words-planes*8)) return 0;
            columns[x/2]=atlas+offset;
        }
        for(plane=0;plane<planes;++plane) {
            uint16_t *dst=(uint16_t *)(void *)(ring+slot*320+plane*V6_TOWER_PLANE_BYTES);
            for(x=0;x<20;++x)
                pair_column(dst+x,columns[x]+plane*8);
        }
        d->tags[slot]=(int16_t)row;d->valid|=bit;
        if(drawn) ++*drawn;
    }
    d->top=(int16_t)top;d->complete=1;
    return 1;
}
int v6_tower_draw_pair_prepare(V6TowerDraw *d,uint8_t *ring,V6TowerStream *s,int top,
    const uint16_t offsets[1024],const uint16_t *atlas,unsigned words,unsigned count,
    unsigned planes,unsigned *drawn)
{ return pair_prepare(d,ring,s,top,offsets,atlas,words,count,planes,drawn,0,31); }
int v6_tower_draw_pair_prepare_verified(V6TowerDraw *d,uint8_t *ring,V6TowerStream *s,int top,
    const uint16_t offsets[1024],const uint16_t *atlas,unsigned words,unsigned count,
    unsigned planes,unsigned *drawn)
{ return pair_prepare(d,ring,s,top,offsets,atlas,words,count,planes,drawn,1,31); }
int v6_tower_draw_pair_prepare_budget(V6TowerDraw *d,uint8_t *ring,V6TowerStream *s,int top,
    const uint16_t offsets[1024],const uint16_t *atlas,unsigned words,unsigned count,
    unsigned planes,unsigned *drawn,unsigned budget)
{ return pair_prepare(d,ring,s,top,offsets,atlas,words,count,planes,drawn,0,budget); }
int v6_tower_pairs_validate(V6TowerStream *s,const uint16_t offsets[1024],
    unsigned words,unsigned count,unsigned planes)
{
    unsigned row,x;
    if(!count || count>32 || !planes || planes>2 || words<planes*8) return 0;
    for(row=0;row<s->height;++row) {
        const uint16_t *tiles=v6_tower_row(s,(int)row,0);
        if(!tiles) return 0;
        for(x=0;x<40;x+=2) {
            unsigned offset;
            if(tiles[x]>=count || tiles[x+1]>=count) return 0;
            offset=offsets[tiles[x]*32+tiles[x+1]];
            if(offset==0xffff || offset>words-planes*8) return 0;
        }
    }
    return s->height!=0;
}
