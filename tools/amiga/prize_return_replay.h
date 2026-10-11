/* Canonical V Stitch lower start, checkpoint acquisition and preserved-checkpoint
 * west loop. Only ordinary left/right/fire inputs; no post-start placements. */
static unsigned v6_prize_return_replay(unsigned tick)
{
    static const uint8_t buttons[285]={0,0,0,0,0,0,0,0,0,0,0,0,5,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,5,5,5,5,5,5,5,5,1,1,1,1,1,1,1,1,5,5,5,5,5,5,5,5,1,1,1,1,1,1,1,1,5,5,5,5,5,5,5,5,1,1,1,1,1,1,1,1,5,5,5,5,5,5,5,5,1,1,1,1,1,1,1,1,5,5,5,5,5,5,5,5,0,0,0,0,0,0,0,0,2,2,6,6,6,6,6,6,6,6,0,0,6,6,6,6,6,6,6,6,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,6,6,6,6,6,6,6,6,2,2,2,2,2,2,2,2,1,1,1,1,2,2,2,2,2,2,2,2,6,6,6,6,6,6,6,6,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,2,6,6,6,6,6,6,6,6,2,2,2,2,2,2,2,2,1,1,2,2,2,2,2,2,2,2,1,1,1,1,1,1,1,1,0,0,0,0,5,5,1,1,5,5,5,5,5,5,5,5,1,1,1,1,1,1,1,1,0,0};
    if(tick>=480)return v6_prize_collection_replay(tick-480);
    if(tick<195)return v6_prize_checkpoint_replay(tick);
    tick-=195;
    return tick<285?buttons[tick]:0;
}
