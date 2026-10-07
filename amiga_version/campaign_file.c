#include "campaign_file.h"
static int same(const char *a,const char *b)
{ while(*a && *a==*b){++a;++b;}return *a==*b; }
int v6_campaign_read(const V6CampaignIO *io,const char *name,V6CheckpointSave *c,V6HallwayStory *s)
{
    uint8_t bytes[V6_CAMPAIGN_SAVE_BYTES],extra;intptr_t h;int got,tail,closed;
    if(!io || !io->open || !io->read || !io->close || !name || !*name || !c || !s)return V6_SAVE_INVALID;
    h=io->open(name,0);if(!h)return V6_SAVE_IO;
    got=io->read(h,bytes,sizeof(bytes));tail=got==(int)sizeof(bytes)?io->read(h,&extra,1):-1;
    closed=io->close(h);
    if(!closed || got<0 || (got==(int)sizeof(bytes) && tail<0))return V6_SAVE_IO;
    if(got!=(int)sizeof(bytes) || tail!=0 || !v6_campaign_decode(c,s,bytes,sizeof(bytes)))return V6_SAVE_CORRUPT;
    return V6_SAVE_OK;
}
int v6_campaign_write_new(const V6CampaignIO *io,const char *name,const char *temp,const V6CheckpointSave *c,const V6HallwayStory *s)
{
    uint8_t bytes[V6_CAMPAIGN_SAVE_BYTES];V6CheckpointSave check;V6HallwayStory story;
    intptr_t h;int a,b,wrote,closed,result;
    if(!io || !io->exists || !io->open || !io->read || !io->write || !io->close || !io->rename || !io->remove
       || !name || !*name || !temp || !*temp || same(name,temp)
       || !v6_campaign_encode(bytes,sizeof(bytes),c,s))return V6_SAVE_INVALID;
    a=io->exists(name);b=io->exists(temp);
    if(a<0 || b<0)return V6_SAVE_IO;
    if(a || b)return V6_SAVE_EXISTS;
    h=io->open(temp,1);if(!h)return V6_SAVE_IO;
    wrote=io->write(h,bytes,sizeof(bytes));closed=io->close(h);
    if(wrote!=(int)sizeof(bytes) || !closed){io->remove(temp);return V6_SAVE_IO;}
    result=v6_campaign_read(io,temp,&check,&story);
    if(result!=V6_SAVE_OK){io->remove(temp);return result;}
    /* Require exact bytes, not just a second valid but altered record. */
    { uint8_t verified[V6_CAMPAIGN_SAVE_BYTES];unsigned i;
      if(!v6_campaign_encode(verified,sizeof(verified),&check,&story)){io->remove(temp);return V6_SAVE_CORRUPT;}
      for(i=0;i<sizeof(bytes);++i)if(bytes[i]!=verified[i]){io->remove(temp);return V6_SAVE_CORRUPT;}
    }
    if(!io->rename(temp,name)){io->remove(temp);return V6_SAVE_IO;}
    return V6_SAVE_OK;
}
