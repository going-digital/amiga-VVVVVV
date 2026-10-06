#include "tower_session.h"
static unsigned play(V6TowerSession *s,const V6Room *room,unsigned input,
                      int direction,int mini,V6TowerGameplay *world)
{
    unsigned events;
    int contacts;
    const V6TowerTiles *tiles=(const void *)room->tiles;
    if(s->death_timer!=-1 || s->life_timer>5) input|=V6_NO_CONTROL;
    events=v6_player_input(&s->player,input,&s->motion);
    /* Contacts refresh during the death pause too; movement stays frozen. */
    if(s->death_timer!=-1) {
        contacts=v6_player_contacts(&s->player,room);
        s->player.ground=contacts&1 ? 2 : s->player.ground-1;
        s->player.roof=contacts&2 ? 2 : s->player.roof-1;
    }
    if(v6_tower_session_tick(s,direction,0,mini)) return events;
    if(world) {
        unsigned saves=v6_checkpoints_update(world->checkpoints,world->count,
            &s->player,world->save.room_x,world->save.room_y,&world->save);
        world->activations+=saves;
        if(saves) {
            unsigned i;uint32_t bit=1;
            world->active_mask=world->pending_mask=0;
            for(i=0;i<world->count;++i,bit<<=1)
                if(world->checkpoints[i].active) world->active_mask|=bit;
            s->save_x=world->save.x;s->save_y=world->save.y;
            s->save_gravity=world->save.gravity;s->save_dir=world->save.dir;
        }
    }
    v6_player_physics(&s->player,room,&s->motion,0,0);
    if(world) v6_tower_checkpoints_collide(world,&s->player);
    if(v6_player_hurt(&s->player,room)) v6_tower_session_die(s);
    if(v6_tower_camera_edges(&s->camera,s->player.y,1,direction,
                            tiles->invincible,s->life_timer)&V6_TOWER_EDGE_DEATH)
        v6_tower_session_die(s);
    if(world) {
        V6TowerExit exit=v6_tower_boundary(&s->player,s->camera.y);
        world->exit.room_x=exit.room_x;world->exit.room_y=exit.room_y;
        world->exit.lerp_dx=exit.lerp_dx;
        if(world->exit.lerp_dx>0) ++world->wrap_left;
        if(world->exit.lerp_dx<0) ++world->wrap_right;
    }
    return events;
}
unsigned v6_tower_session_play(V6TowerSession *s,const V6Room *room,unsigned input,
                               int direction,int mini)
{ return play(s,room,input,direction,mini,0); }
unsigned v6_tower_session_play_world(V6TowerSession *s,const V6Room *room,
                                    unsigned input,V6TowerGameplay *world)
{ return play(s,room,input,0,0,world); }
void v6_tower_session_init(V6TowerSession *s,int x,int y,int gravity,int direction)
{
    v6_player_init(&s->player,x,y,gravity);
    s->player.dir=direction;
    s->save_x=x;s->save_y=y;s->save_gravity=gravity;s->save_dir=direction;
    s->motion.ax=0;s->motion.pending_y=y;
    s->camera.y=s->camera.old_y=0;s->camera.mode=0;
    s->camera.seek=s->camera.seek_frames=0;
    s->camera.spike_top=s->camera.spike_bottom=0;
    s->camera.old_spike_top=s->camera.old_spike_bottom=0;
    s->camera.colour_superstate=0;s->resume_delay=0;
    s->death_timer=-1;s->life_timer=0;s->invisible=0;s->noflashing=0;
    s->deaths=s->respawns=s->life_calls=0;
}
void v6_tower_session_die(V6TowerSession *s)
{
    if(s->death_timer==-1) s->death_timer=30;
}
static int advance_life(void *context)
{
    V6TowerSession *s=context;
    ++s->life_calls;
    if(s->life_timer>0) {
        s->invisible=s->life_timer==2 || s->life_timer==6 || s->life_timer>=8;
        if(s->life_timer>5) s->player.gravity=s->save_gravity;
        --s->life_timer;
        if(s->life_timer<=0 || s->noflashing) s->invisible=0;
    }
    return s->life_timer;
}
int v6_tower_session_tick(V6TowerSession *s,int direction,int stopped,int mini)
{
    v6_tower_camera_tick(&s->camera,s->player.y,1,direction,stopped,mini);
    v6_tower_camera_recover(&s->camera,&s->resume_delay,s->life_timer,advance_life,s);
    v6_tower_camera_death(&s->camera,s->death_timer);
    if(s->death_timer==-1) return 0;
    if(s->death_timer==30) ++s->deaths;
    if(--s->death_timer<=0) {
        /* Same-room Map::resetplayer retains old positions and input/contact
         * state, but resets velocity and pending position to the saved point. */
        s->player.x=s->save_x;s->player.y=s->save_y;
        s->player.vx=s->player.vy=s->player.ay=0;
        s->motion.ax=0;s->motion.pending_y=s->save_y;
        s->player.dir=s->save_dir;s->player.gravity=s->save_gravity;
        s->life_timer=10;s->invisible=1;s->death_timer=-1;++s->respawns;
    }
    return 1;
}
