#ifndef V6_TELEPORTER_ADMISSION_H
#define V6_TELEPORTER_ADMISSION_H
#include "teleporter_menu.h"
#define V6_EXPLORED_BYTES 50
#define V6_SOURCE_TELEPORTERS 17
typedef struct { uint8_t rooms[V6_EXPLORED_BYTES]; } V6Exploration;
void v6_exploration_init(V6Exploration *);
/* Absolute normal-world room coordinates 100..119. Invalid visits retain map. */
int v6_exploration_visit(V6Exploration *,int room_x,int room_y);
int v6_exploration_seen(const V6Exploration *,int room_x,int room_y);
/* Intersect explored source teleporters with the caller's validated resident
 * routes. Output follows Map.cpp's original order, regardless of input order.
 * Residency includes collision, renderer, normal arrival and checkpoint support;
 * explored alone never admits an unsupported route. Session exploration only:
 * caller owns persistence. Invalid lists/insufficient space retain output/count.
 * Zero residents/zero matches are valid and publish count 0. */
int v6_teleporter_admit(const V6Exploration *,const V6TeleporterDestination *,
    unsigned residents,V6TeleporterDestination *out,unsigned capacity,unsigned *count);
#endif
