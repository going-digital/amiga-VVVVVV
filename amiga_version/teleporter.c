/* Adapted from Entity.cpp type-14 creation, update and rule-3 collision.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "teleporter.h"
void v6_teleporter_init(V6Teleporter *t,int x,int y,int id)
{
    t->x=x;t->y=y;t->id=id;t->tile=1;t->onentity=1;t->state=0;
}
void v6_teleporter_collide(V6Teleporter *t,const V6Player *p)
{
    if(t->onentity>0 && v6_player_overlaps(p,t->x,t->y,96,96))
        t->state=t->onentity;
}
static void region(V6TeleporterRegion *r,const V6Teleporter *t)
{
    r->active=1;r->x=t->x-32;r->y=t->y-32;r->w=r->h=160;
}
unsigned v6_teleporter_update(V6Teleporter *t,V6TeleporterRegion *r,
    V6Checkpoint *bank,unsigned count,const V6Player *p,int rx,int ry,
    int time_trial,int nodeath,V6CheckpointSave *save)
{
    unsigned events=0,i;
    if(t->state==1) {
        if(t->tile==1) {
            t->tile=2;region(r,t);
            for(i=0;i<count;++i) bank[i].active=0;
            save->x=t->x+44;save->y=t->y+44;save->gravity=0;
            save->dir=p->dir;save->room_x=rx;save->room_y=ry;save->id=t->id;
            events=V6_TELEPORTER_SAVED;
            if(!time_trial && !nodeath) events|=V6_TELEPORTER_MESSAGE;
        }
        t->onentity=0;t->state=0;
    } else if(t->state==2) {
        t->onentity=0;t->tile=6;region(r,t);t->state=0;
    }
    return events;
}
int v6_teleporter_checkpoint_valid(const V6Teleporter *t,const V6CheckpointSave *s)
{
    return t && s && s->id==t->id && s->x==t->x+44 && s->y==t->y+44 &&
        s->gravity==0 && (s->dir==0 || s->dir==1);
}
