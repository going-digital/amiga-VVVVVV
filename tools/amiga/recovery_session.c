/* Test-only post-respawn state fixture; no checkpoint activation or exits. */
#include "slice.h"
#include "platform.h"
static V6Slice slice;
static V6Room room;
static V6Terrain terrain;
static V6Platform platforms[4];
static V6Block blocks[4];
static unsigned count,flags;
static V6PlayerMotion motion;
static V6PlatformPush push;
static unsigned move(V6Player *p,const V6Room *r,unsigned input,int life,void *context)
{
    unsigned result=v6_player_input(p,input,&motion);
    (void)context;
    push.pending_y=motion.pending_y;
    v6_platform_transport(p,r,platforms,count,blocks,count,flags,life,&push);
    v6_player_physics(p,r,&motion,0,0);
    v6_platform_disable_overlaps(p,platforms,count,blocks,count);
    v6_player_unstick(p,r);
    return result;
}
void recovery_init(const V6Player *p,const uint16_t *tiles,int gravity,int cached)
{
    v6_slice_init(&slice,p->x+4,p->y+(gravity?2:7),gravity?20:21);
    count=0;
    slice.player=*p;slice.life_timer=10;slice.checkpoint_active=1;
    room=(V6Room){tiles,0,0,0,0,0};
    v6_terrain_build(&terrain,&room);
    if(cached) room.terrain=&terrain;
}
unsigned recovery_step(unsigned input,int restart)
{
    return count ? v6_slice_step_movement(&slice,&room,input,restart,move,0) :
        v6_slice_step(&slice,&room,input,restart);
}
void recovery_read(V6Player *p,int *state)
{
    *p=slice.player;
    state[0]=slice.life_timer;state[1]=slice.death_timer;
    state[2]=slice.deaths;state[3]=slice.respawns;state[4]=slice.exits;
}

void recovery_platform_init(const V6Player *p,const uint16_t *tiles,int gravity,
                            int cached,const V6Platform *actors,unsigned n,unsigned axes)
{
    unsigned i;
    recovery_init(p,tiles,gravity,cached);
    count=n;flags=axes;
    for(i=0;i<n;++i) {
        platforms[i]=actors[i];
        blocks[i]=(V6Block){actors[i].x,actors[i].y,32,8,V6_BLOCK,0};
    }
    room.blocks=blocks;room.block_count=n;
    motion=(V6PlayerMotion){0,p->y};push=(V6PlatformPush){p->y,0,0};
}
void recovery_platform_read(V6Platform *actors,V6Block *collision,int *pending,V6PlatformPush *visual)
{
    unsigned i;
    for(i=0;i<count;++i) {actors[i]=platforms[i];collision[i]=blocks[i];}
    *pending=motion.pending_y;*visual=push;
}
