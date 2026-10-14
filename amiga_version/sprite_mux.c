#include "sprite_mux.h"
static int plan_core(V6MuxPlan *out,const V6MuxActor *a,unsigned count,int reuse)
{
    V6MuxPlan *p=out;uint16_t i,j,order[14],prior[14],end[8]={0},hint=0;
    if(!out || !a || count>14)return 0;
    if(reuse && p->count==count && count){hint=1;
        for(i=0;i<count;++i){prior[i]=p->spans[i].actor;if(prior[i]>=count){hint=0;break;}}
    }
    p->count=0;for(i=0;i<8;++i)p->used[i]=0;
    for(i=0;i<count;++i){int16_t first,last,left,y=a[i].y;V6MuxSpan *span;
        left=a[i].x+a[i].crop;
        if(y>=216 || y+(int)a[i].height<=16 || left>=320 || left<=-16)continue;
        first=y<16?16-y:0;
        last=y+(int)a[i].height>216?216-y:a[i].height;
        j=p->count;span=&p->spans[j];
        span->actor=i;span->channel=0;span->first=first;span->last=last;span->left=128+left;
        span->start=52+y+first;span->stop=52+y+last;
        span->words=2+(last-first)*2;
        span->clip=a[i].width==16?0xffffU:(uint16_t)(0xffffU<<(16-a[i].width));
        if(left<0)span->clip&=(uint16_t)(0xffffU>>-left);
        if(left>304)span->clip&=(uint16_t)(0xffffU<<(left-304));
        order[p->count]=p->count;++p->count;
    }
    if(hint && p->count==count)for(i=0;i<count;++i)order[i]=prior[i];
    /* Sort small indices, rather than repeatedly copying DMA descriptors. */
    for(i=1;i<p->count;++i){uint16_t node=order[i];j=i;
        while(j && (p->spans[order[j-1]].start>p->spans[node].start ||
            (p->spans[order[j-1]].start==p->spans[node].start && order[j-1]>node))){order[j]=order[j-1];--j;}
        order[j]=node;
    }
    for(i=0;i<p->count;++i){uint16_t channel=8;V6MuxSpan *s=&p->spans[order[i]];
        for(j=0;j<8;++j)if(end[j]<=s->start && p->used[j]+s->words+2<=196){channel=j;break;}
        if(channel==8)return 0;
        s->channel=(uint16_t)channel;s->words=p->used[channel];
        p->used[channel]+=(uint16_t)(2+(s->last-s->first)*2);
        end[channel]=s->stop+2;
    }
    /* Reorder in place by permutation cycles. Owned native descriptors do
     * not need a second complete plan copy on every gameplay update. */
    for(i=0;i<p->count;++i)if(order[i]!=i){V6MuxSpan saved=p->spans[i];j=i;
        while(order[j]!=i){uint16_t from=order[j];p->spans[j]=p->spans[from];order[j]=j;j=from;}
        p->spans[j]=saved;order[j]=j;
    }
    return 1;
}
int v6_sprite_mux_plan(V6MuxPlan *out,const V6MuxActor *a,unsigned count)
{
    unsigned i;V6MuxPlan candidate;
    if(!out || !a || count>14)return 0;
    for(i=0;i<count;++i)if(!a[i].rows || !a[i].width || a[i].width>16 || !a[i].height || a[i].height>32 ||
        a[i].crop>16 || a[i].colour>0xfff)return 0;
    if(!plan_core(&candidate,a,count,0))return 0;
    *out=candidate;return 1;
}
int v6_sprite_mux_owned_plan(V6MuxPlan *out,const V6MuxActor *a,unsigned count)
{return plan_core(out,a,count,0);}
int v6_sprite_mux_owned_replan(V6MuxPlan *out,const V6MuxActor *a,unsigned count)
{return plan_core(out,a,count,1);}
void v6_sprite_mux_dma(uint16_t *const out[8],const V6MuxPlan *p,const V6MuxActor *a)
{
    unsigned i,j;
    for(i=0;i<8;++i)out[i][0]=out[i][1]=0;
    for(i=0;i<p->count;++i){const V6MuxSpan *s=&p->spans[i];const V6MuxActor *actor=&a[s->actor];
        uint16_t *d=out[s->channel]+s->words;
        *d++=(uint16_t)(((s->start&255)<<8)|(s->left>>1));
        *d++=(uint16_t)(((s->stop&255)<<8)|((s->start&256)>>6)|((s->stop&256)>>7)|(s->left&1));
        if(actor->crop==0)for(j=s->first;j<s->last;++j){uint16_t bits=(uint16_t)(actor->rows[j]>>16)&s->clip;
            *d++=bits;*d++=(s->channel&1)?bits:0;}
        else if(actor->crop==16)for(j=s->first;j<s->last;++j){uint16_t bits=(uint16_t)actor->rows[j]&s->clip;
            *d++=bits;*d++=(s->channel&1)?bits:0;}
        else {unsigned shift=16-actor->crop;
            for(j=s->first;j<s->last;++j){uint16_t bits=(uint16_t)(actor->rows[j]>>shift)&s->clip;
                *d++=bits;*d++=(s->channel&1)?bits:0;}}
        d[0]=d[1]=0;
    }
}
static void emit(uint16_t *out,unsigned *n,unsigned r,unsigned v)
{out[(*n)++]=(uint16_t)r;out[(*n)++]=(uint16_t)v;}
static void palette(uint16_t *out,unsigned *n,const V6MuxPlan *p,unsigned index,const V6MuxActor *a,unsigned *epoch)
{
    const V6MuxSpan *s=&p->spans[index];unsigned line=s->start-1;
    if(!index || p->spans[index-1].start!=s->start){
        if(line>=255 && !*epoch){emit(out,n,0xffdf,0xfffe);*epoch=256;}
        if(line!=255)emit(out,n,((line&255)<<8)|0xdf,0xfffe);
    }
    emit(out,n,0x1a2+s->channel*4,a[s->actor].colour);
}
static int overlay_valid(const V6MuxOverlay *o)
{
    return !o || (!((o->bitmap|o->blank)&1) && o->bitmap<=0xfffffc && o->blank<=0xfffffc &&
        o->start>=68 && o->stop>o->start && o->stop<=268 && o->stop-o->start<=32 && o->colour<=0xfff);
}
static void overlay_event(uint16_t *out,unsigned *n,const V6MuxOverlay *o,unsigned phase,unsigned *epoch)
{
    unsigned line=(phase?o->stop:o->start)-1,i;
    if(line>=255 && !*epoch){emit(out,n,0xffdf,0xfffe);*epoch=256;}
    /* Install the inert pointers/colours early; enable the extra planes last,
     * after the preceding line's fetches and before the next DDF start. */
    if(line!=255)emit(out,n,((line&255)<<8)|(phase?0xdf:0xd1),0xfffe);
    if(!phase){emit(out,n,0xec,o->blank>>16);emit(out,n,0xee,o->blank);
        emit(out,n,0xf0,o->bitmap>>16);emit(out,n,0xf2,o->bitmap);
        for(i=4;i<8;++i)emit(out,n,0x180+i*2,o->colour);}
    emit(out,n,0x100,phase?0x3600:0x5600);
}
static unsigned next_line(const V6MuxPlan *p,unsigned event,const V6MuxOverlay *o,unsigned phase)
{
    unsigned line=event<p->count?p->spans[event].start-1:512;
    if(o && phase<2){unsigned other=(phase?o->stop:o->start)-1;if(other<=line)line=other;}
    return line;
}
static void next_event(uint16_t *out,unsigned *n,const V6MuxPlan *p,const V6MuxActor *a,
    unsigned *event,const V6MuxOverlay *o,unsigned *phase,unsigned *epoch)
{
    if(o && *phase<2 && (*event==p->count ||
        (unsigned)(*phase?o->stop:o->start)<=p->spans[*event].start))
        overlay_event(out,n,o,(*phase)++,epoch);
    else palette(out,n,p,(*event)++,a,epoch);
}
static unsigned copper(uint16_t *out,const uint16_t *game,unsigned words,
    const V6MuxPlan *p,const V6MuxActor *a,int validate,const V6MuxOverlay *o)
{
    unsigned i,n=0,event=0,epoch=0,game_epoch=0,end=0,phase=0;
    if(!out || !game || out==game || !p || !a || words<2 || words>512 || (words&1) || p->count>14 || words+p->count*4+(o?30:2)>512 || !overlay_valid(o))return 0;
    if(validate)for(i=0;i<words;i+=2){unsigned r=game[i],v=game[i+1];
        if(r==0xffff){if(v!=0xfffe)return 0;end=1;break;}
        if((r&1)?v!=0xfffe:r>0x1fe)return 0;
    }
    else end=game[words-2]==0xffff && game[words-1]==0xfffe;
    if(!end)return 0;
    for(i=0;i<words;i+=2){unsigned r=game[i],v=game[i+1],line;
        if(r==0xffff)break;
        if(r&1){
            if(r==0xffdf){line=255;game_epoch=256;}else line=game_epoch+(r>>8);
            while(next_line(p,event,o,phase)<=line)next_event(out,&n,p,a,&event,o,&phase,&epoch);
            if(r==0xffdf){if(epoch)continue;epoch=256;}
        }
        emit(out,&n,r,v);
    }
    while(next_line(p,event,o,phase)<512)next_event(out,&n,p,a,&event,o,&phase,&epoch);
    emit(out,&n,0xffff,0xfffe);return n;
}
unsigned v6_sprite_mux_copper(uint16_t *out,const uint16_t *game,unsigned words,
    const V6MuxPlan *p,const V6MuxActor *a)
{return copper(out,game,words,p,a,1,0);}
unsigned v6_sprite_mux_rendered_copper(uint16_t *out,const uint16_t *game,unsigned words,
    const V6MuxPlan *p,const V6MuxActor *a)
{return copper(out,game,words,p,a,0,0);}

unsigned v6_sprite_mux_append_palette(uint16_t *out,unsigned words,const V6MuxPlan *p,const V6MuxActor *a)
{
    unsigned n=words-2,i,epoch=0;
    if(!out || !p || !a || words<2 || words+p->count*4+2>512)return 0;
    for(i=0;i<p->count;++i)palette(out,&n,p,i,a,&epoch);
    emit(out,&n,0xffff,0xfffe);return n;
}

unsigned v6_sprite_mux_overlay_copper(uint16_t *out,const uint16_t *game,unsigned words,
    const V6MuxPlan *p,const V6MuxActor *a,const V6MuxOverlay *o)
{return copper(out,game,words,p,a,0,o);}
unsigned v6_sprite_mux_append_overlay(uint16_t *out,unsigned words,const V6MuxPlan *p,
    const V6MuxActor *a,const V6MuxOverlay *o)
{
    unsigned n,event=0,epoch=0;
    if(!out || !p || !a || words<2 || words+p->count*4+(o?30:2)>512 || !overlay_valid(o))return 0;
    n=words-2;
    /* The static prefix precedes every actor. Merge the two overlay events
     * directly; avoid rediscovering the next event twice for each sprite. */
    if(o){
        while(event<p->count && p->spans[event].start<o->start)
            palette(out,&n,p,event++,a,&epoch);
        overlay_event(out,&n,o,0,&epoch);
        while(event<p->count && p->spans[event].start<o->stop)
            palette(out,&n,p,event++,a,&epoch);
        overlay_event(out,&n,o,1,&epoch);
    }
    while(event<p->count)palette(out,&n,p,event++,a,&epoch);
    emit(out,&n,0xffff,0xfffe);return n;
}
/* Rectangle-only channel pressure over the optional actor's DMA band. */
int v6_sprite_mux_pressure(const V6MuxActor *a,unsigned count,const V6MuxActor *optional)
{
    unsigned i,b0=0,b1=0,b2=0,tail0=0,tail1=0;int start,end;
    if(!a || !optional || count>14)return 1;
    if(optional->x+(int)optional->crop>=320 || optional->x+(int)optional->crop<=-16)return 0;
    start=optional->y<16?16:optional->y;end=optional->y+(int)optional->height;
    if(end>216)end=216;
    if(start>=end)return 0;
    end+=2;
    for(i=0;i<count;++i){int x=a[i].x+(int)a[i].crop,first,last,f,l;unsigned weight=1,mask,carry;
        if(x>=320 || x<=-16 || a[i].y>=216 || a[i].y+(int)a[i].height<=16)continue;
        first=a[i].y<16?16:a[i].y;last=a[i].y+(int)a[i].height;
        if(last>216)last=216;
        last+=2;
        if(i+1<count && a[i+1].y==a[i].y && a[i+1].height==a[i].height){
            int nx=a[i+1].x+(int)a[i+1].crop;
            if(nx<320 && nx>-16){weight=2;++i;}
        }
        if(end-start>32 && first<=start+32 && last>start+32){tail0+=weight;if(tail0>=8)return 1;}
        if(end-start>33 && first<=start+33 && last>start+33){tail1+=weight;if(tail1>=8)return 1;}
        f=first-start;l=last-start;if(f<0)f=0;if(l>end-start)l=end-start;if(l>32)l=32;
        if(f>=l || f>=32 || l<=0)continue;
        mask=l-f==32?0xffffffffU:((1U<<(l-f))-1)<<f;
        if(weight==1){carry=b0&mask;b0^=mask;mask=carry;}
        carry=b1&mask;b1^=mask;
        if(b2&carry)return 1;
        b2^=carry;
    }
    return 0;
}
/* Retain a valid previous channel assignment while actors move. */
int v6_sprite_mux_update(V6MuxPlan *out,const V6MuxActor *a,unsigned count)
{
    V6MuxPlan p;uint16_t end[8]={0};unsigned i,j,visible=0;
    if(!out || !a || count>14 || !out->count || out->count>14)return 0;
    for(i=0;i<count;++i){int x=a[i].x+(int)a[i].crop;
        if(x<320 && x>-16 && a[i].y<216 && a[i].y+(int)a[i].height>16)++visible;}
    if(visible!=out->count)return 0;
    p.count=out->count;for(i=0;i<8;++i)p.used[i]=0;
    for(i=0;i<p.count;++i){V6MuxSpan *s=&p.spans[i];const V6MuxActor *actor;int x,first,last;
        *s=out->spans[i];if(s->actor>=count || s->channel>=8)return 0;
        actor=&a[s->actor];x=actor->x+(int)actor->crop;
        first=actor->y<16?16-actor->y:0;last=actor->y+(int)actor->height>216?216-actor->y:(int)actor->height;
        if(first>=last || x>=320 || x<=-16)return 0;
        s->first=first;s->last=last;s->left=128+x;s->start=52+actor->y+first;s->stop=52+actor->y+last;
        s->clip=(uint16_t)(0xffffU<<(16-actor->width));
        if(x<0)s->clip&=(uint16_t)(0xffffU>>-x);
        if(x>304)s->clip&=(uint16_t)(0xffffU<<(x-304));
    }
    for(i=1;i<p.count;++i){V6MuxSpan node=p.spans[i];j=i;
        while(j && p.spans[j-1].start>node.start){p.spans[j]=p.spans[j-1];--j;}
        p.spans[j]=node;
    }
    for(i=0;i<p.count;++i){V6MuxSpan *s=&p.spans[i];unsigned words=2+(s->last-s->first)*2,channel=s->channel;
        if(end[channel]>s->start || p.used[channel]+words+2>196)return 0;
        s->words=p.used[channel];p.used[channel]+=words;end[channel]=s->stop+2;
    }
    for(i=0;i<p.count;++i)out->spans[i]=p.spans[i];
    for(i=0;i<8;++i)out->used[i]=p.used[i];
    out->count=p.count;return 1;
}
