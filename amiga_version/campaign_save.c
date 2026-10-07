#include "campaign_save.h"
static uint32_t crc(const uint8_t *p,unsigned n)
{
    uint32_t c=0xffffffffU;unsigned i,b;
    for(i=0;i<n;++i) { c^=p[i];for(b=0;b<8;++b)c=(c>>1)^((c&1)?0xedb88320U:0); }
    return c^0xffffffffU;
}
static void put(uint8_t *p,uint32_t v)
{ p[0]=(uint8_t)(v>>24);p[1]=(uint8_t)(v>>16);p[2]=(uint8_t)(v>>8);p[3]=(uint8_t)v; }
static uint32_t get(const uint8_t *p)
{ return ((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3]; }
static int valid(const V6CheckpointSave *c,const V6HallwayStory *s)
{
    int tower=c->room_x==109 && (c->room_y==104 || c->room_y==109);
    int hall=(c->room_x==110 && c->room_y==104)||(c->room_x==108 && c->room_y==109)||(c->room_x==111 && c->room_y==104);
    return (tower||hall) && c->x>=0 && c->x<=320 && c->y>=0 && c->y<=(tower?5600:240)
        && (c->gravity==0 || c->gravity==1) && (c->dir==0 || c->dir==1)
        && c->id>=-1 && c->id<=0x7fffffff
        && !s->time_trial && !s->translator_exploring
        && (s->rescue_triggered==0 || s->rescue_triggered==1)
        && (s->red_rescued==0 || s->red_rescued==1)
        && (s->companion==0 || s->companion==9)
        && s->red_rescued==s->rescue_triggered
        && (s->companion!=9 || s->red_rescued);
}
int v6_campaign_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,const V6HallwayStory *s)
{
    uint8_t p[V6_CAMPAIGN_SAVE_BYTES];unsigned i;
    if(!out || !c || !s || n!=sizeof(p) || !valid(c,s))return 0;
    p[0]='V';p[1]='6';p[2]='C';p[3]='S';p[4]=0;p[5]=1;p[6]=0;p[7]=sizeof(p);
    put(p+8,(uint32_t)c->x);put(p+12,(uint32_t)c->y);put(p+16,(uint32_t)c->gravity);
    put(p+20,(uint32_t)c->dir);put(p+24,(uint32_t)c->room_x);put(p+28,(uint32_t)c->room_y);
    put(p+32,(uint32_t)c->id);
    put(p+36,(uint32_t)(s->rescue_triggered|s->red_rescued<<1|(s->companion==9)<<2));
    put(p+40,crc(p,40));for(i=0;i<sizeof(p);++i)out[i]=p[i];return 1;
}
int v6_campaign_decode(V6CheckpointSave *out,V6HallwayStory *story,const uint8_t *p,size_t n)
{
    V6CheckpointSave c;V6HallwayStory s;uint32_t f,id;unsigned i;
    if(!out || !story || !p || n!=V6_CAMPAIGN_SAVE_BYTES)return 0;
    if(p[0]!='V'||p[1]!='6'||p[2]!='C'||p[3]!='S'||p[4]||p[5]!=1||p[6]||p[7]!=n
       || get(p+40)!=crc(p,40))return 0;
    for(i=8;i<32;i+=4)if(get(p+i)>0x7fffffffU)return 0;
    id=get(p+32);if(id>0x7fffffffU && id!=0xffffffffU)return 0;
    c.x=(int)get(p+8);c.y=(int)get(p+12);c.gravity=(int)get(p+16);c.dir=(int)get(p+20);
    c.room_x=(int)get(p+24);c.room_y=(int)get(p+28);c.id=id==0xffffffffU?-1:(int)id;
    f=get(p+36);if(f&~7U)return 0;
    s.time_trial=s.translator_exploring=0;s.rescue_triggered=f&1;s.red_rescued=(f>>1)&1;s.companion=(f&4)?9:0;
    if(!valid(&c,&s))return 0;
    *out=c;*story=s;return 1;
}

int v6_campaign_checkpoint_valid(const V6CheckpointSave *s,const V6Checkpoint *bank,unsigned count)
{
    unsigned i;
    if(!s || !bank || count>32 || (s->dir!=0 && s->dir!=1))return 0;
    for(i=0;i<count;++i) {
        const V6Checkpoint *c=&bank[i];
        if(c->id==s->id && (c->tile==20 || c->tile==21))
            return s->x==c->x-4 && s->y==c->y-(c->tile==20?2:7) && s->gravity==(c->tile==20);
    }
    return 0;
}
