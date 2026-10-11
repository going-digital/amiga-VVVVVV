#include "teleporter_draw.h"
int v6_teleporter_draw(uint16_t *dma,const uint16_t base[96][6],
    const uint16_t mask[96][6],int x,int y)
{
    unsigned channel;int first,last;
    if(!dma || !base || !mask || x< -32768 || x>32767 || y< -32768 || y>32767) return 0;
    first=y<16?16-y:0;last=y+96>216?216-y:96;
    for(channel=0;channel<6;++channel) {
        uint16_t *d=dma+channel*V6_TELEPORTER_DMA_WORDS;
        int left=x+(int)channel*16,row;
        unsigned start,stop,horizontal;uint16_t clip=0xffff;
        d[0]=d[1]=0;
        if(first>=last || first>=96 || last<=0 || left>=320 || left<=-16) continue;
        if(left<0) clip&=0xffffu>>-left;
        if(left>304) clip&=(uint16_t)(0xffffu<<(left-304));
        start=52+y+first;stop=52+y+last;horizontal=128+left;
        *d++=((start&255)<<8)|(horizontal>>1);
        *d++=((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(horizontal&1);
        for(row=first;row<last;++row) {
            uint16_t overlay=mask[row][channel]&clip;
            *d++=(base[row][channel]&clip)&~overlay;
            *d++=overlay;
        }
        d[0]=d[1]=0;
    }
    return 1;
}

void v6_teleporter_copy_dma(uint16_t *out,const uint16_t *in)
{
#if defined(__m68k__)
    /* Six longwords per block: 1176 words = 98 blocks. MOVEM accepts the
     * two-byte alignment of our Chip banks; no uint32_t pointer cast. */
#if (V6_TELEPORTER_CHANNELS*V6_TELEPORTER_DMA_WORDS*2)%24
#error Teleporter DMA size must be a whole number of MOVEM blocks
#endif
    unsigned blocks=(V6_TELEPORTER_CHANNELS*V6_TELEPORTER_DMA_WORDS*2)/24-1;
    __asm volatile(
        "1: movem.l (%1)+,%%d0-%%d5\n\t"
        "movem.l %%d0-%%d5,(%0)\n\t"
        "lea 24(%0),%0\n\t"
        "dbra %2,1b"
        : "+a"(out),"+a"(in),"+d"(blocks)
        : : "d0","d1","d2","d3","d4","d5","memory","cc");
#else
    unsigned i;
    for(i=0;i<V6_TELEPORTER_CHANNELS*V6_TELEPORTER_DMA_WORDS;++i)out[i]=in[i];
#endif
}
