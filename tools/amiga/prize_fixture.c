/* Host trace for the native test-only placement fixture. Integration agreement,
 * not an independent desktop-loop implementation. */
#include "prize.h"
#include "slice.h"
typedef struct {
    V6Prize prize;V6Room room;V6Slice slice;V6Collect bank;unsigned events,pickups;
} Fixture;
static unsigned movement(V6Player *p,const V6Room *r,unsigned input,int life,void *context)
{
    Fixture *f=context;unsigned events;
    (void)r;
    f->events|=v6_prize_live(&f->prize,&f->room,p,input,life,&f->bank,&events);
    if(f->events&V6_PRIZE_SAVE) {v6_slice_apply_save(&f->slice,&f->prize.save);events|=V6_EVENT_SAVE;}
    return events;
}
void prize_fixture(const uint16_t *source,int32_t *trace,unsigned count)
{
    uint16_t tiles[1200];V6Terrain terrain;
    const V6RoomSetup setup={111,107,240,136,20,443490};
    Fixture f;unsigned tick,i;
    for(i=0;i<1200;++i)tiles[i]=source[i];
    f.room=(V6Room){tiles,0,0,&terrain,0,0};
    v6_terrain_build(&terrain,&f.room);
    v6_slice_init_world(&f.slice,&setup,1,0);v6_collect_clear(&f.bank);
    v6_prize_init(&f.prize,&f.room,&f.bank,-1,f.slice.player.y);f.pickups=0;
    for(tick=1;tick<=count;++tick) {
        unsigned restart=tick==100,events;
        if(tick==1 || tick==45 || tick==65 || tick==90) {
            int y=tick==1?70:tick==45?110:tick==65?126:128;
            v6_player_init(&f.slice.player,tick==90?192:124,y,1);
            v6_prize_respawn(&f.prize,y);
        }
        f.events=0;
        if(f.slice.death_timer>=0 || restart)f.events|=v6_prize_death(&f.prize,&f.room);
        if(f.events&V6_PRIZE_TILE)v6_terrain_set_tile(&terrain,tiles,0,0,18,9,59);
        events=v6_slice_step_entities(&f.slice,&f.room,0,restart,movement,&f);
        if(events&V6_EVENT_RESPAWN)v6_prize_respawn(&f.prize,f.slice.player.y);
        if(f.events&V6_PRIZE_PICKUP)++f.pickups;
        int32_t *t=trace+(tick-1)*16;
        t[0]=f.slice.player.x;t[1]=f.slice.player.y;t[2]=f.slice.death_timer;
        t[3]=f.prize.waiting.x;t[4]=f.prize.waiting.state;t[5]=f.prize.waiting.vx;
        for(i=0;i<3;++i)t[6+i]=f.prize.disappearing[i].state;
        t[9]=f.prize.block_count;t[10]=f.prize.trinket.visible;t[11]=f.pickups;
        t[12]=f.bank.bits[0];t[13]=tiles[9*40+18];t[14]=f.slice.respawns;t[15]=f.events;
    }
}