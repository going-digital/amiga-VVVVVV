#ifndef V6_PIXEL_COLLISION_H
#define V6_PIXEL_COLLISION_H
#include <stdint.h>
/* 32x32 masks, bit 31 at x=0. Collision masks use source red != 0,
 * independently of alpha and of the visible sprite mask. */
int v6_pixel_hit(const uint32_t *a, int ax, int ay,
                 const uint32_t *b, int bx, int by);
#endif
