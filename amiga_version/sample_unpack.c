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
