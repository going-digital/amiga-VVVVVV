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
/* Horizontal transport stage, after platform updates and before normal player
 * physics. pending_y is the retained Entity::newyp, not necessarily player.y.
 * Returns 1 when transport was attempted (including a zero-speed platform).
 * life_timer >= 8 suppresses transport as in Logic.cpp. */
int v6_platform_carry_horizontal(V6Player *, const V6Room *,
                                 const V6Platform *, unsigned, int life_timer, int pending_y);
/* Pending position and render-contact fields used by movingplatformfix. */
typedef struct { int pending_y, visual_ground, visual_roof; } V6PlatformPush;
void v6_platform_push_vertical(V6Platform *, V6Player *, const V6Room *, V6PlatformPush *);
/* Post-physics overlap stage. blocks must be the mutable list viewed by room.
 * Disabled blocks stay disabled until their next platform update. */
void v6_platform_disable_overlaps(const V6Player *, const V6Platform *, unsigned,
                                  V6Block *, unsigned);
enum { V6_PLATFORMS_VERTICAL=1, V6_PLATFORMS_HORIZONTAL=2 };
/* Pre-physics stage, after player input. Platforms must be in original entity
 * order; blocks must be the mutable list referenced by room. Flags are room
 * creation flags, not inferred from current velocities. push.pending_y retains
 * the player's previous pending Y. Skipped passes leave their state untouched.
 * Only ordinary platforms (behaviours 0..3); caller handles complete-stop. */
void v6_platform_transport(V6Player *, const V6Room *, V6Platform *, unsigned,
                            V6Block *, unsigned, unsigned flags, int life_timer,
                            V6PlatformPush *);
#endif
