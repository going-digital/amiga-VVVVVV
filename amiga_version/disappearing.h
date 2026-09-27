#ifndef V6_DISAPPEARING_H
#define V6_DISAPPEARING_H
#include "blocks.h"
/* Ordinary disappearing-platform lifecycle. The caller owns collision blocks,
 * rendering and scheduling. Collision arms state 1 after the update pass.
 * DISABLE disables every block at the origin; CREATE requests a 32x8 block.
 * Desktop createblock reuses the first disabled slot, or appends if none exist;
 * it must not simply restore the block formerly associated with this platform.
 * The special death-time tile patch in room (111,107) is caller-owned. */
typedef struct { int state,life,walking_frame,on_entity,invisible; } V6Disappearing;
enum { V6_DISAPPEAR_SOUND=1,V6_DISAPPEAR_DISABLE=2,V6_DISAPPEAR_CREATE=4,V6_DISAPPEAR_FULL=8 };
void v6_disappearing_init(V6Disappearing *);
void v6_disappearing_contact(V6Disappearing *,int overlapping);
unsigned v6_disappearing_step(V6Disappearing *);
/* Run during death instead of the normal update; finish collapse and arm
 * recharge. State 4 does not advance until live entity updates resume. */
unsigned v6_disappearing_death(V6Disappearing *);
/* Apply lifecycle and collision-bank changes together. On FULL neither the
 * platform nor the bank changes; provision space or retry the update. Keep
 * V6Room.block_count synchronized with the returned bank count. */
unsigned v6_disappearing_update(V6Disappearing *,int x,int y,V6Block *,
                                unsigned *count,unsigned capacity,int dying);
#endif
