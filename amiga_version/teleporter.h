#ifndef V6_TELEPORTER_H
#define V6_TELEPORTER_H
#include "checkpoints.h"
/* Entity type 14: activation is deferred from collision to entity update.
 * Caller handles returned sound/message requests and owns room persistence. */
typedef struct { int x,y,id,tile,onentity,state; } V6Teleporter;
typedef struct { int active,x,y,w,h; } V6TeleporterRegion;
enum { V6_TELEPORTER_SAVED=1, V6_TELEPORTER_MESSAGE=2 };
void v6_teleporter_init(V6Teleporter *,int x,int y,int id);
void v6_teleporter_collide(V6Teleporter *,const V6Player *);
/* time_trial/nodeath suppress only the saved-message request, like source.
 * State 2 is silent arrival initialization and never changes the save. */
unsigned v6_teleporter_update(V6Teleporter *,V6TeleporterRegion *,
    V6Checkpoint *,unsigned,const V6Player *,int room_x,int room_y,
    int time_trial,int nodeath,V6CheckpointSave *);
/* Validate a canonical teleporter checkpoint without accepting arbitrary
 * coordinates or trusting the record's checksum alone. Caller must select the
 * teleporter bank by room identity before using this check. */
int v6_teleporter_checkpoint_valid(const V6Teleporter *,const V6CheckpointSave *);
#endif
