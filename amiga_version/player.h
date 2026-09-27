#ifndef V6_PLAYER_H
#define V6_PLAYER_H
#include <stdint.h>
#include "terrain.h"
#include "blocks.h"

#define V6_ONE 16777216L
enum { V6_LEFT = 1, V6_RIGHT = 2, V6_FLIP = 4, V6_NO_CONTROL = 8 };
enum { V6_EVENT_FLIP = 1 };

/* Positions are integer pixels as in Ent.h; velocities are signed 8.24.
 * Scalar operations reproduce binary32 rounding in the bounded player range.
 * This core covers one player, static tiles and caller-supplied collision
 * blocks. Platform transport/crushing, conveyors, gravity lines and scripts
 * remain outside it. */
typedef struct {
    int32_t x, y, old_x, old_y, vx, vy, ay;
    int32_t ground, roof, tap_left, tap_right, held, buffer, gravity, dir, flips;
} V6Player;

typedef struct V6Room {
    const uint16_t *tiles;
    int tileset, extra_row;
    /* Optional immutable cache; rebuild after changing tiles or room settings. */
    const V6Terrain *terrain;
    /* Caller-owned dynamic blocks; may move without rebuilding terrain. */
    const V6Block *blocks;
    unsigned block_count;
} V6Room;

void v6_player_init(V6Player *p, int x, int y, int gravity);
/* Optional collision-animation hook: after input/contact probes, before
 * velocity integration. The callback must not mutate the player. */
typedef void (*V6ContactHook)(const V6Player *, void *);
int v6_player_contacts(const V6Player *, const V6Room *);
unsigned v6_player_step_hook(V6Player *, const V6Room *, unsigned, V6ContactHook, void *);
unsigned v6_player_step(V6Player *p, const V6Room *room, unsigned input);
int v6_player_hurt(const V6Player *p, const V6Room *room);
int v6_player_overlaps(const V6Player *p, int x, int y, int w, int h);

#endif
