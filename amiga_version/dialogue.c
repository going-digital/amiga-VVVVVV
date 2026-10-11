#include "dialogue.h"
int v6_dialogue_replace_line(uint8_t *out,const uint8_t font[128][8],unsigned count,
    unsigned line,const char *text)
{
    unsigned i,length=0,x,y,top;uint8_t *ink;
    if(!out || !font || !text || !count || count>V6_RESCUE_MAX_LINES || line>=count)return 0;
    while(text[length]) {
        if(length>=36 || (unsigned char)text[length]>=128)return 0;
        ++length;
    }
    ink=out+V6_DIALOGUE_PLANE_BYTES;top=(V6_DIALOGUE_HEIGHT-count*8)/2+line*8;
    for(y=0;y<8;++y)for(x=2;x<38;++x)ink[(top+y)*40+x]=0;
    x=(40-length)/2;
    for(i=0;i<length;++i)for(y=0;y<8;++y)
        ink[(top+y)*40+x+i]=font[(unsigned char)text[i]][y];
    return 1;
}
int v6_dialogue_draw(uint8_t *out,const uint8_t font[128][8],const V6RescueSpeech *speech)
{
    unsigned line,x,y,i,lengths[V6_RESCUE_MAX_LINES],top;
    uint8_t *ink;
    if(!out || !font || !speech || !speech->count || speech->count>V6_RESCUE_MAX_LINES) return 0;
    for(line=0;line<speech->count;++line) {
        const unsigned char *s=(const void *)speech->lines[line];
        if(!s) return 0;
        for(i=0;s[i];++i) if(i>=36 || s[i]>=128) return 0;
        lengths[line]=i;
    }
    ink=out+V6_DIALOGUE_PLANE_BYTES;
    for(i=0;i<V6_DIALOGUE_PLANE_BYTES;++i) { out[i]=255;ink[i]=0; }
    for(x=1;x<39;++x) ink[4*40+x]=ink[43*40+x]=255;
    for(y=5;y<43;++y) { ink[y*40+1]=128;ink[y*40+38]=1; }
    top=(V6_DIALOGUE_HEIGHT-speech->count*8)/2;
    for(line=0;line<speech->count;++line) {
        x=(40-lengths[line])/2;
        for(i=0;i<lengths[line];++i)
            for(y=0;y<8;++y) ink[(top+line*8+y)*40+x+i]=font[(unsigned char)speech->lines[line][i]][y];
    }
    return 1;
}
