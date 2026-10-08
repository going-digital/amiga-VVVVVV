#include "audio_policy.h"
int v6_audio_choose(unsigned allowed,unsigned busy,const unsigned priority[4],
    const unsigned age[4],unsigned incoming_priority)
{
    unsigned i;int best=-1;
    if((allowed|busy)>15 || !priority || !age)return -2;
    for(i=0;i<4;++i)if((allowed&(1U<<i)) && !(busy&(1U<<i)))return (int)i;
    for(i=0;i<4;++i)if((allowed&(1U<<i)) && priority[i]<incoming_priority) {
        if(best<0 || priority[i]<priority[best] ||
           (priority[i]==priority[best] && age[i]>age[best]))best=(int)i;
    }
    return best;
}
