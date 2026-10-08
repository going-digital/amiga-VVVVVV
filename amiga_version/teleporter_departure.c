/* Adapted from Input.cpp normal selection and Game.cpp states 4000..4003.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "teleporter_departure.h"
static int valid(const V6Teleporter *t)
{
    return t && t->x>=-44 && t->x<=276 && t->y>=-44 && t->y<=196;
}
void v6_teleporter_departure_init(V6TeleporterDeparture *d)
{
    d->state=d->delay=d->flash=d->shake=d->locked=d->travel=0;
    d->control=1;d->events=0;
}
int v6_teleporter_departure_start(V6TeleporterDeparture *d,V6Teleporter *t,V6TeleporterRegion *r)
{
    if(!d || !r || !valid(t) || d->state || d->delay || d->locked || d->travel)return 0;
    d->state=4000;d->control=0;d->events=0;r->active=0;t->tile=6;return 1;
}
int v6_teleporter_departure_tick(V6TeleporterDeparture *d,int *invisible,V6Teleporter *t)
{
    if(!d || !invisible || !valid(t) ||
       (d->state && (d->state<4000 || d->state>4003)) || d->delay<0 || d->delay>10)return 0;
    d->events=0;
    if(!d->state)return 1;
    if(d->delay>0)--d->delay;
    if(d->delay)return 1;
    switch(d->state) {
    case 4000:
        ++d->state;d->delay=10;d->flash=5;d->shake=10;d->events=V6_DEPARTURE_FLASH;break;
    case 4001:
        ++d->state;d->delay=0;d->flash=5;d->shake=0;d->events=V6_DEPARTURE_TELEPORT;break;
    case 4002:
        ++d->state;d->delay=10;*invisible=1;t->tile=1;break;
    case 4003:
        d->state=d->delay=d->locked=0;d->travel=1;d->events=V6_DEPARTURE_TRAVEL;break;
    }
    return 1;
}
