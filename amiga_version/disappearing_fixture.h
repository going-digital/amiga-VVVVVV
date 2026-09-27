/* Synthetic lifecycle scene, not a campaign room. */
#define PLATFORM_COUNT 1
#define SLICE_CAPTION "SYNTHETIC DISAPPEARING PLATFORM"
#ifdef V6_RETRIGGER_REPLAY
/* Deliberately respawn on the platform before recharge completes. */
static const V6RoomSetup room_setups[]={{0,0,112,77,21,0}};
#else
static const V6RoomSetup room_setups[]={{0,0,204,144,21,0}};
#endif
static const int platform_setup[1][2]={{104,93}};
static void disappearing_fixture_tiles(uint16_t *tiles)
{
    unsigned x,y;
    for(y=0;y<30;++y) for(x=0;x<40;++x)
        *tiles++=(y==18 && x>=9 && x<20)?6:((y==20 && x>=24 && x<31)?495:0);
}
