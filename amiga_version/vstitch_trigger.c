/* Spacestation2.cpp rn(50,43), Game.cpp state 8, Textbox.cpp update.
 * Original source copyright Terry Cavanagh; see ../LICENSE.md. */
#include "vstitch_trigger.h"
void v6_vstitch_trigger_init(V6VStitchTrigger *t)
{
    t->active=t->pending=t->visible=t->timer=t->level=t->mode=0;
    t->contacts=t->hints=0;
}
void v6_vstitch_trigger_enter(V6VStitchTrigger *t,int x,int y,int nocutscenes)
{ t->active=x==112 && y==107 && !nocutscenes; }
int v6_vstitch_trigger_contact(V6VStitchTrigger *t,const V6Player *p)
{
    if(!t->active || t->pending || p->x<=-18 || p->x>=106 ||
       p->y<=-23 || p->y>=110)return 0;
    t->pending=1;++t->contacts;return 1;
}
int v6_vstitch_trigger_dispatch(V6VStitchTrigger *t,int *seen)
{
    if(!t->pending)return 0;
    t->active=0;t->pending=0;
    if(*seen)return 0;
    *seen=1;t->visible=1;t->timer=60;t->level=5;t->mode=0;
    ++t->hints;return 1;
}
void v6_vstitch_hint_tick(V6VStitchTrigger *t)
{
    if(!t->visible)return;
    if(t->mode==0) { if(++t->level>=10){t->level=10;t->mode=1;} }
    else if(t->mode==2 && --t->level<=5){t->level=5;t->visible=0;}
    if(t->timer>0 && !--t->timer)t->mode=2;
}
