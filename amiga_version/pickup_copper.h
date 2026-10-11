#ifndef V6_PICKUP_COPPER_H
#define V6_PICKUP_COPPER_H
#include <stdint.h>
/* Pointer/format segment for the source-positioned pickup and sliding bars.
 * 5-plane dual playfield only inside overlay strips: FG uses planes 1/3/5,
 * BG retains plane 2 and plane 4 reads an all-zero 3040-byte Chip bitmap.
 * Normal 3-plane format and sprite priorities are restored between strips.
 * Requires 176 words; invalid arguments leave output unchanged. */
#define V6_PICKUP_COPPER_WORDS 176
unsigned v6_pickup_copper(uint16_t *,uint32_t fg,uint32_t bg,unsigned fo,unsigned bo,
    uint32_t bank,uint32_t zero,int text,unsigned bars);
#endif
