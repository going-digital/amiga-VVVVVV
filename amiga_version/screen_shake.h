#ifndef V6_SCREEN_SHAKE_H
#define V6_SCREEN_SHAKE_H
#include <stdint.h>
/* Graphics::renderfixedpre samples offsets while the shake timer is positive,
 * even in noflashing mode. Caller owns random generation and timer decay. */
typedef struct { int16_t x,y; } V6ScreenShake;
typedef struct {
    int16_t x,y;
    uint16_t source_x,source_y,destination_x,destination_y,width,height;
} V6ScreenShakePlan;
void v6_screen_shake_init(V6ScreenShake *);
/* Two uniform samples represent fRandom() as sample/65536 in [0,1).
 * Inactive timers retain previous offsets. Invalid calls retain state. */
int v6_screen_shake_pre(V6ScreenShake *,int timer,const uint16_t samples[2]);
/* Plan the source's 320x240 viewport translation with clipping. The renderer
 * must clear exposed edges black and translate sprites/text with the scene.
 * Flip mode negates physical Y displacement, matching the final texture flip.
 * noflashing/inactive timers produce an unshifted full viewport. Screenshot
 * borders are drawn afterward, without translation. Invalid calls retain out. */
int v6_screen_shake_plan(const V6ScreenShake *,int timer,int noflashing,int flip,
    V6ScreenShakePlan *out);
#endif
