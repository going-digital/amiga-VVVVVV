#ifndef V6_PRIZE_RETURN_H
#define V6_PRIZE_RETURN_H
#include "platform.h"
/* Candidate west-route actor composition. Checkpoints, terrain, death timing,
 * graphics and room/save admission belong to the campaign caller. */
typedef struct {
    V6Platform platforms[6];
    V6Enemy enemies[2];
    V6Block blocks[6];
    V6PlatformPush push;
    unsigned platform_count,enemy_count,flags;
} V6PrizeReturn;
/* Accept only A Deception (110,107) and Down Under (110,106).
 * Bind caller-owned actor blocks to the supplied room. */
int v6_prize_return_init(V6PrizeReturn *,V6Room *,int room_x,int room_y,int player_y);
/* Live input phase, after player input and before checkpoint/entity updates. */
void v6_prize_return_platforms(V6PrizeReturn *,V6Room *,V6Player *,int life,int pending_y);
/* Live entity phase, reverse creation order; enemies use current platform blocks. */
void v6_prize_return_entities(V6PrizeReturn *,const V6Room *);
/* Post-physics contact phase. Returns one bit per overlapping enemy as pixel-test candidates.
 * Source sprite collisions require v6_pixel_hit before the caller starts death.
 * Platform overlap disabling must precede stuck prevention. */
unsigned v6_prize_return_contacts(V6PrizeReturn *,const V6Player *);
#endif
