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
void v6_companion_step(V6Companion *c,const V6Player *p,const V6Room *room,int death)
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
    /* Collision animation observes pre-integration velocity, as in Logic.cpp. */
    v6_player_physics(&c->body,room,&c->motion,animate,c);
    if(death>-1)c->frame=c->body.dir?12:13;
    ++c->steps;
}
