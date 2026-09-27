/* Player subset of Entity.cpp::animatehumanoidcollision. */
#include "animation.h"
int v6_collision_frame(V6CollisionAnimation *a, const V6Player *p, int ground, int roof, int death)
{
    int frame=p->dir?0:3;
    --a->delay;
    if (ground>0 || roof>0) {
        if (p->vx) {
            if (a->delay<=1) { a->delay=4; ++a->walk; }
            if (a->walk>=2) a->walk=0;
            frame+=a->walk+1;
        }
        if (roof>0) frame+=6;
    } else frame+=1+(p->gravity?6:0);
    if (death>-1) frame=(p->dir?12:13)+(p->gravity?2:0);
    return frame;
}
