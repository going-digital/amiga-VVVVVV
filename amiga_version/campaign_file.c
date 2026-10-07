#include "campaign_file.h"
static unsigned fold(unsigned c){return c>='A' && c<='Z'?c+'a'-'A':c;}
static int same(const char *a,const char *b)
{ while(*a && fold((unsigned char)*a)==fold((unsigned char)*b)){++a;++b;}return fold((unsigned char)*a)==fold((unsigned char)*b); }
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
static int paths(const V6CampaignIO *io,const char *a,const char *b,const char *c)
{
    return io && io->exists && io->open && io->read && io->write && io->close && io->rename && io->remove
        && a && *a && b && *b && c && *c && !same(a,b) && !same(a,c) && !same(b,c);
}
int v6_campaign_recover(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,
                        V6CheckpointSave *out,V6HallwayStory *story)
{
    V6CheckpointSave c,b;V6HallwayStory s,bs;int a,t,k,result;
    if(!out || !story || !paths(io,name,temp,backup))return V6_SAVE_INVALID;
    a=io->exists(name);t=io->exists(temp);k=io->exists(backup);
    if(a<0 || t<0 || k<0)return V6_SAVE_IO;
    if(!a && !k)return t?V6_SAVE_EXISTS:V6_SAVE_IO;
    result=v6_campaign_read(io,a?name:backup,&c,&s);
    if(result)return result;
    if(a && k) { result=v6_campaign_read(io,backup,&b,&bs);if(result)return result; }
    if(!a) {
        if(!io->rename(backup,name))return V6_SAVE_IO;
        result=v6_campaign_read(io,name,&c,&s);if(result)return result;
        k=0;
    }
    if(t && !io->remove(temp))return V6_SAVE_IO;
    if(k && !io->remove(backup))return V6_SAVE_IO;
    *out=c;*story=s;return V6_SAVE_OK;
}
int v6_campaign_replace(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,
                        const V6CheckpointSave *c,const V6HallwayStory *s)
{
    uint8_t bytes[V6_CAMPAIGN_SAVE_BYTES],checkbytes[V6_CAMPAIGN_SAVE_BYTES];
    V6CheckpointSave check;V6HallwayStory story;intptr_t h;unsigned i;
    int a,t,k,result,wrote,closed;
    if(!paths(io,name,temp,backup) || !v6_campaign_encode(bytes,sizeof(bytes),c,s))return V6_SAVE_INVALID;
    a=io->exists(name);t=io->exists(temp);k=io->exists(backup);
    if(a<0 || t<0 || k<0)return V6_SAVE_IO;
    if(!a && !t && !k)return v6_campaign_write_new(io,name,temp,c,s);
    result=v6_campaign_recover(io,name,temp,backup,&check,&story);
    if(result)return result;
    h=io->open(temp,1);if(!h)return V6_SAVE_IO;
    wrote=io->write(h,bytes,sizeof(bytes));closed=io->close(h);
    if(wrote!=(int)sizeof(bytes) || !closed){io->remove(temp);return V6_SAVE_IO;}
    result=v6_campaign_read(io,temp,&check,&story);
    if(result){io->remove(temp);return result;}
    if(!v6_campaign_encode(checkbytes,sizeof(checkbytes),&check,&story)){io->remove(temp);return V6_SAVE_CORRUPT;}
    for(i=0;i<sizeof(bytes);++i)if(bytes[i]!=checkbytes[i]){io->remove(temp);return V6_SAVE_CORRUPT;}
    if(!io->rename(name,backup))return V6_SAVE_IO;
    /* A failed promotion leaves the old record in backup for startup recovery. */
    if(!io->rename(temp,name))return V6_SAVE_IO;
    result=v6_campaign_read(io,name,&check,&story);if(result)return result;
    if(!v6_campaign_encode(checkbytes,sizeof(checkbytes),&check,&story))return V6_SAVE_CORRUPT;
    for(i=0;i<sizeof(bytes);++i)if(bytes[i]!=checkbytes[i])return V6_SAVE_CORRUPT;
    if(!io->remove(backup))return V6_SAVE_IO;
    return V6_SAVE_OK;
}
