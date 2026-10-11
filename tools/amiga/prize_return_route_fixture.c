/* Host integration oracle, not an independent desktop-loop implementation. */
#include "prize.h"
#include "tower_route.h"
#include "prize_checkpoint_replay.h"
#include "prize_return_sprite.h"
#include "animation.h"
#include "prize_return_sprite_assets.h"
typedef struct {
    V6Prize prize;V6Collect collected;V6TowerRoute route;V6TowerSession session;
    V6TowerGameplay world;V6Terrain terrain[5];uint16_t tiles[5][1200];
    V6Checkpoint checkpoint[9];V6TowerRouteRoom rooms[5];
    V6Platform conveyors[2];V6Block blocks[2];unsigned pickups,patches;
    V6PrizeReturn west;V6ReturnEnemyAnimation enemy_animation[2];
    V6CollisionAnimation player_animation;int player_frame;unsigned enemy_hits;
} Fixture;
static int events(Fixture *f,unsigned e)
{
    if(e&V6_PRIZE_FULL)return 0;
    if(e&V6_PRIZE_PICKUP)++f->pickups;
    if(e&V6_PRIZE_TILE) {
        int changed=v6_terrain_set_tile(&f->terrain[1],f->tiles[1],0,0,18,9,59);
        if(changed<0)return 0;
        if(changed)++f->patches;
    }
    return 1;
}
static int platforms(V6TowerRoute *r,void *context)
{
    Fixture *f=context;V6TowerSession *s=r->session;
    if(r->index==1)v6_prize_platform(&f->prize,&r->room,&s->player,s->life_timer,s->motion.pending_y);
    else if(r->index==0) {
        V6PlatformPush push={s->motion.pending_y,0,0};
        v6_platform_transport(&s->player,&r->room,f->conveyors,2,f->blocks,2,
            V6_PLATFORMS_HORIZONTAL,s->life_timer,&push);
    }
    else if(r->index>=3)
        v6_prize_return_platforms(&f->west,&r->room,&s->player,s->life_timer,s->motion.pending_y);
    return 1;
}
static int entities(V6TowerRoute *r,void *context)
{
    Fixture *f=context;
    if(r->index>=3)v6_prize_return_entities(&f->west,&r->room);
    return r->index!=1 || events(f,v6_prize_entities(&f->prize,&r->room,&f->collected));
}
static int contacts(V6TowerRoute *r,void *context)
{
    Fixture *f=context;
    if(r->index==1)v6_prize_collide(&f->prize,&r->session->player);
    else if(r->index>=3) {
        v6_prize_return_contacts(&f->west,&r->session->player);
        const uint32_t *m[2];
        for(unsigned i=0;i<2;++i)m[i]=f->enemy_animation[i].frame<0?
            return_player_collision[0]:return_enemy_collision[f->enemy_animation[i].frame];
        if(v6_prize_return_pixel_hurt(&f->west,&r->session->player,
            return_player_collision[f->player_frame],m[0],m[1])) {
            ++f->enemy_hits;v6_tower_session_die(r->session);
        }
    }
    return 1;
}
static int death(V6TowerRoute *r,void *context)
{
    Fixture *f=context;
    return r->index!=1 || events(f,v6_prize_death(&f->prize,&r->room));
}
static void enter(Fixture *f)
{
    V6TowerRoute *r=&f->route;
    r->room.terrain=&f->terrain[r->index];
    if(r->index==1)v6_prize_init(&f->prize,&r->room,&f->collected,f->world.save.id,f->session.player.y);
    else if(r->index==0) {
        for(unsigned i=0;i<2;++i) {
            v6_conveyor_init(&f->conveyors[i],i?104:16,i?184:104,8+i,4,64);
            f->blocks[i]=(V6Block){i?104:16,i?184:104,32,8,V6_BLOCK,0};
        }
        r->room.blocks=f->blocks;r->room.block_count=2;
    } else if(r->index>=3) {
        v6_prize_return_init(&f->west,&r->room,110,r->index==3?107:106,f->session.player.y);
        for(unsigned i=0;i<2;++i)v6_return_enemy_animation_init(&f->enemy_animation[i]);
    }
}
static int fixture(const uint16_t *north,const uint16_t *south,const uint16_t *east,const uint16_t *west,const uint16_t *northwest,const unsigned *inputs,int32_t *trace,unsigned count)
{
    Fixture f={0};V6TowerRoute *r=&f.route;V6TowerSession *s=&f.session;
    V6TowerGameplay *w=&f.world;
    V6TowerRouteHooks hooks={platforms,entities,contacts,death};
    for(unsigned i=0;i<1200;++i){f.tiles[0][i]=north[i];f.tiles[1][i]=south[i];}
    f.checkpoint[0]=(V6Checkpoint){144,168,21,442490,0,0};
    f.checkpoint[1]=(V6Checkpoint){24,112,20,442491,0,0};
    f.checkpoint[2]=(V6Checkpoint){240,136,20,443490,0,0};
    for(unsigned i=0;i<2;++i) {
        /* decoded terrain bypasses the packed placeholder, as in native. */
        f.rooms[i]=(V6TowerRouteRoom){111,106+(int)i,(const uint8_t *)"x",1,
            &f.checkpoint[i?2:0],i?1:2,f.tiles[i],0,0};
        V6Room room={f.tiles[i],0,0,0,0,0};
        v6_terrain_build(&f.terrain[i],&room);
    }
    if(east) {
        for(unsigned i=0;i<1200;++i)f.tiles[2][i]=east[i];
        f.checkpoint[3]=(V6Checkpoint){280,192,21,443500,0,0};
        f.checkpoint[4]=(V6Checkpoint){64,80,21,443501,0,0};
        f.rooms[2]=(V6TowerRouteRoom){112,107,(const uint8_t *)"x",1,
            &f.checkpoint[3],2,f.tiles[2],0,0};
        V6Room room={f.tiles[2],0,0,0,0,0};v6_terrain_build(&f.terrain[2],&room);
    }
    for(unsigned i=3;i<5;++i) {
        const uint16_t *src=i==3?west:northwest;
        for(unsigned t=0;t<1200;++t)f.tiles[i][t]=src[t];
        f.checkpoint[5+(i-3)*2]=(V6Checkpoint){i==3?152:56,i==3?32:64,i==3?21:20,i==3?443480:442480,0,0};
        f.checkpoint[6+(i-3)*2]=(V6Checkpoint){i==3?152:280,i==3?184:152,i==3?20:21,i==3?443481:442481,0,0};
        f.rooms[i]=(V6TowerRouteRoom){110,i==3?107:106,(const uint8_t *)"x",1,
            &f.checkpoint[5+(i-3)*2],2,f.tiles[i],0,0};
        V6Room room={f.tiles[i],0,0,0,0,0};v6_terrain_build(&f.terrain[i],&room);
    }
    w->save=(V6CheckpointSave){276,185,0,1,112,107,443500};
    v6_tower_session_init(s,w->save.x,w->save.y,w->save.gravity,1);
    s->save_x=w->save.x;s->save_y=w->save.y;
    s->save_gravity=w->save.gravity;s->save_dir=w->save.dir;
    /* Candidate-only host bank; no native room or save admission. */
    r->session=s;r->world=w;r->rooms=f.rooms;r->count=5;
    if(!v6_tower_route_load(r,w->save.room_x,w->save.room_y,1))return 0;
    enter(&f);
    for(unsigned tick=0;tick<count;++tick) {
        unsigned previous=r->index;
        /* main.cpp runs gamerenderfixed before gamelogic. Ordinary death
         * does not stop enemy animation; the pickup pause is outside this fixture. */
        if(r->index>=3)for(unsigned i=0;i<f.west.enemy_count;++i)
            v6_return_enemy_animation_tick(&f.enemy_animation[i],0);
        f.player_frame=v6_collision_frame(&f.player_animation,&s->player,
            s->player.ground,s->player.roof,s->death_timer);
        if(!v6_tower_route_step_hooks(r,tick<195?v6_prize_checkpoint_replay(tick):inputs[tick-195],&hooks,&f))return 0;
        if(previous!=r->index)enter(&f);
        int32_t *d=trace+tick*32;
        d[0]=7+r->index;d[1]=s->player.x;d[2]=s->player.y;d[3]=s->player.gravity;
        d[4]=s->death_timer;d[5]=w->save.id;d[6]=w->save.x;d[7]=w->save.y;
        d[8]=w->save.gravity;d[9]=w->save.room_x;d[10]=w->save.room_y;d[11]=0;
        d[12]=r->room.block_count;d[13]=f.prize.waiting.x;d[14]=f.prize.waiting.state;
        d[15]=f.pickups;d[16]=f.patches;d[17]=v6_collect_has(&f.collected,6);
        d[18]=f.prize.trinket.visible;d[19]=f.tiles[1][9*40+18];
        for(unsigned i=0;i<3;++i)d[20+i]=f.prize.disappearing[i].state;
        d[23]=s->respawns;d[24]=f.enemy_hits;d[25]=s->player.vx;d[26]=s->player.vy;
        d[27]=s->motion.pending_y;d[28]=f.west.platforms[0].y;
        d[29]=f.west.enemies[0].x;d[30]=f.west.enemies[1].x;d[31]=r->error;
    }
    return 1;
}

int prize_return_route_fixture(const uint16_t *north,const uint16_t *south,
    const uint16_t *east,const uint16_t *west,const uint16_t *northwest,
    const unsigned *inputs,int32_t *trace,unsigned count)
{
    return fixture(north,south,east,west,northwest,inputs,trace,count);
}
