#ifndef V6_SAVE_SUMMARY_H
#define V6_SAVE_SUMMARY_H
#include <stdint.h>
#include "trinkets.h"
/* Source clock: 30 fixed updates per displayed second, including menu ticks.
 * Caller excludes unfocused time/DOS suspension, as in the original loop. */
typedef struct {uint16_t hours,minutes,seconds,frames;} V6SaveClock;
typedef struct {
    V6SaveClock clock;
    int16_t room_x,room_y;
    uint16_t trinkets,crew_mask,exists;
} V6SaveSummary;
void v6_save_clock_init(V6SaveClock *);
/* Invalid state or a saturated 65535-hour clock is rejected unchanged. */
int v6_save_clock_tick(V6SaveClock *,int countdown);
/* Original English M:SS / H:MM:SS (no centiseconds), capacity >=12. */
int v6_save_clock_text(char out[12],const V6SaveClock *);
/* Snapshot at the Save action, before the end-of-tick clock update.
 * Caller supplies actual six crew flags; incomplete story flags cannot infer
 * them. Normal 20x20 world and canonical 100-bit collection only. */
int v6_save_summary_capture(V6SaveSummary *,const V6SaveClock *,int,int,
    const V6Collect *,unsigned crew_mask);
/* Failed I/O retains the preceding successful summary. Session-only model;
 * current V5 records do not store these fields. */
int v6_save_summary_publish(V6SaveSummary *,const V6SaveSummary *,int success);
#endif
