#include "campaign_menu.h"
static void copy(void *out,const void *in,unsigned n)
{volatile uint8_t *d=out;const volatile uint8_t *s=in;while(n--)*d++=*s++;}
static unsigned fold(unsigned c){return c>='A' && c<='Z'?c+'a'-'A':c;}
static int same(const char *a,const char *b)
{while(*a && fold((unsigned char)*a)==fold((unsigned char)*b)){++a;++b;}return fold((unsigned char)*a)==fold((unsigned char)*b);}
static int paths(const V6CampaignIO *io,const char *a,const char *b,const char *c)
{return io && io->exists && io->open && io->read && io->write && io->close && io->rename && io->remove && a && *a && b && *b && c && *c && !same(a,b) && !same(a,c) && !same(b,c);}
int v6_campaign_menu_read(const V6CampaignIO *io,const char *name,V6MenuRecord *out)
{
    uint8_t bytes[V6_CAMPAIGN_MENU_BYTES],extra;intptr_t h;int got,tail,closed;
    if(!io || !io->open || !io->read || !io->close || !name || !*name || !out)return V6_SAVE_INVALID;
    h=io->open(name,0);if(!h)return V6_SAVE_IO;
    got=io->read(h,bytes,sizeof(bytes));tail=(got==44 || got==96 || got==112 || got==144)?io->read(h,&extra,1):-1;
    closed=io->close(h);
    if(!closed || got<0 || ((got==44 || got==96 || got==112 || got==144) && tail<0))return V6_SAVE_IO;
    if(tail!=0 || !v6_campaign_menu_decode(out,bytes,(size_t)got))return V6_SAVE_CORRUPT;
    return V6_SAVE_OK;
}
int v6_campaign_menu_recover(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,V6MenuRecord *out)
{
    V6MenuRecord r,previous;int a,t,k,result;
    if(!out || !paths(io,name,temp,backup))return V6_SAVE_INVALID;
    a=io->exists(name);t=io->exists(temp);k=io->exists(backup);
    if(a<0 || t<0 || k<0)return V6_SAVE_IO;
    if(!a && !k)return t?V6_SAVE_EXISTS:V6_SAVE_IO;
    result=v6_campaign_menu_read(io,a?name:backup,&r);if(result)return result;
    if(a && k){result=v6_campaign_menu_read(io,backup,&previous);if(result)return result;}
    if(!a){if(!io->rename(backup,name))return V6_SAVE_IO;result=v6_campaign_menu_read(io,name,&r);if(result)return result;k=0;}
    if(t && !io->remove(temp))return V6_SAVE_IO;
    if(k && !io->remove(backup))return V6_SAVE_IO;
    copy(out,&r,sizeof(r));return V6_SAVE_OK;
}
static int verify(const V6CampaignIO *io,const char *name,const uint8_t expected[V6_CAMPAIGN_MENU_BYTES])
{
    V6MenuRecord r;uint8_t bytes[V6_CAMPAIGN_MENU_BYTES];unsigned i;int result;
    result=v6_campaign_menu_read(io,name,&r);if(result)return result;
    if(!v6_campaign_menu_encode(bytes,sizeof(bytes),&r))return V6_SAVE_CORRUPT;
    for(i=0;i<sizeof(bytes);++i)if(bytes[i]!=expected[i])return V6_SAVE_CORRUPT;
    return V6_SAVE_OK;
}
int v6_campaign_menu_replace(const V6CampaignIO *io,const char *name,const char *temp,const char *backup,const V6MenuRecord *r)
{
    uint8_t bytes[V6_CAMPAIGN_MENU_BYTES];V6MenuRecord previous;intptr_t h;int a,t,k,wrote,closed,result;
    if(!paths(io,name,temp,backup) || !v6_campaign_menu_encode(bytes,sizeof(bytes),r))return V6_SAVE_INVALID;
    a=io->exists(name);t=io->exists(temp);k=io->exists(backup);
    if(a<0 || t<0 || k<0)return V6_SAVE_IO;
    if(a || t || k){result=v6_campaign_menu_recover(io,name,temp,backup,&previous);if(result)return result;a=1;}
    h=io->open(temp,1);if(!h)return V6_SAVE_IO;
    wrote=io->write(h,bytes,sizeof(bytes));closed=io->close(h);
    if(wrote!=(int)sizeof(bytes) || !closed){io->remove(temp);return V6_SAVE_IO;}
    result=verify(io,temp,bytes);if(result){io->remove(temp);return result;}
    if(a && !io->rename(name,backup))return V6_SAVE_IO;
    if(!io->rename(temp,name)){if(!a)io->remove(temp);return V6_SAVE_IO;}
    result=verify(io,name,bytes);if(result)return result;
    if(a && !io->remove(backup))return V6_SAVE_IO;
    return V6_SAVE_OK;
}
