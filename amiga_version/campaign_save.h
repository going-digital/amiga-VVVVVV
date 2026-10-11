#ifndef V6_CAMPAIGN_SAVE_H
#define V6_CAMPAIGN_SAVE_H
#include <stddef.h>
#include <stdint.h>
#include "checkpoints.h"
#include "hallway_crew.h"
#include "station_trigger.h"
#include "teleporter_admission.h"
#include "trinkets.h"
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
/* Version 3 keeps the 96-byte map layout. Story flags additionally encode
 * yellow triggered=8, rescued=16, companion7=32. Reserved bytes remain zero.
 * The two story outputs retain their existing ABI; at most one companion is
 * active. Reads migrate V1/V2 with yellow state cleared. Older APIs reject V3.
 * Frown room admission is V3-only; source-bank validation remains mandatory. */
int v6_campaign_progress_encode(uint8_t *,size_t,const V6CheckpointSave *,
    const V6HallwayStory *,const V6StationStory *,const V6Exploration *);
int v6_campaign_progress_decode(V6CheckpointSave *,V6HallwayStory *,V6StationStory *,
    V6Exploration *,const uint8_t *,size_t);
/* V4: unchanged checkpoint/story/map prefix through byte 89; collection bank
 * at 90..102, zero reserved bytes 103..107, CRC32 at 108. Older reads seed an
 * empty collection bank. Older APIs reject V4, preventing collection loss.
 * V4 additionally admits Prize (111,107), canonical checkpoint 443490.
 * All five outputs are published together; rejected input changes nothing. */
#define V6_CAMPAIGN_COLLECTION_BYTES 112
int v6_campaign_collection_encode(uint8_t *,size_t,const V6CheckpointSave *,
    const V6HallwayStory *,const V6StationStory *,const V6Exploration *,const V6Collect *);
int v6_campaign_collection_decode(V6CheckpointSave *,V6HallwayStory *,V6StationStory *,
    V6Exploration *,V6Collect *,const uint8_t *,size_t);
#endif
