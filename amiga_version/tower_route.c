#include "tower_route.h"
#include "room_codec.h"
static int find(const V6TowerRoute *r,int x,int y)
{
    unsigned i;
    for(i=0;i<r->count;++i) if(r->rooms[i].x==x && r->rooms[i].y==y) return (int)i;
    return -1;
}
int v6_tower_route_load(V6TowerRoute *r,int x,int y,int respawn)
{
    int index=find(r,x,y),was_tower=!r->rooms[r->index].packed;
    const V6TowerRouteRoom *next;
    V6TowerSession *s=r->session;V6TowerGameplay *w=r->world;
    unsigned activations=w->activations,left=w->wrap_left,right=w->wrap_right;
    uint16_t candidate[1200];
    if(index<0) return 0;
    next=&r->rooms[index];
    if(next->count>32 || (next->count && !next->checkpoints) ||
       (next->packed && !next->decoded && !v6_unpack_room(next->packed,next->bytes,candidate,1200))) return 0;
    if(next->packed && !next->decoded) {
        unsigned i;
        for(i=0;i<1200;++i) r->tiles[i]=candidate[i];
    }
    if(!v6_tower_gameplay_init(w,next->checkpoints,next->count,&w->save)) return 0;
    w->activations=activations;w->wrap_left=left;w->wrap_right=right;
    r->index=(unsigned)index;++r->transitions;
    r->tele_region.active=r->tele_region.x=r->tele_region.y=r->tele_region.w=r->tele_region.h=0;
    if(next->teleporter) {
        V6Teleporter *t=next->teleporter;
        v6_teleporter_init(t,t->x,t->y,t->id);
    }
    if(next->packed) {
        r->room.tiles=next->decoded?next->decoded:r->tiles;r->room.tileset=2;r->room.extra_row=0;
        r->room.terrain=0;r->room.blocks=0;r->room.block_count=0;
    } else v6_player_tower_room(&r->room,r->tower);
    s->camera.y=s->camera.old_y=0;s->camera.mode=0;
    s->camera.seek=s->camera.seek_frames=0;
    s->camera.spike_top=s->camera.spike_bottom=0;
    s->camera.old_spike_top=s->camera.old_spike_bottom=0;
    s->camera.colour_superstate=0;s->resume_delay=0;
    if(!next->packed) {
        if(y==109) { s->player.y+=5368;s->camera.y=s->camera.old_y=5368; }
    }
    /* Map::gotoroom resets physics history after entrance transforms. */
    s->player.old_x=s->player.x;s->player.old_y=s->player.y;
    if(respawn) {
        s->player.x=w->save.x;s->player.y=w->save.y;
        s->player.vx=s->player.vy=s->player.ay=0;
        s->motion.ax=0;s->motion.pending_y=s->player.y;
        s->player.gravity=w->save.gravity;s->player.dir=w->save.dir;
        s->save_x=w->save.x;s->save_y=w->save.y;
        s->save_gravity=w->save.gravity;s->save_dir=w->save.dir;
        if(!next->packed && !was_tower) {
            int camera=s->player.y-120;
            if(camera<0) camera=0;
            if(camera>5368) camera=5368;
            s->camera.y=s->camera.old_y=(int16_t)camera;
        }
        ++r->returns;
    }
    return 1;
}
int v6_tower_route_init(V6TowerRoute *r,V6TowerSession *s,V6TowerGameplay *w,
    const V6TowerRouteRoom *rooms,unsigned count,int x,int y,const V6TowerTiles *tower)
{
    unsigned i;
    if(!count || !rooms || !tower) return 0;
    for(i=0;i<count;++i) if(rooms[i].x==x && rooms[i].y==y) break;
    if(i==count || rooms[i].packed) return 0;
    r->session=s;r->world=w;r->rooms=rooms;r->count=count;r->index=i;r->tower=tower;
    r->transitions=r->returns=r->error=0;
    r->tele_region.active=r->tele_region.x=r->tele_region.y=r->tele_region.w=r->tele_region.h=0;
    r->tele_events=0;v6_player_tower_room(&r->room,tower);
    return 1;
}
static int restore(V6TowerRoute *r)
{
    V6TowerSession *s=r->session;V6TowerGameplay *w=r->world;
    const V6TowerRouteRoom *here=&r->rooms[r->index];
    if(here->x!=w->save.room_x || here->y!=w->save.room_y) {
        if(!v6_tower_route_load(r,w->save.room_x,w->save.room_y,1)) return 0;
    } else {
        s->player.x=w->save.x;s->player.y=w->save.y;
        s->player.vx=s->player.vy=s->player.ay=0;
        s->motion.ax=0;s->motion.pending_y=s->player.y;
        s->player.gravity=w->save.gravity;s->player.dir=w->save.dir;
    }
    s->death_timer=-1;s->life_timer=10;s->invisible=1;++s->respawns;
    return 1;
}
static int cross(V6TowerRoute *r,int dx,int dy)
{
    V6Player *p=&r->session->player;
    const V6TowerRouteRoom *here=&r->rooms[r->index];
    int old_x=p->x,old_y=p->y;
    p->x-=dx*320;p->y-=dy*240;
    if(v6_tower_route_load(r,here->x+dx,here->y+dy,0)) return 1;
    p->x=old_x;p->y=old_y;
    return 0;
}
int v6_tower_route_boundary(V6TowerRoute *r)
{
    V6Player *p=&r->session->player;
    if(r->error) return 0;
    if(!r->rooms[r->index].packed) return 1;
    /* Logic.cpp evaluates vertical edges first. Horizontal destination
     * coordinates then come from the newly loaded room, not the old one. */
    if(p->y>=238 && !cross(r,0,1)) goto failed;
    if(p->y< -2 && !cross(r,0,-1)) goto failed;
    if(!r->rooms[r->index].packed) return 1;
    if(p->x< -14 && !cross(r,-1,0)) goto failed;
    if(p->x>=308 && !cross(r,1,0)) goto failed;
    return 1;
failed:
    r->error=1;return 0;
}
int v6_tower_route_step(V6TowerRoute *r,unsigned input)
{
    V6TowerSession *s=r->session;V6TowerGameplay *w=r->world;
    const V6TowerRouteRoom *here=&r->rooms[r->index];
    int x=here->x,y=here->y;
    if(r->error) return 0;
    r->tele_events=0;
    if(!here->packed) {
        /* Camera/death phases run in the old tower before a remote save
         * changes its collision and checkpoint bank. */
        int respawns=s->respawns;
        v6_tower_session_play_room(s,&r->room,input,w,x,y);
        if(s->respawns!=respawns && (x!=w->save.room_x || y!=w->save.room_y)) {
            /* The same-tower helper already reset the player. Restore its
             * death position for Map::gotoroom's history/entrance phase, then
             * let the remote load apply the saved position afterward. */
            s->player.x=s->player.old_x;s->player.y=s->player.old_y;
            if(!v6_tower_route_load(r,w->save.room_x,w->save.room_y,1)) goto failed;
        } else if(w->exit.room_x) {
            if(!v6_tower_route_load(r,w->exit.room_x,w->exit.room_y,0)) goto failed;
        }
        return 1;
    }
    if(s->death_timer!=-1 || s->life_timer>5) input|=V6_NO_CONTROL;
    if(s->life_timer>5) s->player.gravity=s->save_gravity;
    v6_tower_session_life(s);
    v6_player_input(&s->player,input,&s->motion);
    if(s->death_timer!=-1) {
        int contacts=v6_player_contacts(&s->player,&r->room);
        s->player.ground=contacts&1?2:s->player.ground-1;
        s->player.roof=contacts&2?2:s->player.roof-1;
        if(s->death_timer==30) ++s->deaths;
        if(--s->death_timer<=0 && !restore(r)) goto failed;
        return 1;
    }
    {
        unsigned saves=v6_checkpoints_update(w->checkpoints,w->count,&s->player,x,y,&w->save);
        w->activations+=saves;
        if(saves) {
            unsigned i;uint32_t bit=1;w->active_mask=w->pending_mask=0;
            for(i=0;i<w->count;++i,bit<<=1) if(w->checkpoints[i].active) w->active_mask|=bit;
            s->save_x=w->save.x;s->save_y=w->save.y;
            s->save_gravity=w->save.gravity;s->save_dir=w->save.dir;
        }
    }
    if(here->teleporter) {
        r->tele_events=v6_teleporter_update(here->teleporter,&r->tele_region,
            w->checkpoints,w->count,&s->player,x,y,0,0,&w->save);
        if(r->tele_events&V6_TELEPORTER_SAVED) {
            ++w->activations;w->active_mask=0;
            s->save_x=w->save.x;s->save_y=w->save.y;
            s->save_gravity=w->save.gravity;s->save_dir=w->save.dir;
        }
    }
    v6_player_physics(&s->player,&r->room,&s->motion,0,0);
    v6_tower_checkpoints_collide(w,&s->player);
    if(here->teleporter)v6_teleporter_collide(here->teleporter,&s->player);
    if(v6_player_hurt(&s->player,&r->room)) v6_tower_session_die(s);
    return v6_tower_route_boundary(r);
failed:
    r->error=1;return 0;
}
