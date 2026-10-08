#ifndef V6_PAULA_VOICE_H
#define V6_PAULA_VOICE_H
#include "audio.h"
/* One hardware-panned Paula channel. Retains the tested one-shot engine's
 * cooldown, silence reload and two-IRQ drain; every plan touches only this
 * channel. The caller owns Chip samples, channel allocation and OS takeover. */
typedef struct { V6Audio audio;unsigned channel; } V6PaulaVoice;
int v6_paula_init(V6PaulaVoice *,unsigned channel,uint32_t silence);
int v6_paula_request(V6PaulaVoice *,const V6AudioSample *,V6AudioPlan *);
/* Once per PAL field, including gameplay pauses; pending is this channel's IRQ. */
int v6_paula_tick(V6PaulaVoice *,int pending,V6AudioPlan *);
int v6_paula_stop(V6PaulaVoice *,V6AudioPlan *);
#endif
