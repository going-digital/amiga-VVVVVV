#include "sprites.h"

unsigned v6_sprite_colour_register(unsigned channel)
{
    return 0x180 + 2 * (17 + (channel / 2) * 4 + (channel & 1) * 2);
}

void v6_sprites_begin(V6Sprites *batch, uint16_t *dma)
{
    unsigned i;
    batch->dma=dma; batch->count=0;
    for (i=0;i<V6_SPRITE_CHANNELS;++i) {
        dma[i*V6_SPRITE_WORDS]=dma[i*V6_SPRITE_WORDS+1]=0;
        batch->colours[i]=0;
    }
}

int v6_sprites_add(V6Sprites *batch, const uint32_t rows[32],
                   int x, int y, unsigned crop, unsigned colour)
{
    int first, last, left, row;
    unsigned channel, start, stop, horizontal;
    uint16_t clip=0xffff, *data;
    if (!rows || crop>16 || colour>0xfff || x < -32768 || x > 32767 ||
        y < -32768 || y > 32767) return V6_SPRITE_INVALID;
    left=x+(int)crop;
    first=y<16?16-y:0;
    last=y+32>216?216-y:32;
    if (first>=last || first>=32 || last<=0 || left>=320 || left<=-16)
        return V6_SPRITE_CLIPPED;
    if (batch->count==V6_SPRITE_CHANNELS) return V6_SPRITE_FULL;
    channel=batch->count++;
    batch->colours[channel]=(uint16_t)colour;
    data=batch->dma+channel*V6_SPRITE_WORDS;
    if (left<0) clip >>= -left;
    if (left>304) clip &= (uint16_t)(0xffff << (left-304));
    start=52+y+first; stop=52+y+last; horizontal=129+left;
    *data++=((start&255)<<8)|(horizontal>>1);
    *data++=((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(horizontal&1);
    for (row=first;row<last;++row) {
        uint16_t bits=(uint16_t)(rows[row]>>(16-crop))&clip;
        *data++=bits;
        *data++=(channel&1)?bits:0;
    }
    data[0]=data[1]=0;
    return (int)channel;
}
