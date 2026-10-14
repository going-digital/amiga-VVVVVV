#ifndef V6_TERMINAL_H
#define V6_TERMINAL_H
#include "player.h"
typedef struct { int x,y,tile,parameter,state,onentity,active; } V6Terminal;
void v6_terminal_init(V6Terminal *,int x,int y,int tile_offset,int parameter,int highlight);
/* Like checkpoints, contact requests state 1 after physics. The next entity
 * update highlights the terminal and emits one touch cue. This is independent
 * of activating the associated activity block/read script. */
void v6_terminal_contact(V6Terminal *,const V6Player *);
unsigned v6_terminal_tick(V6Terminal *);
#endif
