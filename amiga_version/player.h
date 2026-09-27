#ifndef V6_PLAYER_H
#define V6_PLAYER_H
#include <stdint.h>

#define V6_ONE 16777216L
enum { V6_LEFT = 1, V6_RIGHT = 2, V6_FLIP = 4, V6_NO_CONTROL = 8 };
enum { V6_EVENT_FLIP = 1 };

/* Positions are integer pixels as in Ent.h; velocities are signed 8.24.
 * Scalar operations reproduce binary32 rounding in the bounded player range.
 * This core covers one player and static tiles, including one-way blocks.
 * Moving entities, conveyors, gravity lines and scripts remain outside it. */
typedef struct {
    int32_t x, y, old_x, old_y, vx, vy, ay;
    int32_t ground, roof, tap_left, tap_right, held, buffer, gravity, dir, flips;
} V6Player;

typedef struct {
    const uint16_t *tiles;
    int tileset, extra_row;
} V6Room;

void v6_player_init(V6Player *p, int x, int y, int gravity);
unsigned v6_player_step(V6Player *p, const V6Room *room, unsigned input);
int v6_player_hurt(const V6Player *p, const V6Room *room);
int v6_player_overlaps(const V6Player *p, int x, int y, int w, int h);

#endif
