#ifndef V6_ANIMATION_H
#define V6_ANIMATION_H
#include "player.h"
typedef struct { int delay, walk; } V6CollisionAnimation;
int v6_collision_frame(V6CollisionAnimation *, const V6Player *, int visual_ground, int visual_roof, int death);
#endif
