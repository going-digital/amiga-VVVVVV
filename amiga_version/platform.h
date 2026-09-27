#ifndef V6_PLATFORM_H
#define V6_PLATFORM_H
#include "enemy.h"
/* Ordinary 32x8 platforms, bounce behaviours 0..3, integer speeds -16..16.
 * Uses the bounded movement state shared with enemies, but rule 2 ignores
 * collision blocks (including other platforms and directional barriers).
 * Player carrying/crushing and platform rendering are separate operations. */
typedef V6Enemy V6Platform;
int v6_platform_init(V6Platform *, int x, int y, int behavior, int speed,
                     int x1, int y1, int x2, int y2);
/* Caller must supply the platform's block at its current origin. Preserve
 * entity order at the caller; this updates one platform and its block. */
void v6_platform_step(V6Platform *, const V6Room *, V6Block *, unsigned count);
/* First BLOCK contact, then first horizontal platform at that origin, as in
 * checkplatform/hplatformat. Supports this API's behaviours 0..3 only.
 * Returns velocity in integer pixels/tick, or -1000 for no eligible platform.
 * This selects a transport velocity; it does not move the player. */
int v6_platform_contact_speed(const V6Player *, const V6Block *, unsigned,
                               const V6Platform *, unsigned, int roof);
#endif
