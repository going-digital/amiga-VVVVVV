#ifndef V6_TOWER_CAMERA_H
#define V6_TOWER_CAMERA_H
#include <stdint.h>
/* The early tower-camera phase in Logic.cpp, followed by map bounds.
 * Caller owns mode changes from death/respawn, player-edge corrections, colour
 * updates and tick scheduling. This is not the complete tower game loop.
 * Inputs must remain within tower world coordinates (player y: -256..5856,
 * camera/seek: -8192..8192). Direction 0 ascends, 1 descends. */
typedef struct {
    int16_t y,old_y,mode,seek,seek_frames,spike_top,spike_bottom;
    int16_t old_spike_top,old_spike_bottom,colour_superstate;
} V6TowerCamera;
void v6_tower_camera_tick(V6TowerCamera *,int player_y,int player_valid,
    int direction,int stopped,int mini);
#endif
