/* Entity.cpp checkactivity/disableblock and Input.cpp interaction ordering.
 * Copyright Terry Cavanagh; see ../LICENSE.md. */
#include "activity.h"
int v6_activity_find(const V6Block *blocks,unsigned count,const V6Player *p)
{
    unsigned i;int x,y;
    if(!p || (!blocks && count))return -1;
    x=p->x+6;y=p->y+2;
    for(i=0;i<count;++i){const V6Block *b=&blocks[i];
        if(b->type==V6_ACTIVITY && b->w>0 && b->h>0 &&
           x<b->x+b->w && x+12>b->x && y<b->y+b->h && y+21>b->y)return (int)i;
    }
    return -1;
}
V6ActivityResult v6_activity_input(V6Block *blocks,unsigned count,int active,
    const V6Player *p,const V6ActivitySignals *s)
{
    V6ActivityResult out={V6_INTERACT_NONE,0,-1,-1};
    int stationary;
    if(!p || !s || (!blocks && count) || !s->pressed || !s->control ||
       s->dying || s->life>5 || s->script_running)return out;
    stationary=p->vx>-33554432 && p->vx<33554432 &&
        p->vy>-16777216 && p->vy<16777216;
    if(s->teleporter_ready){out.consumed=1;
        if(stationary)out.action=V6_INTERACT_TELEPORTER;
    }else if(active>=0 && (unsigned)active<count){
        /* Input.cpp trusts the retained index, without rechecking its type,
         * rectangle or overlap until the next checkactivity call. */
        out.consumed=1;
        if(stationary){out.action=V6_INTERACT_ACTIVITY;out.index=active;
            out.script=blocks[active].trigger;blocks[active].w=blocks[active].h=0;}
    }
    return out;
}
