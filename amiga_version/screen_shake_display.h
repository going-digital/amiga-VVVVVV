#ifndef V6_SCREEN_SHAKE_DISPLAY_H
#define V6_SCREEN_SHAKE_DISPLAY_H
#include "screen_shake.h"
/* Shift a dual playfield using DIW clipping and fine scroll. A negative X
 * shift fetches one extra word per row, with modulo -2. Source rings must
 * have one readable guard word; its pixels fall outside the display window.
 * A fourth, constant-one plane makes PF2 opaque inside DIW, so COLOR00 can
 * remain black outside DIW even when all scene colours flash grey.
 * During flash, only the constant mask plane is displayed (one plane).
 * Mask is at least 9602 bytes of 0xffff words. Inactive Chip list only.
 * Caller sets colours, sprites and foreground priority. Needs 64 words.
 * Returns 0 without mutation for invalid input. */
#define V6_SHAKE_MASK_BYTES 9602
#define V6_SHAKE_DISPLAY_WORDS 64
unsigned v6_screen_shake_display(uint16_t *,const V6ScreenShakePlan *,
    uint32_t fg,uint32_t bg,uint32_t mask,unsigned fo,unsigned bo,int flash);
/* Same translated scene with the ordinary 48-row dialogue strip. The strip
 * shares fine scroll and vertical translation; flash covers it too. Caption
 * needs one readable guard word for a negative-X fetch. Needs 128 words. */
#define V6_SHAKE_CAPTION_WORDS 128
unsigned v6_screen_shake_caption(uint16_t *,const V6ScreenShakePlan *,
    uint32_t fg,uint32_t bg,uint32_t mask,unsigned fo,unsigned bo,int flash,
    uint32_t caption,unsigned tint,unsigned c1,unsigned c3);
#endif
