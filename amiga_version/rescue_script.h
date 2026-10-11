#ifndef V6_RESCUE_SCRIPT_H
#define V6_RESCUE_SCRIPT_H
#include "hallway_crew.h"
#include "station_trigger.h"
#define V6_RESCUE_MAX_LINES 4
enum {
    V6_R_IF_SKIP,V6_R_BARS,V6_R_FLOOR,V6_R_MOOD,V6_R_WAIT_BARS,
    V6_R_RESCUED,V6_R_CUE,V6_R_TEXT,V6_R_POSITION,V6_R_SHOW,V6_R_HIDE,
    V6_R_FADE,V6_R_WAIT_FADE,V6_R_DELAY,V6_R_COMPANION,V6_R_FOLLOW,V6_R_TILE
};
typedef struct { unsigned index,speaker,count; const char *lines[V6_RESCUE_MAX_LINES]; } V6RescueSpeech;
typedef struct { unsigned op; int value; const V6RescueSpeech *speech; } V6RescueOp;
typedef struct { const V6RescueOp *ops; unsigned count; } V6RescueProgram;
typedef struct { int bars_ready,fade_ready,onroof,advance; } V6RescueSignals;
/* Renderer owns animation readiness; advance is a released/pressed edge.
 * Programs, speech descriptors and strings must outlive the runner.
 * Cue and flip counters are requests for platform consumers, not audio/DMA. */
typedef struct {
    const V6RescueProgram *normal,*skip,*program;
    const V6RescueSpeech *draft,*speech;
    unsigned pc,active,error,delay,waiting,bars,control,mood,following;
    unsigned skip_enabled,ui_serial,cues,flips;
    int fade,position,cue_speaker;
    int tile;unsigned tile_serial; /* Absolute crew tile request; apply on serial change. */
} V6RescueScript;
int v6_rescue_start(V6RescueScript *,const V6RescueProgram *,const V6RescueProgram *,int skip);
/* Bounded program steps; wait commands retain their PC until ready. */
void v6_rescue_tick(V6RescueScript *,V6HallwayStory *,const V6RescueSignals *);
/* Same runner/waits, directed only at yellow story fields. Presentation uses
 * the caller's crew colour; speech speaker 0 is crew, 1 is player. Yellow's
 * early follow/tile commands do not synthesize a player gravity flip. */
void v6_station_rescue_tick(V6RescueScript *,V6StationStory *,const V6RescueSignals *);
#endif
