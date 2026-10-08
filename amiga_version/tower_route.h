#ifndef V6_TOWER_ROUTE_H
#define V6_TOWER_ROUTE_H
#include "tower_session.h"
#include "teleporter.h"
#include <stddef.h>
/* Resident route: tower entrances and supported ordinary rooms.
 * Room data/checkpoint banks must outlive the route. A NULL packed room is
 * the streamed main tower; other rooms decode exactly 40x30 tiles. */
typedef struct {
    int x,y;
    const uint8_t *packed;
    size_t bytes;
    V6Checkpoint *checkpoints;
    unsigned count;
    /* Optional immutable 1200-tile view prepared before the frame loop. */
    const uint16_t *decoded;
    V6Teleporter *teleporter; /* Optional source type-14 entity, caller-owned. */
    unsigned tileset; /* Ordinary-room source tileset (0..2); tower ignores it. */
} V6TowerRouteRoom;
typedef struct {
    V6TowerSession *session;
    V6TowerGameplay *world;
    const V6TowerRouteRoom *rooms;
    unsigned count,index,transitions,returns,error;
    const V6TowerTiles *tower;
    V6Room room;
    uint16_t tiles[1200];
    V6TeleporterRegion tele_region;
    unsigned tele_events; /* Saved/message requests from the latest step. */
} V6TowerRoute;
/* Existing session/save are retained. Init requires a tower entrance and a
 * player already in world coordinates; use load to start in a hallway. */
int v6_tower_route_init(V6TowerRoute *,V6TowerSession *,V6TowerGameplay *,
    const V6TowerRouteRoom *,unsigned,int x,int y,const V6TowerTiles *);
/* Change collision and checkpoint banks. Entrance transforms/history resets
 * precede saved-position restore. A hallway -> tower respawn snaps the camera;
 * a hallway destination uses a fixed zero camera.
 * Unknown/malformed rooms return 0 before changing room/checkpoint state. */
int v6_tower_route_load(V6TowerRoute *,int x,int y,int respawn);
/* Script.cpp normal teleport room-change stage, before arrival effects.
 * Caller enforces exploration/menu eligibility and pauses player control for
 * the subsequent arrival sequence. Destination must be a different resident
 * ordinary room with a canonical teleporter. Invalid requests retain all state.
 * Seeds the source (150,110) entry (88,110 for 117,117), gravity zero, silent entity state 2 and
 * destination centre checkpoint; does not play effects or run arrival states. */
int v6_tower_route_teleport(V6TowerRoute *,int x,int y);
/* Returns 0 on unsupported exit/load failure (error is latched), 1 otherwise.
 * Renderer must rebuild both inactive banks after index changes; it owns DMA
 * and may pause logic while doing that. Unsupported exits leave an explicit
 * error; they are never treated as empty rooms or silently respawned. */
int v6_tower_route_step(V6TowerRoute *,unsigned input);
/* Optional live ordinary-room script phase, after input and before entity
 * updates/physics. Never called while dead or in the streamed tower. It may
 * change player motion and entity state, but must not load/change room banks.
 * A failed phase latches the route error before physics runs. */
typedef int (*V6TowerRoutePhase)(V6TowerRoute *,void *);
int v6_tower_route_step_phase(V6TowerRoute *,unsigned input,V6TowerRoutePhase,void *);
/* Ordinary non-wrapping room edges, in desktop vertical/horizontal order.
 * Each successful crossing resets physics history through route_load.
 * Missing/malformed destinations retain coordinates at the failed edge and
 * latch error. A prior successful vertical crossing remains committed. */
int v6_tower_route_boundary(V6TowerRoute *);
#endif
