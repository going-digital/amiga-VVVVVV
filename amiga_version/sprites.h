#ifndef V6_SPRITES_H
#define V6_SPRITES_H
#include <stdint.h>
#define V6_SPRITE_CHANNELS 8
#define V6_SPRITE_WORDS 68
/* Add in priority order (player first). One monochrome, 16x32 crop per
 * channel (wide requests consume up to two channels); no attachment or vertical multiplexing. DMA storage must be Chip
 * RAM on target, and only the inactive bank may be changed. */
typedef struct {
    uint16_t *dma;
    uint16_t colours[V6_SPRITE_CHANNELS];
    unsigned count;
} V6Sprites;
enum { V6_SPRITE_CLIPPED=-1, V6_SPRITE_FULL=-2, V6_SPRITE_INVALID=-3 };
void v6_sprites_begin(V6Sprites *batch, uint16_t *dma);
/* Return channel 0..7 or a result above. Clipped/failed requests consume no
 * channel. x/y locate the source 32x32 frame; crop is its first visible column.
 * Coordinates must fit signed 16 bits, crop 0..16, colour RGB12. */
int v6_sprites_add(V6Sprites *batch, const uint32_t rows[32],
                   int x, int y, unsigned crop, unsigned colour);
/* Each pair shares four colours. Even channels use index 1, odd index 3,
 * allowing independent monochrome colours without palette conflicts. */
/* Wide monochrome request: allocate all required channels atomically. Width
 * 1..32, crop+width<=32. Return the first channel; failure changes no DMA data. */
int v6_sprites_add_wide(V6Sprites *, const uint32_t rows[32],
                        int x, int y, unsigned crop, unsigned width, unsigned colour);
/* As above, emitting only height rows (1..32), for short objects. */
int v6_sprites_add_rect(V6Sprites *, const uint32_t rows[32],
                        int x, int y, unsigned crop, unsigned width,
                        unsigned height, unsigned colour);
unsigned v6_sprite_colour_register(unsigned channel);
#endif
