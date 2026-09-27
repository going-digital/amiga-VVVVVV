/* Adapted from Entity.cpp behaviours 14/15 and Ent.cpp outside. */
#include "platform_gate.h"
static int gate_outside(V6Platform *p)
{
    if(p->x<p->x1) {p->x=p->x1;return 1;}
    if(p->y<p->y1) {p->y=p->y1;return 1;}
    if(p->x+p->w>p->x2) {p->x=p->x2-p->w;return 1;}
    if(p->y+p->h>p->y2) {p->y=p->y2-p->h;return 1;}
    return 0;
}
int v6_platform_gate_behavior(V6Platform *p,const V6Disappearing *gates,const int *x,unsigned count)
{
    unsigned i;
    if(p->behavior!=14 && p->behavior!=15) return 0;
    if(p->state==0) {
        int target=p->x+(p->behavior==14?-32:32);
        for(i=0;i<count;++i) if(gates[i].state==3 && x[i]==target) {
            /* The source recursively executes state 3 for each match. No
             * movement occurs in that recursion, so duplicate matches agree. */
            p->vx=p->behavior==14?-p->speed:p->speed;
            p->onwall=2;p->state=1;
        }
    } else if(p->state==1) {
        if(gate_outside(p)) p->state=p->onwall;
    } else if(p->state==2 || p->state==3) {
        int velocity=p->state==2?-p->speed:p->speed;
        p->vx=p->behavior==14?-velocity:velocity;
        p->onwall=p->state==2?3:2;p->state=1;
    }
    return 1;
}
