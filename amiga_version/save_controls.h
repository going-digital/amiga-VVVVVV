#ifndef V6_SAVE_CONTROLS_H
#define V6_SAVE_CONTROLS_H
#include "player.h"
enum { V6_SAVE_ACTION_NONE,V6_SAVE_ACTION_SAVE,V6_SAVE_ACTION_LOAD };
typedef struct { unsigned right_down,suppress_fire; } V6SaveControls;
/* One action per right-button edge. A load chord consumes fire until release,
 * including release/repress of right while fire stays held. Poll every field. */
unsigned v6_save_controls_tick(V6SaveControls *,int right,int fire);
unsigned v6_save_controls_filter(const V6SaveControls *,unsigned input);
#endif
