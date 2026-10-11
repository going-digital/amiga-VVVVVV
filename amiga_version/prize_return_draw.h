#ifndef V6_PRIZE_RETURN_DRAW_H
#define V6_PRIZE_RETURN_DRAW_H
#include "prize_return.h"
/* Four fixed x strips (88,136,184,232), each 240 rows of eight bytes:
 * four source background bytes in plane 0, then four in plane 1.
 * Caller owns an inactive, fixed-camera two-plane ring and one last_y[4]
 * per buffer. Reset last_y to -1 after a full room fill. Tile repeats over
 * the platform's 32x8 footprint; mask retains original alpha. */
int v6_prize_return_draw_platforms(uint8_t *ring,const V6PrizeReturn *,
    const uint8_t *strips,const uint8_t tile[16],const uint8_t mask[8],int last_y[4]);
/* Fixed source conveyor origins, opaque tiles, two planes; even ring base. */
void v6_prize_return_draw_conveyors(uint8_t *ring,const uint8_t treads[16]);
#endif
