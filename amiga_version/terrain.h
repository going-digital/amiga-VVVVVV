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
/* Edit a caller-owned 40x30 tile buffer and rebuild its collision cache.
 * Returns 1 if changed (caller must redraw), 0 if unchanged, -1 for invalid
 * coordinates/format. The buffer must be the one used by the caller's room.
 * Call with a cache already built for the supplied tileset/extra_row. */
int v6_terrain_set_tile(V6Terrain *,uint16_t *tiles,int tileset,int extra_row,
                        int x,int y,uint16_t tile);
static inline int v6_terrain_solid(const V6Terrain *t, int x, int y)
{
    return (unsigned)(x+1)<42 && (unsigned)(y+1)<32 ? t->solid[y+1][x+1] : 0;
}
#endif
