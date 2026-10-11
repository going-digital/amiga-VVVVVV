#ifndef V6_TRINKETS_H
#define V6_TRINKETS_H
#include "player.h"
/* The original collect bank has 100 identities, shared by coins and trinkets.
 * Keep the complete bank, including currently unused campaign identities. */
enum { V6_COLLECT_COUNT=100, V6_COLLECT_BYTES=13 };
typedef struct { unsigned char bits[V6_COLLECT_BYTES]; } V6Collect;
typedef struct { int x,y,id,visible,pending; } V6Trinket;
void v6_collect_clear(V6Collect *);
int v6_collect_has(const V6Collect *,int id);
/* Canonical packed bank: reject nonzero spare bits without changing output. */
int v6_collect_import(V6Collect *,const unsigned char *);
int v6_trinket_init(V6Trinket *,int x,int y,int id,const V6Collect *);
/* Rule-3 collision arms pickup; call before stuck prevention. */
void v6_trinket_collide(V6Trinket *,const V6Player *);
/* Run at this entity's update position on the following live tick. Returns
 * one pickup event; caller handles sound and the normal-game pickup screen.
 * Do not run during death. Collection survives room recreation and respawn. */
int v6_trinket_update(V6Trinket *,V6Collect *);
#endif
