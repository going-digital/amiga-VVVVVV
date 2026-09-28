#ifndef V6_TOWER_COMPOSE_H
#define V6_TOWER_COMPOSE_H
#include <stdint.h>
/* Full-viewport baseline for two-plane software parallax. Each source is a
 * 320x256 planar ring; opacity is a 320x256 one-plane ring, aligned to fg.
 * One mask bit selects foreground, zero selects background (including black).
 * Output is 320x240, two separate 9600-byte planes, and must not overlap inputs.
 * Offsets are 0..255. Returns 0 without writing for invalid offsets.
 * This has no DMA scheduling or cache policy; measure before native adoption. */
int v6_tower_compose(uint8_t *out,const uint8_t *fg,const uint8_t *bg,
    const uint8_t *opacity,unsigned fg_offset,unsigned bg_offset);
/* Build one mask-ring tile row from the converter's 8-byte-per-tile masks.
 * Tile zero masks are empty, matching drawtowermap's skip of tile zero.
 * Validates all IDs before writing. */
int v6_tower_mask_row(uint8_t *ring,int row,const uint16_t *tiles,
    const uint8_t *masks,unsigned count);
#endif
