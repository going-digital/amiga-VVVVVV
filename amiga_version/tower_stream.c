#include "tower_stream.h"
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
