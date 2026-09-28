#include "tower_session.h"
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
