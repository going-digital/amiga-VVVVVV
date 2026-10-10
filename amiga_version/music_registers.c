#include "music_registers.h"
int v6_music_register_plan(const V6AudioPlan *in,unsigned music,unsigned sfx,V6AudioPlan *out)
{
 unsigned i,n=0;
 if(!in || !out || (music|sfx)>15 || (music&sfx) || in->count>16)return 0;
 /* Validate the entire stream before writing, including suppressed channels. */
 for(i=0;i<in->count;++i) {
  unsigned reg=in->writes[i].reg,value=in->writes[i].value;
  if(value>65535)return 0;
  if(reg==0x96){if(value&~0x800fU)return 0;}
  else if(reg==0x9c){if(value&~0x8780U)return 0;}
  else {
   unsigned offset=(reg-0xa0)&15;
   if(reg<0xa0 || reg>0xd8 || offset>8 || (offset&1) || (offset==8 && value>64))return 0;
  }
 }
 for(i=0;i<in->count;++i) {
  unsigned reg=in->writes[i].reg,value=in->writes[i].value;
  if(reg==0x96){value=(value&0x8000)|(value&music);if(!(value&15))continue;}
  else if(reg==0x9c){value=(value&0x8000)|(value&(music<<7));if(!(value&0x780))continue;}
  else if(!(music&(1U<<((reg-0xa0)>>4))))continue;
  out->writes[n].reg=reg;out->writes[n++].value=value;
 }
 out->count=n;return 1;
}
