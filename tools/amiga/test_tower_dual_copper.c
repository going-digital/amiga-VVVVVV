/* Decode emitted events independently, then model each visible DMA address. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "tower_copper.h"
int main(void)
{
    unsigned fo,bo;
    for(fo=0;fo<256;++fo) for(bo=0;bo<256;++bo) {
        uint16_t words[36];uint32_t ptr[3]={0,0,0};
        uint32_t addresses[240][3];unsigned i,n,line=0,epoch=0,y,k,next=0;
        for(i=0;i<36;++i) words[i]=0xa55a;
        n=v6_tower_dual_copper(words+1,0x1f000,0x35000,fo,bo);
        assert(n<=34 && n>=16 && words[0]==0xa55a && words[n+1]==0xa55a);
        for(i=1;i<n+1;i+=2) {
            unsigned reg=words[i],value=words[i+1];
            if(reg==0xffff) { assert(value==0xfffe && i==n-1);break; }
            if(reg&1) {
                unsigned target=(reg>>8)+epoch;
                assert(value==0xfffe);
                if(reg==0xffdf && epoch==0) { target=255;epoch=256; }
                assert(target>=line);line=target;
                /* Reset occurs after this line's fetch. Initial wait is 44. */
                while(next<240 && next+52<=line) {
                    for(k=0;k<3;++k) { addresses[next][k]=ptr[k];ptr[k]+=40; }
                    ++next;
                }
            } else {
                assert(reg>=0xe0 && reg<=0xea);k=(reg-0xe0)/4;
                if((reg&2)==0) ptr[k]=(ptr[k]&65535)|((uint32_t)value<<16);
                else ptr[k]=(ptr[k]&0xffff0000)|value;
            }
        }
        while(next<240) {
            for(k=0;k<3;++k) { addresses[next][k]=ptr[k];ptr[k]+=40; }
            ++next;
        }
        for(y=0;y<240;++y) {
            assert(addresses[y][0]==0x1f000+((fo+y)&255)*40);
            assert(addresses[y][1]==0x35000+((bo+y)&255)*40);
            assert(addresses[y][2]==0x21800+((fo+y)&255)*40);
        }
    }
    {
        uint16_t words[34],before[34];memset(words,0xa5,sizeof(words));memcpy(before,words,sizeof(words));
        assert(!v6_tower_dual_copper(words,1,0,0,0));
        assert(!v6_tower_dual_copper(words,0,1,0,0));
        assert(!v6_tower_dual_copper(words,0,0,256,0));
        assert(!v6_tower_dual_copper(words,0,0,0,256));
        assert(!v6_tower_dual_copper(words,0xffb002,0,0,0));
        assert(!v6_tower_dual_copper(words,0,0xffd802,0,0));
        assert(!memcmp(words,before,sizeof(words)));
    }
    puts("PASS: 65536 offset pairs, 47185920 modeled plane addresses; invalid inputs unchanged");
    return 0;
}
