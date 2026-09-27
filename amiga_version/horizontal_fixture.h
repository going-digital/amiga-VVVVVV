/* Synthetic target regression, never a campaign room. Included only by the
 * horizontal replay build, after slice.h. Terrain uses an existing solid tile. */
#define PLATFORM_COUNT 1
#ifdef V6_WAITING_REPLAY
#define SLICE_CAPTION "SYNTHETIC WAITING PLATFORM TEST"
#else
#define SLICE_CAPTION "SYNTHETIC HORIZONTAL RIDE TEST"
#endif
static const V6RoomSetup room_setups[]={{0,0,160,100,21,0}};
static const int platform_setup[1][2]={{144,116}};
static void horizontal_fixture_tiles(uint16_t *tiles)
{
    unsigned x,y;
    for(y=0;y<30;++y) for(x=0;x<40;++x)
        *tiles++=(y>=27 || x==0 || x==39)?495:0;
}
