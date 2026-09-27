#ifndef V6_PLATFORM_GATE_H
#define V6_PLATFORM_GATE_H
#include "platform.h"
#include "disappearing.h"
/* Behaviour update only for platform behaviours 14/15. Caller supplies all
 * disappearing entities in source order and parallel X coordinates. Y does
 * not participate in the source trigger. State 0 waits; initial vx/vy must be
 * zero. Use the ordinary platform bounds, integer speed -16..16 and states
 * 0..3. Run before movement, including at entity creation. Does not move the
 * platform, update blocks or perform player transport. Returns 0 for other
 * behaviours without changing state. */
int v6_platform_gate_behavior(V6Platform *,const V6Disappearing *,const int *x,unsigned count);
#endif
