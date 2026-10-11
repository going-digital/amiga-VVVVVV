#ifndef V6_PRIZE_INPUT_REPLAY_H
#define V6_PRIZE_INPUT_REPLAY_H
/* Zero-based world ticks. Starts at Shenanigan checkpoint 442490; only
 * ordinary left/right/fire inputs follow. Includes a source spike death,
 * respawn, south crossing, all three gate collapses and remote death return. */
static unsigned v6_prize_input_replay(unsigned tick)
{
    static const unsigned char direction[16]={0,2,0,0,2,1,2,1,0,2,0,1,0,1,1,1};
    if(tick<126) {
        unsigned segment=tick>>3;
        return direction[segment]|((!(tick&7) && ((0x6232U>>segment)&1))?4:0);
    }
    return tick<150?2:0;
}
#endif
