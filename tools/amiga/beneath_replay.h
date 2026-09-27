/* Normal-input route: flip onto the first platform, back down onto the lower
 * platform, then up onto the right platform. Wait for collapse and spike death. */
static unsigned beneath_replay_input(unsigned tick)
{
    return (tick<=35?V6_RIGHT:0) | ((tick==5 || tick==13 || tick==27)?V6_FLIP:0);
}
