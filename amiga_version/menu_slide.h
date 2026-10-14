#ifndef V6_MENU_SLIDE_H
#define V6_MENU_SLIDE_H
#include <stdint.h>
/* Compose the frozen gameplay Copper prefix with a translated 4/5-plane menu.
 * Gameplay's ring wraps and overlay changes above the boundary are retained.
 * Sprite pointers are installed before line 44; caller supplies DMA chains
 * clipped to the gameplay band followed by the translated menu actors. */
#define V6_MENU_SLIDE_WORDS 512
unsigned v6_menu_slide_copper(uint16_t *out,const uint16_t *game,unsigned words,
    uint32_t bitmap,unsigned planes,const uint16_t palette[32],
    const uint32_t sprites[8],unsigned offset);
/* Re-arm menu sprites after the clipped game sprites have reached VSTOP.
 * Data pointers skip the two control words; the Copper writes POS/CTL itself.
 * Menu sprite starts must leave two black rows for these register writes. */
unsigned v6_menu_slide_rearm(uint16_t *,unsigned words,const uint32_t data[8],
    const uint16_t controls[8][2],unsigned offset);
#endif
