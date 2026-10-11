#ifndef V6_PRIZE_H
#define V6_PRIZE_H
#include "platform_gate.h"
#include "trinkets.h"
#include "checkpoints.h"
enum { V6_PRIZE_SOUND=1, V6_PRIZE_PICKUP=2, V6_PRIZE_SAVE=4,
       V6_PRIZE_TILE=8, V6_PRIZE_FULL=16, V6_PRIZE_GATE_SOUND_SHIFT=5,
       V6_PRIZE_GATE_SOUND_MASK=7<<V6_PRIZE_GATE_SOUND_SHIFT };
/* Individual gate sound bits retain source identity alongside legacy SOUND.
 * Audio order is pickup, then gates 2, 1, 0. A missing slot returns 4. */
static inline unsigned v6_prize_audio_cue(unsigned events,unsigned slot)
{
    if(slot==0)return (events&V6_PRIZE_PICKUP)?3:4;
    if(slot<=3)return (events&(1U<<(V6_PRIZE_GATE_SOUND_SHIFT+3-slot)))?2:4;
    return 4;
}
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
/* Campaign composition: platform pass after input; entities after checkpoint
 * updates; contacts after physics and before checkpoints/stuck correction.
 * The route owns player motion and its checkpoint bank in this mode. */
void v6_prize_platform(V6Prize *,V6Room *,V6Player *,int life,int pending_y);
unsigned v6_prize_entities(V6Prize *,V6Room *,V6Collect *);
void v6_prize_collide(V6Prize *,V6Player *);
/* After input: horizontal platform pass, then reverse non-platform entities
 * (checkpoint, trinket, disappearing 2..0), then player physics/collisions.
 * Returns player-input events separately to avoid overlapping event bits. */
unsigned v6_prize_live(V6Prize *,V6Room *,V6Player *,unsigned input,int life,
                       V6Collect *,unsigned *player_events);
/* Run each death tick; relocate a moving platform left of x=152 as source
 * Logic.cpp does, and report special tile patch before caller respawns.
 * Caller applies tile (18,9)=59 to both terrain and display. */
unsigned v6_prize_death(V6Prize *,V6Room *);
/* Same-room respawn resets retained player movement only, preserving actors. */
void v6_prize_respawn(V6Prize *,int player_y);
#endif
