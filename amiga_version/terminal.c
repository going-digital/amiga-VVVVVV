/* Entity.cpp terminal creation, rule-3 contact and terminal logic.
 * Copyright Terry Cavanagh; see ../LICENSE.md. */
#include "terminal.h"
void v6_terminal_init(V6Terminal *t,int x,int y,int offset,int parameter,int highlight)
{
    if(!t)return;
    t->x=x;t->y=y;t->tile=16+offset;t->parameter=parameter;
    t->state=t->active=0;t->onentity=highlight?1:0;
}
void v6_terminal_contact(V6Terminal *t,const V6Player *p)
{
    if(t && p && t->onentity>0 && v6_player_overlaps(p,t->x,t->y,16,16))t->state=t->onentity;
}
unsigned v6_terminal_tick(V6Terminal *t)
{
    if(!t || t->state!=1)return 0;
    t->active=1;t->onentity=0;t->state=0;return 1;
}
