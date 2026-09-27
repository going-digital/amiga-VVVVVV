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

int v6_platform_gate_init(V6Platform *p,int x,int y,int kind,int speed,
    int x1,int y1,int x2,int y2,const V6Disappearing *g,const int *gx,unsigned n)
{
    if(kind!=14 && kind!=15) return 0;
    if(!v6_platform_init(p,x,y,kind==14?2:3,speed,x1,y1,x2,y2)) return 0;
    p->behavior=kind;p->state=p->onwall=p->vx=p->vy=0;
    v6_platform_gate_behavior(p,g,gx,n);
    return 1;
}
static void gate_step(V6Platform *p,const V6Room *r,V6Block *b,unsigned count,
    const V6Disappearing *g,const int *gx,unsigned n)
{
    int x=p->x,y=p->y;
    if(p->behavior!=14 && p->behavior!=15) {v6_platform_step(p,r,b,count);return;}
    v6_blocks_disable_at(b,count,x,y);
    v6_platform_gate_behavior(p,g,gx,n);
    v6_enemy_move(p,r,0,0);
    v6_blocks_move(b,count,x,y,p->x,p->y,p->w,p->h);
}
void v6_platform_gate_transport(V6Player *p,const V6Room *r,V6Platform *a,unsigned count,
    V6Block *b,unsigned bn,unsigned flags,int life,V6PlatformPush *push,
    const V6Disappearing *g,const int *gx,unsigned gn)
{
    unsigned i;
    if(flags&V6_PLATFORMS_VERTICAL) for(i=count;i>0;--i) {
        V6Platform *e=&a[i-1];
        if(e->vx) continue;
        gate_step(e,r,b,bn,g,gx,gn);
        v6_platform_push_vertical(e,p,r,push);
    }
    if(flags&V6_PLATFORMS_HORIZONTAL) {
        for(i=count;i>0;--i) {
            V6Platform *e=&a[i-1];
            if(e->vy) continue;
            gate_step(e,r,b,bn,g,gx,gn);
        }
        v6_platform_carry_horizontal(p,r,a,count,life,push->pending_y);
    }
}
