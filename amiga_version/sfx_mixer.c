#include "sfx_mixer.h"
void v6_sfx_init(V6SfxMixer *m)
{
    unsigned i;
    for(i=0;i<V6_SFX_VOICES;++i) {
        m->voices[i].pcm=0;m->voices[i].bytes=m->voices[i].position=0;
    }
    m->starts=m->completed=m->dropped=0;
}
int v6_sfx_play(V6SfxMixer *m,const uint8_t *pcm,size_t bytes)
{
    unsigned i;
    if(!m || !pcm || !bytes)return 0;
    for(i=0;i<V6_SFX_VOICES;++i)if(!m->voices[i].pcm) {
        m->voices[i].pcm=pcm;m->voices[i].bytes=bytes;m->voices[i].position=0;
        ++m->starts;return 1;
    }
    ++m->dropped;return 0;
}
int v6_sfx_render(V6SfxMixer *m,uint8_t *output,size_t count)
{
    size_t n;unsigned i;
    if(!m || (count && !output))return 0;
    for(i=0;i<V6_SFX_VOICES;++i) {
        const V6SfxVoice *v=&m->voices[i];
        if(v->pcm && (!v->bytes || v->position>=v->bytes))return 0;
        if(!v->pcm && (v->bytes || v->position))return 0;
    }
    for(n=0;n<count;++n) {
        int sum=0;
        for(i=0;i<V6_SFX_VOICES;++i) {
            V6SfxVoice *v=&m->voices[i];
            if(v->pcm) {
                unsigned sample=v->pcm[v->position++];
                sum+=sample<128?(int)sample:(int)sample-256;
                if(v->position==v->bytes) {
                    v->pcm=0;v->bytes=v->position=0;++m->completed;
                }
            }
        }
        output[n]=(uint8_t)(sum/4);
    }
    return 1;
}
