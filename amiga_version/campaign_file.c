#include "campaign_file.h"
static unsigned fold(unsigned c){return c>='A' && c<='Z'?c+'a'-'A':c;}
static int same(const char *a,const char *b)
{ while(*a && fold((unsigned char)*a)==fold((unsigned char)*b)){++a;++b;}return fold((unsigned char)*a)==fold((unsigned char)*b); }
static int encode_record(uint8_t *p,unsigned n,const V6CheckpointSave *c,
    const V6HallwayStory *s,const V6Exploration *e)
{ return e?v6_campaign_state_encode(p,n,c,s,e):v6_campaign_encode(p,n,c,s); }
static int read_record(const V6CampaignIO *io,const char *name,V6CheckpointSave *c,V6HallwayStory *s,V6Exploration *e)
{
    uint8_t bytes[V6_CAMPAIGN_STATE_BYTES],extra;unsigned size=e?V6_CAMPAIGN_STATE_BYTES:V6_CAMPAIGN_SAVE_BYTES;intptr_t h;int got,tail,closed;
    if(!io || !io->open || !io->read || !io->close || !name || !*name || !c || !s)return V6_SAVE_INVALID;
    h=io->open(name,0);if(!h)return V6_SAVE_IO;
    got=io->read(h,bytes,size);tail=(got==(int)size || (e && got==V6_CAMPAIGN_SAVE_BYTES))?io->read(h,&extra,1):-1;
    closed=io->close(h);
    if(!closed || got<0 || ((got==(int)size || (e && got==V6_CAMPAIGN_SAVE_BYTES)) && tail<0))return V6_SAVE_IO;
    if(tail!=0 || !(e?v6_campaign_state_decode(c,s,e,bytes,(size_t)got):v6_campaign_decode(c,s,bytes,(size_t)got)))return V6_SAVE_CORRUPT;
    return V6_SAVE_OK;
}
static int write_new(const V6CampaignIO *io,const char *name,const char *temp,const V6CheckpointSave *c,const V6HallwayStory *s,const V6Exploration *e)
{
    uint8_t bytes[V6_CAMPAIGN_STATE_BYTES];unsigned size=e?V6_CAMPAIGN_STATE_BYTES:V6_CAMPAIGN_SAVE_BYTES;V6CheckpointSave check;V6HallwayStory story;V6Exploration map;
    intptr_t h;int a,b,wrote,closed,result;
    if(!io || !io->exists || !io->open || !io->read || !io->write || !io->close || !io->rename || !io->remove
       || !name || !*name || !temp || !*temp || same(name,temp)
       || !encode_record(bytes,size,c,s,e))return V6_SAVE_INVALID;
    a=io->exists(name);b=io->exists(temp);
    if(a<0 || b<0)return V6_SAVE_IO;
    if(a || b)return V6_SAVE_EXISTS;
    h=io->open(temp,1);if(!h)return V6_SAVE_IO;
    wrote=io->write(h,bytes,size);closed=io->close(h);
    if(wrote!=(int)size || !closed){io->remove(temp);return V6_SAVE_IO;}
    result=read_record(io,temp,&check,&story,e?&map:0);
    if(result!=V6_SAVE_OK){io->remove(temp);return result;}
    /* Require exact bytes, not just a second valid but altered record. */
    { uint8_t verified[V6_CAMPAIGN_STATE_BYTES];unsigned i;
      if(!encode_record(verified,size,&check,&story,e?&map:0)){io->remove(temp);return V6_SAVE_CORRUPT;}
      for(i=0;i<size;++i)if(bytes[i]!=verified[i]){io->remove(temp);return V6_SAVE_CORRUPT;}
    }
    if(!io->rename(temp,name)){io->remove(temp);return V6_SAVE_IO;}
    return V6_SAVE_OK;
}
static int paths(const V6CampaignIO *io,const char *a,const char *b,const char *c)
{
    return io && io->exists && io->open && io->read && io->write && io->close && io->rename && io->remove
        && a && *a && b && *b && c && *c && !same(a,b) && !same(a,c) && !same(b,c);
}
static int recover(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,
                        V6CheckpointSave *out,V6HallwayStory *story,V6Exploration *e)
{
    V6CheckpointSave c,b;V6HallwayStory s,bs;V6Exploration map,bmap;int a,t,k,result;
    if(!out || !story || !paths(io,name,temp,backup))return V6_SAVE_INVALID;
    a=io->exists(name);t=io->exists(temp);k=io->exists(backup);
    if(a<0 || t<0 || k<0)return V6_SAVE_IO;
    if(!a && !k)return t?V6_SAVE_EXISTS:V6_SAVE_IO;
    result=read_record(io,a?name:backup,&c,&s,e?&map:0);
    if(result)return result;
    if(a && k) { result=read_record(io,backup,&b,&bs,e?&bmap:0);if(result)return result; }
    if(!a) {
        if(!io->rename(backup,name))return V6_SAVE_IO;
        result=read_record(io,name,&c,&s,e?&map:0);if(result)return result;
        k=0;
    }
    if(t && !io->remove(temp))return V6_SAVE_IO;
    if(k && !io->remove(backup))return V6_SAVE_IO;
    *out=c;*story=s;
    if(e) {unsigned i;for(i=0;i<V6_EXPLORED_BYTES;++i)((volatile uint8_t *)e->rooms)[i]=map.rooms[i];}
    return V6_SAVE_OK;
}
static int replace(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,
                        const V6CheckpointSave *c,const V6HallwayStory *s,const V6Exploration *e)
{
    uint8_t bytes[V6_CAMPAIGN_STATE_BYTES],checkbytes[V6_CAMPAIGN_STATE_BYTES];
    unsigned size=e?V6_CAMPAIGN_STATE_BYTES:V6_CAMPAIGN_SAVE_BYTES;V6Exploration map;
    V6CheckpointSave check;V6HallwayStory story;intptr_t h;unsigned i;
    int a,t,k,result,wrote,closed;
    if(!paths(io,name,temp,backup) || !encode_record(bytes,size,c,s,e))return V6_SAVE_INVALID;
    a=io->exists(name);t=io->exists(temp);k=io->exists(backup);
    if(a<0 || t<0 || k<0)return V6_SAVE_IO;
    if(!a && !t && !k)return write_new(io,name,temp,c,s,e);
    result=recover(io,name,temp,backup,&check,&story,e?&map:0);
    if(result)return result;
    h=io->open(temp,1);if(!h)return V6_SAVE_IO;
    wrote=io->write(h,bytes,size);closed=io->close(h);
    if(wrote!=(int)size || !closed){io->remove(temp);return V6_SAVE_IO;}
    result=read_record(io,temp,&check,&story,e?&map:0);
    if(result){io->remove(temp);return result;}
    if(!encode_record(checkbytes,size,&check,&story,e?&map:0)){io->remove(temp);return V6_SAVE_CORRUPT;}
    for(i=0;i<size;++i)if(bytes[i]!=checkbytes[i]){io->remove(temp);return V6_SAVE_CORRUPT;}
    if(!io->rename(name,backup))return V6_SAVE_IO;
    /* A failed promotion leaves the old record in backup for startup recovery. */
    if(!io->rename(temp,name))return V6_SAVE_IO;
    result=read_record(io,name,&check,&story,e?&map:0);if(result)return result;
    if(!encode_record(checkbytes,size,&check,&story,e?&map:0))return V6_SAVE_CORRUPT;
    for(i=0;i<size;++i)if(bytes[i]!=checkbytes[i])return V6_SAVE_CORRUPT;
    if(!io->remove(backup))return V6_SAVE_IO;
    return V6_SAVE_OK;
}

int v6_campaign_read(const V6CampaignIO *io,const char *name,V6CheckpointSave *c,V6HallwayStory *s)
{ return read_record(io,name,c,s,0); }
int v6_campaign_write_new(const V6CampaignIO *io,const char *name,const char *temp,const V6CheckpointSave *c,const V6HallwayStory *s)
{ return write_new(io,name,temp,c,s,0); }
int v6_campaign_recover(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,V6CheckpointSave *c,V6HallwayStory *s)
{ return recover(io,name,temp,backup,c,s,0); }
int v6_campaign_replace(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,const V6CheckpointSave *c,const V6HallwayStory *s)
{ return replace(io,name,temp,backup,c,s,0); }

int v6_campaign_state_read(const V6CampaignIO *io,const char *name,V6CheckpointSave *c,V6HallwayStory *s,V6Exploration *e)
{ if(!e)return V6_SAVE_INVALID;return read_record(io,name,c,s,e); }
int v6_campaign_state_write_new(const V6CampaignIO *io,const char *name,const char *temp,const V6CheckpointSave *c,const V6HallwayStory *s,const V6Exploration *e)
{ if(!e)return V6_SAVE_INVALID;return write_new(io,name,temp,c,s,e); }
int v6_campaign_state_recover(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,V6CheckpointSave *c,V6HallwayStory *s,V6Exploration *e)
{ if(!e)return V6_SAVE_INVALID;return recover(io,name,temp,backup,c,s,e); }
int v6_campaign_state_replace(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,const V6CheckpointSave *c,const V6HallwayStory *s,const V6Exploration *e)
{ if(!e)return V6_SAVE_INVALID;return replace(io,name,temp,backup,c,s,e); }
