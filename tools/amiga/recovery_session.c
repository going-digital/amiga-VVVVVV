/* Test-only post-respawn state fixture; no checkpoint activation or exits. */
#include "slice.h"
static V6Slice slice;
static V6Room room;
static V6Terrain terrain;
void recovery_init(const V6Player *p,const uint16_t *tiles,int gravity,int cached)
{
    v6_slice_init(&slice,p->x+4,p->y+(gravity?2:7),gravity?20:21);
    slice.player=*p;slice.life_timer=10;slice.checkpoint_active=1;
    room=(V6Room){tiles,0,0,0,0,0};
    v6_terrain_build(&terrain,&room);
    if(cached) room.terrain=&terrain;
}
unsigned recovery_step(unsigned input,int restart)
{ return v6_slice_step(&slice,&room,input,restart); }
void recovery_read(V6Player *p,int *state)
{
    *p=slice.player;
    state[0]=slice.life_timer;state[1]=slice.death_timer;
    state[2]=slice.deaths;state[3]=slice.respawns;state[4]=slice.exits;
}
