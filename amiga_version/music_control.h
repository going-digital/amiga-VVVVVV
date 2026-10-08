#ifndef V6_MUSIC_CONTROL_H
#define V6_MUSIC_CONTROL_H
#include <stdint.h>
/* Base 16-track source policy only. No player, samples or DMA ownership.
 * Commands emit ordered adapter operations. Available bits model successful
 * backend starts; the caller must keep this mask accurate. Source control gain
 * is 0..128, not Paula volume. The adapter also applies user-volume scaling.
 * Tick is elapsed game timestep in ms; tracker replay has its own clock.
 * Durations are limited to 60000 ms; timestep to 1000 ms. */
enum {V6_MUSIC_PLAY,V6_MUSIC_NICEPLAY,V6_MUSIC_PAUSE,V6_MUSIC_HALT,
 V6_MUSIC_RESUME,V6_MUSIC_RESUME_FADE,V6_MUSIC_FADE_OUT,V6_MUSIC_FADE_IN,V6_MUSIC_SILENCE};
enum {V6_MUSIC_START=1,V6_MUSIC_STOP_CLOCK,V6_MUSIC_RESUME_CLOCK,V6_MUSIC_GAIN};
typedef struct {int32_t kind,track,value;} V6MusicOp;
typedef struct {int32_t count;V6MusicOp ops[4];} V6MusicPlan;
typedef struct {
 int32_t current,halted_song,queued,nice,quick,safe,fade_in,fade_out,volume;
 int32_t present,paused,available;
 int32_t start,end,duration,elapsed;
} V6MusicControl;
int v6_music_init(V6MusicControl *,unsigned available);
/* Invalid input leaves state and output plan unchanged. PLAY accepts -1 or
 * a base ID; NICEPLAY accepts a base ID. FADE_OUT arg is quick (0/1).
 * RESUME_FADE and FADE_IN arg is duration ms. Other commands ignore arg. */
int v6_music_command(V6MusicControl *,unsigned command,int arg,V6MusicPlan *);
int v6_music_tick(V6MusicControl *,unsigned timestep_ms,V6MusicPlan *);
/* Connect normalized main-map selection to source niceplay. Script/no-change
 * rooms preserve all controller state and emit an empty plan. Invalid inputs
 * preserve both state and plan. See music_area.h for coordinate/flag bounds. */
int v6_music_change_area(V6MusicControl *,int x,int y,int script_running,
    int flip_mode,int time_trial,V6MusicPlan *);
#endif
