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
/* Initialize a waiting platform and execute its creation-time behaviour.
 * Invalid kind/speed/geometry leaves the destination unchanged. */
int v6_platform_gate_init(V6Platform *,int x,int y,int kind,int speed,
    int x1,int y1,int x2,int y2,const V6Disappearing *,const int *gate_x,unsigned gates);
/* Mixed ordinary/waiting-platform transport. Gate states are a snapshot of
 * the source entity pass at this point; caller owns their later updates.
 * Preserves reverse-order, velocity-selected passes (including zero speed),
 * block relocation, vertical push and life-timer-gated horizontal carrying. */
void v6_platform_gate_transport(V6Player *,const V6Room *,V6Platform *,unsigned,
    V6Block *,unsigned,unsigned flags,int life_timer,V6PlatformPush *,
    const V6Disappearing *,const int *gate_x,unsigned gates);
#endif
