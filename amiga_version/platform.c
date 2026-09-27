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
