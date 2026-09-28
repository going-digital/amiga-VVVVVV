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
