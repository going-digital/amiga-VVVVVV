/* Test-only inputs, one byte per 34 ms tick. Reaches (119,110) from the
 * initial checkpoint without modifying player state or disabling hazards. */
static const unsigned char transition_replay[] = {
    1,1,1,5,5,5,1,1,1,4,4,4,1,1,1,1,1,1,
    5,5,5,5,5,5,1,1,1,0,0,0,5,5,5,2,2,2,
    1,1,1,1,1,1,0,0,0,1,1,1,0,0,0,1,1,1
};
