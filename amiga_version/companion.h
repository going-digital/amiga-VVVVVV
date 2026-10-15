#ifndef V6_COMPANION_H
#define V6_COMPANION_H
#include "player.h"
#include "animation.h"
/* Source AI 10/1 following in bounded static rooms; yellow has the AI 1
 * leftward acceleration restraint in Energize (110,105). No tower
 * companion, harm, gravity-line interaction or other crew AI is synthesized. */
typedef struct {
    V6Player body;
    V6PlayerMotion motion;
    V6CollisionAnimation animation;
    int visible,following,mood,frame;
    unsigned spawns,steps,follow_steps;
} V6Companion;
void v6_companion_init(V6Companion *);
void v6_companion_idle(V6Companion *,int visible);
/* Map::spawncompanion case 9; the player has already entered the destination. */
void v6_companion_enter(V6Companion *,int companion,int tower,int room_x,const V6Player *);
/* Execute before player physics: the source entity loop visits crew first. */
void v6_companion_step(V6Companion *,const V6Player *,const V6Room *,int death);
/* Source type-16 idle spawn and Map companion 7 roof entry. */
void v6_station_companion_idle(V6Companion *,int visible);
void v6_station_companion_enter(V6Companion *,int companion,int room_x,int room_y,const V6Player *);
/* Station entry uses AI 1; only Energize applies its x<155 restraint.
 * This suppresses acceleration, preserving source inertia and direction. */
void v6_station_companion_step(V6Companion *,const V6Player *,const V6Room *,
    int death,int room_x,int room_y);
/* Exact one-step physics memo for immutable static rooms. Reset after room or
 * tile changes. Animation and AI still execute. Collision blocks bypass it; non-solid activities may change safely. */
typedef struct {int32_t body[10],ax,pending_y;const uint16_t *tiles;const V6Terrain *terrain;
    int tileset,extra_row;unsigned valid;int32_t after[10],pending_after;} V6CompanionRest;
void v6_companion_rest_reset(V6CompanionRest *);
void v6_station_companion_step_rest(V6Companion *,const V6Player *,const V6Room *,
    int death,int room_x,int room_y,V6CompanionRest *);
/* Prime from a copy, without advancing gameplay/animation/counters. Each entry
 * records an exact zero-acceleration transition; changed live inputs miss. */
void v6_companion_rest_prime(V6CompanionRest *,unsigned,const V6Companion *,const V6Room *);
void v6_companion_rest_prime_motion(V6CompanionRest *,unsigned,const V6Companion *,const V6Room *,int32_t ax);
void v6_station_companion_step_memo(V6Companion *,const V6Player *,const V6Room *,
    int death,int room_x,int room_y,V6CompanionRest *,unsigned);
#endif
