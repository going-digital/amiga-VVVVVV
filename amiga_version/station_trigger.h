#ifndef V6_STATION_TRIGGER_H
#define V6_STATION_TRIGGER_H
#include "player.h"
/* Station 2's yellow rescue flags are independent of Seeing Red's flags.
 * Caller owns campaign persistence; this candidate room is not admitted by
 * the native renderer/save bank yet. Companion is the source integer ID. */
typedef struct {
    int time_trial,translator_exploring,companion,rescue_triggered,yellow_rescued;
} V6StationStory;
enum { V6_STATION_SCRIPT_NONE,V6_STATION_SCRIPT_RESCUE_YELLOW };
typedef struct { int active,pending;unsigned requests; } V6StationTrigger;
int v6_station_crew_visible(int room_x,int room_y,const V6StationStory *);
void v6_station_trigger_init(V6StationTrigger *);
/* Room entry rearms from source flags without discarding a retained request. */
void v6_station_trigger_enter(V6StationTrigger *,int room_x,int room_y,const V6StationStory *);
/* Source trigger 34: strict player collision-box intersection with (0,0,140,240),
 * remove the trigger, set flag 10 and retain a rescueyellow request once.
 * Does not mark yellow rescued or change companion; those are script actions. */
int v6_station_trigger_step(V6StationTrigger *,V6StationStory *,const V6Player *);
int v6_station_trigger_take(V6StationTrigger *);

/* Original trigger 30, Game.cpp flag 4; caller owns its persistent bit. */
typedef struct {int active,pending;unsigned requests;} V6FirstStepsTrigger;
void v6_firststeps_enter(V6FirstStepsTrigger *,int x,int y,int nocutscenes);
void v6_firststeps_contact(V6FirstStepsTrigger *,const V6Player *);
int v6_firststeps_dispatch(V6FirstStepsTrigger *,unsigned seen);

/* Original Conundrum triggers 21/22; persistent bits 1/2 map flags 2/3.
 * Timed hint runs alongside physics, without consuming flip or locking control. */
typedef struct {unsigned active,pending,contacts,removed,visible,timer,level,mode,hints;} V6ConundrumTrigger;
void v6_conundrum_enter(V6ConundrumTrigger *,int x,int y,int nocutscenes);
void v6_conundrum_contact(V6ConundrumTrigger *,const V6Player *);
unsigned v6_conundrum_dispatch(V6ConundrumTrigger *,uint16_t *flags);
void v6_conundrum_tick(V6ConundrumTrigger *);
#endif
