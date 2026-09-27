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
static void wide_tests(void)
{
    static const int xs[]={-32,-17,-1,0,1,304,319,320};
    unsigned width,crop,i,prefix,cases=0;
    for(width=1;width<=32;++width) for(crop=0;crop+width<=32;++crop)
    for(i=0;i<sizeof(xs)/sizeof(xs[0]);++i) for(prefix=0;prefix<8;++prefix) {
        int x=xs[i],left=x+(int)crop,right=left+(int)width,result;
        unsigned n,required,row;
        uint16_t before[8*68];
        if(left<0) left=0;
        if(right>320) right=320;
        required=right>left?(unsigned)(right-left+15)/16:0;
        reset();
        for(n=0;n<prefix;++n) assert(v6_sprites_add(&batch,rows,0,16,0,n)==(int)n);
        memcpy(before,batch.dma,sizeof(before));
        result=v6_sprites_add_wide(&batch,rows,x,190,crop,width,0xf66);
        if (!required || prefix+required>8) {
            assert(result==(!required?V6_SPRITE_CLIPPED:V6_SPRITE_FULL));
            assert(batch.count==prefix && !memcmp(before,batch.dma,sizeof(before)));
        } else {
            assert(result==(int)prefix && batch.count==prefix+required);
            assert(!memcmp(before,batch.dma,prefix*68*sizeof(uint16_t)));
            for(row=0;row<26;++row) {
                unsigned pixels[320]={0},col;
                for(n=prefix;n<batch.count;++n) {
                    uint16_t *d=batch.dma+n*68;
                    int sx=((d[0]&255)*2+(d[1]&1))-129;
                    assert(batch.colours[n]==0xf66);
                    for(col=0;col<16;++col) if(sx+(int)col>=0 && sx+(int)col<320)
                        pixels[sx+col]+=((d[2+row*2]>>(15-col))&1);
                    assert(!d[54] && !d[55]);
                }
                for(col=0;col<320;++col) {
                    unsigned expected=(int)col>=left && (int)col<right ? (rows[row]>>(31-((int)col-x)))&1 : 0;
                    assert(pixels[col]==expected);
                }
            }
        }
        guards(); ++cases;
    }
    printf("PASS: %u wide-sprite decode and atomic allocation cases\n",cases);
}
static void rectangle_tests(void)
{
    unsigned height,prefix,cases=0;
    int y;
    for(height=1;height<=32;++height) for(y=-32;y<=216;++y)
    for(prefix=0;prefix<8;++prefix) {
        int result,top=y<16?16:y,bottom=y+(int)height;
        unsigned i;
        uint16_t before[8*68];
        if(bottom>216) bottom=216;
        reset();
        for(i=0;i<prefix;++i) v6_sprites_add(&batch,rows,0,16,0,0x123);
        memcpy(before,batch.dma,sizeof(before));
        result=v6_sprites_add_rect(&batch,rows,100,y,0,32,height,0xf6b);
        if(top>=bottom || prefix>6) {
            assert(result==(top>=bottom?V6_SPRITE_CLIPPED:V6_SPRITE_FULL));
            assert(batch.count==prefix && !memcmp(before,batch.dma,sizeof(before)));
        } else {
            assert(result==(int)prefix && batch.count==prefix+2);
            for(i=prefix;i<batch.count;++i) {
                uint16_t *d=batch.dma+i*68;
                unsigned r;
                assert(((d[0]>>8)|((d[1]&4)<<6))-52==top);
                assert(((d[1]>>8)|((d[1]&2)<<7))-52==bottom);
                for(r=0;r<(unsigned)(bottom-top);++r) {
                    uint16_t bits=i==prefix?rows[top-y+r]>>16:rows[top-y+r];
                    assert(d[2+r*2]==bits && d[3+r*2]==((i&1)?bits:0));
                }
                assert(!d[2+r*2] && !d[3+r*2]);
            }
        }
        guards();++cases;
    }
    reset();
    assert(v6_sprites_add_rect(&batch,rows,0,16,0,32,0,0)==V6_SPRITE_INVALID);
    assert(v6_sprites_add_rect(&batch,rows,0,16,0,32,33,0)==V6_SPRITE_INVALID);
    printf("PASS: %u variable-height sprite cases\n",cases);
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
    wide_tests();
    rectangle_tests();
    return 0;
}
