#include "region_cache.h"
#include "room_codec.h"
static unsigned word(const uint8_t *p){return ((unsigned)p[0]<<8)|p[1];}
static uint32_t longword(const uint8_t *p){return ((uint32_t)word(p)<<16)|word(p+2);}
static uint32_t crc(const uint8_t *p,unsigned n)
{
    uint32_t v=0xffffffffUL;unsigned i;
    while(n--){v^=*p++;for(i=0;i<8;++i)v=(v>>1)^((v&1)?0xedb88320UL:0);}
    return ~v;
}
static const uint16_t *words(uint8_t *p,unsigned n)
{
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    unsigned i;for(i=0;i<n;++i){uint8_t a=p[i*2];p[i*2]=p[i*2+1];p[i*2+1]=a;}
#else
    (void)n;
#endif
    return (const uint16_t *)p;
}
static int display_valid(const V6RegionRoom *r)
{
    const uint8_t *p=r->display;unsigned size=r->display_bytes,y,x;uint16_t row[40];
    if(size<190 || longword(p)!=0x56365452UL || word(p+4)!=1 || word(p+6)!=40 || word(p+8)!=30 || r->pair_words<16)return -1;
    for(y=0;y<30;++y){const uint8_t *d=p+10+y*6;uint32_t at=longword(d);unsigned length=word(d+4);
        if(!length || at>size-190 || length>size-190-at || !v6_unpack_room(p+190+at,length,row,40))return -(int)(100+y);
        for(x=0;x<40;x+=2){unsigned offset;
            if(row[x]>=r->tile_count || row[x+1]>=r->tile_count)return -(int)(200+y);
            offset=r->offsets[row[x]*32+row[x+1]];
            if(offset==0xffff || offset>(unsigned)r->pair_words-16)return -(int)(300+y);}
    }
    return 1;
}
static int decode(V6RegionSlot *slot,unsigned region,unsigned size)
{
    uint8_t *p=(uint8_t *)slot->data;unsigned count,i,at;slot->failure=10;
    if(size<20 || size>V6_REGION_BYTES || longword(p)!=0x56365247UL || word(p+4)!=1 ||
       word(p+6)!=region || word(p+10) || longword(p+12)!=size ||
       longword(p+size-4)!=crc(p,size-4))return 0;
    slot->failure=20;count=word(p+8);if(!count || count>V6_REGION_ROOMS)return 0;
    at=16+count*32;
    for(i=0;i<count;++i){const uint8_t *d=p+16+i*32;V6RegionRoom *r=&slot->rooms[i];
        unsigned bytes,used,j,display;
        if(at>size-4)return 0;
        r->id=word(d);r->x=word(d+2);r->y=word(d+4);r->tileset=word(d+6);
        r->tile_count=word(d+8);r->pair_words=word(d+10);r->display_bytes=word(d+12);
        bytes=longword(d+20);display=r->display_bytes;
        used=2408+r->tile_count*64+r->pair_words*2+display+(display&1);
        if(r->x<100 || r->x>=120 || r->y<100 || r->y>=120 || r->tileset>2 ||
           !r->tile_count || r->tile_count>32 || !r->pair_words || r->pair_words>4096 ||
           word(d+14)!=r->tile_count*32 || longword(d+16)!=at ||
           longword(d+24) || longword(d+28) || bytes!=used || bytes>size-4-at)return 0;
        for(j=0;j<i;++j)if(slot->rooms[j].id==r->id ||
            (slot->rooms[j].x==r->x && slot->rooms[j].y==r->y))return 0;
        slot->failure=30;r->tiles=words(p+at,1200);r->palette=words(p+at+2400,4);
        r->offsets=words(p+at+2408,r->tile_count*32);
        r->pairs=words(p+at+2408+r->tile_count*64,r->pair_words);
        r->display=p+at+2408+r->tile_count*64+r->pair_words*2;
        {int valid=display_valid(r);if(valid!=1){slot->failure=(unsigned)-valid;return 0;}}
        /* Explicit words also avoid GCC 14 m68k narrowing an autoincrement
         * comparison to bytes while retaining the wrong pointer stride. */
        if((r->palette[0]|r->palette[1]|r->palette[2]|r->palette[3])&0xf000)return 0;
        at+=bytes;
    }
    if(at!=size-4)return 0;
    slot->count=count;slot->region=region;slot->valid=1;slot->failure=0;return 1;
}
void v6_region_init(V6RegionCache *c)
{
    unsigned i;c->active=V6_REGION_SLOTS;c->clock=c->hits=c->misses=c->reads=c->errors=0;
    for(i=0;i<V6_REGION_SLOTS;++i)c->slots[i].valid=0;
}
const V6RegionRoom *v6_region_get(V6RegionCache *c,unsigned region,unsigned room,V6RegionRead read,void *context)
{
    unsigned i,j,slot=V6_REGION_SLOTS,size=0;
    for(i=0;i<V6_REGION_SLOTS;++i)if(c->slots[i].valid && c->slots[i].region==region){slot=i;break;}
    if(slot==V6_REGION_SLOTS){++c->misses;
        for(i=0;i<V6_REGION_SLOTS;++i)if(i!=c->active &&
            (slot==V6_REGION_SLOTS || !c->slots[i].valid || c->slots[i].used<c->slots[slot].used))slot=i;
        if(slot==V6_REGION_SLOTS || !read){++c->errors;return 0;}
        c->slots[slot].valid=0;c->slots[slot].failure=1;++c->reads;
        if(!read(context,region,c->slots[slot].data,V6_REGION_BYTES,&size) || !decode(&c->slots[slot],region,size)){
            c->slots[slot].valid=0;++c->errors;return 0;}
    }else ++c->hits;
    for(j=0;j<c->slots[slot].count;++j)if(c->slots[slot].rooms[j].id==room){
        c->active=slot;c->slots[slot].used=++c->clock;return &c->slots[slot].rooms[j];}
    ++c->errors;return 0;
}
