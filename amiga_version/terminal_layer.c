#include "terminal_layer.h"
typedef uint32_t Long __attribute__((may_alias));
static uint32_t pixel_long(uint32_t v)
{
#if __BYTE_ORDER__ == __ORDER_LITTLE_ENDIAN__
    return __builtin_bswap32(v);
#else
    return v;
#endif
}
int v6_terminal_layer_decode(uint8_t row[40],const uint8_t *in,unsigned size)
{
    unsigned at=0,n=0;
    while(at<size){unsigned token=in[at++],count=(token&127)+1;
        if(count>40-n)return 0;
        if(token&128){uint8_t value;if(at==size)return 0;value=in[at++];while(count--)row[n++]=value;}
        else {if(count>size-at)return 0;while(count--)row[n++]=in[at++];}
    }
    return n==40;
}
unsigned v6_terminal_layer_occlude(uint16_t *dma)
{
    unsigned first=(dma[0]>>8)|((dma[1]&4)<<6),last=(dma[1]>>8)|((dma[1]&2)<<7),i,count=0;
    static const unsigned bounds[2][2]={{112,136},{138,207}};
    for(i=0;i<2;++i){unsigned y=first>bounds[i][0]?first:bounds[i][0],end=last<bounds[i][1]?last:bounds[i][1];
        count+=end>y?end-y:0;
        for(;y<end;++y){unsigned at=2+(y-first)*2;dma[at]=dma[at+1]=0;}}
    return count;
}
static uint32_t bar_mask(unsigned position,unsigned x,int bottom)
{
    int n=bottom?(int)x*32+32-(360-(int)position):(int)position-(int)x*32;
    if(n<=0)return 0;
    if(n>=32)return 0xffffffffUL;
    return bottom?0xffffffffUL>>(32-n):0xffffffffUL<<(32-n);
}
void v6_terminal_layer_bars(uint8_t *bitmap,const uint8_t *world,unsigned position,unsigned previous)
{
    unsigned x,y,b;
    for(b=0;b<2;++b)for(x=0;x<10;++x){uint32_t mask=pixel_long(bar_mask(position,x,b));
        if(mask==pixel_long(bar_mask(previous,x,b)))continue;
        if(!mask){
            for(y=0;y<16;++y){unsigned at=((b?224:0)+y)*10+x;
                ((Long *)bitmap)[at]=((const Long *)world)[at];
                ((Long *)bitmap)[2400+at]=((const Long *)world)[2560+at];((Long *)bitmap)[4800+at]=0;}
            continue;
        }
        if(mask==0xffffffffUL){
            for(y=0;y<16;++y){unsigned at=((b?224:0)+y)*10+x;
                ((Long *)bitmap)[at]=0;((Long *)bitmap)[2400+at]=((Long *)bitmap)[4800+at]=0xffffffffUL;}
            continue;
        }
        for(y=0;y<16;++y){unsigned at=((b?224:0)+y)*10+x;
            ((Long *)bitmap)[at]=((const Long *)world)[at]&~mask;
            ((Long *)bitmap)[2400+at]=(((const Long *)world)[2560+at]&~mask)|mask;
            ((Long *)bitmap)[4800+at]=mask;}
    }
}
static uint16_t *pair(uint16_t *p,unsigned r,unsigned v){*p++=r;*p++=v;return p;}
static uint16_t *pointer(uint16_t *p,unsigned r,uint32_t a)
{*p++=r;*p++=a>>16;*p++=r+2;*p++=a;return p;}
static uint16_t *foreground(uint16_t *p,uint32_t a,unsigned stride,int high)
{p=pointer(p,0xe0,a);p=pointer(p,0xe8,a+stride);return high?pointer(p,0xf0,a+stride*2):p;}
static unsigned shade(unsigned value){unsigned n=0;value+=8;while(value>=17){value-=17;++n;}return n*0x111;}
static uint16_t *resume(uint16_t *p,uint32_t world,uint32_t blank,
    const V6MuxOverlay *npc,unsigned y,int npc_on,unsigned c0,unsigned c1)
{
    p=foreground(p,world+y*40,10240,0);
    p=pointer(p,0xe4,world+20480+((200+y)&255)*40);
    if(npc_on && npc){p=pointer(p,0xec,blank);p=pointer(p,0xf0,npc->bitmap+(52+y-npc->start)*40);}
    p=pair(p,0x180,c0);p=pair(p,0x182,c1);return pair(p,0x100,npc_on?0x5600:0x3600);
}
unsigned v6_terminal_layer_copper(uint16_t *out,const uint16_t *in,unsigned words,
    uint32_t bitmap,uint32_t caption_bitmap,uint32_t world,uint32_t blank,
    const V6MuxOverlay *npc,int visible,unsigned gray)
{
    uint16_t *p=out;const uint16_t *end=in+words,*scan;
    uint16_t epoch=0,in_epoch=0,event=0,installed=0,npc_on=0,caption=0,c0=0,c1=0;
    static const uint16_t text_lines[6]={67,111,135,137,206,275},bar_lines[2]={67,275};
    const uint16_t *lines=visible?text_lines:bar_lines;uint16_t events=visible?6:2;
    unsigned fill=0,remaining=gray;
    while(remaining>=6){remaining-=6;++fill;}
    if(!out || !in || out==in || words<2 || words>340 || (words&1) ||
       in[words-2]!=0xffff || in[words-1]!=0xfffe || ((bitmap|caption_bitmap|world|blank)&1) || gray>174)return 0;
    for(scan=in;scan<end && !(*scan&1);scan+=2){if(*scan==0x180)c0=scan[1];if(*scan==0x182)c1=scan[1];}
    fill=shade(fill);gray=shade(gray);
    while(in<end){uint16_t r=*in++,v=*in++,line;
        line=r==0xffff?512:(r&1)?(r==0xffdf?255:in_epoch+(r>>8)):0;
        if(r&1)while(event<events && lines[event]<=line){unsigned at=lines[event++];
            if(at>=255 && !epoch){p=pair(p,0xffdf,0xfffe);epoch=256;}
            p=pair(p,((at&255)<<8)|0xdf,0xfffe);
            if(at==275){p=foreground(p,bitmap+8960,9600,1);p=pointer(p,0xec,blank);
                p=pair(p,0x18c,0);p=pair(p,0x100,0x5600);}
            else if(at==111 || at==137){caption=1;p=pointer(p,0xe0,caption_bitmap+(at-51)*40);
                p=pair(p,0x180,fill);p=pair(p,0x182,gray);p=pair(p,0x100,0x1200);}
            else {caption=0;p=resume(p,world,blank,npc,at-51,npc_on,c0,c1);}
        }
        if(r==0xffff)break;
        if(r==0xffdf){in_epoch=256;if(epoch)continue;epoch=256;}
        if(r==0x100){
            if(!installed){p=pair(p,r,0x5600);p=foreground(p,bitmap,9600,1);p=pointer(p,0xec,blank);p=pair(p,0x18c,0);installed=1;}
            else {npc_on=v==0x5600;if(!caption)p=pair(p,r,v);}
            continue;
        }
        if(r==0xe0 || r==0xe2 || r==0xe8 || r==0xea || (caption && (r==0xe4 || r==0xe6)))continue;
        p=pair(p,r,v);
    }
    p=pair(p,0xffff,0xfffe);return installed && p-out<=512?(unsigned)(p-out):0;
}

int v6_terminal_scene_prefix(V6TerminalPrefix *prefix,const uint16_t *base,unsigned words)
{
    unsigned i;prefix->c0=prefix->c1=0;
    for(i=0;i+1<words && !(base[i]&1);i+=2){
        if(base[i]==0x180)prefix->c0=base[i+1];
        if(base[i]==0x182)prefix->c1=base[i+1];}
    prefix->words=i;return i+1<words && base[i]==0x2c01 && words<=192;
}
void v6_terminal_scene_windows(V6TerminalPrefix *prefix,uint32_t bitmap,uint32_t captions,uint32_t world,uint32_t blank)
{
    unsigned i;uint16_t *p,*start;
    static const uint16_t lines[6]={67,111,135,137,206,275};
    start=p=prefix->blocks[6];p=pair(p,0x18c,0);p=pair(p,0x2c01,0xfffe);
    p=foreground(p,bitmap,9600,1);p=pointer(p,0xec,blank);p=pointer(p,0xe4,world+20480+8000);
    prefix->sizes[6]=p-start;
    for(i=0;i<6;++i){unsigned line=lines[i];start=p=prefix->blocks[i];
        if(i==5){p=foreground(p,bitmap+8960,9600,1);p=pointer(p,0xec,blank);
            p=pair(p,0x18c,0);p=pair(p,0x100,0x5600);}
        else if(i==1 || i==3){p=pointer(p,0xe0,captions+(line-51)*40);
            p=pair(p,0x180,0);p=pair(p,0x182,0);p=pair(p,0x100,0x1200);}
        else p=resume(p,world,blank,0,line-51,0,prefix->c0,prefix->c1);
        prefix->sizes[i]=p-start;
    }
}
static uint16_t *block(uint16_t *out,const uint16_t *in,unsigned words)
{
#ifdef __m68k__
    unsigned i;
    for(i=words>>3;i;--i){
        __asm volatile("movem.l (%1)+,%%d0-%%d3\n\tmovem.l %%d0-%%d3,(%0)\n\tlea 16(%0),%0"
            : "+a"(out),"+a"(in) : : "d0","d1","d2","d3","memory","cc");}
    for(i=0;i<(words&7);++i)*out++=*in++;
#else
    while(words--)*out++=*in++;
#endif
    return out;
}
unsigned v6_terminal_scene_copper(uint16_t *out,const V6TerminalPrefix *prefix,
    const V6MuxPlan *plan,const V6MuxActor *actors,const V6MuxOverlay *npc,
    uint32_t bitmap,uint32_t caption_bitmap,uint32_t world,uint32_t blank,int visible,unsigned gray)
{
    uint16_t *p=out+prefix->words;
    uint16_t text=0,sprite=0,phase=0,wrap=0,epoch=0,npc_on=0,caption=0,last_line=44;
    static const uint16_t text_lines[6]={67,111,135,137,206,275},bar_lines[2]={67,275};
    const uint16_t *lines=visible?text_lines:bar_lines;uint16_t count=visible?6:2;
    unsigned fill=0;
    if(!out || !prefix || prefix->words>190 || plan->count>14 || gray>174)return 0;
    if(visible){switch(gray){
        case 87:fill=0x111;gray=0x555;break;
        case 104:fill=0x111;gray=0x666;break;
        case 121:fill=0x111;gray=0x777;break;
        case 139:fill=0x111;gray=0x888;break;
        case 156:fill=0x222;gray=0x999;break;
        case 174:fill=0x222;gray=0xaaa;break;
        default:return 0;
    }}
    (void)bitmap;(void)caption_bitmap;
    out[1]=0x5600;p=block(p,prefix->blocks[6],prefix->sizes[6]);
    for(;;){uint16_t line=512,kind=0,next;
        if(text<count){line=lines[text];kind=1;}
        if(!wrap && 107<line){line=107;kind=2;}
        if(npc && phase<2){next=(phase?npc->stop:npc->start)-1;if(next<line){line=next;kind=3;}}
        if(sprite<plan->count){next=plan->spans[sprite].start-1;if(next<line){line=next;kind=4;}}
        if(line==512)break;
        if(line>=255 && !epoch){p=pair(p,0xffdf,0xfffe);epoch=256;}
        if(line!=255 && line!=last_line)p=pair(p,((line&255)<<8)|0xdf,0xfffe);
        last_line=line;
        if(kind==1){unsigned which=visible?text:(text?5:0),size=prefix->sizes[which];uint16_t *start=p;++text;
            if(which==1 || which==3){caption=1;p=block(p,prefix->blocks[which],size);start[5]=fill;start[7]=gray;}
            else {caption=0;
                if(which!=5 && npc_on && npc){p=block(p,prefix->blocks[which],size-2);
                    p=pointer(p,0xec,blank);p=pointer(p,0xf0,npc->bitmap+(line+1-npc->start)*40);p=pair(p,0x100,0x5600);}
                else p=block(p,prefix->blocks[which],size);
            }
        }else if(kind==2){wrap=1;p=pointer(p,0xe4,world+20480);}
        else if(kind==3){unsigned i;npc_on=!phase;
            if(!phase){p=pointer(p,0xec,blank);p=pointer(p,0xf0,npc->bitmap);
                for(i=4;i<8;++i)p=pair(p,0x180+i*2,npc->colour);}
            if(!caption)p=pair(p,0x100,phase?0x3600:0x5600);
            ++phase;
        }else {const V6MuxSpan *s=&plan->spans[sprite++];
            p=pair(p,0x1a2+s->channel*4,actors[s->actor].colour);}
    }
    p=pair(p,0xffff,0xfffe);return p-out<=512?(unsigned)(p-out):0;
}
