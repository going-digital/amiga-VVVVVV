#include "campaign_menu.h"
static void copy(void *out,const void *in,unsigned n)
{volatile uint8_t *d=out;const volatile uint8_t *s=in;while(n--)*d++=*s++;}
static uint32_t crc(const uint8_t *p,unsigned n)
{uint32_t c=0xffffffffU;unsigned i,b;for(i=0;i<n;++i){c^=p[i];for(b=0;b<8;++b)c=(c>>1)^((c&1)?0xedb88320U:0);}return c^0xffffffffU;}
static unsigned get16(const uint8_t *p){return ((unsigned)p[0]<<8)|p[1];}
static uint32_t get32(const uint8_t *p){return ((uint32_t)get16(p)<<16)|get16(p+2);}
static void put16(uint8_t *p,unsigned n){p[0]=(uint8_t)(n>>8);p[1]=(uint8_t)n;}
static void put32(uint8_t *p,uint32_t n){put16(p,(unsigned)(n>>16));put16(p+2,(unsigned)n);}
static void clock_put(uint8_t *p,const V6SaveClock *c)
{put16(p,c->hours);put16(p+2,c->minutes);put16(p+4,c->seconds);put16(p+6,c->frames);}
static void clock_get(V6SaveClock *c,const uint8_t *p)
{c->hours=(uint16_t)get16(p);c->minutes=(uint16_t)get16(p+2);c->seconds=(uint16_t)get16(p+4);c->frames=(uint16_t)get16(p+6);}
static int valid(const V6MenuRecord *r)
{
    char text[12];V6SaveSummary scratch;unsigned i,count=0;
    if(!v6_save_clock_text(text,&r->menu.clock) || r->menu.deaths>0x7fffffffU ||
       r->menu.crew_mask>63 || !(r->menu.crew_mask&1) ||
       ((r->menu.crew_mask>>2)&1)!=(unsigned)r->yellow.yellow_rescued ||
       ((r->menu.crew_mask>>3)&1)!=(unsigned)r->red.red_rescued || r->menu.last.exists>1)return 0;
    if(r->menu.last.exists) {
        if(!v6_save_summary_publish(&scratch,&r->menu.last,1) || !(scratch.crew_mask&1) ||
           (r->menu.last.crew_mask&r->menu.crew_mask)!=r->menu.last.crew_mask)return 0;
        for(i=0;i<100;++i)if(r->collected.bits[i>>3]&(1U<<(i&7)))++count;
        if(r->menu.last.trinkets>count)return 0;
        /* A saved receipt cannot be from the future. */
        if(r->menu.last.clock.hours>r->menu.clock.hours)return 0;
        if(r->menu.last.clock.hours==r->menu.clock.hours && r->menu.last.clock.minutes>r->menu.clock.minutes)return 0;
        if(r->menu.last.clock.hours==r->menu.clock.hours && r->menu.last.clock.minutes==r->menu.clock.minutes &&
           r->menu.last.clock.seconds>r->menu.clock.seconds)return 0;
        if(r->menu.last.clock.hours==r->menu.clock.hours && r->menu.last.clock.minutes==r->menu.clock.minutes &&
           r->menu.last.clock.seconds==r->menu.clock.seconds && r->menu.last.clock.frames>r->menu.clock.frames)return 0;
    } else {
        const uint8_t *p=(const void *)&r->menu.last;
        for(i=0;i<sizeof(r->menu.last);++i)if(p[i])return 0;
    }
    return 1;
}
int v6_campaign_menu_encode(uint8_t *out,size_t n,const V6MenuRecord *r)
{
    uint8_t p[V6_CAMPAIGN_MENU_BYTES],old[V6_CAMPAIGN_HINT_BYTES];unsigned i;
    if(!out || !r || n!=sizeof(p) || !valid(r) ||
       !v6_campaign_menu_prefix_encode(old,sizeof(old),&r->checkpoint,&r->red,&r->yellow,&r->explored,&r->collected,&r->hints))return 0;
    for(i=0;i<108;++i)p[i]=old[i];
    p[5]=6;p[7]=sizeof(p);
    clock_put(p+108,&r->menu.clock);put32(p+116,r->menu.deaths);
    p[120]=(uint8_t)r->menu.crew_mask;p[121]=(uint8_t)r->menu.last.exists;
    clock_put(p+122,&r->menu.last.clock);
    put16(p+130,(unsigned)r->menu.last.room_x);put16(p+132,(unsigned)r->menu.last.room_y);
    put16(p+134,r->menu.last.trinkets);put16(p+136,r->menu.last.crew_mask);
    p[138]=p[139]=0;put32(p+140,crc(p,140));copy(out,p,sizeof(p));return 1;
}
int v6_campaign_menu_decode(V6MenuRecord *out,const uint8_t *p,size_t n)
{
    V6MenuRecord r;uint8_t old[V6_CAMPAIGN_HINT_BYTES];unsigned i;
    if(!out || !p)return 0;
    {volatile uint8_t *q=(void *)&r;for(i=0;i<sizeof(r);++i)q[i]=0;}
    if(n==V6_CAMPAIGN_MENU_BYTES) {
        if(p[4] || p[5]!=6 || p[6] || p[7]!=n || p[138] || p[139] || get32(p+140)!=crc(p,140))return 0;
        for(i=0;i<108;++i)old[i]=p[i];
        old[7]=sizeof(old);put32(old+108,crc(old,108));
        clock_get(&r.menu.clock,p+108);r.menu.deaths=get32(p+116);
        r.menu.crew_mask=p[120];r.menu.last.exists=p[121];clock_get(&r.menu.last.clock,p+122);
        r.menu.last.room_x=(int16_t)get16(p+130);r.menu.last.room_y=(int16_t)get16(p+132);
        r.menu.last.trinkets=(uint16_t)get16(p+134);r.menu.last.crew_mask=(uint16_t)get16(p+136);
        p=old;n=sizeof(old);
    }
    if(p==old){if(!v6_campaign_menu_prefix_decode(&r.checkpoint,&r.red,&r.yellow,&r.explored,&r.collected,&r.hints,p,n))return 0;}
    else if(!v6_campaign_hint_decode(&r.checkpoint,&r.red,&r.yellow,&r.explored,&r.collected,&r.hints,p,n))return 0;
    if(p!=old)r.menu.crew_mask=(uint16_t)(1|(r.yellow.yellow_rescued<<2)|(r.red.red_rescued<<3));
    if(!valid(&r))return 0;
    copy(out,&r,sizeof(r));return 1;
}
