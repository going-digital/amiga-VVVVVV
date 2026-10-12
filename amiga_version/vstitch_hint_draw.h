#ifndef V6_VSTITCH_HINT_DRAW_H
#define V6_VSTITCH_HINT_DRAW_H
#include <stdint.h>
enum { V6_HINT_TOP=155,V6_HINT_HEIGHT=33,V6_HINT_BYTES=40*V6_HINT_HEIGHT };
/* Source English ENTER hint, balanced two-line wrapping, 200x33 box at x=60.
 * Rows preserve source alpha border tiles 40..47 and one-pixel line spacing.
 * Invalid row leaves outputs unchanged. Font is the original 8-pixel font. */
int v6_vstitch_hint_row(unsigned,uint8_t mask[40],uint8_t ink[40],
    const uint8_t font[128][8],const uint8_t border[8][8]);
/* Packed OCS fill (high word) and ink (low word), using source grey 174,
 * r/6 fill and interpolation over the 34ms fixed timestep. Invalid levels
 * return zero. Elapsed is clamped; no floating point or target division. */
uint32_t v6_vstitch_hint_colours(unsigned previous,unsigned level,unsigned elapsed);
/* Five-plane strip preserves live foreground/background outside the box.
 * The bank has three 3040-byte planes (existing pickup stride); zero supplies
 * the otherwise unused second background plane. Needs 100 Copper words. */
#define V6_HINT_COPPER_WORDS 100
unsigned v6_vstitch_hint_copper(uint16_t *,uint32_t fg,uint32_t bg,unsigned fo,unsigned bo,
    uint32_t bank,uint32_t zero,unsigned fill,unsigned ink);
#endif
