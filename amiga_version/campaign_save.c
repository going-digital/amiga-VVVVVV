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
    int hall=(c->room_x==110 && (c->room_y==104 || c->room_y==105))||(c->room_x==108 && c->room_y==109)||(c->room_x==111 && c->room_y==104);
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
    put(p+40,crc(p,40));for(i=0;i<sizeof(p);++i)out[i]=p[i];
    return 1;
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

int v6_campaign_state_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *s,const V6Exploration *e)
{
    uint8_t p[V6_CAMPAIGN_STATE_BYTES];unsigned i;
    if(!out || !e || n!=sizeof(p) || !c || !s || !valid(c,s))return 0;
    /* Keep the codec standalone: no dependency on menu admission at link time. */
    { unsigned room=(unsigned)(c->room_y-100)*20+(unsigned)(c->room_x-100);
      if(!(e->rooms[room>>3] & (1U<<(room&7))))return 0; }
    if(!v6_campaign_encode(p,V6_CAMPAIGN_SAVE_BYTES,c,s))return 0;
    p[5]=2;p[7]=sizeof(p);
    for(i=0;i<V6_EXPLORED_BYTES;++i)p[40+i]=e->rooms[i];
    p[90]=p[91]=0;put(p+92,crc(p,92));
    for(i=0;i<sizeof(p);++i)out[i]=p[i];
    return 1;
}
int v6_campaign_state_decode(V6CheckpointSave *out,V6HallwayStory *story,
    V6Exploration *explored,const uint8_t *p,size_t n)
{
    V6CheckpointSave c;V6HallwayStory s;V6Exploration e;
    uint8_t legacy[V6_CAMPAIGN_SAVE_BYTES];unsigned i,room;
    if(!out || !story || !explored || !p)return 0;
    if(n==V6_CAMPAIGN_SAVE_BYTES) {
        if(!v6_campaign_decode(&c,&s,p,n))return 0;
        for(i=0;i<V6_EXPLORED_BYTES;++i)e.rooms[i]=0;
        room=(unsigned)(c.room_y-100)*20+(unsigned)(c.room_x-100);
        e.rooms[room>>3]=(uint8_t)(1U<<(room&7));
    } else {
        if(n!=V6_CAMPAIGN_STATE_BYTES || p[4] || p[5]!=2 || p[6] || p[7]!=n
           || p[90] || p[91] || get(p+92)!=crc(p,92))return 0;
        /* Reuse all legacy semantic guards, without weakening its version check. */
        for(i=0;i<40;++i)legacy[i]=p[i];
        legacy[5]=1;legacy[7]=sizeof(legacy);put(legacy+40,crc(legacy,40));
        if(!v6_campaign_decode(&c,&s,legacy,sizeof(legacy)))return 0;
        for(i=0;i<V6_EXPLORED_BYTES;++i)e.rooms[i]=p[40+i];
        room=(unsigned)(c.room_y-100)*20+(unsigned)(c.room_x-100);
        if(!(e.rooms[room>>3] & (1U<<(room&7))))return 0;
    }
    *out=c;*story=s;
    for(i=0;i<V6_EXPLORED_BYTES;++i)((volatile uint8_t *)explored->rooms)[i]=e.rooms[i];
    return 1;
}

static int progress_valid(const V6CheckpointSave *c,const V6HallwayStory *red,
    const V6StationStory *yellow,unsigned version)
{
    V6CheckpointSave bounded=*c;
    /* Keep legacy admission unchanged; V5 also admits V Stitch. */
    if(c->room_x==115 && c->room_y==105 && version==6){
        if(!(c->x==148 && c->y==161 && c->gravity==0 && c->id==441530))return 0;
        bounded.room_x=111;bounded.room_y=104;
    } else if(c->room_x==115 && c->room_y==103 && version==6){
        if(!(c->x==228 && c->y==182 && c->gravity==1 && c->id==1))return 0;
        bounded.room_x=111;bounded.room_y=104;
    } else if(c->room_x==114 && c->room_y==103 && version==6){
        if(!((c->x==188 && c->y==46 && c->gravity==1 && c->id==439520) ||
             (c->x==108 && c->y==153 && c->gravity==0 && c->id==439521)))return 0;
        bounded.room_x=111;bounded.room_y=104;
    } else if(c->room_x==113 && c->room_y==103 && version==6){
        if(!((c->x==20 && c->y==161 && c->gravity==0 && c->id==439510) ||
             (c->x==276 && c->y==46 && c->gravity==1 && c->id==439511)))return 0;
        bounded.room_x=111;bounded.room_y=104;
    } else if(c->room_x==112 && c->room_y>=103 && c->room_y<=106 && version==6) {
        static const int cp[6][5]={{106,284,153,0,442500},{105,60,73,0,441501},
            {105,60,134,1,441502},{104,52,97,0,440500},{104,276,185,0,440501},{103,164,97,0,439500}};
        unsigned i;int found=0;
        for(i=0;i<6;++i)if(c->room_y==cp[i][0] && c->x==cp[i][1] && c->y==cp[i][2] &&
            c->gravity==cp[i][3] && c->id==cp[i][4])found=1;
        if(!found)return 0;
        bounded.room_x=111;bounded.room_y=104;
    } else if(c->room_x==111 && c->room_y==107 && version>=4) {
        if(c->x!=236 || c->y!=134 || c->gravity!=1 || c->id!=443490)return 0;
        bounded.room_y=104;
    } else if(c->room_x==112 && c->room_y==107 && version>=5) {
        if(c->gravity!=0 || !((c->x==276 && c->y==185 && c->id==443500) ||
                            (c->x==60 && c->y==73 && c->id==443501)))return 0;
        bounded.room_x=111;bounded.room_y=104;
    } else if(c->room_x==111 && (c->room_y==105 || c->room_y==106))bounded.room_y=104;
    return valid(&bounded,red) && !yellow->time_trial && !yellow->translator_exploring
        && (yellow->rescue_triggered==0 || yellow->rescue_triggered==1)
        && (yellow->yellow_rescued==0 || yellow->yellow_rescued==1)
        && yellow->rescue_triggered==yellow->yellow_rescued
        && (yellow->companion==0 || yellow->companion==7)
        && (!yellow->companion || yellow->yellow_rescued)
        && !(red->companion && yellow->companion);
}
static int progress_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *red,const V6StationStory *yellow,const V6Exploration *e,unsigned version)
{
    uint8_t p[V6_CAMPAIGN_STATE_BYTES];unsigned i,room;uint32_t flags;
    if(!out || !c || !red || !yellow || !e || n!=sizeof(p) || !progress_valid(c,red,yellow,version))return 0;
    room=(unsigned)(c->room_y-100)*20+(unsigned)(c->room_x-100);
    if(!(e->rooms[room>>3] & (1U<<(room&7))))return 0;
    p[0]='V';p[1]='6';p[2]='C';p[3]='S';p[4]=0;p[5]=(uint8_t)version;p[6]=0;p[7]=sizeof(p);
    put(p+8,(uint32_t)c->x);put(p+12,(uint32_t)c->y);put(p+16,(uint32_t)c->gravity);
    put(p+20,(uint32_t)c->dir);put(p+24,(uint32_t)c->room_x);put(p+28,(uint32_t)c->room_y);
    put(p+32,(uint32_t)c->id);
    flags=(uint32_t)(red->rescue_triggered | red->red_rescued<<1 | (red->companion==9)<<2
        | yellow->rescue_triggered<<3 | yellow->yellow_rescued<<4 | (yellow->companion==7)<<5);
    put(p+36,flags);
    for(i=0;i<V6_EXPLORED_BYTES;++i)p[40+i]=e->rooms[i];
    p[90]=p[91]=0;put(p+92,crc(p,92));
    for(i=0;i<sizeof(p);++i)out[i]=p[i];
    return 1;
}
static int progress_decode(V6CheckpointSave *out,V6HallwayStory *red,
    V6StationStory *yellow,V6Exploration *explored,const uint8_t *p,size_t n,unsigned version)
{
    V6CheckpointSave c;V6HallwayStory r;V6StationStory y={0,0,0,0,0};V6Exploration e;
    uint32_t f,id;unsigned i,room;
    if(!out || !red || !yellow || !explored || !p)return 0;
    if(n==V6_CAMPAIGN_SAVE_BYTES || (n==V6_CAMPAIGN_STATE_BYTES && p[5]==2)) {
        if(!v6_campaign_state_decode(&c,&r,&e,p,n))return 0;
    } else {
        if(n!=V6_CAMPAIGN_STATE_BYTES || p[0]!='V' || p[1]!='6' || p[2]!='C' || p[3]!='S'
           || p[4] || p[5]!=version || p[6] || p[7]!=n || p[90] || p[91] || get(p+92)!=crc(p,92))return 0;
        for(i=8;i<32;i+=4)if(get(p+i)>0x7fffffffU)return 0;
        id=get(p+32);if(id>0x7fffffffU && id!=0xffffffffU)return 0;
        c.x=(int)get(p+8);c.y=(int)get(p+12);c.gravity=(int)get(p+16);c.dir=(int)get(p+20);
        c.room_x=(int)get(p+24);c.room_y=(int)get(p+28);c.id=id==0xffffffffU?-1:(int)id;
        f=get(p+36);if(f&~63U)return 0;
        r.time_trial=r.translator_exploring=0;r.rescue_triggered=f&1;r.red_rescued=(f>>1)&1;r.companion=(f&4)?9:0;
        y.rescue_triggered=(f>>3)&1;y.yellow_rescued=(f>>4)&1;y.companion=(f&32)?7:0;
        if(!progress_valid(&c,&r,&y,version))return 0;
        for(i=0;i<V6_EXPLORED_BYTES;++i)e.rooms[i]=p[40+i];
        room=(unsigned)(c.room_y-100)*20+(unsigned)(c.room_x-100);
        if(!(e.rooms[room>>3] & (1U<<(room&7))))return 0;
    }
    *out=c;*red=r;*yellow=y;
    for(i=0;i<V6_EXPLORED_BYTES;++i)((volatile uint8_t *)explored->rooms)[i]=e.rooms[i];
    return 1;
}

/* Public V3 entry points retain their original admission and version guards. */
int v6_campaign_progress_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *red,const V6StationStory *yellow,const V6Exploration *e)
{ return progress_encode(out,n,c,red,yellow,e,3); }
int v6_campaign_progress_decode(V6CheckpointSave *out,V6HallwayStory *red,
    V6StationStory *yellow,V6Exploration *explored,const uint8_t *p,size_t n)
{ return progress_decode(out,red,yellow,explored,p,n,3); }

int v6_campaign_collection_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *red,const V6StationStory *yellow,const V6Exploration *e,
    const V6Collect *collected)
{
    uint8_t p[V6_CAMPAIGN_COLLECTION_BYTES];unsigned i;
    if(!out || !collected || n!=sizeof(p) || (collected->bits[12]&0xf0))return 0;
    /* Validate the shared prefix in private scratch, then publish only V4. */
    if(!progress_encode(p,V6_CAMPAIGN_STATE_BYTES,c,red,yellow,e,4))return 0;
    p[5]=4;p[7]=sizeof(p);
    for(i=0;i<V6_COLLECT_BYTES;++i)p[90+i]=collected->bits[i];
    for(i=103;i<108;++i)p[i]=0;
    put(p+108,crc(p,108));
    for(i=0;i<sizeof(p);++i)out[i]=p[i];
    return 1;
}
int v6_campaign_collection_decode(V6CheckpointSave *out,V6HallwayStory *red,
    V6StationStory *yellow,V6Exploration *explored,V6Collect *collected,
    const uint8_t *p,size_t n)
{
    V6CheckpointSave c;V6HallwayStory r;V6StationStory y;V6Exploration e;
    V6Collect bank;uint8_t previous[V6_CAMPAIGN_STATE_BYTES];unsigned i;
    if(!out || !red || !yellow || !explored || !collected || !p)return 0;
    for(i=0;i<V6_COLLECT_BYTES;++i)bank.bits[i]=0;
    if(n==V6_CAMPAIGN_COLLECTION_BYTES) {
        if(p[4] || p[5]!=4 || p[6] || p[7]!=n || (p[102]&0xf0)
           || get(p+108)!=crc(p,108))return 0;
        for(i=103;i<108;++i)if(p[i])return 0;
        for(i=0;i<90;++i)previous[i]=p[i];
        previous[5]=4;previous[7]=sizeof(previous);previous[90]=previous[91]=0;
        put(previous+92,crc(previous,92));
        if(!progress_decode(&c,&r,&y,&e,previous,sizeof(previous),4))return 0;
        for(i=0;i<V6_COLLECT_BYTES;++i)bank.bits[i]=p[90+i];
    } else if(!v6_campaign_progress_decode(&c,&r,&y,&e,p,n))return 0;
    *out=c;*red=r;*yellow=y;
    for(i=0;i<V6_EXPLORED_BYTES;++i)((volatile uint8_t *)explored->rooms)[i]=e.rooms[i];
    for(i=0;i<V6_COLLECT_BYTES;++i)((volatile uint8_t *)collected->bits)[i]=bank.bits[i];
    return 1;
}

static int hint_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *red,const V6StationStory *yellow,const V6Exploration *e,
    const V6Collect *collected,const V6CampaignHints *hints,unsigned version)
{
    uint8_t p[V6_CAMPAIGN_HINT_BYTES];unsigned i;
    if(!out || !collected || !hints || n!=sizeof(p) || (collected->bits[12]&0xf0) ||
       (hints->map_hint_seen!=0 && hints->map_hint_seen!=1))return 0;
    if(!progress_encode(p,V6_CAMPAIGN_STATE_BYTES,c,red,yellow,e,version))return 0;
    p[7]=sizeof(p);put(p+36,get(p+36)|((uint32_t)hints->map_hint_seen<<6));
    for(i=0;i<V6_COLLECT_BYTES;++i)p[90+i]=collected->bits[i];
    for(i=103;i<108;++i)p[i]=0;
    put(p+108,crc(p,108));for(i=0;i<sizeof(p);++i)out[i]=p[i];
    return 1;
}
static int hint_decode(V6CheckpointSave *out,V6HallwayStory *red,
    V6StationStory *yellow,V6Exploration *explored,V6Collect *collected,V6CampaignHints *hints,
    const uint8_t *p,size_t n,unsigned version)
{
    V6CheckpointSave c;V6HallwayStory r;V6StationStory y;V6Exploration e;V6Collect bank;
    V6CampaignHints h={0};uint8_t previous[V6_CAMPAIGN_STATE_BYTES];unsigned i;uint32_t flags;
    if(!out || !red || !yellow || !explored || !collected || !hints || !p)return 0;
    if(n==V6_CAMPAIGN_HINT_BYTES && p[5]==version) {
        if(p[4] || p[6] || p[7]!=n || (p[102]&0xf0) || get(p+108)!=crc(p,108))return 0;
        for(i=103;i<108;++i)if(p[i])return 0;
        flags=get(p+36);if(flags&~127U)return 0;h.map_hint_seen=(flags>>6)&1;
        for(i=0;i<90;++i)previous[i]=p[i];
        previous[7]=sizeof(previous);put(previous+36,flags&63U);
        previous[90]=previous[91]=0;put(previous+92,crc(previous,92));
        if(!progress_decode(&c,&r,&y,&e,previous,sizeof(previous),version))return 0;
        for(i=0;i<V6_COLLECT_BYTES;++i)bank.bits[i]=p[90+i];
    } else if(!v6_campaign_collection_decode(&c,&r,&y,&e,&bank,p,n))return 0;
    *out=c;*red=r;*yellow=y;*hints=h;
    for(i=0;i<V6_EXPLORED_BYTES;++i)((volatile uint8_t *)explored->rooms)[i]=e.rooms[i];
    for(i=0;i<V6_COLLECT_BYTES;++i)((volatile uint8_t *)collected->bits)[i]=bank.bits[i];
    return 1;
}

int v6_campaign_hint_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *r,const V6StationStory *y,const V6Exploration *e,
    const V6Collect *b,const V6CampaignHints *h)
{return hint_encode(out,n,c,r,y,e,b,h,5);}
int v6_campaign_hint_decode(V6CheckpointSave *c,V6HallwayStory *r,V6StationStory *y,
    V6Exploration *e,V6Collect *b,V6CampaignHints *h,const uint8_t *p,size_t n)
{return hint_decode(c,r,y,e,b,h,p,n,5);}
int v6_campaign_menu_prefix_encode(uint8_t *out,size_t n,const V6CheckpointSave *c,
    const V6HallwayStory *r,const V6StationStory *y,const V6Exploration *e,
    const V6Collect *b,const V6CampaignHints *h)
{return hint_encode(out,n,c,r,y,e,b,h,6);}
int v6_campaign_menu_prefix_decode(V6CheckpointSave *c,V6HallwayStory *r,V6StationStory *y,
    V6Exploration *e,V6Collect *b,V6CampaignHints *h,const uint8_t *p,size_t n)
{return p && n==V6_CAMPAIGN_HINT_BYTES && p[5]==6 && hint_decode(c,r,y,e,b,h,p,n,6);}
