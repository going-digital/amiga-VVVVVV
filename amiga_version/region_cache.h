#ifndef V6_REGION_CACHE_H
#define V6_REGION_CACHE_H
#include <stdint.h>
#define V6_REGION_BYTES 12288
#define V6_REGION_ROOMS 2
#define V6_REGION_SLOTS 2
typedef struct {
    uint16_t id,x,y,tileset,tile_count,pair_words,display_bytes;
    const uint16_t *tiles,*palette,*offsets,*pairs;
    const uint8_t *display;
} V6RegionRoom;
typedef struct {
    uint16_t data[V6_REGION_BYTES/2];
    V6RegionRoom rooms[V6_REGION_ROOMS];
    unsigned valid,region,count,used,failure;
} V6RegionSlot;
typedef struct {
    V6RegionSlot slots[V6_REGION_SLOTS];
    unsigned active,clock,hits,misses,reads,errors;
} V6RegionCache;
/* Reader runs only on misses. It must bound all writes to capacity, reject
 * oversized files and report an exact length. Caller owns OS/DMA suspension. */
typedef int (*V6RegionRead)(void *,unsigned,void *,unsigned,unsigned *);
void v6_region_init(V6RegionCache *);
/* Current slot stays pinned until the candidate is completely validated.
 * A failed miss may evict the other slot but never changes the active room.
 * Views live until their slot is evicted; always request before using one. */
const V6RegionRoom *v6_region_get(V6RegionCache *,unsigned region,unsigned room,
                               V6RegionRead,void *);
#endif
