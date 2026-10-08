#ifndef V6_TELEPORTER_COLOUR_H
#define V6_TELEPORTER_COLOUR_H
#include <stdint.h>
/* Graphics::getcol(102), quantized by taking each RGB channel's high nibble.
 * Four independent uniform samples represent fRandom() in [0,1), as r/65536.
 * Caller owns randomness and refresh timing. No floating point is required.
 * noflashing selects the source's fixed (196,196,223) colour without samples.
 * NULL samples also select this fixed colour. */
uint16_t v6_teleporter_flash_colour(const uint16_t samples[4],int noflashing);
#endif
