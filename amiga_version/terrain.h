#ifndef V6_TERRAIN_H
#define V6_TERRAIN_H
#include <stdint.h>
/* 64-byte stride avoids multiplication in 68000 collision queries. The
 * one-tile border reproduces Map::collide's edge duplication. */
typedef struct {
    uint8_t solid[32][64];
    int directional;
} V6Terrain;
struct V6Room;
void v6_terrain_build(V6Terrain *, const struct V6Room *);
static inline int v6_terrain_solid(const V6Terrain *t, int x, int y)
{
    return (unsigned)(x+1)<42 && (unsigned)(y+1)<32 ? t->solid[y+1][x+1] : 0;
}
#endif
