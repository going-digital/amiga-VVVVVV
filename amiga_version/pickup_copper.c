#include "pickup_copper.h"
#include "pickup_draw.h"
#include "tower_draw.h"
static uint16_t *reg(uint16_t *p,unsigned address,unsigned value)
{*p++=(uint16_t)address;*p++=(uint16_t)value;return p;}
static uint16_t *pointer(uint16_t *p,unsigned address,uint32_t value)
{p=reg(p,address,value>>16);return reg(p,address+2,value);}
static uint16_t *foreground(uint16_t *p,uint32_t value,unsigned stride)
{p=pointer(p,0xe0,value);return pointer(p,0xe8,value+stride);}
unsigned v6_pickup_copper(uint16_t *out,uint32_t fg,uint32_t bg,unsigned fo,unsigned bo,
    uint32_t bank,uint32_t zero,int text,unsigned bars,unsigned fill,unsigned ink)
{
    uint16_t *p=out;
    unsigned start[4],end[4],fline,bline,line,i,epoch=0;
    const unsigned top[4]={0,V6_PICKUP_TOP,137,224},height[4]={16,42,24,16};
    const unsigned offset[4]={0,V6_PICKUP_TEXT_OFFSET,V6_PICKUP_TEXT_OFFSET+52*40,V6_PICKUP_BOTTOM_OFFSET};
    if(!out || fo>255 || bo>255 || ((fg|bg|bank|zero)&1) ||
       fg>0x1000000UL-V6_TOWER_RING_BYTES || bg>0x1000000UL-V6_TOWER_PLANE_BYTES ||
       bank>0x1000000UL-V6_PICKUP_BANK_BYTES || zero>0x1000000UL-V6_PICKUP_PLANE_BYTES ||
       (text!=0 && text!=1) || bars>361 || fill>0xfff || ink>0xfff)return 0;
    fline=fo>16?307-fo:512;bline=bo>16?307-bo:512;
    for(i=0;i<4;++i) {
        unsigned active=(i==1 || i==2)?(unsigned)text:i==0?bars>0:bars>40;
        start[i]=active?51+top[i]:512;end[i]=active?51+top[i]+height[i]:512;
        if(active && fline>=start[i] && fline<=end[i])fline=512;
    }
    p=reg(p,0x2c01,0xfffe);p=foreground(p,fg+fo*40,V6_TOWER_PLANE_BYTES);
    p=pointer(p,0xe4,bg+bo*40);
    for(;;) {
        line=fline<bline?fline:bline;
        for(i=0;i<4;++i){if(start[i]<line)line=start[i];if(end[i]<line)line=end[i];}
        if(line==512)break;
        if(line>=255 && !epoch){p=reg(p,0xffdf,0xfffe);epoch=1;}
        if(line!=255)p=reg(p,((line&255)<<8)|0xdf,0xfffe);
        if(fline==line){p=foreground(p,fg,V6_TOWER_PLANE_BYTES);fline=512;}
        if(bline==line){p=pointer(p,0xe4,bg);bline=512;}
        for(i=0;i<4;++i) {
            if(start[i]==line) {
                unsigned stride=(i==1 || i==2)?V6_PICKUP_PLANE_BYTES:V6_PICKUP_BAR_PLANE_BYTES;uint32_t address=bank+offset[i];
                p=foreground(p,address,stride);p=pointer(p,0xf0,address+2*stride);
                p=pointer(p,0xec,zero);
                p=reg(p,0x100,0x5600);p=reg(p,0x104,0x20);
                p=reg(p,0x188,(i==1 || i==2)?fill:0);p=reg(p,0x18a,ink);
                start[i]=512;
            }
            if(end[i]==line) {
                p=foreground(p,fg+((fo+top[i]+height[i])&255)*40,V6_TOWER_PLANE_BYTES);
                p=reg(p,0x100,0x3600);p=reg(p,0x104,0x24);end[i]=512;
            }
        }
    }
    p=reg(p,0xffff,0xfffe);return (unsigned)(p-out);
}
