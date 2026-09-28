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
