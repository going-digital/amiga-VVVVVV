#include "tower_stream.h"
static inline __attribute__((always_inline)) const uint16_t *cached_row(V6TowerStream *s,int y)
{
    unsigned slot=(unsigned)y&31;
    if(y>=-32768 && y<=32767 &&
       (s->valid==0xffffffffUL || (s->valid&((uint32_t)1<<slot))) && s->tags[slot]==y)
        return s->tiles[slot];
    return v6_tower_row(s,y,0);
}
static inline __attribute__((always_inline)) int row_solid(const uint16_t *row,int x,int minimum)
{
    int tile;
    if(!row) return 0;
    if(x<0 || x>=40) return 0;
    tile=row[x];
    return tile>=minimum && tile<=27;
}
int v6_tower_walls(void *context,int x,int y,int invincible)
{
    V6TowerStream *s=context;
    int left=x+6,top=y+2,l=left/8,r=(left+11)/8,t=top/8,b=(top+20)/8;
    int minimum=invincible?6:12,gy,previous=t,middle=(left+6)/8;
    int check_middle=middle!=l && middle!=r;
    if(l==-1) l=0;
    if(l==40) l=39;
    if(r==-1) r=0;
    if(r==40) r=39;
    if(middle==-1) middle=0;
    if(middle==40) middle=39;
    const uint16_t *row=cached_row(s,t);
    if(row_solid(row,l,minimum) || row_solid(row,r,minimum) ||
       (check_middle && row_solid(row,middle,minimum))) return 1;
    row=cached_row(s,b);
    if(row_solid(row,l,minimum) || row_solid(row,r,minimum) ||
       (check_middle && row_solid(row,middle,minimum))) return 1;
    for(gy=6;gy<=12;gy+=6) {
        int at=(top+gy)/8;
        if(at!=t && at!=b && at!=previous) {
            row=cached_row(s,at);
            if(row_solid(row,l,minimum) || row_solid(row,r,minimum)) return 1;
        }
        previous=at;
    }
    return 0;
}
int v6_tower_tile(void *context,int x,int y)
{
    V6TowerStream *s=context;
    const uint16_t *row;
    if(x==-1) x=0;
    if(x==40) x=39;
    if(x<0 || x>=40) return 0;
    /* Collision probes repeatedly hit the same few decoded rows. Avoid the
     * general decoder call on a valid logical cache hit. */
    row=cached_row(s,y);
    return row ? row[x] : -1;
}
#include "room_codec.h"
static unsigned read16(const uint8_t *p)
{ return ((unsigned)p[0]<<8)|p[1]; }
static uint32_t read32(const uint8_t *p)
{ return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3]; }
int v6_tower_open(V6TowerStream *s,const uint8_t *data,size_t size)
{
    unsigned height,i;
    size_t base;
    if(size<10 || data[0]!='V' || data[1]!='6' || data[2]!='T' || data[3]!='R' ||
       read16(data+4)!=1 || read16(data+6)!=40) return 0;
    height=read16(data+8);
    if(!height || height>700) return 0;
    base=10+height*6;
    if(base>size) return 0;
    for(i=0;i<height;++i) {
        const uint8_t *entry=data+10+i*6;
        uint32_t offset=read32(entry);
        unsigned length=read16(entry+4);
        if(!length || offset>size-base || length>size-base-offset) return 0;
    }
    s->data=data;s->size=size;s->height=(uint16_t)height;s->valid=0;
    return 1;
}
const uint16_t *v6_tower_row(V6TowerStream *s,int row,unsigned *decoded)
{
    unsigned slot;
    uint32_t bit;
    int source_row;
    const uint8_t *entry,*packet;
    if(decoded) *decoded=0;
    if(row< -32768 || row>32767 || !s->height || s->height>700) return 0;
    slot=(unsigned)row&31;bit=(uint32_t)1<<slot;
    if((s->valid&bit) && s->tags[slot]==row) return s->tiles[slot];
    /* Bounded unsigned remainder avoids a 32-bit libgcc modulo call. The
     * magnitude is at most 32768; doubling never overflows uint16_t. */
    {
        unsigned value=(unsigned)(row<0?-row:row);
        unsigned divisor=s->height;
        while(divisor<=value/2) divisor*=2;
        while(divisor>=s->height) {
            if(value>=divisor) value-=divisor;
            divisor/=2;
        }
        source_row=row<0?-(int)value:(int)value;
    }
    if(source_row<0) source_row+=s->height;
    entry=s->data+10+source_row*6;
    packet=s->data+10+s->height*6+read32(entry);
    s->valid&=~bit;
    if(!v6_unpack_room(packet,read16(entry+4),s->tiles[slot],40)) return 0;
    s->tags[slot]=(int16_t)row;s->valid|=bit;
    if(decoded) *decoded=1;
    return s->tiles[slot];
}
