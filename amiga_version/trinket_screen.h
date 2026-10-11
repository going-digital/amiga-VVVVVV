#ifndef V6_TRINKET_SCREEN_H
#define V6_TRINKET_SCREEN_H
#include "trinkets.h"
/* Normal-game Game.cpp states 1000..1003. Input precedes state update;
 * gameplay uses stopped from the preceding update, as in Logic.cpp.
 * The caller owns jumpheld and must latch it when input returns one. */
enum { V6_TRINKET_SHOW=1, V6_TRINKET_HIDE=2,
       V6_TRINKET_SILENCE=4, V6_TRINKET_CUE=8, V6_TRINKET_FADE_IN=16 };
typedef struct {
    int state,delay,control,stopped,bars,advance,visible,count;
} V6TrinketScreen;
void v6_trinket_screen_init(V6TrinketScreen *);
/* Called once for a normal-game pickup, after the bank has been updated.
 * No tracker/DMA ownership: returned events go to the audio adapter.
 * Music resumes with the source 3000 ms fade when FADE_IN is returned. */
unsigned v6_trinket_screen_begin(V6TrinketScreen *,const V6Collect *,int music_present);
int v6_trinket_screen_input(V6TrinketScreen *,int action,int jumpheld);
unsigned v6_trinket_screen_tick(V6TrinketScreen *,int music_present);
#endif
