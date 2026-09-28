#include "tower_camera.h"
void v6_tower_camera_tick(V6TowerCamera *c,int player_y,int valid,
    int direction,int stopped,int mini)
{
    int target=player_y-120;
    c->old_y=c->y;c->old_spike_top=c->spike_top;c->old_spike_bottom=c->spike_bottom;
    if(!stopped) {
        if(c->mode==0) c->mode=1;
        else if(c->mode==1) c->y+=direction==0?-2:2;
        else if(c->mode==4) {
            if(valid) c->seek=c->y-target;
            c->seek=(int16_t)c->seek/10;
            c->seek_frames=10;c->mode=5;
        } else if(c->mode==5) {
            if(c->spike_top>0) c->spike_top-=2;
            if(c->spike_bottom>0) c->spike_bottom-=2;
            if(c->seek_frames>0) {
                c->y-=c->seek;
                if(valid && ((c->seek>0 && c->y<target) ||
                             (c->seek<=0 && c->y>target))) c->y=target;
                --c->seek_frames;
            } else {
                if(valid) c->y=target;
                c->mode=0;c->colour_superstate=0;
            }
        }
    }
    if(c->y<=0) c->y=0;
    if(c->y>=(mini?568:5368)) c->y=mini?568:5368;
}

unsigned v6_tower_camera_edges(V6TowerCamera *c,int player_y,int valid,
    int direction,int invincible,int life_sequence)
{
    unsigned events=0;
    int relative;
    if(life_sequence!=0) return 0;
    relative=player_y-c->y;
    if(valid) {
        if(!invincible) {
            if(relative<=0 || relative>=208) events|=V6_TOWER_EDGE_DEATH;
        } else if(relative<=8) {
            c->y-=relative<=0?(direction==1?12:8):2;
            events|=V6_TOWER_EDGE_REDRAW;
        } else if(relative>=200) {
            c->y+=relative>=208?(direction==0?12:8):2;
            events|=V6_TOWER_EDGE_REDRAW;
        }
    }
    relative=player_y-c->y;
    if(valid && relative<=40) {
        if(++c->spike_top>=8) c->spike_top=8;
    } else if(c->spike_top>0) --c->spike_top;
    if(valid && relative>=164) {
        if(++c->spike_bottom>=8) c->spike_bottom=8;
    } else if(c->spike_bottom>0) --c->spike_bottom;
    return events;
}

void v6_tower_camera_recover(V6TowerCamera *c,int16_t *delay,int life_sequence,
    int (*advance)(void *),void *context)
{
    if(life_sequence<=0) return;
    if(c->mode==2) {
        c->seek_frames=20;c->mode=4;*delay=4;
    }
    if(c->seek_frames<=0) {
        if(*delay<=0) {
            if(advance(context)==0) c->mode=1;
        } else --*delay;
    }
}
void v6_tower_camera_death(V6TowerCamera *c,int death_sequence)
{
    if(death_sequence!=-1) { c->colour_superstate=1;c->mode=2; }
}
