#include "paula_voice.h"
static void single(V6AudioPlan *p,unsigned channel)
{
    unsigned i,n=0;
    for(i=0;i<p->count;++i) {
        unsigned reg=p->writes[i].reg,value=p->writes[i].value;
        if(reg>=0xb0 && reg<=0xbf)continue; /* Drop the stereo duplicate. */
        if(reg>=0xa0 && reg<=0xaf)reg+=channel*16;
        else if(reg==0x96)value=(value&0x8200)|(1U<<channel);
        else if(reg==0x9c)value=0x80U<<channel;
        p->writes[n].reg=reg;p->writes[n++].value=value;
    }
    p->count=n;
}
static int valid(const V6PaulaVoice *v,const V6AudioPlan *p)
{
    return v && p && v->channel<4 && v->audio.state<=V6_AUDIO_DRAINING;
}
int v6_paula_init(V6PaulaVoice *v,unsigned channel,uint32_t silence)
{
    if(!v || channel>=4 || !v6_audio_init(&v->audio,silence))return 0;
    v->channel=channel;return 1;
}
int v6_paula_request(V6PaulaVoice *v,const V6AudioSample *s,V6AudioPlan *p)
{
    if(!valid(v,p) || !v6_audio_request(&v->audio,s,p))return 0;
    single(p,v->channel);return 1;
}
int v6_paula_tick(V6PaulaVoice *v,int pending,V6AudioPlan *p)
{
    if(!valid(v,p))return 0;
    v6_audio_tick(&v->audio,pending,p);single(p,v->channel);return 1;
}
int v6_paula_stop(V6PaulaVoice *v,V6AudioPlan *p)
{
    if(!valid(v,p))return 0;
    v6_audio_stop(&v->audio,p);single(p,v->channel);return 1;
}
