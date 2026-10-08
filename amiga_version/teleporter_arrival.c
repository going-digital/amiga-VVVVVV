/* Adapted from Game.cpp normal teleporter arrival states 4010..4019.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "teleporter_arrival.h"
void v6_teleporter_arrival_init(V6TeleporterArrival *a)
{
    a->state=a->delay=a->flash=a->shake=a->advance_text=0;a->control=1;a->events=0;
}
int v6_teleporter_arrival_start(V6TeleporterArrival *a)
{
    if(!a || a->state || a->delay)return 0;
    a->state=4010;a->control=0;a->events=0;return 1;
}
int v6_teleporter_arrival_tick(V6TeleporterArrival *a,V6Player *p,V6PlayerMotion *motion,
    int *invisible,V6Teleporter *t,V6TeleporterRegion *r)
{
    if(!a || !p || !motion || !invisible || !t || !r ||
       (a->state && (a->state<4010 || a->state>4019)) || a->delay<0 || a->delay>15 ||
       t->x< -44 || t->x>276 || t->y< -44 || t->y>196)return 0;
    a->events=0;
    if(!a->state)return 1;
    if(a->delay>0)--a->delay;
    if(a->delay)return 1;
    switch(a->state) {
    case 4010:
        ++a->state;a->delay=15;a->flash=5;a->shake=90;a->events=V6_ARRIVAL_FLASH;break;
    case 4011:
        ++a->state;a->flash=5;a->shake=0;a->events=V6_ARRIVAL_TELEPORT;break;
    case 4012:
        ++a->state;a->delay=5;
        p->x=p->old_x=t->x+44;p->y=p->old_y=t->y+44;
        t->tile=2;*invisible=0;p->dir=1;
        p->ay=p->vy=-6*V6_ONE;motion->ax=p->vx=6*V6_ONE;
        break;
    case 4013:case 4014:
        ++a->state;p->x+=10;break;
    case 4015:
        ++a->state;p->x+=8;break;
    case 4016:
        ++a->state;p->x+=6;break;
    case 4017:
        ++a->state;p->x+=3;break;
    case 4018:
        ++a->state;a->delay=15;p->x+=1;break;
    case 4019:
        a->events=V6_ARRIVAL_SAVE;
        r->active=1;r->x=t->x-32;r->y=t->y-32;r->w=r->h=160;
        a->control=1;a->advance_text=0;a->state=0;break;
    }
    return 1;
}
