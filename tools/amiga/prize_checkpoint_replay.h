/* Canonical V Stitch lower checkpoint; ordinary inputs thereafter. */
static unsigned v6_prize_checkpoint_replay(unsigned tick)
{
    static const unsigned lengths[8]={6,5,4,5,5,4,5,5};
    unsigned i;
    if(!tick)return 0;
    --tick;
    for(i=0;i<8;++i) {
        unsigned duration=lengths[i]+16;
        if(tick<duration)return tick<lengths[i]?(tick?1:5):0;
        tick-=duration;
    }
    if(tick<10)return 1; /* Cross west, then approach the alcove. */
    tick-=10;
    if(tick<12)return 0;
    tick-=12;
    if(!tick)return 4;
    --tick;
    if(tick<3)return 1;
    tick-=3;
    if(tick<18)return 0;
    tick-=18;
    return tick<20?2:0; /* Source ceiling death, then checkpoint respawn. */
}
