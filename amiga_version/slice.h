#ifndef V6_SLICE_H
#define V6_SLICE_H
#include "player.h"
#include "checkpoints.h"
enum { V6_EVENT_DEATH = 2, V6_EVENT_SAVE = 4, V6_EVENT_RESPAWN = 8, V6_EVENT_EXIT = 16, V6_EVENT_ROOM = 32 };
typedef struct { int x, y, checkpoint_x, checkpoint_y, checkpoint_tile, checkpoint_id; } V6RoomSetup;
typedef struct {
    const V6RoomSetup *rooms;
    int room_count, room_index, save_room, transitions;
    V6Player player;
    int checkpoint_x, checkpoint_y, checkpoint_tile;
    int save_x, save_y, save_gravity, save_dir;
    int checkpoint_active, checkpoint_pending;
    int death_timer, life_timer, deaths, respawns, exits;
    int frame, walking_frame, frame_delay;
} V6Slice;
void v6_slice_init(V6Slice *, int checkpoint_x, int checkpoint_y, int checkpoint_tile);
void v6_slice_init_world(V6Slice *, const V6RoomSetup *, int count, int initial);
unsigned v6_slice_transition(V6Slice *);
/* Movement callback runs only on live ticks, after input gating and life-timer
 * decrement, before checkpoint/hazard/transition handling. */
typedef unsigned (*V6SliceMovement)(V6Player *, const V6Room *, unsigned input,
                                    int life_timer, void *);
/* External entity callback owns checkpoint update/collision stages. It applies
 * saves through the helper below and returns V6_EVENT_SAVE. On room changes,
 * the caller must reload its room-specific checkpoint list. */
void v6_slice_apply_save(V6Slice *,const V6CheckpointSave *);
unsigned v6_slice_step_entities(V6Slice *,const V6Room *,unsigned,int,
                                V6SliceMovement,void *);
unsigned v6_slice_step_movement(V6Slice *, const V6Room *, unsigned, int,
                                V6SliceMovement, void *);
unsigned v6_slice_step_hook(V6Slice *, const V6Room *, unsigned, int, V6ContactHook, void *);
unsigned v6_slice_step(V6Slice *, const V6Room *, unsigned input, int restart);
#endif
