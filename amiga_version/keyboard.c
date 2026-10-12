#include "keyboard.h"
#include "map_menu.h"
void v6_keyboard_init(V6Keyboard *k)
{
    unsigned i;for(i=0;i<16;++i)k->down[i]=0;
}
unsigned v6_keyboard_decode(unsigned serial)
{
    unsigned b=(~serial)&255;
    return (b>>1)|((b&1)<<7);
}
void v6_keyboard_receive(V6Keyboard *k,unsigned serial)
{
    unsigned code=v6_keyboard_decode(serial),key=code&127,mask=1U<<(key&7);
    /* 0x78..0x7f are protocol codes rather than physical keys. Overflow,
     * lost-sync, self-test failure and a new power-up stream invalidate held keys. */
    if(key>=0x78) {
        if(code==0xf9 || code==0xfa || code==0xfc || code==0xfd)v6_keyboard_init(k);
        return;
    }
    if(code&128)k->down[key>>3]&=(uint8_t)~mask;
    else k->down[key>>3]|=(uint8_t)mask;
}
static unsigned held(const V6Keyboard *k,unsigned key)
{
    return (k->down[key>>3]>>(key&7))&1;
}
unsigned v6_keyboard_map_buttons(const V6Keyboard *k)
{
    unsigned b=0;
    if(held(k,0x43)||held(k,0x44))b|=V6_MAP_ENTER;
    if(held(k,0x4f))b|=V6_MAP_LEFT;
    if(held(k,0x4e))b|=V6_MAP_RIGHT;
    if(held(k,0x40)||held(k,0x31)||held(k,0x34))b|=V6_MAP_ACTION;
    return b;
}
