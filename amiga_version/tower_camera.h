#ifndef V6_TOWER_CAMERA_H
#define V6_TOWER_CAMERA_H
#include <stdint.h>
/* The early tower-camera phase in Logic.cpp, followed by map bounds.
 * Caller owns mode changes from death/respawn, colour updates and tick
 * scheduling; the separate late-phase helper handles player edges. This is not the complete tower game loop.
 * Inputs must remain within tower world coordinates (player y: -256..5856,
 * camera/seek: -8192..8192). Direction 0 ascends, 1 descends. */
typedef struct {
    int16_t y,old_y,mode,seek,seek_frames,spike_top,spike_bottom;
    int16_t old_spike_top,old_spike_bottom,colour_superstate;
} V6TowerCamera;
void v6_tower_camera_tick(V6TowerCamera *,int player_y,int player_valid,
    int direction,int stopped,int mini);
#define V6_TOWER_EDGE_DEATH 1u
#define V6_TOWER_EDGE_REDRAW 2u
/* Late phase, after player movement, when the tower gameplay branch runs.
 * Nonzero life_sequence suppresses it. Returns requested death/redraw events;
 * caller sets deathseq=30 for DEATH. Invincibility alone permits edge camera
 * correction. Spike levels use the corrected position. No clamping here:
 * desktop bounds apply on the next early camera tick. */
unsigned v6_tower_camera_edges(V6TowerCamera *,int player_y,int player_valid,
    int direction,int invincible,int life_sequence);
/* After the early camera tick, including when gameplay is stopped. The caller
 * owns resume_delay and lifeseq. advance(context) must perform exactly one
 * lifecycle update and return the resulting lifeseq; it is called only when
 * recovery seeking and resume delay permit it. A non-null callback is required.
 * This retains the desktop ordering without duplicating player life logic. */
void v6_tower_camera_recover(V6TowerCamera *,int16_t *resume_delay,int life_sequence,
    int (*advance)(void *),void *context);
/* Run after recovery, at entry to the desktop death-processing phase.
 * death_sequence == -1 is inactive; every other value freezes the camera. */
void v6_tower_camera_death(V6TowerCamera *,int death_sequence);
#endif
