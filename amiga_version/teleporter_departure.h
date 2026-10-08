#ifndef V6_TELEPORTER_DEPARTURE_H
#define V6_TELEPORTER_DEPARTURE_H
#include "teleporter.h"
/* Normal selector departure, Input.cpp and Game.cpp states 4000..4003.
 * Caller owns entity colours, input/physics, effect decay/rendering and travel. */
typedef struct {
    int state,delay,control,flash,shake,locked,travel;
    unsigned events;
} V6TeleporterDeparture;
enum { V6_DEPARTURE_FLASH=1,V6_DEPARTURE_TELEPORT=2,V6_DEPARTURE_TRAVEL=4 };
void v6_teleporter_departure_init(V6TeleporterDeparture *);
/* Start after a validated remote menu selection. Disables the active region
 * and player control, selects the flashing teleporter tile. Player colour is
 * flashing until state 4002 restores cyan; visibility is unchanged at start.
 * Active, locked or unconsumed travel requests are refused without mutation. */
int v6_teleporter_departure_start(V6TeleporterDeparture *,V6Teleporter *,V6TeleporterRegion *);
/* Run after locked input, before entity updates/physics. State 4003 unlocks
 * state and emits TRAVEL once. The travel flag persists until the caller
 * clears it after a successful room handoff, as Script::teleport does.
 * No room load, checkpoint change, file I/O or player-motion change occurs.
 * Invalid state/delay/geometry retains all outputs; inactive ticks clear events. */
int v6_teleporter_departure_tick(V6TeleporterDeparture *,int *invisible,V6Teleporter *);
#endif
