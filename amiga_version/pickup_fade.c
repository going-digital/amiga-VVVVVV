/* Adapted from Textbox.cpp and Graphics.cpp; copyright Terry Cavanagh.
 * See ../LICENSE.md. */
#include "pickup_fade.h"
void v6_pickup_fade_init(V6PickupFade *s)
{s->level=s->old_level=s->mode=s->visible=0;}
void v6_pickup_fade_show(V6PickupFade *s)
{s->level=s->old_level=5;s->mode=0;s->visible=1;}
void v6_pickup_fade_remove(V6PickupFade *s)
{if(s->visible){s->level=10;s->mode=2;}}
void v6_pickup_fade_tick(V6PickupFade *s)
{
    if(!s->visible)return;
    s->old_level=s->level;
    if(s->mode==0){if(++s->level>=10){s->level=10;s->mode=1;}}
    else if(s->mode==2){if(--s->level<=5){s->level=5;s->visible=0;}}
}
uint32_t v6_pickup_fade_colours(const V6PickupFade *s,unsigned elapsed)
{
    uint32_t brightness;
    if(!s->visible)return 0;
    if(elapsed>34000)elapsed=34000;
    brightness=(uint32_t)(uint16_t)s->old_level*(uint16_t)(34000-elapsed)+
        (uint32_t)(uint16_t)s->level*(uint16_t)elapsed;
    /* Source gray=floor(174*brightness/340000), fill=gray/6. Convert
     * nearest OCS levels by comparing exact integer threshold ceilings,
     * avoiding five DIVU operations on each render field. */
#define AT(gray) (((gray)*340000UL+173)/174)
    if(brightness<AT(128)) {
        if(brightness<AT(111))return brightness<AT(94)?0x01110555UL:0x01110666UL;
        return 0x01110777UL;
    }
    if(brightness<AT(156))return brightness<AT(145)?0x01110888UL:0x01110999UL;
    return brightness<AT(162)?0x02220999UL:0x02220aaaUL;
#undef AT
}
