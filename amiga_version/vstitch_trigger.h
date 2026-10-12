#ifndef V6_VSTITCH_TRIGGER_H
#define V6_VSTITCH_TRIGGER_H
#include "player.h"
/* Source trigger 8 and flag 13. Flag persistence belongs to the caller.
 * The hint does not pause physics, consume fire, or change control state. */
typedef struct {
    int active,pending,visible,timer,level,mode;
    unsigned contacts,hints;
} V6VStitchTrigger;
void v6_vstitch_trigger_init(V6VStitchTrigger *);
/* Entry creates the source trigger even if flag 13 is already set. */
void v6_vstitch_trigger_enter(V6VStitchTrigger *,int x,int y,int nocutscenes);
/* Post-physics source trigger collision; dispatch on the next state pass. */
int v6_vstitch_trigger_contact(V6VStitchTrigger *,const V6Player *);
int v6_vstitch_trigger_dispatch(V6VStitchTrigger *,int *seen);
/* Fixed rendering updates textboxes before gameplay. Level is in tenths;
 * the source .5..1 fade takes five updates in either direction. */
void v6_vstitch_hint_tick(V6VStitchTrigger *);
#endif
