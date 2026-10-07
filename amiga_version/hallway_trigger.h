#ifndef V6_HALLWAY_TRIGGER_H
#define V6_HALLWAY_TRIGGER_H
#include "hallway_crew.h"
#include "player.h"
enum { V6_SCRIPT_NONE, V6_SCRIPT_RESCUE_RED };
/* One retained script request; the consumer must present/execute it. Entry
 * rearms from campaign flags, without discarding an unconsumed request. */
typedef struct { int active, pending; unsigned requests; } V6HallwayTrigger;
void v6_hallway_trigger_init(V6HallwayTrigger *);
void v6_hallway_trigger_enter(V6HallwayTrigger *,int x,int y,const V6HallwayStory *);
/* Source trigger 36: intersect the player's 12x21 collision box, set flag 8,
 * remove the trigger, and request rescuered once. Does not mark red rescued
 * or change companion; those are script commands, not trigger side effects. */
int v6_hallway_trigger_step(V6HallwayTrigger *,V6HallwayStory *,const V6Player *);
int v6_hallway_trigger_take(V6HallwayTrigger *);
#endif
