#ifndef V6_TOWER_STREAM_H
#define V6_TOWER_STREAM_H
#include <stddef.h>
#include <stdint.h>
/* V6TR v1: big-endian magic/version/width/height (10 bytes), then height
 * entries of payload-relative uint32 offset and uint16 packet length.
 * Rows use room_codec packets and decode to exactly 40 tile IDs.
 * Packed data must remain resident and immutable for the stream lifetime. */
typedef struct {
    const uint8_t *data;
    size_t size;
    uint32_t valid;
    uint16_t height;
    int16_t tags[32];
    uint16_t tiles[32][40];
} V6TowerStream;
/* Validate header and every directory span. Failure leaves stream unchanged.
 * Packet contents are checked lazily when read. Supports heights 1..700. */
int v6_tower_open(V6TowerStream *,const uint8_t *,size_t);
/* After successful open: logical row -32768..32767, wrapped positively at map height for lookup.
 * Logical (not wrapped) row selects the cache slot, preserving contiguous
 * windows across map wrap even when height is not a multiple of 32.
 * Returns NULL on invalid row/packet. Sets decoded to 1 only for a successful
 * cache miss (optional pointer). A failed decode never leaves a valid slot.
 * Returned view lasts until another logical row uses that slot or reopen.
 * This is a tile-row cache, not a display ring or camera implementation. */
const uint16_t *v6_tower_row(V6TowerStream *,int row,unsigned *decoded);
#endif
