#include "hallway_trigger.h"
void v6_hallway_trigger_init(V6HallwayTrigger *t)
{
    t->active=t->pending=0;t->requests=0;
}
void v6_hallway_trigger_enter(V6HallwayTrigger *t,int x,int y,const V6HallwayStory *s)
{
    t->active=v6_hallway_crew_visible(x,y,s);
}
int v6_hallway_trigger_step(V6HallwayTrigger *t,V6HallwayStory *s,const V6Player *p)
{
    if(!t->active || t->pending || !s || !p) return 0;
    /* Rect (208,0,32,240), player rect (x+6,y+2,12,21). Algebraically
     * equivalent strict intersection, avoiding coordinate-add overflow. */
    if(p->x<=190 || p->x>=234 || p->y<=-23 || p->y>=238) return 0;
    t->active=0;
    if(s->rescue_triggered) return 0;
    s->rescue_triggered=1;t->pending=V6_SCRIPT_RESCUE_RED;++t->requests;
    return 1;
}
int v6_hallway_trigger_take(V6HallwayTrigger *t)
{
    int request=t->pending;t->pending=V6_SCRIPT_NONE;return request;
}
