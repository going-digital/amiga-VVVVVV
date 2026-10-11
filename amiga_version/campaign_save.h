#ifndef V6_CAMPAIGN_SAVE_H
#define V6_CAMPAIGN_SAVE_H
#include <stddef.h>
#include <stdint.h>
#include "checkpoints.h"
#include "hallway_crew.h"
#include "teleporter_admission.h"
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
/* Version 2: the first 40 bytes retain the checkpoint/story layout, followed
 * by all 400 explored-room bits, two zero reserved bytes, and CRC32 at 92.
 * The checkpoint room must be explored. Decode also accepts version 1 and
 * seeds only its checkpoint room; it never invents other visited rooms.
 * All three outputs are published together after validation. Legacy APIs
 * continue to accept/write only version 1, preventing silent map loss. */
#define V6_CAMPAIGN_STATE_BYTES 96
int v6_campaign_state_encode(uint8_t *,size_t,const V6CheckpointSave *,
    const V6HallwayStory *,const V6Exploration *);
int v6_campaign_state_decode(V6CheckpointSave *,V6HallwayStory *,V6Exploration *,
    const uint8_t *,size_t);
/* Bank must belong to the saved room. Only source checkpoint-derived spawns
 * are accepted; an initial save with id -1 is not a checkpoint restart. */
int v6_campaign_checkpoint_valid(const V6CheckpointSave *,const V6Checkpoint *,unsigned);
#endif
