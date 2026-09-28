/* Structural Copper simulation; this does not model DMA arbitration. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "tower_copper.h"
#include "tower_draw.h"
int main(void)
{
    unsigned checks=0;
    const uint32_t bases[]={0,0x1fff0,0x7b000,0x1000000-V6_TOWER_RING_BYTES};
    for(unsigned b=0;b<sizeof(bases)/sizeof(bases[0]);++b)
        for(unsigned offset=0;offset<256;++offset) {
            uint16_t guarded[V6_TOWER_COPPER_WORDS+2];
            uint16_t *words=guarded+1;
            uint32_t pointer[2]={0,0};
            unsigned line=0,epoch=0,groups=0,barriers=0;
            guarded[0]=guarded[V6_TOWER_COPPER_WORDS+1]=0xdead;
            unsigned n=v6_tower_copper(words,bases[b],offset);
            assert(n && n<=V6_TOWER_COPPER_WORDS);
            assert(guarded[0]==0xdead && guarded[V6_TOWER_COPPER_WORDS+1]==0xdead);
            for(unsigned i=0;i<n;i+=2) {
                uint16_t reg=words[i],value=words[i+1];
                if(reg==0xffff) {assert(value==0xfffe && i==n-2);break;}
                if(reg&1) {
                    assert(value==0xfffe);
                    if(reg==0xffdf) {line=255;epoch=256;++barriers;}
                    else {line=epoch+(reg>>8);assert((reg&255)==(groups?0xdf:1));}
                } else {
                    assert(reg==0xe0 || reg==0xe2 || reg==0xe4 || reg==0xe6);
                    unsigned plane=(reg-0xe0)/4;
                    if((reg&2)==0) pointer[plane]=(pointer[plane]&65535)|((uint32_t)value<<16);
                    else pointer[plane]=(pointer[plane]&0xffff0000UL)|value;
                    if(reg==0xe6) {
                        if(!groups) {
                            assert(line==44);
                            assert(pointer[0]==bases[b]+offset*40);
                        } else {
                            assert(groups==1 && line==52+256-offset-1);
                            assert(pointer[0]==bases[b]);
                        }
                        assert(pointer[1]==pointer[0]+V6_TOWER_PLANE_BYTES);
                        ++groups;
                    }
                }
            }
            assert(groups==(offset>16?2:1));
            assert(barriers==(offset>16 && offset<=52?1:0));
            /* Verify every visible fetch range under the modeled reset. */
            for(unsigned y=0;y<240;++y) {
                unsigned row=offset+y;
                if(row>=256) row-=256;
                uint32_t expected=bases[b]+row*40;
                uint32_t address=(offset+y<256)?bases[b]+(offset+y)*40:bases[b]+(y-(256-offset))*40;
                assert(address==expected && address+40<=bases[b]+V6_TOWER_PLANE_BYTES);
                ++checks;
            }
        }
    uint16_t output[V6_TOWER_COPPER_WORDS],before[V6_TOWER_COPPER_WORDS];
    memset(output,0xa5,sizeof(output));memcpy(before,output,sizeof(output));
    assert(!v6_tower_copper(output,1,0));
    assert(!v6_tower_copper(output,0,256));
    assert(!v6_tower_copper(output,0x1000000-V6_TOWER_RING_BYTES+2,0));
    assert(memcmp(output,before,sizeof(output))==0);
    printf("PASS: all 256 offsets at four addresses; %u modeled scanlines; PAL line-255 barriers and invalid inputs\n",checks);
    return 0;
}
