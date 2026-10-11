#ifndef V6_PICKUP_FADE_H
#define V6_PICKUP_FADE_H
#include <stdint.h>
/* Source Textbox.cpp lifecycle, in tenths. Tick after script show/remove.
 * Removal resumes gameplay immediately; drawing survives until level .5. */
typedef struct {unsigned level,old_level,mode,visible;} V6PickupFade;
void v6_pickup_fade_init(V6PickupFade *);
void v6_pickup_fade_show(V6PickupFade *);
void v6_pickup_fade_remove(V6PickupFade *);
void v6_pickup_fade_tick(V6PickupFade *);
/* Interpolated source gray 174 and fill gray/6, nearest OCS 4-bit levels.
 * Packed fill<<16 | ink. Elapsed is clamped to the 34 ms timestep. */
uint32_t v6_pickup_fade_colours(const V6PickupFade *,unsigned elapsed);
#endif
