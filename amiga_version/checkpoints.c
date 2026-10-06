/* Adapted from Entity.cpp checkpoint creation, update and rule-3 collision.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "checkpoints.h"
int v6_checkpoint_init(V6Checkpoint *c,int x,int y,int tile,int id,int saved_id)
{
    if(tile!=20 && tile!=21) return 0;
    c->x=x;c->y=y;c->tile=tile;c->id=id;
    c->active=id==saved_id;c->pending=0;
    return 1;
}
int v6_checkpoint_update(V6Checkpoint *checkpoints,unsigned count,unsigned index,
                         const V6Player *p,int room_x,int room_y,V6CheckpointSave *save)
{
    unsigned i;
    V6Checkpoint *c;
    if(index>=count) return 0;
    c=&checkpoints[index];
    if(!c->pending) return 0;
    for(i=0;i<count;++i) checkpoints[i].active=0;
    c->active=1;c->pending=0;
    save->x=c->x-4;save->y=c->y-(c->tile==20?2:7);
    save->gravity=c->tile==20;save->dir=p->dir;
    save->room_x=room_x;save->room_y=room_y;save->id=c->id;
    return 1;
}
unsigned v6_checkpoints_update(V6Checkpoint *c,unsigned count,const V6Player *p,
                               int room_x,int room_y,V6CheckpointSave *save)
{
    unsigned i,events=0;
    for(i=count;i>0;--i)
        if(c[i-1].pending) events+=v6_checkpoint_update(c,count,i-1,p,room_x,room_y,save);
    return events;
}
void v6_checkpoints_collide(V6Checkpoint *c,unsigned count,const V6Player *p)
{
    unsigned i;
    for(i=0;i<count;++i)
        if(!c[i].active && c[i].y>p->y-14 && c[i].y<p->y+23 &&
           v6_player_overlaps(p,c[i].x,c[i].y,16,16))
            c[i].pending=1;
}
