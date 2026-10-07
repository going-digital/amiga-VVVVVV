#ifndef V6_COMPANION_H
#define V6_COMPANION_H
#include "player.h"
#include "animation.h"
/* Vermilion only: source AI 10 and AI 1 subset in the two resident hallways.
 * The special AI 1 restraint in room 110,105 is outside this route. No tower
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
#endif
