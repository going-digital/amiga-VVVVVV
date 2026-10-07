#include <proto/dos.h>
#include <dos/dos.h>
#include "campaign_dos.h"
static int exists(const char *p)
{
    BPTR lock=Lock((CONST_STRPTR)p,ACCESS_READ);
    if(lock){UnLock(lock);return 1;}
    return IoErr()==ERROR_OBJECT_NOT_FOUND?0:-1;
}
static intptr_t open_file(const char *p,int write)
{ return (intptr_t)Open((CONST_STRPTR)p,write?MODE_NEWFILE:MODE_OLDFILE); }
static int read_file(intptr_t h,void *p,unsigned n){return (int)Read((BPTR)h,p,n);}
static int write_file(intptr_t h,const void *p,unsigned n){return (int)Write((BPTR)h,(APTR)p,n);}
static int close_file(intptr_t h){return Close((BPTR)h)!=0;}
static int rename_file(const char *a,const char *b){return Rename((CONST_STRPTR)a,(CONST_STRPTR)b)!=0;}
static int remove_file(const char *p){return DeleteFile((CONST_STRPTR)p)!=0;}
const V6CampaignIO v6_campaign_dos={exists,open_file,read_file,write_file,close_file,rename_file,remove_file};
