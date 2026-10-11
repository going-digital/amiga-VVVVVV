#ifndef V6_SCREEN_SHAKE_DMA_H
#define V6_SCREEN_SHAKE_DMA_H
#include "screen_shake.h"
/* Translate an already clipped, unattached sprite in inactive DMA memory.
 * Preserve its pixels, clip to the fixed 320x240 viewport, retain terminator.
 * Caller must reconstruct pristine DMA before translating again. */
int v6_screen_shake_sprite(uint16_t *dma,unsigned words,int x,int y);
#endif
