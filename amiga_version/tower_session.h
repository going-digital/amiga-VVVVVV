#ifndef V6_TOWER_SESSION_H
#define V6_TOWER_SESSION_H
#include "tower_camera.h"
#include "player.h"
#include "tower_gameplay.h"
/* Same-tower checkpoint lifecycle. Room changes, scripts, statistics and
 * entity-list rebuilding remain caller-owned. */
typedef struct {
    V6Player player;
    V6PlayerMotion motion;
    V6TowerCamera camera;
    int save_x,save_y,save_gravity,save_dir;
    int death_timer,life_timer,invisible,noflashing,deaths,respawns,life_calls;
    int16_t resume_delay;
} V6TowerSession;
void v6_tower_session_init(V6TowerSession *,int x,int y,int gravity,int direction);
void v6_tower_session_die(V6TowerSession *);
/* Early camera -> gated lifecycle -> death phase. Returns nonzero while the
 * death branch occupies this tick (including its respawn tick). Caller runs
 * live player movement and late edge rules only when zero is returned. */
int v6_tower_session_tick(V6TowerSession *,int direction,int stopped,int mini);
/* Single-player tower gameplay. Excludes entities, exits and scripts. */
unsigned v6_tower_session_play(V6TowerSession *,const V6Room *,unsigned input,
                               int direction,int mini);
/* Main-tower checkpoints and boundaries in their live gameplay phases.
 * Do not call again after a room exit until its destination has been loaded. */
unsigned v6_tower_session_play_world(V6TowerSession *,const V6Room *,unsigned,
                                    V6TowerGameplay *);
#endif
