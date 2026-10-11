/* Source composition: Spacestation2.cpp rooms rn(48,43) and rn(48,42).
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "prize_return.h"
int v6_prize_return_init(V6PrizeReturn *s,V6Room *r,int x,int y,int player_y)
{
    static const int conveyor_x[6]={104,168,232,56,120,184};
    unsigned i;
    if(x!=110 || (y!=106 && y!=107))return 0;
    s->platform_count=y==107?6:4;s->enemy_count=y==107?2:0;
    s->flags=y==107?V6_PLATFORMS_HORIZONTAL:V6_PLATFORMS_VERTICAL;
    s->push.pending_y=player_y;s->push.visual_ground=s->push.visual_roof=0;
    for(i=0;i<s->platform_count;++i) {
        int px,py;
        if(y==107) {
            /* Source meta 10 is a 64-wide conveyor normalized to behaviour 8.
             * Its collision block remains 32-wide until the first live update. */
            px=conveyor_x[i];py=i<3?80:144;
            v6_conveyor_init(&s->platforms[i],px,py,8,4,i==2 || i==5?32:64);
        } else {
            px=88+(int)i*48;py=112;
            v6_platform_init(&s->platforms[i],px,py,i&1,4,88,64,264,168);
        }
        s->blocks[i]=(V6Block){px,py,32,8,V6_BLOCK,0};
    }
    if(y==107) {
        v6_enemy_init(&s->enemies[0],272,120,2,8,0,0,320,240,0,0,16,16);
        v6_enemy_init(&s->enemies[1],32,96,3,8,0,0,320,240,0,0,16,16);
    }
    r->blocks=s->blocks;r->block_count=s->platform_count;
    return 1;
}
void v6_prize_return_platforms(V6PrizeReturn *s,V6Room *r,V6Player *p,int life,int pending_y)
{
    s->push.pending_y=pending_y;
    v6_platform_transport(p,r,s->platforms,s->platform_count,s->blocks,
        s->platform_count,s->flags,life,&s->push);
}
void v6_prize_return_entities(V6PrizeReturn *s,const V6Room *r)
{
    unsigned i;
    for(i=s->enemy_count;i>0;--i) {
        V6Enemy *e=&s->enemies[i-1];
        V6Block candidates[6];unsigned j,count=0;
        /* These two source enemies move horizontally. A block outside their
         * fixed vertical span cannot affect either axis of checkwall, even
         * during its speed-reduction retries. Keep the original block order. */
        if(e->behavior>=2 && !e->vy && r->block_count<=6) {
            int top=e->y+e->cy,bottom=top+e->h;
            for(j=0;j<r->block_count;++j) {
                const V6Block *b=&r->blocks[j];
                if(b->y<bottom && b->y+b->h>top)candidates[count++]=*b;
            }
            v6_enemy_step(e,r,candidates,count);
        } else v6_enemy_step(e,r,r->blocks,r->block_count);
    }
}
unsigned v6_prize_return_contacts(V6PrizeReturn *s,const V6Player *p)
{
    unsigned i,hits=0;
    v6_platform_disable_overlaps(p,s->platforms,s->platform_count,s->blocks,s->platform_count);
    for(i=0;i<s->enemy_count;++i) {
        const V6Enemy *e=&s->enemies[i];
        if(v6_player_overlaps(p,e->x+e->cx,e->y+e->cy,e->w,e->h))hits|=1U<<i;
    }
    return hits;
}
