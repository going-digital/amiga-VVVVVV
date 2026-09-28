#ifndef V6_TOWER_DRAW_H
#define V6_TOWER_DRAW_H
#include "tower_stream.h"
#define V6_TOWER_PLANE_BYTES 10240
#define V6_TOWER_RING_BYTES 20480
/* Separate validity per display buffer; reset after stream/atlas changes.
 * Tile atlas is count entries of 16 bytes: eight rows of plane 0, then plane 1.
 * Caller owns an inactive 320x256 two-plane ring. No DMA registers are touched. */
typedef struct { uint32_t valid; int16_t tags[32]; } V6TowerDraw;
void v6_tower_draw_reset(V6TowerDraw *);
/* Validate all 40 tile IDs before writing one 8-pixel-high logical row. */
int v6_tower_draw_row(uint8_t *ring,int row,const uint16_t *tiles,
                      const uint8_t *atlas,unsigned count);
/* Populate 31 consecutive rows (240 pixels plus fine-scroll coverage).
 * Returns 1 on success. On failure, do not publish this buffer: previously
 * completed rows may have changed. Counters report completed work, optionally.
 * No camera policy, Copper wrap or parallax is implied by this helper. */
int v6_tower_draw_prepare(V6TowerDraw *,uint8_t *ring,V6TowerStream *,int top_row,
    const uint8_t *atlas,unsigned count,unsigned *decoded,unsigned *drawn);
/* Same cache/window policy, for a one-plane ring and 8-byte-per-tile atlas. */
int v6_tower_draw_mono_prepare(V6TowerDraw *,uint8_t *,V6TowerStream *,int,
    const uint8_t *,unsigned,unsigned *);
#endif
