#include "tower_copper.h"
#include "tower_draw.h"
static uint16_t *pointers(uint16_t *p,uint32_t base)
{
    unsigned plane;
    for(plane=0;plane<2;++plane) {
        uint32_t address=base+plane*V6_TOWER_PLANE_BYTES;
        *p++=(uint16_t)(0xe0+plane*4);*p++=(uint16_t)(address>>16);
        *p++=(uint16_t)(0xe2+plane*4);*p++=(uint16_t)address;
    }
    return p;
}
unsigned v6_tower_copper(uint16_t *out,uint32_t ring,unsigned offset)
{
    uint16_t *p=out;
    unsigned last_line;
    if(offset>=256 || (ring&1) || ring>0x1000000UL-V6_TOWER_RING_BYTES) return 0;
    *p++=0x2c01;*p++=0xfffe;
    p=pointers(p,ring+offset*40);
    if(offset>16) {
        /* End the last ring scanline after DDF fetches. Pointer writes may
         * continue into the next line, before its first fetch at h=0x38. */
        last_line=52+256-offset-1;
        if(last_line>=255) {
            *p++=0xffdf;*p++=0xfffe;
        }
        if(last_line!=255) {
            *p++=(uint16_t)(((last_line&255)<<8)|0xdf);*p++=0xfffe;
        }
        p=pointers(p,ring);
    }
    *p++=0xffff;*p++=0xfffe;
    return (unsigned)(p-out);
}

static uint16_t *one_pointer(uint16_t *p,unsigned reg,uint32_t address)
{
    *p++=(uint16_t)reg;*p++=(uint16_t)(address>>16);
    *p++=(uint16_t)(reg+2);*p++=(uint16_t)address;
    return p;
}
static uint16_t *dual_foreground(uint16_t *p,uint32_t address)
{
    p=one_pointer(p,0xe0,address);
    return one_pointer(p,0xe8,address+V6_TOWER_PLANE_BYTES);
}
unsigned v6_tower_dual_copper(uint16_t *out,uint32_t fg,uint32_t bg,
    unsigned fo,unsigned bo)
{
    uint16_t *p=out;
    unsigned fline,bline,line,epoch=0;
    if(fo>255 || bo>255 || ((fg|bg)&1) ||
       fg>0x1000000UL-V6_TOWER_RING_BYTES ||
       bg>0x1000000UL-V6_TOWER_PLANE_BYTES) return 0;
    *p++=0x2c01;*p++=0xfffe;
    p=dual_foreground(p,fg+fo*40);
    p=one_pointer(p,0xe4,bg+bo*40);
    fline=fo>16?307-fo:512;bline=bo>16?307-bo:512;
    while(fline!=512 || bline!=512) {
        line=fline<bline?fline:bline;
        if(line>=255 && !epoch) {
            *p++=0xffdf;*p++=0xfffe;epoch=1;
            /* The barrier itself is the wait when the event is line 255. */
            if(line==255) goto reset;
        }
        *p++=(uint16_t)(((line&255)<<8)|0xdf);*p++=0xfffe;
reset:
        if(fline==line) { p=dual_foreground(p,fg);fline=512; }
        if(bline==line) { p=one_pointer(p,0xe4,bg);bline=512; }
    }
    *p++=0xffff;*p++=0xfffe;
    return (unsigned)(p-out);
}

#include "dialogue.h"
static uint16_t *reg(uint16_t *p,unsigned address,unsigned value)
{
    *p++=(uint16_t)address;*p++=(uint16_t)value;return p;
}
unsigned v6_tower_caption_copper(uint16_t *out,uint32_t fg,uint32_t bg,
    unsigned fo,unsigned bo,uint32_t caption,unsigned tint,unsigned c1,unsigned c3)
{
    uint16_t *p=out;
    unsigned fline,bline,begin=51+V6_DIALOGUE_TOP,end=51+V6_DIALOGUE_TOP+V6_DIALOGUE_HEIGHT,line,epoch=0;
    if(fo>255 || bo>255 || ((fg|bg|caption)&1) ||
       fg>0x1000000UL-V6_TOWER_RING_BYTES || bg>0x1000000UL-V6_TOWER_PLANE_BYTES ||
       caption>0x1000000UL-V6_DIALOGUE_BYTES || (tint|c1|c3)>0xfff) return 0;
    p=reg(p,0x2c01,0xfffe);p=dual_foreground(p,fg+fo*40);p=one_pointer(p,0xe4,bg+bo*40);
    fline=fo>16?307-fo:512;bline=bo>16?307-bo:512;
    /* These pointers do not fetch while the caption owns the display. The
     * explicit resume pointers include any source-ring wrap inside the strip. */
    if(fline>=begin && fline<=end) fline=512;
    if(bline>=begin && bline<=end) bline=512;
    while(fline!=512 || bline!=512 || begin!=512 || end!=512) {
        line=fline<bline?fline:bline;
        if(begin<line) line=begin;
        if(end<line) line=end;
        if(line>=255 && !epoch) { p=reg(p,0xffdf,0xfffe);epoch=1; }
        if(line!=255) p=reg(p,((line&255)<<8)|0xdf,0xfffe);
        if(fline==line) { p=dual_foreground(p,fg);fline=512; }
        if(bline==line) { p=one_pointer(p,0xe4,bg);bline=512; }
        if(begin==line) {
            p=reg(p,0x100,0x2200);p=reg(p,0x104,0);
            p=one_pointer(p,0xe0,caption);p=one_pointer(p,0xe4,caption+V6_DIALOGUE_PLANE_BYTES);
            p=reg(p,0x182,0);p=reg(p,0x186,tint);begin=512;
        }
        if(end==line) {
            p=reg(p,0x100,0x3600);p=reg(p,0x104,0x24);
            p=dual_foreground(p,fg+((fo+V6_DIALOGUE_TOP+V6_DIALOGUE_HEIGHT)&255)*40);
            p=one_pointer(p,0xe4,bg+((bo+V6_DIALOGUE_TOP+V6_DIALOGUE_HEIGHT)&255)*40);
            p=reg(p,0x182,c1);p=reg(p,0x186,c3);end=512;
        }
    }
    p=reg(p,0xffff,0xfffe);return (unsigned)(p-out);
}
