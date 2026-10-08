#ifndef V6_TELEPORTER_ARRIVAL_H
#define V6_TELEPORTER_ARRIVAL_H
#include "teleporter.h"
/* Normal, unlocked Game.cpp states 4010..4019 (Building/Energize).
 * Other destinations' special arrival scripts, departure and trial/no-death
 * modes are outside this core. Caller owns physics, effect decay and DOS. */
typedef struct { int state,delay,control,flash,shake,advance_text; unsigned events; } V6TeleporterArrival;
enum { V6_ARRIVAL_FLASH=1,V6_ARRIVAL_TELEPORT=2,V6_ARRIVAL_SAVE=4 };
void v6_teleporter_arrival_init(V6TeleporterArrival *);
/* Start after a successful normal teleport handoff. Active starts are refused. */
int v6_teleporter_arrival_start(V6TeleporterArrival *);
/* One Game::updatestate phase. Input runs first, locked by prior control;
 * call this before physics so state 4012's scripted ax/ay reach integration.
 * Entity state-2 update/animation remains separate. Effect requests are emitted
 * once; SAVE requests OS-safe persistence, never writes files here.
 * Invalid state/geometry retains all outputs. Inactive ticks clear events only. */
int v6_teleporter_arrival_tick(V6TeleporterArrival *,V6Player *,V6PlayerMotion *,
    int *invisible,V6Teleporter *,V6TeleporterRegion *);
#endif
