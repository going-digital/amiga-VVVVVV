/* Room composition follows Spacestation2.cpp, Logic.cpp and Entity.cpp.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "prize.h"
static const int gate_x[3]={120,120,120};
static const int gate_y[3]={72,112,128};
static unsigned update_gates(V6Prize *s,V6Room *r,int dying)
{
    unsigned i,events=0;
    for(i=3;i>0;--i) {
        unsigned e=v6_disappearing_update_room(&s->disappearing[i-1],120,
            gate_y[i-1],s->blocks,&s->block_count,4,dying,111,107,0);
        if(e&V6_DISAPPEAR_SOUND)events|=V6_PRIZE_SOUND|(1U<<(V6_PRIZE_GATE_SOUND_SHIFT+i-1));
        if(e&V6_DISAPPEAR_DEATH_TILE)events|=V6_PRIZE_TILE;
        if(e&V6_DISAPPEAR_FULL)events|=V6_PRIZE_FULL;
    }
    r->block_count=s->block_count;
    return events;
}
void v6_prize_respawn(V6Prize *s,int player_y)
{
    s->motion.ax=0;s->motion.pending_y=player_y;
    s->push.pending_y=player_y;s->push.visual_ground=s->push.visual_roof=0;
}
void v6_prize_init(V6Prize *s,V6Room *r,const V6Collect *c,int saved_id,int player_y)
{
    unsigned i;
    for(i=0;i<3;++i) {
        v6_disappearing_init(&s->disappearing[i]);
        s->blocks[i]=(V6Block){120,gate_y[i],32,8,V6_BLOCK,0};
    }
    v6_platform_gate_init(&s->waiting,88,72,15,4,0,0,320,240,
                         s->disappearing,gate_x,3);
    s->blocks[3]=(V6Block){88,72,32,8,V6_BLOCK,0};
    s->block_count=4;r->blocks=s->blocks;r->block_count=4;
    v6_trinket_init(&s->trinket,192,128,6,c);
    v6_checkpoint_init(&s->checkpoint,240,136,20,443490,saved_id);
    s->save=(V6CheckpointSave){236,134,1,1,111,107,443490};
    v6_prize_respawn(s,player_y);
}
void v6_prize_platform(V6Prize *s,V6Room *r,V6Player *p,int life,int pending_y)
{
    s->push.pending_y=pending_y;
    /* Waiting platforms see the previous live states: gates update later. */
    v6_platform_gate_transport(p,r,&s->waiting,1,s->blocks,s->block_count,
        V6_PLATFORMS_HORIZONTAL,life,&s->push,s->disappearing,gate_x,3);
}
unsigned v6_prize_entities(V6Prize *s,V6Room *r,V6Collect *c)
{
    unsigned events=0;
    if(v6_trinket_update(&s->trinket,c))events|=V6_PRIZE_PICKUP;
    events|=update_gates(s,r,0);
    return events;
}
void v6_prize_collide(V6Prize *s,V6Player *p)
{
    unsigned i;
    /* Source entity collision order, before stuck prevention/damage. */
    for(i=0;i<3;++i)v6_disappearing_contact(&s->disappearing[i],
        v6_player_overlaps(p,120,gate_y[i]-1,32,10));
    v6_platform_disable_overlaps(p,&s->waiting,1,s->blocks,s->block_count);
    v6_trinket_collide(&s->trinket,p);
}
unsigned v6_prize_live(V6Prize *s,V6Room *r,V6Player *p,unsigned input,int life,
                       V6Collect *c,unsigned *player_events)
{
    unsigned events=0;
    *player_events=v6_player_input(p,input,&s->motion);
    v6_prize_platform(s,r,p,life,s->motion.pending_y);
    if(v6_checkpoint_update(&s->checkpoint,1,0,p,111,107,&s->save))events|=V6_PRIZE_SAVE;
    events|=v6_prize_entities(s,r,c);
    v6_player_physics(p,r,&s->motion,0,0);
    v6_prize_collide(s,p);
    v6_checkpoints_collide(&s->checkpoint,1,p);
    v6_player_unstick(p,r);
    return events;
}
unsigned v6_prize_death(V6Prize *s,V6Room *r)
{
    unsigned events=update_gates(s,r,1);
    /* Logic.cpp death branch: keep the moving platform to the right of the
     * special (18,9) tile. Preserve velocity/state and render history. There
     * is no retained newxp in this core; the next move starts from current x. */
    if(s->waiting.x<152) {
        int x=s->waiting.x,y=s->waiting.y;
        v6_blocks_disable_at(s->blocks,s->block_count,x,y);
        s->waiting.x=152;
        v6_blocks_move(s->blocks,s->block_count,x,y,152,y,s->waiting.w,s->waiting.h);
    }
    return events;
}
