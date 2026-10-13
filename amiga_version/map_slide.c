#include "map_slide.h"
#include "map_draw.h"
static uint16_t *reg(uint16_t *p,unsigned r,unsigned v)
{*p++=(uint16_t)r;*p++=(uint16_t)v;return p;}
static uint16_t *ptr(uint16_t *p,unsigned r,uint32_t a)
{p=reg(p,r,a>>16);return reg(p,r+2,a);}
unsigned v6_map_slide_copper(uint16_t *out,uint32_t fg,uint32_t bg,
    unsigned bo,uint32_t map,const uint16_t palette[32],uint32_t blank,uint32_t cursor,unsigned offset)
{
    uint16_t *p=out;unsigned i,line,epoch=0;
    if(!out || !palette || !offset || offset>=240 || bo>255 || ((fg|bg|map|blank|cursor)&1) ||
       fg>0x1000000UL-20480 || bg>0x1000000UL-10240 ||
       map>0x1000000UL-V6_MAP_BITMAP_BYTES || blank>0xfffffc || cursor>0x1000000UL-136)return 0;
    for(i=0;i<32;++i)if(((const volatile uint16_t *)palette)[i]>0xfff)return 0;
    p=ptr(p,0x120,cursor);
    p=reg(p,0x2c01,0xfffe);
    p=ptr(p,0xe0,fg);p=ptr(p,0xe4,bg+bo*40);p=ptr(p,0xe8,fg+10240);
    line=51+offset;
    if(bo>16 && 307-bo<line) {
        unsigned wrap=307-bo;
        if(wrap>=255) {p=reg(p,0xffdf,0xfffe);epoch=1;}
        if(wrap!=255)p=reg(p,((wrap&255)<<8)|0xdf,0xfffe);
        p=ptr(p,0xe4,bg);
    }
    if(line>=255 && !epoch)p=reg(p,0xffdf,0xfffe);
    if(line!=255)p=reg(p,((line&255)<<8)|0xdf,0xfffe);
    /* Set all DMA pointers before the next line's DDF fetch. Install the
       rest of the palette during the two initial black menu rows. */
    p=reg(p,0x100,0x5200);
    for(i=0;i<5;++i)p=ptr(p,0xe0+i*4,map+i*V6_MAP_PLANE_BYTES);
    p=reg(p,0x104,0x20);
    for(i=0;i<32;++i)p=reg(p,0x180+i*2,palette[i]);
    for(i=1;i<8;++i)p=ptr(p,0x120+i*4,blank);
    p=reg(p,0xffff,0xfffe);return (unsigned)(p-out);
}
void v6_map_slide_clip(uint16_t sprite[68],unsigned offset)
{
    unsigned start=(sprite[0]>>8)|((sprite[1]&4)<<6);
    unsigned stop=(sprite[1]>>8)|((sprite[1]&2)<<7),boundary=52+offset;
    if(!sprite[0] || stop<=boundary)return;
    if(start>=boundary) {sprite[0]=sprite[1]=sprite[2]=sprite[3]=0;return;}
    sprite[1]=(uint16_t)((sprite[1]&0x00fd)|((boundary&255)<<8)|((boundary>>7)&2));
    sprite[2+(boundary-start)*2]=sprite[3+(boundary-start)*2]=0;
}

void v6_map_slide_channel(uint16_t sprite[68],unsigned channel)
{
    unsigned i;
    if(channel>=8)return;
    for(i=0;i<32;++i)sprite[3+i*2]=(channel&1)?sprite[2+i*2]:0;
}
unsigned v6_map_slide_cursor(uint16_t sprite[68],const uint32_t rows[32],unsigned x,unsigned y)
{
    unsigned i,height,start,stop,h;
    if(!sprite || !rows || x>308)return 0;
    for(i=0;i<68;++i)sprite[i]=0;
    if(y>=240)return 0;
    height=y>231?240-y:9;start=52+y;stop=start+height;h=128+x;
    sprite[0]=(uint16_t)(((start&255)<<8)|(h>>1));
    sprite[1]=(uint16_t)(((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(h&1));
    for(i=0;i<height;++i)sprite[2+i*2]=(uint16_t)(rows[i]>>16)&0xfff0;
    return height;
}
