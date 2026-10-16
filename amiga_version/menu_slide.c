#include "menu_slide.h"
static void emit(uint16_t *out,unsigned *n,unsigned r,unsigned v)
{out[(*n)++]=(uint16_t)r;out[(*n)++]=(uint16_t)v;}
static unsigned compose(uint16_t *out,const uint16_t *game,unsigned words,
    uint32_t bitmap,unsigned planes,const uint16_t palette[32],
    const uint32_t sprites[8],unsigned offset,int owned)
{
    unsigned i,n=0,epoch=0,line=51+offset,end=0,kept=0,past=0;
    if(!out || !game || !palette || !sprites || out==game || words<2 || words>V6_MENU_SLIDE_WORDS ||
       (words&1) || !offset || offset>=240 || (planes!=4 && planes!=5) ||
       (bitmap&1) || bitmap>0x1000000UL-planes*9600UL)return 0;
    if(!owned)for(i=0;i<32;++i)if(((const volatile uint16_t *)palette)[i]>0xfff)return 0;
    if(!owned)for(i=0;i<8;++i)if((sprites[i]&1) || sprites[i]>0xfffffc)return 0;
    /* Validate before touching the caller's inactive list. */
    for(i=0;i<words;i+=2) {
        unsigned r=game[i],v=game[i+1];
        if(r==0xffff){if(!owned && v!=0xfffe)return 0;end=1;break;}
        if(r&1) {
            unsigned y;
            if(!owned && v!=0xfffe)return 0;
            if(r==0xffdf){y=255;epoch=256;}else y=epoch+(r>>8);
            if(y>=line)past=1;
        } else if(!owned && r>0x1fe)return 0;
        if(!past)kept=i+2;
    }
    if(!end || 32+kept+10+planes*4+64+2>V6_MENU_SLIDE_WORDS)return 0;
    for(i=0;i<8;++i){emit(out,&n,0x120+i*4,sprites[i]>>16);emit(out,&n,0x122+i*4,sprites[i]);}
    epoch=0;
    for(i=0;i<kept;i+=2) {
        unsigned r=game[i],v=game[i+1];
        if(r==0xffdf)epoch=256;
        if(!(r&1) && r>=0x120 && r<=0x13e)continue;
        emit(out,&n,r,v);
    }
    if(line>=255 && !epoch)emit(out,&n,0xffdf,0xfffe);
    if(line!=255)emit(out,&n,((line&255)<<8)|0xdf,0xfffe);
    emit(out,&n,0x100,(planes<<12)|0x200);
    for(i=0;i<planes;++i){uint32_t a=bitmap+i*9600UL;emit(out,&n,0xe0+i*4,a>>16);emit(out,&n,0xe2+i*4,a);}
    emit(out,&n,0x102,0);emit(out,&n,0x104,0x20);
    for(i=0;i<32;++i)emit(out,&n,0x180+i*2,palette[i]);
    emit(out,&n,0xffff,0xfffe);return n;
}

unsigned v6_menu_slide_copper(uint16_t *out,const uint16_t *game,unsigned words,
    uint32_t bitmap,unsigned planes,const uint16_t palette[32],const uint32_t sprites[8],unsigned offset)
{return compose(out,game,words,bitmap,planes,palette,sprites,offset,0);}
unsigned v6_menu_slide_owned_copper(uint16_t *out,const uint16_t *game,unsigned words,
    uint32_t bitmap,unsigned planes,const uint16_t palette[32],const uint32_t sprites[8],unsigned offset)
{return compose(out,game,words,bitmap,planes,palette,sprites,offset,1);}

static unsigned rearm(uint16_t *out,unsigned words,const uint32_t data[8],
    const uint16_t controls[8][2],unsigned offset,int owned)
{
    unsigned i,n,epoch=0,line=52+offset;
    if(!out || !data || !controls || words<2 || (words&1) || words+68>V6_MENU_SLIDE_WORDS ||
       !offset || offset>=240 || out[words-2]!=0xffff || out[words-1]!=0xfffe)return 0;
    if(!owned)for(i=0;i<8;++i){unsigned start,stop;
        if((data[i]&1) || data[i]>0xfffffc || (controls[i][1]&0xf8))return 0;
        start=(controls[i][0]>>8)|((controls[i][1]&4)<<6);
        stop=(controls[i][1]>>8)|((controls[i][1]&2)<<7);
        if(controls[i][0] || controls[i][1])if(start<line+2 || stop<=start || stop>292)return 0;
    }
    if(owned)epoch=51+offset>=255?256:0;
    else for(i=0;i<words-2;i+=2)if(out[i]==0xffdf)epoch=256;
    n=words-2;
    if(line>=255 && !epoch)emit(out,&n,0xffdf,0xfffe);
    if(line!=255)emit(out,&n,((line&255)<<8)|0xdf,0xfffe);
    for(i=0;i<8;++i){emit(out,&n,0x120+i*4,data[i]>>16);emit(out,&n,0x122+i*4,data[i]);
        emit(out,&n,0x140+i*8,controls[i][0]);emit(out,&n,0x142+i*8,controls[i][1]);}
    emit(out,&n,0xffff,0xfffe);return n;
}

unsigned v6_menu_slide_rearm(uint16_t *out,unsigned words,const uint32_t data[8],
    const uint16_t controls[8][2],unsigned offset)
{return rearm(out,words,data,controls,offset,0);}
unsigned v6_menu_slide_owned_rearm(uint16_t *out,unsigned words,const uint32_t data[8],
    const uint16_t controls[8][2],unsigned offset)
{return rearm(out,words,data,controls,offset,1);}
