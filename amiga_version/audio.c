#include "audio.h"
static void write(V6AudioPlan *p,unsigned reg,unsigned value)
{
    p->writes[p->count].reg=reg;p->writes[p->count++].value=value;
}
static void stop(V6AudioPlan *p)
{
    p->count=0;write(p,0x96,3);write(p,0xa8,0);write(p,0xb8,0);write(p,0x9c,0x180);
}
static void location(V6AudioPlan *p,unsigned base,uint32_t address,unsigned bytes)
{
    write(p,base,address>>16);write(p,base+2,address&65535);write(p,base+4,bytes/2);
}
int v6_audio_init(V6Audio *a,uint32_t silence)
{
    if(!a || (silence&1) || silence>0x80000UL-2) return 0;
    a->silence=silence;a->state=a->starts=a->completed=a->replaced=a->error=a->interrupts=a->wait=0;
    return 1;
}
int v6_audio_request(V6Audio *a,const V6AudioSample *s,V6AudioPlan *p)
{
    if(!a || !s || !p || (s->address&1) || s->bytes<1024 || s->bytes>131070 ||
       (s->bytes&1) || s->address>0x80000UL-s->bytes || s->period<124 ||
       s->period>1024 || s->volume>64) return 0;
    if(a->state!=V6_AUDIO_IDLE) ++a->replaced;
    a->sample.address=s->address;a->sample.bytes=s->bytes;
    a->sample.period=s->period;a->sample.volume=s->volume;
    stop(p);a->wait=1;a->state=V6_AUDIO_STOPPING;return 1;
}
void v6_audio_tick(V6Audio *a,int pending,V6AudioPlan *p)
{
    unsigned channel;p->count=0;
    if(a->state==V6_AUDIO_STOPPING) {
        if(a->wait) { --a->wait;return; }
        /* An entire field with DMA off exceeds two sampling periods for
         * these short cues (period 161). Clear stale IRQs before restarting. */
        write(p,0x9c,0x180);
        for(channel=0;channel<2;++channel) {
            unsigned base=0xa0+channel*16;
            location(p,base,a->sample.address,a->sample.bytes);
            write(p,base+6,a->sample.period);write(p,base+8,a->sample.volume);
        }
        write(p,0x96,0x8203);a->state=V6_AUDIO_PLAYING;++a->starts;
    } else if(pending && a->state==V6_AUDIO_PLAYING) {
        /* First DMA IRQ: the current block has been latched. Queue silence
         * for its reload, while the source sample continues to play. */
        location(p,0xa0,a->silence,2);location(p,0xb0,a->silence,2);
        write(p,0x9c,0x180);a->state=V6_AUDIO_DRAINING;++a->interrupts;
    } else if(pending && a->state==V6_AUDIO_DRAINING) {
        stop(p);a->state=V6_AUDIO_IDLE;++a->completed;++a->interrupts;
    }
}
void v6_audio_stop(V6Audio *a,V6AudioPlan *p)
{
    stop(p);a->state=V6_AUDIO_IDLE;
}
