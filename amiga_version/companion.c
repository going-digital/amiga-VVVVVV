/* Adapted from VVVVVV Entity.cpp and Map.cpp.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "companion.h"
static void spawn(V6Companion *c,int x,int y,int dir,int32_t vx,int following)
{
    v6_player_init(&c->body,x,y,0);c->body.dir=dir;c->body.vx=vx;
    c->motion.ax=0;c->motion.pending_y=y;
    c->animation.delay=c->animation.walk=0;
    c->visible=1;c->following=following;c->mood=!following;
    c->frame=c->mood?147:(dir?0:3);++c->spawns;
}
void v6_companion_init(V6Companion *c)
{
    v6_player_init(&c->body,0,0,0);c->motion.ax=c->motion.pending_y=0;
    c->animation.delay=c->animation.walk=0;
    c->visible=c->following=c->mood=c->frame=0;c->spawns=c->steps=c->follow_steps=0;
}
void v6_companion_idle(V6Companion *c,int visible)
{
    c->visible=0;
    if(visible) spawn(c,264,185,0,0,0);
}
void v6_companion_enter(V6Companion *c,int companion,int tower,int room_x,const V6Player *p)
{
    c->visible=0;
    if(companion==9 && !tower) spawn(c,room_x==110 && p->x<20?100:p->x,185,p->dir,p->vx,1);
}
static void animate(const V6Player *p,void *context)
{
    V6Companion *c=context;
    c->frame=v6_collision_frame(&c->animation,p,p->ground,p->roof,-1);
    if(c->mood)c->frame+=144;
}
void v6_companion_rest_reset(V6CompanionRest *r){r->valid=0;}
static int rest_same(const V6CompanionRest *r,const V6Companion *c,const V6Room *room)
{
    const V6Player *p=&c->body;
    return r->ax==c->motion.ax && r->tiles==room->tiles && r->terrain==room->terrain && r->tileset==room->tileset &&
        r->extra_row==room->extra_row && !room->block_count &&
        r->body[0]==p->x && r->body[1]==p->y && r->body[2]==p->old_x && r->body[3]==p->old_y &&
        r->body[4]==p->vx && r->body[5]==p->vy && r->body[6]==p->ay &&
        r->body[7]==p->ground && r->body[8]==p->roof && r->body[9]==p->gravity &&
        r->pending_y==c->motion.pending_y;
}
static void rest_store(V6CompanionRest *r,const V6Companion *c,const V6Room *room)
{
    const V6Player *p=&c->body;
    r->body[0]=p->x;r->body[1]=p->y;r->body[2]=p->old_x;r->body[3]=p->old_y;
    r->body[4]=p->vx;r->body[5]=p->vy;r->body[6]=p->ay;r->body[7]=p->ground;r->body[8]=p->roof;r->body[9]=p->gravity;
    r->ax=c->motion.ax;r->pending_y=c->motion.pending_y;r->tiles=room->tiles;r->terrain=room->terrain;
    r->tileset=room->tileset;r->extra_row=room->extra_row;
}
static void rest_result(V6CompanionRest *r,const V6Companion *c)
{
    const V6Player *p=&c->body;
    r->after[0]=p->x;r->after[1]=p->y;r->after[2]=p->old_x;r->after[3]=p->old_y;
    r->after[4]=p->vx;r->after[5]=p->vy;r->after[6]=p->ay;
    r->after[7]=p->ground;r->after[8]=p->roof;r->after[9]=p->gravity;
    r->pending_after=c->motion.pending_y;
}
static void rest_apply(const V6CompanionRest *r,V6Companion *c)
{
    V6Player *p=&c->body;
    /* The contact hook runs before integration. Only ground/roof have changed
     * at that point; direction, animation state and counters remain live. */
    p->ground=r->after[7];p->roof=r->after[8];animate(p,c);
    p->x=r->after[0];p->y=r->after[1];p->old_x=r->after[2];p->old_y=r->after[3];
    p->vx=r->after[4];p->vy=r->after[5];p->ay=r->after[6];p->gravity=r->after[9];
    c->motion.ax=0;c->motion.pending_y=r->pending_after;
}
void v6_companion_rest_prime_motion(V6CompanionRest *out,unsigned count,
    const V6Companion *source,const V6Room *room,int32_t ax)
{
    V6Companion copy;unsigned i;
    volatile uint8_t *dest=(volatile uint8_t *)&copy;
    const uint8_t *bytes=(const uint8_t *)source;
    for(i=0;i<sizeof(copy);++i)dest[i]=bytes[i];
    for(i=0;i<count;++i){V6CompanionRest *r=&out[i];r->valid=0;
        if(room->tileset==V6_TILE_SOURCE_TOWER || !room->terrain || room->block_count)continue;
        copy.motion.ax=ax;rest_store(r,&copy,room);
        v6_player_physics_crew(&copy.body,room,&copy.motion,0,0);
        rest_result(r,&copy);r->valid=1;
    }
}
void v6_companion_rest_prime(V6CompanionRest *out,unsigned count,
    const V6Companion *source,const V6Room *room)
{v6_companion_rest_prime_motion(out,count,source,room,0);}
static void step(V6Companion *c,const V6Player *p,const V6Room *room,int death,int restrained,int station,V6CompanionRest *rest,unsigned count)
{
    if(!c->visible) return;
    c->motion.ax=0;
    if(c->following) {
        ++c->follow_steps;
        if(p->x>c->body.x+5)c->body.dir=1;
        else if(p->x<c->body.x-5)c->body.dir=0;
        if(p->x>c->body.x+45)c->motion.ax=3*V6_ONE;
        else if(p->x<c->body.x-45)c->motion.ax=-3*V6_ONE;
    }
    if(restrained && c->body.x<155 && c->motion.ax<0)c->motion.ax=0;
    /* Collision animation observes pre-integration velocity, as in Logic.cpp. */
    {unsigned i;
        for(i=0;rest && i<count;++i)if(rest[i].valid && rest_same(&rest[i],c,room))break;
        if(rest && i<count)rest_apply(&rest[i],c);
        else {
            if(rest)rest_store(rest,c,room);
            v6_player_physics_crew(&c->body,room,&c->motion,animate,c);
            if(rest){rest_result(rest,c);rest->valid=room->tileset!=V6_TILE_SOURCE_TOWER && room->terrain && !room->block_count;}
        }
    }
    if(death>-1)c->frame=(c->body.dir?12:13)+(station?2:0);
    ++c->steps;
}

void v6_station_companion_idle(V6Companion *c,int visible)
{
    c->visible=0;
    if(visible) {
        spawn(c,42,86,1,0,0);c->body.gravity=1;c->frame=150;
    }
}
void v6_station_companion_enter(V6Companion *c,int companion,int x,int y,const V6Player *p)
{
    c->visible=0;
    if(companion==7 && y<=105) {
        spawn(c,x==110?320:p->x,86,p->dir,p->vx,1);
        c->body.gravity=1;c->frame=6;
    }
}

void v6_companion_step(V6Companion *c,const V6Player *p,const V6Room *room,int death)
{ step(c,p,room,death,0,0,0,0); }
void v6_station_companion_step(V6Companion *c,const V6Player *p,const V6Room *room,
    int death,int room_x,int room_y)
{ step(c,p,room,death,room_x==110 && room_y==105,1,0,0); }

void v6_station_companion_step_rest(V6Companion *c,const V6Player *p,const V6Room *room,
    int death,int room_x,int room_y,V6CompanionRest *rest)
{step(c,p,room,death,room_x==110 && room_y==105,1,rest,1);}

void v6_station_companion_step_memo(V6Companion *c,const V6Player *p,const V6Room *room,
    int death,int room_x,int room_y,V6CompanionRest *rest,unsigned count)
{step(c,p,room,death,room_x==110 && room_y==105,1,rest,count);}
