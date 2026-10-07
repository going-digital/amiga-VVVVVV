#ifndef V6_TELEPORTER_ANIMATION_H
#define V6_TELEPORTER_ANIMATION_H
/* Desktop teleporter animation state. Supply the next int(fRandom()*6)
 * choice (0..5); it is used only when a delay expires. RNG ownership stays
 * with the caller. Invalid choices leave the state unchanged. */
typedef struct { int frame,delay,walking; } V6TeleporterAnimation;
int v6_teleporter_animate(V6TeleporterAnimation *,int tile,int noflashing,unsigned choice);
#endif
