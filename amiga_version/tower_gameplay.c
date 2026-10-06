/* Adapted from the main-tower boundary branch in desktop Logic.cpp. */
#include "tower_gameplay.h"
int v6_tower_gameplay_init(V6TowerGameplay *w,V6Checkpoint *c,unsigned count,
                          const V6CheckpointSave *save)
{
    unsigned i;uint32_t bit=1;
    if(count>32 || (count && !c)) return 0;
    w->checkpoints=c;w->count=count;
    w->save.x=save->x;w->save.y=save->y;w->save.gravity=save->gravity;
    w->save.dir=save->dir;w->save.room_x=save->room_x;
    w->save.room_y=save->room_y;w->save.id=save->id;
    w->activations=w->wrap_left=w->wrap_right=0;
    w->exit.room_x=w->exit.room_y=w->exit.lerp_dx=0;
    w->active_mask=w->pending_mask=0;
    for(i=0;i<count;++i,bit<<=1) {
        c[i].active=c[i].id==save->id;c[i].pending=0;
        if(c[i].active) w->active_mask|=bit;
    }
    return 1;
}
void v6_tower_checkpoints_collide(V6TowerGameplay *w,const V6Player *p)
{
    unsigned i;uint32_t bit=1;
    for(i=0;i<w->count;++i,bit<<=1) {
        V6Checkpoint *c=&w->checkpoints[i];
        if(!c->active && c->y>p->y-14 && c->y<p->y+23 &&
           v6_player_overlaps(p,c->x,c->y,16,16)) {
            c->pending=1;w->pending_mask|=bit;
        }
    }
}
V6TowerExit v6_tower_boundary(V6Player *p,int camera_y)
{
    V6TowerExit result={0,0,0};
    if(camera_y>=500 && camera_y<=5000) {
        if(p->x<=-10) { p->x+=320;result.lerp_dx=320; }
        else if(p->x>310) { p->x-=320;result.lerp_dx=-320; }
    } else {
        if(p->x< -14) {
            p->x+=320;p->y-=671*8;result.room_x=108;result.room_y=109;
        }
        if(p->x>=308) {
            p->x-=320;result.room_x=110;result.room_y=104;
        }
    }
    return result;
}
