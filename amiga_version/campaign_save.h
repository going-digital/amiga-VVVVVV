#ifndef V6_CAMPAIGN_SAVE_H
#define V6_CAMPAIGN_SAVE_H
#include <stddef.h>
#include <stdint.h>
#include "checkpoints.h"
#include "hallway_crew.h"
/* Bounded route save, not desktop XML or a mid-cutscene snapshot.
 * 44 bytes: V6CS, BE16 version/length, seven BE32 checkpoint fields,
 * BE32 story flags, BE32 IEEE CRC32 of the preceding 40 bytes.
 * Flags: triggered=1, rescued=2, companion9=4. Runtime modes excluded.
 * Codec bounds include Building Apport; callers must additionally select
 * and validate their supported source bank (see campaign_route.h).
 * Caller must save only after scripts finish and use OS-safe disk I/O.
 * Rejected input leaves the output unchanged; buffers may not overlap. */
#define V6_CAMPAIGN_SAVE_BYTES 44
int v6_campaign_encode(uint8_t *,size_t,const V6CheckpointSave *,const V6HallwayStory *);
int v6_campaign_decode(V6CheckpointSave *,V6HallwayStory *,const uint8_t *,size_t);
/* Bank must belong to the saved room. Only source checkpoint-derived spawns
 * are accepted; an initial save with id -1 is not a checkpoint restart. */
int v6_campaign_checkpoint_valid(const V6CheckpointSave *,const V6Checkpoint *,unsigned);
#endif
