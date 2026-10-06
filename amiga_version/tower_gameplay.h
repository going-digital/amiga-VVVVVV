#ifndef V6_TOWER_GAMEPLAY_H
#define V6_TOWER_GAMEPLAY_H
#include "checkpoints.h"
/* Main-tower boundary results. room_x==0 means remain in the tower.
 * An exit transforms player coordinates as the desktop does; the caller must
 * load the destination before another gameplay tick. lerp_dx adjusts render
 * interpolation history, not the physics old_x field. */
typedef struct { int room_x,room_y,lerp_dx; } V6TowerExit;
V6TowerExit v6_tower_boundary(V6Player *,int camera_y);
typedef struct {
    V6Checkpoint *checkpoints;
    unsigned count;
    V6CheckpointSave save;
    unsigned activations,wrap_left,wrap_right;
    V6TowerExit exit;
    uint32_t active_mask,pending_mask;
} V6TowerGameplay;
/* Up to 32 checkpoints; gameplay owns their active/pending state after init.
 * Invalid capacity leaves world/bank unchanged. */
int v6_tower_gameplay_init(V6TowerGameplay *,V6Checkpoint *,unsigned,
                          const V6CheckpointSave *);
void v6_tower_checkpoints_collide(V6TowerGameplay *,const V6Player *);
/* Caller supplies original entity order, initialized checkpoint state and
 * an existing save record. This module does not own storage or disk saves. */
#endif
