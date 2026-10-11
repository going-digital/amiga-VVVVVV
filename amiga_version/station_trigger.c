#include "station_trigger.h"
int v6_station_crew_visible(int x,int y,const V6StationStory *s)
{
    return s && x==111 && y==105 && (!s->time_trial || s->translator_exploring)
        && !s->companion && !s->rescue_triggered && !s->yellow_rescued;
}
void v6_station_trigger_init(V6StationTrigger *t)
{ if(t){t->active=t->pending=0;t->requests=0;} }
void v6_station_trigger_enter(V6StationTrigger *t,int x,int y,const V6StationStory *s)
{ if(t)t->active=v6_station_crew_visible(x,y,s); }
int v6_station_trigger_step(V6StationTrigger *t,V6StationStory *s,const V6Player *p)
{
    if(!t || !t->active || t->pending || !s || !p)return 0;
    /* Player bounds (x+6,y+2,12,21); subtract constants to avoid overflow. */
    if(p->x<=-18 || p->x>=134 || p->y<=-23 || p->y>=238)return 0;
    t->active=0;
    if(s->rescue_triggered)return 0;
    s->rescue_triggered=1;t->pending=V6_STATION_SCRIPT_RESCUE_YELLOW;++t->requests;
    return 1;
}
int v6_station_trigger_take(V6StationTrigger *t)
{
    int request;if(!t)return V6_STATION_SCRIPT_NONE;
    request=t->pending;t->pending=0;return request;
}
