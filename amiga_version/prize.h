#ifndef V6_PRIZE_H
#define V6_PRIZE_H
#include "platform_gate.h"
#include "trinkets.h"
#include "checkpoints.h"
enum { V6_PRIZE_SOUND=1, V6_PRIZE_PICKUP=2, V6_PRIZE_SAVE=4,
       V6_PRIZE_TILE=8, V6_PRIZE_FULL=16 };
/* Source entities in room (111,107): three disappearing platforms, then the
 * waiting platform, trinket 6 and ceiling checkpoint 443490. The caller owns
 * terrain and collection progress. No room transition or pickup-screen UI. */
typedef struct {
    V6Disappearing disappearing[3];
    V6Platform waiting;
    V6Block blocks[4];
    unsigned block_count;
    V6Trinket trinket;
    V6Checkpoint checkpoint;
    V6CheckpointSave save;
    V6PlayerMotion motion;
    V6PlatformPush push;
} V6Prize;
void v6_prize_init(V6Prize *,V6Room *,const V6Collect *,int saved_id,int player_y);
/* After input: horizontal platform pass, then reverse non-platform entities
 * (checkpoint, trinket, disappearing 2..0), then player physics/collisions.
 * Returns player-input events separately to avoid overlapping event bits. */
unsigned v6_prize_live(V6Prize *,V6Room *,V6Player *,unsigned input,int life,
                       V6Collect *,unsigned *player_events);
/* Run each death tick; report special tile patch before caller respawns.
 * Caller applies tile (18,9)=59 to both terrain and display. */
unsigned v6_prize_death(V6Prize *,V6Room *);
/* Same-room respawn resets retained player movement only, preserving actors. */
void v6_prize_respawn(V6Prize *,int player_y);
#endif
