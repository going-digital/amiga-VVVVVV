#ifndef V6_AUDIO_H
#define V6_AUDIO_H
#include <stdint.h>
/* Exclusive Paula ownership. Caller applies returned register writes in order.
 * Samples contain at least 1024 bytes; periods are 124..1024.
 * tick must be called once per PAL field, even while gameplay is paused.
 * AUD0 request is polled (audio CPU interrupts remain disabled). AUD0/AUD1
 * play the same mono sample in stereo; only AUD0 drives the state machine. */
typedef struct { uint32_t address; unsigned bytes,period,volume; } V6AudioSample;
typedef struct { unsigned reg,value; } V6AudioWrite;
typedef struct { V6AudioWrite writes[16];unsigned count; } V6AudioPlan;
enum { V6_AUDIO_IDLE,V6_AUDIO_STOPPING,V6_AUDIO_PLAYING,V6_AUDIO_DRAINING };
typedef struct {
    V6AudioSample sample;
    uint32_t silence;
    unsigned state,starts,completed,replaced,error,interrupts,wait;
} V6Audio;
/* Numeric range checks do not establish Chip DMA accessibility. */
int v6_audio_init(V6Audio *,uint32_t silence);
int v6_audio_request(V6Audio *,const V6AudioSample *,V6AudioPlan *);
void v6_audio_tick(V6Audio *,int aud0_pending,V6AudioPlan *);
void v6_audio_stop(V6Audio *,V6AudioPlan *);
#endif
