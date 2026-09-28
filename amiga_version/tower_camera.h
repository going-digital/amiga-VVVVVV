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
#endif
