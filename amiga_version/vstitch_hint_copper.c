#include "vstitch_hint_draw.h"
#include "tower_draw.h"
#include "pickup_draw.h"
static uint16_t *reg(uint16_t *p,unsigned address,unsigned value)
{*p++=(uint16_t)address;*p++=(uint16_t)value;return p;}
static uint16_t *pointer(uint16_t *p,unsigned regnum,uint32_t address)
{p=reg(p,regnum,address>>16);return reg(p,regnum+2,address);}
static uint16_t *foreground(uint16_t *p,uint32_t address,unsigned stride)
{p=pointer(p,0xe0,address);return pointer(p,0xe8,address+stride);}
unsigned v6_vstitch_hint_copper(uint16_t *out,uint32_t fg,uint32_t bg,unsigned fo,unsigned bo,
    uint32_t bank,uint32_t zero,unsigned fill,unsigned ink)
{
    uint16_t *p=out;unsigned fline,bline,line,epoch=0;
    unsigned begin=51+V6_HINT_TOP,end=51+V6_HINT_TOP+V6_HINT_HEIGHT;
    if(!out || fo>255 || bo>255 || ((fg|bg|bank|zero)&1) ||
       fg>0x1000000UL-V6_TOWER_RING_BYTES || bg>0x1000000UL-V6_TOWER_PLANE_BYTES ||
       bank>0x1000000UL-3*V6_PICKUP_PLANE_BYTES || zero>0x1000000UL-V6_PICKUP_PLANE_BYTES ||
       fill>0xfff || ink>0xfff)return 0;
    fline=fo>16?307-fo:512;bline=bo>16?307-bo:512;
    if(fline>=begin && fline<=end)fline=512;
    p=reg(p,0x2c01,0xfffe);p=foreground(p,fg+fo*40,V6_TOWER_PLANE_BYTES);
    p=pointer(p,0xe4,bg+bo*40);
    while(fline!=512 || bline!=512 || begin!=512 || end!=512) {
        line=fline<bline?fline:bline;if(begin<line)line=begin;if(end<line)line=end;
        if(line>=255 && !epoch){p=reg(p,0xffdf,0xfffe);epoch=1;}
        if(line!=255)p=reg(p,((line&255)<<8)|0xdf,0xfffe);
        if(fline==line){p=foreground(p,fg,V6_TOWER_PLANE_BYTES);fline=512;}
        if(bline==line){p=pointer(p,0xe4,bg);bline=512;}
        if(begin==line) {
            p=foreground(p,bank,V6_PICKUP_PLANE_BYTES);
            p=pointer(p,0xf0,bank+2*V6_PICKUP_PLANE_BYTES);p=pointer(p,0xec,zero);
            p=reg(p,0x100,0x5600);p=reg(p,0x104,0x20);
            p=reg(p,0x188,fill);p=reg(p,0x18a,ink);begin=512;
        }
        if(end==line) {
            p=foreground(p,fg+((fo+V6_HINT_TOP+V6_HINT_HEIGHT)&255)*40,V6_TOWER_PLANE_BYTES);
            p=reg(p,0x100,0x3600);p=reg(p,0x104,0x24);end=512;
        }
    }
    p=reg(p,0xffff,0xfffe);return (unsigned)(p-out);
}
