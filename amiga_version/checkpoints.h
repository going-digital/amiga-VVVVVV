#ifndef V6_CHECKPOINTS_H
#define V6_CHECKPOINTS_H
#include "player.h"
/* Ordinary floor/ceiling checkpoints in original entity order. State is
 * caller-owned so several checkpoints can coexist in a room. */
typedef struct {
    int x,y,tile,id,active,pending;
} V6Checkpoint;
typedef struct {
    int x,y,gravity,dir,room_x,room_y,id;
} V6CheckpointSave;
int v6_checkpoint_init(V6Checkpoint *,int x,int y,int tile,int id,int saved_id);
/* Run at this checkpoint's entity-update position, after input. Deactivates
 * other checkpoints without clearing their pending activations. Returns 1 for
 * a save; the caller handles sound and persistence once per activation. */
int v6_checkpoint_update(V6Checkpoint *,unsigned count,unsigned index,
                         const V6Player *,int room_x,int room_y,V6CheckpointSave *);
/* Convenience for a checkpoint-only update pass in reverse entity order.
 * Returns the number of saves, not just whether the final saved ID changed. */
unsigned v6_checkpoints_update(V6Checkpoint *,unsigned,const V6Player *,
                               int room_x,int room_y,V6CheckpointSave *);
/* Collision stage: arm inactive overlapping checkpoints for the next update.
 * Call before stuck prevention, like the source entitycollisioncheck. */
void v6_checkpoints_collide(V6Checkpoint *,unsigned,const V6Player *);
#endif
