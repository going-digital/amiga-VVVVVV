#ifndef V6_SLICE_H
#define V6_SLICE_H
#include "player.h"
enum { V6_EVENT_DEATH = 2, V6_EVENT_SAVE = 4, V6_EVENT_RESPAWN = 8, V6_EVENT_EXIT = 16 };
typedef struct {
    V6Player player;
    int checkpoint_x, checkpoint_y, checkpoint_tile;
    int save_x, save_y, save_gravity, save_dir;
    int checkpoint_active, checkpoint_pending;
    int death_timer, life_timer, deaths, respawns, exits;
    int frame, walking_frame, frame_delay;
} V6Slice;
void v6_slice_init(V6Slice *, int checkpoint_x, int checkpoint_y, int checkpoint_tile);
unsigned v6_slice_step(V6Slice *, const V6Room *, unsigned input, int restart);
#endif
