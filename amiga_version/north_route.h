#ifndef V6_NORTH_ROUTE_H
#define V6_NORTH_ROUTE_H
#include "platform.h"
#include "enemy.h"
#include "disappearing.h"
typedef struct {
    V6Platform platforms[3];V6Enemy enemies[5];V6Disappearing gates[3];
    V6Block blocks[4];V6PlatformPush push;
    unsigned room_y,platform_count,enemy_count,gate_count,block_count,flags;
} V6NorthRoute;
int v6_north_init(V6NorthRoute *,V6Room *,int x,int y,int player_y);
void v6_north_platforms(V6NorthRoute *,V6Room *,V6Player *,int life,int pending_y);
unsigned v6_north_entities(V6NorthRoute *,V6Room *,int dying);
unsigned v6_north_contacts(V6NorthRoute *,V6Player *);
#endif
