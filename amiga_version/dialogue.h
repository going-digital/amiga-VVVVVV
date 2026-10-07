#ifndef V6_DIALOGUE_H
#define V6_DIALOGUE_H
#include <stdint.h>
#include "rescue_script.h"
#define V6_DIALOGUE_TOP 16
#define V6_DIALOGUE_HEIGHT 48
#define V6_DIALOGUE_PLANE_BYTES (40*V6_DIALOGUE_HEIGHT)
#define V6_DIALOGUE_BYTES (2*V6_DIALOGUE_PLANE_BYTES)
/* Immutable two-plane caption: opaque black (index 1), glyph/border (index 3).
 * Validate the complete speech before writing any byte. Font is 128x8 bytes. */
int v6_dialogue_draw(uint8_t *,const uint8_t font[128][8],const V6RescueSpeech *);
#endif
