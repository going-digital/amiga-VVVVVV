/* Adapted from Graphics.cpp colour 102; see ../LICENSE.md. */
#include "teleporter_colour.h"
uint16_t v6_teleporter_flash_colour(const uint16_t r[4],int noflashing)
{
    unsigned branch,red,green,blue;
    if(noflashing || !r)return 0xccd;
    branch=((uint32_t)r[0]*150)>>16;
    red=64+(((uint32_t)r[1]*64)>>16);
    green=64+(((uint32_t)r[2]*64)>>16);
    blue=64+(((uint32_t)r[3]*64)>>16);
    if(branch<33)red=((255UL<<16)-(uint32_t)r[1]*64)>>16;
    else if(branch<66)green=((255UL<<16)-(uint32_t)r[2]*64)>>16;
    else if(branch<100)blue=((255UL<<16)-(uint32_t)r[3]*64)>>16;
    else {
        red+=100;green+=100;
        blue=((255UL<<16)-(uint32_t)r[3]*64)>>16;
    }
    return ((red>>4)<<8)|((green>>4)<<4)|(blue>>4);
}
