#include <proto/dos.h>
#include <proto/exec.h>
#include <exec/memory.h>
#include <dos/dosextens.h>
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

static volatile struct { ULONG magic,version,res1,res2,received; } flush_diag={0x56364653,1,0,0,0};
int v6_campaign_dos_flush(const char *device)
{
    struct MsgPort *handler,*reply;struct StandardPacket *packet;BYTE signal;int result;
    if(!device || !*device)return 0;
    handler=DeviceProc((CONST_STRPTR)device);if(!handler)return 0;
    signal=AllocSignal(-1);if(signal<0)return 0;
    reply=AllocMem(sizeof(*reply),MEMF_PUBLIC|MEMF_CLEAR);
    packet=AllocMem(sizeof(*packet),MEMF_PUBLIC|MEMF_CLEAR);
    if(!reply || !packet) {
        if(reply)FreeMem(reply,sizeof(*reply));
        if(packet)FreeMem(packet,sizeof(*packet));
        FreeSignal(signal);return 0;
    }
    reply->mp_Node.ln_Type=NT_MSGPORT;reply->mp_Flags=PA_SIGNAL;
    reply->mp_SigBit=signal;reply->mp_SigTask=FindTask(0);
    reply->mp_MsgList.lh_Head=(struct Node *)&reply->mp_MsgList.lh_Tail;
    reply->mp_MsgList.lh_TailPred=(struct Node *)&reply->mp_MsgList.lh_Head;
    packet->sp_Msg.mn_Node.ln_Type=NT_MESSAGE;
    packet->sp_Msg.mn_Node.ln_Name=(char *)&packet->sp_Pkt;
    packet->sp_Msg.mn_ReplyPort=reply;packet->sp_Msg.mn_Length=sizeof(*packet);
    packet->sp_Pkt.dp_Link=&packet->sp_Msg;packet->sp_Pkt.dp_Port=reply;
    packet->sp_Pkt.dp_Type=ACTION_FLUSH;
    PutMsg(handler,&packet->sp_Msg);WaitPort(reply);
    flush_diag.received=GetMsg(reply)==&packet->sp_Msg;
    flush_diag.res1=packet->sp_Pkt.dp_Res1;flush_diag.res2=packet->sp_Pkt.dp_Res2;
    /* Kickstart 1.3 OFS acknowledges ACTION_FLUSH with Res1=0, Res2=0;
     * the received reply and secondary error determine completion. */
    result=flush_diag.received && packet->sp_Pkt.dp_Res2==0;
    FreeMem(packet,sizeof(*packet));FreeMem(reply,sizeof(*reply));FreeSignal(signal);
    return result;
}
