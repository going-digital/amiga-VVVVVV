/* Entity.cpp simple loop and collisioncheck; see ../LICENSE.md. */
#include "prize_return_sprite.h"
#include "pixel_collision.h"
void v6_return_enemy_animation_init(V6ReturnEnemyAnimation *s)
{ s->delay=s->walk=0;s->frame=-1; }
void v6_return_enemy_animation_tick(V6ReturnEnemyAnimation *s,int stopped)
{
    if(stopped)return;
    if(--s->delay<=0) {
        s->delay=8;
        if(++s->walk==4)s->walk=0;
    }
    s->frame=s->walk;
}
int v6_prize_return_pixel_hurt(const V6PrizeReturn *s,const V6Player *p,
    const uint32_t *player_mask,const uint32_t *enemy0,const uint32_t *enemy1)
{
    unsigned i;
    for(i=0;i<s->enemy_count;++i) {
        const V6Enemy *e=&s->enemies[i];const uint32_t *mask=i?enemy1:enemy0;
        if(mask && v6_player_overlaps(p,e->x+e->cx,e->y+e->cy,e->w,e->h) &&
           v6_pixel_hit(player_mask,p->x,p->y,mask,e->x,e->y))return 1;
    }
    return 0;
}
