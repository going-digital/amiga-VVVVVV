#ifndef V6_TELEPORTER_DRAW_H
#define V6_TELEPORTER_DRAW_H
#include <stdint.h>
#define V6_TELEPORTER_DMA_WORDS 196
#define V6_TELEPORTER_CHANNELS 6
/* Six 16x96 unattached sprites. Source frames are 96 rows of six words.
 * Palette index 1 is the dark base, 2 is the tint; zero is transparent.
 * Caller reserves six consecutive hardware channels with matching pair
 * palettes. DMA must be inactive Chip memory. No registers are touched.
 * x/y are screen coordinates; clipping follows the gameplay strip y=16..215.
 * Invalid input leaves DMA unchanged; fully clipped input emits zero heads. */
int v6_teleporter_draw(uint16_t *dma,const uint16_t base[96][6],
    const uint16_t mask[96][6],int x,int y);
#endif
