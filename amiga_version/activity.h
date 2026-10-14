#ifndef V6_ACTIVITY_H
#define V6_ACTIVITY_H
#include "player.h"
#include "blocks.h"
/* Activities share source block order. trigger is the caller's script key;
 * only V6_ACTIVITY blocks participate, and activation disables that slot. */
int v6_activity_find(const V6Block *,unsigned,const V6Player *);
typedef struct {
    int pressed,control,dying,life,script_running,teleporter_ready;
} V6ActivitySignals;
enum { V6_INTERACT_NONE,V6_INTERACT_ACTIVITY,V6_INTERACT_TELEPORTER };
typedef struct { unsigned action;int consumed,index,script; } V6ActivityResult;
/* Input uses the activity index retained from the preceding logic update.
 * Moving players consume the interaction edge without activating. Velocities
 * are source-equivalent Q8.24; the caller owns release/press edge detection.
 * Teleporter eligibility precedes activities, matching normal game input. */
V6ActivityResult v6_activity_input(V6Block *,unsigned,int,
                                  const V6Player *,const V6ActivitySignals *);
#endif
