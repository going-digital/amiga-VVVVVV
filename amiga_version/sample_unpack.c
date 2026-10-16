#include "sample_unpack.h"
int v6_sample_unpack(uint8_t *out,unsigned capacity,const uint8_t *in,unsigned size)
{
    unsigned at=0,used=0;
    if(!out || !in || !capacity)return 0;
    while(used<capacity){unsigned flags,bit;
        if(at==size)return 0;
        flags=in[at++];
        for(bit=1;bit<256 && used<capacity;bit<<=1){
            if(flags&bit){if(at==size)return 0;out[used++]=in[at++];}
            else {unsigned token,distance,count;
                if(size-at<2)return 0;
                token=((unsigned)in[at]<<8)|in[at+1];at+=2;
                distance=(token>>4)+1;count=(token&15)+3;
                if(distance>used || count>capacity-used)return 0;
                while(count--){out[used]=out[used-distance];++used;}
            }
        }
    }
    return at==size;
}
int v6_sample_unpack_delta(uint8_t *out,unsigned capacity,const uint8_t *in,unsigned size)
{
    unsigned i;uint8_t previous=0;
    if(!v6_sample_unpack(out,capacity,in,size))return 0;
    for(i=0;i<capacity;++i){previous=(uint8_t)(previous+out[i]);out[i]=previous;}
    return 1;
}
int v6_sample_job_init(V6SampleJob *s,uint8_t *out,unsigned capacity,const uint8_t *in,unsigned size)
{
    if(!s || !out || !capacity || !in || !size)return 0;
    s->out=out;s->in=in;s->capacity=capacity;s->size=size;
    s->at=s->used=s->flags=s->bit=s->remaining=s->distance=s->previous=s->error=0;
    return 1;
}
int v6_sample_job_step(V6SampleJob *s,unsigned budget)
{
    if(!s || s->error || !budget)return -1;
    while(budget-- && s->used<s->capacity){unsigned delta;
        if(s->remaining){unsigned pos=s->used-s->distance;
            delta=(uint8_t)(s->out[pos]-(pos?s->out[pos-1]:0));--s->remaining;
        }else{
            if(!s->bit){if(s->at==s->size)goto failed;s->flags=s->in[s->at++];s->bit=1;}
            if(s->flags&s->bit){if(s->at==s->size)goto failed;delta=s->in[s->at++];}
            else {unsigned token;
                if(s->size-s->at<2)goto failed;
                token=((unsigned)s->in[s->at]<<8)|s->in[s->at+1];s->at+=2;
                s->distance=(token>>4)+1;s->remaining=(token&15)+3;
                if(s->distance>s->used || s->remaining>s->capacity-s->used)goto failed;
                {unsigned pos=s->used-s->distance;
                    delta=(uint8_t)(s->out[pos]-(pos?s->out[pos-1]:0));--s->remaining;}
            }
            s->bit=(s->bit<<1)&255;
        }
        s->previous=(s->previous+delta)&255;s->out[s->used++]=(uint8_t)s->previous;
    }
    if(s->used<s->capacity)return 0;
    if(s->at!=s->size || s->remaining)goto failed;
    return 1;
failed:s->error=1;return -1;
}
