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
void v6_firststeps_enter(V6FirstStepsTrigger *t,int x,int y,int nocutscenes)
{t->active=x==115 && y==105 && !nocutscenes;t->pending=0;}
void v6_firststeps_contact(V6FirstStepsTrigger *t,const V6Player *p)
{
    if(!t->active || t->pending || p->x<=54 || p->x>=386 || p->y<=-23 || p->y>=238)return;
    t->pending=1;
}
int v6_firststeps_dispatch(V6FirstStepsTrigger *t,unsigned seen)
{
    if(!t->pending)return 0;
    t->pending=t->active=0;
    if(seen)return 0;
    ++t->requests;return 1;
}

/* Spacestation2 rn(52,41); Game.cpp states 21/22; Textbox.cpp timed fade. */
void v6_conundrum_enter(V6ConundrumTrigger *s,int x,int y,int nocutscenes)
{s->active=x==114 && y==105 && !nocutscenes?3:0;s->pending=0;}
void v6_conundrum_contact(V6ConundrumTrigger *s,const V6Player *p)
{
    unsigned hit=0;
    if(p->y<=-23 || p->y>=238)return;
    if(p->x>262 && p->x<594)hit|=1; /* (280,0,320,240), trigger 21 */
    if(p->x>-8 && p->x<64)hit|=2;   /* (10,0,60,240), trigger 22 */
    hit&=s->active&~s->pending;if(hit){s->pending|=hit;++s->contacts;}
}
unsigned v6_conundrum_dispatch(V6ConundrumTrigger *s,uint16_t *flags)
{
    unsigned hit=s->pending,fresh=0;s->active&=~hit;s->pending=0;
    if(hit&1){++s->removed;if(!(*flags&2)){*flags|=2;if(s->visible)s->mode=2;fresh|=1;}}
    if(hit&2){++s->removed;if(!(*flags&4)){*flags|=4;s->visible=1;s->timer=60;
        s->level=5;s->mode=0;++s->hints;fresh|=2;}}
    return fresh;
}
void v6_conundrum_tick(V6ConundrumTrigger *s)
{
    if(!s->visible)return;
    if(!s->mode){if(++s->level>=10){s->level=10;s->mode=1;}}
    else if(s->mode==2 && --s->level<=5){s->level=5;s->visible=0;}
    if(s->timer && !--s->timer)s->mode=2;
}
