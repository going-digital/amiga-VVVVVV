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

/* Three-plane dual playfield: foreground goes to BPL1/BPL3, background BPL2.
 * Foreground ring is 20480 bytes; background ring is 10240 bytes. Both use
 * independent 0..255 pixel offsets. Caller sets BPLCON0=0x3600, zero modulos,
 * foreground priority and the same PAL viewport/DDF as above. Needs 34 words.
 * Invalid arguments leave output unchanged. Same inactive-list/Chip RAM rules. */
#define V6_TOWER_DUAL_COPPER_WORDS 34
unsigned v6_tower_dual_copper(uint16_t *out,uint32_t foreground,uint32_t background,
    unsigned foreground_offset,unsigned background_offset);

#endif
