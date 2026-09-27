#include "platform.h"
int v6_platform_init(V6Platform *p, int x, int y, int behavior, int speed,
                     int x1, int y1, int x2, int y2)
{
    return v6_enemy_init(p,x,y,behavior,speed,x1,y1,x2,y2,0,0,32,8);
}
void v6_platform_step(V6Platform *p, const V6Room *room, V6Block *blocks, unsigned count)
{
    int x=p->x,y=p->y;
    v6_blocks_disable_at(blocks,count,x,y);
    /* Original rule 2 tests map tiles but skips checkblocks entirely. */
    v6_enemy_step(p,room,0,0);
    v6_blocks_move(blocks,count,x,y,p->x,p->y,p->w,p->h);
}

int v6_platform_contact_speed(const V6Player *p, const V6Block *blocks, unsigned count,
                               const V6Platform *platforms, unsigned platform_count, int roof)
{
    unsigned i,j;
    for(i=0;i<count;++i) {
        const V6Block *b=&blocks[i];
        if(b->type!=V6_BLOCK || !v6_block_hit(b,p->x+6,p->y+2+(roof?-1:1),12,21,0,0,0)) continue;
        for(j=0;j<platform_count;++j) {
            const V6Platform *e=&platforms[j];
            if(e->behavior>=2 && e->behavior<=3 && e->x==b->x && e->y==b->y) return e->vx;
        }
        return -1000;
    }
    return -1000;
}

int v6_platform_carry_horizontal(V6Player *p,const V6Room *room,
                                 const V6Platform *platforms,unsigned count,int life_timer,int pending_y)
{
    int speed;
    if(life_timer>=8) return 0;
    speed=v6_platform_contact_speed(p,room->blocks,room->block_count,platforms,count,0);
    if(speed<=-1000)
        speed=v6_platform_contact_speed(p,room->blocks,room->block_count,platforms,count,1);
    if(speed<=-1000) return 0;
    v6_player_map_move(p,room,p->x+speed,pending_y);
    return 1;
}

void v6_platform_push_vertical(V6Platform *e,V6Player *p,const V6Room *room,V6PlatformPush *state)
{
    int dy;
    if(!v6_player_overlaps(p,e->x+e->cx,e->y+e->cy,e->w,e->h)) return;
    dy=p->vy/V6_ONE;
    p->y+=dy;
    if(!v6_player_overlaps(p,e->x+e->cx,e->y+e->cy,e->w,e->h)) return;
    p->y-=dy;
    p->vy=e->vy*V6_ONE;
    state->pending_y=p->y+e->vy;
    if(v6_player_test_y(p,room,&state->pending_y)) {
        if(e->vy>0) {
            p->y=e->y+e->h; p->vy=0; p->roof=2; state->visual_roof=1;
        } else {
            p->y=e->y-21-2; p->vy=0; p->ground=2; state->visual_ground=1;
        }
    } else e->state=e->onwall;
}

void v6_platform_disable_overlaps(const V6Player *p,const V6Platform *platforms,
                                  unsigned count,V6Block *blocks,unsigned block_count)
{
    unsigned i;
    for(i=0;i<count;++i) {
        const V6Platform *e=&platforms[i];
        if(v6_player_overlaps(p,e->x+e->cx,e->y+e->cy,e->w,e->h))
            v6_blocks_disable_at(blocks,block_count,e->x,e->y);
    }
}

void v6_platform_transport(V6Player *p,const V6Room *room,V6Platform *platforms,
                            unsigned count,V6Block *blocks,unsigned block_count,
                            unsigned flags,int life_timer,V6PlatformPush *push)
{
    unsigned i;
    if(flags&V6_PLATFORMS_VERTICAL)
        for(i=count;i>0;--i) {
            V6Platform *e=&platforms[i-1];
            if(e->vx) continue;
            v6_platform_step(e,room,blocks,block_count);
            v6_platform_push_vertical(e,p,room,push);
        }
    if(flags&V6_PLATFORMS_HORIZONTAL) {
        for(i=count;i>0;--i) {
            V6Platform *e=&platforms[i-1];
            if(e->vy) continue;
            v6_platform_step(e,room,blocks,block_count);
        }
        v6_platform_carry_horizontal(p,room,platforms,count,life_timer,push->pending_y);
    }
}
