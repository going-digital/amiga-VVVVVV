/* Host integration oracle, not an independent desktop-loop implementation. */
#include "prize.h"
#include "tower_route.h"
#include "prize_input_replay.h"
#include "prize_checkpoint_replay.h"
typedef struct {
    V6Prize prize;V6Collect collected;V6TowerRoute route;V6TowerSession session;
    V6TowerGameplay world;V6Terrain terrain[3];uint16_t tiles[3][1200];
    V6Checkpoint checkpoint[5];V6TowerRouteRoom rooms[3];
    V6Platform conveyors[2];V6Block blocks[2];unsigned pickups,patches;
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
    return 1;
}
static int entities(V6TowerRoute *r,void *context)
{
    Fixture *f=context;
    return r->index!=1 || events(f,v6_prize_entities(&f->prize,&r->room,&f->collected));
}
static int contacts(V6TowerRoute *r,void *context)
{
    Fixture *f=context;
    if(r->index==1)v6_prize_collide(&f->prize,&r->session->player);
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
    }
}
static int fixture(const uint16_t *north,const uint16_t *south,const uint16_t *east,int32_t *trace,unsigned count)
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
    w->save=east?(V6CheckpointSave){276,185,0,1,112,107,443500}:
        (V6CheckpointSave){140,161,0,1,111,106,442490};
    v6_tower_session_init(s,w->save.x,w->save.y,w->save.gravity,1);
    /* Only ordinary rooms are needed by this bounded checkpoint fixture. */
    r->session=s;r->world=w;r->rooms=f.rooms;r->count=east?3:2;
    if(!v6_tower_route_load(r,w->save.room_x,w->save.room_y,1))return 0;
    enter(&f);
    for(unsigned tick=0;tick<count;++tick) {
        unsigned previous=r->index;
        if(!v6_tower_route_step_hooks(r,east?v6_prize_checkpoint_replay(tick):v6_prize_input_replay(tick),&hooks,&f))return 0;
        if(previous!=r->index)enter(&f);
        int32_t *d=trace+tick*24;
        d[0]=7+r->index;d[1]=s->player.x;d[2]=s->player.y;d[3]=s->player.gravity;
        d[4]=s->death_timer;d[5]=w->save.id;d[6]=w->save.x;d[7]=w->save.y;
        d[8]=w->save.gravity;d[9]=w->save.room_x;d[10]=w->save.room_y;d[11]=0;
        d[12]=r->room.block_count;d[13]=f.prize.waiting.x;d[14]=f.prize.waiting.state;
        d[15]=f.pickups;d[16]=f.patches;d[17]=v6_collect_has(&f.collected,6);
        d[18]=f.prize.trinket.visible;d[19]=f.tiles[1][9*40+18];
        for(unsigned i=0;i<3;++i)d[20+i]=f.prize.disappearing[i].state;
        d[23]=s->respawns;
    }
    return 1;
}

int prize_input_fixture(const uint16_t *north,const uint16_t *south,int32_t *trace,unsigned count)
{
    return fixture(north,south,0,trace,count);
}
int prize_checkpoint_fixture(const uint16_t *north,const uint16_t *south,const uint16_t *east,int32_t *trace,unsigned count)
{
    return fixture(north,south,east,trace,count);
}
