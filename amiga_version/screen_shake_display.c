#include "screen_shake_display.h"
#include "tower_draw.h"
#include "dialogue.h"
static uint16_t *reg(uint16_t *p,unsigned r,unsigned v){*p++=r;*p++=v;return p;}
static uint16_t *pointer(uint16_t *p,unsigned r,uint32_t v)
{p=reg(p,r,v>>16);return reg(p,r+2,v);}
static uint16_t *foreground(uint16_t *p,uint32_t v)
{p=pointer(p,0xe0,v);return pointer(p,0xe8,v+V6_TOWER_PLANE_BYTES);}
static unsigned display(uint16_t *out,const V6ScreenShakePlan *s,
    uint32_t fg,uint32_t bg,uint32_t mask,unsigned fo,unsigned bo,int flash,
    uint32_t caption,unsigned tint,unsigned c1,unsigned c3)
{
    unsigned top,bottom,fx,bx,line,epoch=0,scroll,begin=512,end=512;uint16_t *p=out;
    if(!out || !s || s->x< -4 || s->x>2 || s->y< -4 || s->y>4 || fo>255 || bo>255 ||
       ((fg|bg|mask)&1) || fg>0x1000000UL-V6_TOWER_RING_BYTES-2 ||
       bg>0x1000000UL-V6_TOWER_PLANE_BYTES-2 || mask>0x1000000UL-V6_SHAKE_MASK_BYTES ||
       s->source_x!=(s->x<0?-s->x:0) || s->destination_x!=(s->x>0?s->x:0) ||
       s->width!=320-(s->x<0?-s->x:s->x) || s->source_y!=(s->y<0?-s->y:0) || s->destination_y!=(s->y>0?s->y:0) ||
       s->height!=240-(s->y<0?-s->y:s->y) ||
       (caption && ((caption&1) || caption>0x1000000UL-V6_DIALOGUE_BYTES-2 || (tint|c1|c3)>0xfff)))return 0;
    top=52+s->destination_y;bottom=top+s->height;
    fo=(fo+s->source_y)&255;bo=(bo+s->source_y)&255;
    scroll=s->x<0?16+s->x:s->x;
    p=reg(p,0x100,flash?0x1200:0x4600);p=reg(p,0x102,scroll*0x11);
    p=reg(p,0x108,s->x<0?0xfffe:0);p=reg(p,0x10a,s->x<0?0xfffe:0);
    p=reg(p,0x08e,(top<<8)|(0x81+(s->x>0?s->x:0)));
    p=reg(p,0x090,((bottom&255)<<8)|(0xc1+(s->x<0?s->x:0)));
    p=reg(p,0x092,s->x<0?0x30:0x38);p=reg(p,0x094,0xd0);
    p=reg(p,0x2c01,0xfffe);p=foreground(p,fg+fo*40);
    p=pointer(p,0xe4,bg+bo*40);p=pointer(p,0xec,mask);
    fx=top+256-fo-1;bx=top+256-bo-1;
    if(flash){p=pointer(p,0xe0,mask);fx=bx=512;}
    if(fx>=bottom-1)fx=512;
    if(bx>=bottom-1)bx=512;
    if(caption && !flash) {
        begin=51+V6_DIALOGUE_TOP+s->y;end=begin+V6_DIALOGUE_HEIGHT;
        if(fx>=begin && fx<=end)fx=512;
        if(bx>=begin && bx<=end)bx=512;
    }
    while(fx!=512 || bx!=512 || begin!=512 || end!=512) {
        line=fx<bx?fx:bx;
        if(begin<line)line=begin;
        if(end<line)line=end;
        if(line>=255 && !epoch){p=reg(p,0xffdf,0xfffe);epoch=1;}
        if(line!=255)p=reg(p,((line&255)<<8)|0xdf,0xfffe);
        if(fx==line){p=foreground(p,fg);fx=512;}
        if(bx==line){p=pointer(p,0xe4,bg);bx=512;}
        if(begin==line) {
            p=reg(p,0x100,0x2200);p=reg(p,0x104,0);
            p=pointer(p,0xe0,caption);p=pointer(p,0xe4,caption+V6_DIALOGUE_PLANE_BYTES);
            p=reg(p,0x182,0);p=reg(p,0x186,tint);begin=512;
        }
        if(end==line) {
            p=reg(p,0x100,0x4600);p=reg(p,0x104,0x24);
            p=foreground(p,fg+((fo+line+1-top)&255)*40);
            p=pointer(p,0xe4,bg+((bo+line+1-top)&255)*40);
            p=reg(p,0x182,c1);p=reg(p,0x186,c3);end=512;
        }
    }
    p=reg(p,0xffff,0xfffe);return p-out;
}
unsigned v6_screen_shake_display(uint16_t *out,const V6ScreenShakePlan *s,
    uint32_t fg,uint32_t bg,uint32_t mask,unsigned fo,unsigned bo,int flash)
{return display(out,s,fg,bg,mask,fo,bo,flash,0,0,0,0);}
unsigned v6_screen_shake_caption(uint16_t *out,const V6ScreenShakePlan *s,
    uint32_t fg,uint32_t bg,uint32_t mask,unsigned fo,unsigned bo,int flash,
    uint32_t caption,unsigned tint,unsigned c1,unsigned c3)
{
    if(!caption)return 0;
    return display(out,s,fg,bg,mask,fo,bo,flash,caption,tint,c1,c3);
}
