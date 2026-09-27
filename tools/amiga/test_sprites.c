/* Decode DMA words back into screen pixels, independently of the encoder. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "sprites.h"
static uint16_t storage[8*68+2];
static uint32_t rows[32];
static V6Sprites batch;
static void reset(void)
{
    memset(storage,0xa5,sizeof(storage));
    v6_sprites_begin(&batch,storage+1);
}
static void guards(void)
{
    assert(storage[0]==0xa5a5 && storage[8*68+1]==0xa5a5);
}
int main(void)
{
    static const int xs[]={-32768,-33,-17,-16,-15,-7,-1,0,1,303,304,305,319,320,32767};
    static const int ys[]={-32768,-32,-17,-16,-15,0,15,16,17,190,203,204,215,216,32767};
    unsigned i,j,crop,ch,cases=0;
    for (i=0;i<32;++i) rows[i]=0xa593e76bu^(0x01020408u*i);
    for (ch=0;ch<8;++ch) for (crop=0;crop<=16;++crop)
    for (i=0;i<sizeof(xs)/sizeof(xs[0]);++i)
    for (j=0;j<sizeof(ys)/sizeof(ys[0]);++j) {
        int x=xs[i],y=ys[j],visible=x+(int)crop<320 && x+(int)crop+16>0 && y<216 && y+32>16;
        unsigned n,r;
        int result;
        uint16_t *d;
        reset();
        for (n=0;n<ch;++n) assert(v6_sprites_add(&batch,rows,0,16,0,n)==(int)n);
        result=v6_sprites_add(&batch,rows,x,y,crop,0xf6b);
        if (!visible) { assert(result==V6_SPRITE_CLIPPED && batch.count==ch); guards(); ++cases; continue; }
        assert(result==(int)ch && batch.count==ch+1 && batch.colours[ch]==0xf6b);
        d=batch.dma+ch*68;
        {
            int left=((d[0]&255)*2+(d[1]&1))-129;
            int top=((d[0]>>8)|((d[1]&4)<<6))-52;
            int bottom=((d[1]>>8)|((d[1]&2)<<7))-52;
            assert(left==x+(int)crop && top==(y<16?16:y));
            assert(bottom==(y+32>216?216:y+32));
            assert(!(d[1]&0x80)); /* unattached */
            for (r=0;r<(unsigned)(bottom-top);++r) {
                unsigned col;
                for (col=0;col<16;++col) {
                    unsigned pixel=((d[2+r*2]>>(15-col))&1)|(((d[3+r*2]>>(15-col))&1)<<1);
                    unsigned source=(rows[top-y+(int)r]>>(31-crop-col))&1;
                    unsigned expected=left+(int)col>=0 && left+(int)col<320 && source ? (ch&1?3:1):0;
                    assert(pixel==expected);
                }
            }
            assert(d[2+r*2]==0 && d[3+r*2]==0);
        }
        for(n=ch+1;n<8;++n) assert(batch.dma[n*68]==0 && batch.dma[n*68+1]==0);
        guards(); ++cases;
    }
    reset();
    for(i=0;i<8;++i) {
        assert(v6_sprites_add(&batch,rows,10,30,0,0x100+i)==(int)i);
        assert(v6_sprite_colour_register(i)==0x1a2+4*i);
    }
    {
        uint16_t before[8*68];
        memcpy(before,batch.dma,sizeof(before));
        assert(v6_sprites_add(&batch,rows,0,16,0,0xfff)==V6_SPRITE_FULL);
        assert(v6_sprites_add(&batch,rows,320,16,0,0xfff)==V6_SPRITE_CLIPPED);
        assert(v6_sprites_add(&batch,rows,0,16,17,0xfff)==V6_SPRITE_INVALID);
        assert(v6_sprites_add(&batch,rows,0,16,0,0x1000)==V6_SPRITE_INVALID);
        assert(v6_sprites_add(&batch,rows,32768,16,0,0xfff)==V6_SPRITE_INVALID);
        assert(v6_sprites_add(&batch,0,0,16,0,0xfff)==V6_SPRITE_INVALID);
        assert(batch.count==8 && !memcmp(before,batch.dma,sizeof(before)));
        for(i=0;i<8;++i) assert(batch.colours[i]==0x100+i);
    }
    v6_sprites_begin(&batch,batch.dma);
    for(i=0;i<8;++i) assert(!batch.dma[i*68] && !batch.dma[i*68+1] && !batch.colours[i]);
    assert(!batch.count); guards();
    printf("PASS: %u sprite DMA decode cases; capacity, reset, invalid requests and guards\n",cases);
    return 0;
}
