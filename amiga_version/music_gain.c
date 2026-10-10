#include "music_gain.h"
static uint32_t multiply(unsigned a,unsigned b)
{
#ifdef __m68k__
 uint32_t product=a;uint16_t right=(uint16_t)b;
 __asm volatile("mulu.w %1,%0":"+d"(product):"d"(right):"cc");
 return product;
#else
 return a*b;
#endif
}
int v6_music_gain_plan(unsigned music_mask,unsigned sfx_mask,
    const unsigned instrument[4],unsigned control,unsigned user,
    int muted,int music_muted,V6AudioPlan *p)
{
 unsigned i,gain;
 if(!instrument || !p || (music_mask|sfx_mask)>15 || (music_mask&sfx_mask) ||
    control>128 || user>256 || (unsigned)muted>1 || (unsigned)music_muted>1)return 0;
 for(i=0;i<4;++i)if(instrument[i]>64)return 0;
 /* Both products fit 16 bits; powers-of-two divisors need no runtime helpers. */
 gain=(unsigned)multiply(control,user)>>8;
 if(muted || music_muted)gain=0;
 p->count=0;
 for(i=0;i<4;++i)if(music_mask&(1U<<i)) {
  p->writes[p->count].reg=0xa8+16*i;
  p->writes[p->count++].value=(unsigned)multiply(instrument[i],gain)>>7;
 }
 return 1;
}
