/* Synthetic upward spike-push fixture, matching the host compression suite. */
#define PLATFORM_COUNT 1
#define SLICE_CAPTION "SYNTHETIC SPIKE PUSH TEST"
static const V6RoomSetup room_setups[]={{0,0,112,77,21,0}};
static const int platform_setup[1][2]={{104,93}};
static void crush_fixture_tiles(uint16_t *tiles)
{
    unsigned x,y;
    for(y=0;y<30;++y) for(x=0;x<40;++x)
        *tiles++=(y==8 && x>=9 && x<20)?6:0;
}
