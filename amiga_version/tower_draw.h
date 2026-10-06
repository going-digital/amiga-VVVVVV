#ifndef V6_TOWER_DRAW_H
#define V6_TOWER_DRAW_H
#include "tower_stream.h"
#define V6_TOWER_PLANE_BYTES 10240
#define V6_TOWER_RING_BYTES 20480
/* Separate validity per display buffer; reset after stream/atlas changes.
 * Tile atlas is count entries of 16 bytes: eight rows of plane 0, then plane 1.
 * Caller owns an inactive 320x256 two-plane ring. No DMA registers are touched. */
typedef struct {
    uint32_t valid;
    int16_t tags[32],top;
    uint16_t complete;
} V6TowerDraw;
/* A successful prepare certifies a contiguous window. A subsequent prepare
 * need only inspect rows outside its overlap. Peer-row copies may populate
 * the new window, but must not modify rows in the overlap. Reset after any
 * other external ring/tag writes or changes to the stream/atlas. */
static inline void v6_tower_draw_span(const V6TowerDraw *d,int top,int *first,int *end)
{
    *first=top;*end=top+31;
    if(!d->complete) return;
    if(top>=d->top && top<=d->top+31) *first=d->top+31;
    else if(top<d->top && top+31>=d->top) *end=d->top;
}
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
/* Offline paired columns: offsets[a*32+b] indexes an atlas of host-endian
 * uint16 words. Each pair has eight words per plane, left tile in high byte.
 * Ring must be word-aligned; planes 1/2 and count 1..32. Unknown pairs use
 * offset 0xffff and fail without writing their row. Atlas/data are immutable. */
int v6_tower_draw_pair_prepare(V6TowerDraw *,uint8_t *,V6TowerStream *,int,
    const uint16_t offsets[1024],const uint16_t *,unsigned atlas_words,
    unsigned count,unsigned planes,unsigned *drawn);
/* Validate every source row before hardware takeover. The verified path may
 * omit repeated ID/offset checks only for these same immutable map/table/
 * atlas bounds. Revalidate after any change, including reopening the stream. */
int v6_tower_pairs_validate(V6TowerStream *,const uint16_t offsets[1024],
    unsigned atlas_words,unsigned count,unsigned planes);
int v6_tower_draw_pair_prepare_verified(V6TowerDraw *,uint8_t *,V6TowerStream *,int,
    const uint16_t offsets[1024],const uint16_t *,unsigned atlas_words,
    unsigned count,unsigned planes,unsigned *drawn);
/* Checked, resumable cold fills. At most budget missing rows are written;
 * returns 2 while incomplete, 1 when publishable, 0 on failure. Keep top/map/
 * atlas fixed while resuming. Incomplete buffers must never be published. */
int v6_tower_draw_pair_prepare_budget(V6TowerDraw *,uint8_t *,V6TowerStream *,int,
    const uint16_t offsets[1024],const uint16_t *,unsigned atlas_words,
    unsigned count,unsigned planes,unsigned *drawn,unsigned budget);
#endif
