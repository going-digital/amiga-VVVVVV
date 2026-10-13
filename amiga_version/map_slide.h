#ifndef V6_MAP_SLIDE_H
#define V6_MAP_SLIDE_H
#include <stdint.h>
/* Bounded stationary resident room: foreground camera zero; background ring
 * offset and gameplay registers supplied by caller, sprite DMA clipped by caller at the menu boundary.
 * Source menu rows 0 and 1 are black, allowing palette installation before
 * the title begins at row 2. Only offsets 1..239; endpoints use normal lists.
 * Inactive Chip list required, 160 words available. */
#define V6_MAP_SLIDE_WORDS 160
unsigned v6_map_slide_copper(uint16_t *,uint32_t fg,uint32_t bg,
    unsigned background_offset,uint32_t map,const uint16_t palette[32],uint32_t blank,uint32_t cursor,unsigned offset);
/* Clip a source sprite DMA block to the gameplay band (physical start 52).
 * Caller supplies a valid un-attached, <=32-row block in an inactive bank. */
void v6_map_slide_clip(uint16_t sprite[68],unsigned offset);
/* Preserve monochrome colour index when moving an actor to a new channel. */
void v6_map_slide_channel(uint16_t sprite[68],unsigned channel);
/* 12x9 map cursor, full 240-row menu viewport (game actor helper uses 216). */
unsigned v6_map_slide_cursor(uint16_t sprite[68],const uint32_t rows[32],unsigned x,unsigned y);
#endif
