#ifndef V6_SFX_MIXER_H
#define V6_SFX_MIXER_H
#include <stddef.h>
#include <stdint.h>
/* Four one-shot voices, signed 8-bit PCM at one common Paula sample period.
 * Samples are caller-owned and must outlive playback. Output goes to a caller
 * buffer; the future DMA streamer owns Chip accessibility and stereo routing.
 * Constant 1/4 gain reserves headroom for all voices; division truncates toward
 * zero. Voices advance even when their sample is zero. No looping/allocation. */
#define V6_SFX_VOICES 4
typedef struct { const uint8_t *pcm;size_t bytes,position; } V6SfxVoice;
typedef struct {
    V6SfxVoice voices[V6_SFX_VOICES];
    /* completed counts rendered source tails, not drained hardware buffers. */
    unsigned starts,completed,dropped;
} V6SfxMixer;
void v6_sfx_init(V6SfxMixer *);
/* Lowest free voice, matching Music.cpp's allocation order. Rejects empty/NULL
 * input without mutation. Busy rejection increments dropped; voices are kept. */
int v6_sfx_play(V6SfxMixer *,const uint8_t *,size_t bytes);
/* Produces exactly count bytes, including silence after the last voice ends.
 * Invalid arguments/voice state retain both mixer and output. A zero-size call
 * is a no-op and may use NULL output. Output must not alias input/mixer storage. */
int v6_sfx_render(V6SfxMixer *,uint8_t *output,size_t count);
#endif
