/* Normal-input route: leave the checkpoint, flip onto the underside of the
 * first platform, then wait for collapse, ceiling-spike death and respawn. */
static unsigned beneath_replay_input(unsigned tick)
{
    return (tick<=12?V6_RIGHT:0) | (tick==5?V6_FLIP:0);
}
