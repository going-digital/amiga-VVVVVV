/* Host/68000 fixture using the same slice movement callback contract as native scenes. */
#include "slice.h"
#include "platform.h"
static V6Slice slice;
static V6Platform platform;
static V6Block collision;
static V6PlayerMotion motion;
static V6PlatformPush push;
static uint16_t tiles[1200];
static V6Terrain terrain;
static V6Room room;
static unsigned updates,events;

static unsigned move(V6Player *p,const V6Room *r,unsigned input,int life,void *context)
{
    unsigned result;
    (void)context;
    result=v6_player_input(p,input,&motion);
    push.pending_y=motion.pending_y;
    v6_platform_transport(p,r,&platform,1,&collision,1,V6_PLATFORMS_VERTICAL,life,&push);
    v6_player_physics(p,r,&motion,0,0);
    v6_platform_disable_overlaps(p,&platform,1,&collision,1);
    v6_player_unstick(p,r);
    ++updates;
    return result;
}
void crush_session_init(int tileset,int down,int tile,int speed,int x,int cached)
{
    unsigned i;
    for(i=0;i<1200;++i) tiles[i]=0;
    for(i=9;i<20;++i) tiles[(down?15:8)*40+i]=(uint16_t)tile;
    room=(V6Room){tiles,tileset,0,0,&collision,1};
    v6_terrain_build(&terrain,&room);
    if(cached) room.terrain=&terrain;
    v6_slice_init(&slice,x+4,(down?97:70)+(down?2:7),down?20:21);
    v6_platform_init(&platform,104,down?91:93,down?0:1,speed,48,32,224,200);
    collision=(V6Block){platform.x,platform.y,32,8,V6_BLOCK,0};
    motion=(V6PlayerMotion){0,slice.player.y};
    push=(V6PlatformPush){slice.player.y,0,0};
    updates=events=0;
}
void crush_session_step(void)
{
    events=v6_slice_step_movement(&slice,&room,0,0,move,0);
    if(events&V6_EVENT_RESPAWN) {
        motion=(V6PlayerMotion){0,slice.player.y};
        push=(V6PlatformPush){slice.player.y,0,0};
    }
}
void crush_session_read(V6Player *p,V6Platform *e,V6Block *b,int *state)
{
    *p=slice.player;*e=platform;*b=collision;
    state[0]=slice.death_timer;state[1]=slice.life_timer;
    state[2]=slice.deaths;state[3]=slice.respawns;
    state[4]=(int)updates;state[5]=(int)events;
}
