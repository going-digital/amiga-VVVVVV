/* Session lifecycle checks; movement equivalence is tested separately. */
#include <assert.h>
#include <stdio.h>
#include "slice.h"
#include "room_codec.h"
#include "prototype_room.h"
#include "transition_replay.h"
static int contact_calls;
static void observe_contact(const V6Player *p, void *context)
{
    assert(context == &contact_calls);
    assert(p->x == 76 && p->y == 73 && p->vx == 0 && p->dir == 1);
    ++contact_calls;
}
static int movement_calls, observed_life;
static unsigned observed_input;
static unsigned observe_movement(V6Player *p,const V6Room *room,unsigned input,int life,void *context)
{
    assert(context==&movement_calls);
    ++movement_calls;observed_life=life;observed_input=input;
    return v6_player_step(p,room,input);
}
typedef struct {
    V6Slice *slice;
    V6Checkpoint checkpoints[2];
    V6CheckpointSave save;
    V6PlayerMotion motion;
} CheckpointSession;
static unsigned checkpoint_movement(V6Player *p,const V6Room *room,unsigned input,int life,void *context)
{
    CheckpointSession *c=context;
    unsigned events=v6_player_input(p,input,&c->motion);
    (void)life;
    if(v6_checkpoints_update(c->checkpoints,2,p,100,100,&c->save)) {
        v6_slice_apply_save(c->slice,&c->save);events|=V6_EVENT_SAVE;
    }
    v6_player_physics(p,room,&c->motion,0,0);
    v6_checkpoints_collide(c->checkpoints,2,p);
    return events;
}
static void multiple_checkpoints(void)
{
    uint16_t tiles[1200]={0};
    V6Room room={tiles,0,0,0,0,0};
    V6Slice s;
    CheckpointSession c={0};
    int i;
    unsigned events;
    c.slice=&s;
    v6_slice_init(&s,64,176,20);
    c.motion.pending_y=s.player.y;
    v6_checkpoint_init(&c.checkpoints[0],64,176,20,445550,-1);
    v6_checkpoint_init(&c.checkpoints[1],212,192,21,445551,-1);
    events=v6_slice_step_entities(&s,&room,0,0,checkpoint_movement,&c);
    assert(!(events&V6_EVENT_SAVE) && c.checkpoints[0].pending);
    events=v6_slice_step_entities(&s,&room,0,0,checkpoint_movement,&c);
    assert((events&V6_EVENT_SAVE) && c.save.id==445550 && s.save_gravity==1);
    /* Place at the second checkpoint to isolate save/respawn from traversal. */
    v6_player_init(&s.player,208,185,0);c.motion.pending_y=s.player.y;
    events=v6_slice_step_entities(&s,&room,0,0,checkpoint_movement,&c);
    assert(!(events&V6_EVENT_SAVE) && c.checkpoints[1].pending);
    events=v6_slice_step_entities(&s,&room,V6_LEFT,0,checkpoint_movement,&c);
    assert(events&V6_EVENT_SAVE);
    assert(c.save.id==445551 && s.save_x==208 && s.save_y==185);
    assert(!s.save_gravity && !s.save_dir);
    assert(!c.checkpoints[0].active && c.checkpoints[1].active);
    v6_slice_step_entities(&s,&room,0,1,checkpoint_movement,&c);
    for(i=0;i<29;++i) events=v6_slice_step_entities(&s,&room,0,0,checkpoint_movement,&c);
    assert(events&V6_EVENT_RESPAWN);
    assert(s.player.x==208 && s.player.y==185 && !s.player.gravity && !s.player.dir);
    assert(c.checkpoints[1].active && c.save.id==445551);
    assert(s.life_timer==10 && !s.checkpoint_pending);
}
/* Holding flip through a death must not become a fresh press on respawn. */
static void held_flip_respawn(void)
{
    uint16_t tiles[1200]={0};
    V6Room room={tiles,0,0,0,0,0};
    V6Slice s;
    int i;
    for(i=0;i<40;++i) tiles[20*40+i]=80;
    v6_slice_init(&s,80,144,21);
    s.player.ground=2;s.player.held=1;s.player.flips=3;
    v6_slice_step(&s,&room,V6_FLIP,1);
    for(i=0;i<29;++i) v6_slice_step(&s,&room,V6_FLIP,0);
    assert(s.respawns==1 && s.player.held==1);
    for(i=0;i<10;++i) {
        assert(!(v6_slice_step(&s,&room,V6_FLIP,0)&V6_EVENT_FLIP));
        assert(s.player.gravity==0 && s.player.flips==3);
    }
    v6_slice_step(&s,&room,0,0);
    assert(v6_slice_step(&s,&room,V6_FLIP,0)&V6_EVENT_FLIP);
    assert(s.player.gravity==1 && s.player.flips==4);
}

int main(void)
{
    multiple_checkpoints();
    uint16_t tiles[1200] = {0};
    V6Room room = {tiles, 1, 1, 0, 0, 0};
    V6Slice s;
    unsigned events;
    int i;
    v6_slice_init(&s,80,80,21);
    s.life_timer=8;
    v6_slice_step_movement(&s,&room,V6_RIGHT,0,observe_movement,&movement_calls);
    assert(movement_calls==1 && observed_life==7 && (observed_input&V6_NO_CONTROL));
    assert(s.checkpoint_pending);
    v6_slice_step_movement(&s,&room,0,1,observe_movement,&movement_calls);
    for(i=0;i<29;++i) v6_slice_step_movement(&s,&room,0,0,observe_movement,&movement_calls);
    assert(movement_calls==1 && s.respawns==1);
    v6_slice_step_movement(&s,&room,V6_RIGHT,0,observe_movement,&movement_calls);
    assert(movement_calls==2 && observed_life==9 && (observed_input&V6_NO_CONTROL));
    v6_slice_init(&s, 80, 80, 21);
    v6_slice_step_hook(&s,&room,V6_RIGHT,0,observe_contact,&contact_calls);
    assert(contact_calls==1 && s.player.x>76);
    v6_slice_step_hook(&s,&room,0,1,observe_contact,&contact_calls);
    assert(contact_calls==1);
    v6_slice_init(&s, 80, 80, 21);
    assert(s.player.x == 76 && s.player.y == 73 && s.player.gravity == 0);
    v6_slice_step(&s, &room, 0, 0);
    assert(s.checkpoint_pending && !s.checkpoint_active);
    assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_SAVE);
    events = v6_slice_step(&s, &room, 0, 1);
    assert(events & V6_EVENT_DEATH);
    assert(s.deaths == 1 && s.death_timer == 29);
    for (i = 0; i < 28; ++i) {
        assert(!(v6_slice_step(&s, &room, V6_RIGHT, 0) & V6_EVENT_RESPAWN));
    }
    assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_RESPAWN);
    assert(s.player.x == 76 && s.player.y == 73 && s.life_timer == 10);
    for (i = 0; i < 5; ++i) {
        v6_slice_step(&s, &room, V6_RIGHT, 0);
        assert(s.player.x == 76);
    }
    v6_slice_step(&s, &room, V6_RIGHT, 0);
    assert(s.player.x > 76);
    v6_slice_init(&s, 224, 96, 20);
    assert(s.player.x == 220 && s.player.y == 94 && s.player.gravity == 1);
    s.player.x = 310;
    assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_EXIT);
    assert(s.exits == 1 && s.respawns == 1 && s.deaths == 0);
    assert(s.player.x == 220 && s.player.y == 94);
    {
        const V6RoomSetup rooms[] = {{100,110,224,96,20,10000},{119,110,72,168,21,111190}};
        v6_slice_init_world(&s, rooms, 2, 0);
        s.player.x = -15;
        assert(v6_slice_transition(&s) == V6_EVENT_ROOM);
        assert(s.room_index == 1 && s.player.x == 305 && !s.checkpoint_active);
        v6_slice_step(&s, &room, 0, 1);
        for (i=0;i<29;++i) events = v6_slice_step(&s, &room, 0, 0);
        assert((events & (V6_EVENT_ROOM|V6_EVENT_RESPAWN)) == (V6_EVENT_ROOM|V6_EVENT_RESPAWN));
        assert(s.room_index == 0 && s.player.x == 220 && s.player.y == 94);
        s.player.x=-15;
        v6_slice_transition(&s);
        s.player.x=68; s.player.y=161; s.player.gravity=0; s.life_timer=0;
        v6_slice_step(&s, &room, 0, 0);
        assert(s.checkpoint_pending);
        assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_SAVE);
        assert(s.save_room==1 && s.save_x==68 && s.save_y==161 && !s.save_gravity);
        s.player.x=308;
        assert(v6_slice_transition(&s) & V6_EVENT_ROOM);
        assert(s.room_index==0 && !s.checkpoint_active);
        v6_slice_step(&s, &room, 0, 1);
        for (i=0;i<29;++i) events=v6_slice_step(&s, &room, 0, 0);
        assert(events & V6_EVENT_ROOM);
        assert(s.room_index==1 && s.player.x==68 && s.player.y==161 && !s.player.gravity);
        s.player.y=238;
        assert(v6_slice_transition(&s) & V6_EVENT_EXIT);
        assert(s.room_index==1 && s.player.x==68 && s.player.y==161);
    }
    {
        uint16_t geometry[SLICE_ROOM_COUNT][1200];
        for (i=0;i<SLICE_ROOM_COUNT;++i)
            assert(v6_unpack_room(packed_rooms[i],packed_sizes[i],geometry[i],1200));
        v6_slice_init_world(&s,room_setups,SLICE_ROOM_COUNT,0);
        for (i=0;i<(int)sizeof(transition_replay);++i) {
            V6Room actual={geometry[s.room_index],1,1,0,0,0};
            v6_slice_step(&s,&actual,transition_replay[i],0);
            assert(s.deaths==0 && s.exits==0);
        }
        assert(s.room_index==1 && s.transitions==1 && s.respawns==0);
        assert(s.player.x>=300 && s.player.x<308);
        room.tiles=geometry[1];
        v6_slice_step(&s,&room,0,1);
        for(i=0;i<29;++i) events=v6_slice_step(&s,&room,0,0);
        assert(events & V6_EVENT_ROOM);
        assert(s.room_index==0 && s.player.x==220 && s.player.y==94);
    }
    held_flip_respawn();
    puts("PASS: checkpoint, death delay, respawn controls, ceiling spawn, room wrap, cross-room saves/respawns, original-room replay");
    return 0;
}
