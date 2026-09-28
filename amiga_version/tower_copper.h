#ifndef V6_TOWER_COPPER_H
#define V6_TOWER_COPPER_H
#include <stdint.h>
/* Pointer-only Copper segment for a 320x240 PAL viewport beginning at line 52.
 * Caller configures two planes, zero modulo, DDF 0x38..0xd0 and DIW separately.
 * Ring is 320x256, two non-interleaved planes, 10240 bytes each.
 * Segment waits at line 44, sets initial pointers, optionally resets pointers
 * after the last fetched ring line, and ends with the standard Copper stop.
 * Must be built in an inactive list and published safely by the caller.
 * Caller must supply DMA-accessible Chip RAM; numeric range checks alone
 * do not establish that an address is usable on the target machine.
 * Addresses are even 24-bit bus addresses. Returns word count or 0; invalid
 * arguments leave output unchanged. A 24-word output buffer is required. */
#define V6_TOWER_COPPER_WORDS 24
unsigned v6_tower_copper(uint16_t *out,uint32_t ring,unsigned pixel_offset);
#endif
