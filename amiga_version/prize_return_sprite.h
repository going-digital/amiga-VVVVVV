#ifndef V6_PRIZE_RETURN_SPRITE_H
#define V6_PRIZE_RETURN_SPRITE_H
#include "prize_return.h"
/* Entity::animateentities simple-loop subset, stepped by the fixed renderer,
 * not each physical PAL display field. Frames are offsets into source 92..95. */
typedef struct { int delay,walk,frame; } V6ReturnEnemyAnimation;
void v6_return_enemy_animation_init(V6ReturnEnemyAnimation *);
/* Source blackout/completestop suppress the entire fixed-render animation pass.
 * Death does not suppress it. Initial drawframe is tile 0 until the first pass;
 * -1 represents that pre-animation state for the caller. */
void v6_return_enemy_animation_tick(V6ReturnEnemyAnimation *,int stopped);
/* Rectangle broad-phase and original red-channel pixel collision. Caller
 * supplies full 32x32 masks selected by source collision/render animation.
 * Pass source tile-0 mask for an enemy whose initial drawframe is still zero.
 * NULL skips an enemy; it must not substitute for a live animation frame. */
int v6_prize_return_pixel_hurt(const V6PrizeReturn *,const V6Player *,
    const uint32_t *player_mask,const uint32_t *enemy0,const uint32_t *enemy1);
#endif
