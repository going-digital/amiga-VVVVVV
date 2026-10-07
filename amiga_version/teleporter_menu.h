#ifndef V6_TELEPORTER_MENU_H
#define V6_TELEPORTER_MENU_H
#include "teleporter.h"
/* Caller supplies source-ordered, explored, resident destinations only.
 * This state owns no gameplay or rendering data. Menu ticks pause gameplay.
 * Confirmation emits a request; the caller validates/loads the destination. */
typedef struct { int room_x,room_y; } V6TeleporterDestination;
typedef struct { unsigned ready,open,selected,held; int room_x,room_y; } V6TeleporterMenu;
enum { V6_TELE_MENU_LEFT=1,V6_TELE_MENU_RIGHT=2,V6_TELE_MENU_CONFIRM=4,
       V6_TELE_MENU_CANCEL=8 };
enum { V6_TELE_MENU_NONE=0,V6_TELE_MENU_OPENED=1,V6_TELE_MENU_CHANGED=2,
       V6_TELE_MENU_CLOSED=3,V6_TELE_MENU_TRAVEL=4 };
void v6_teleporter_menu_init(V6TeleporterMenu *);
/* Desktop Logic.cpp readiness: +25 inside the active region, -50 otherwise.
 * enabled means normal mode, alive, controllable, and no running script. */
void v6_teleporter_menu_ready(V6TeleporterMenu *,const V6TeleporterRegion *,
    const V6Player *,int enabled);
/* Opening requires interact (CONFIRM), readiness >20, integer abs(vx)<=1,
 * integer vy==0, and a current-room entry. All buttons must be released
 * between menu actions, matching Input.cpp's shared jumpheld latch.
 * Invalid destination lists retain state; travel output changes only on TRAVEL. */
unsigned v6_teleporter_menu_tick(V6TeleporterMenu *,const V6TeleporterDestination *,
    unsigned count,int room_x,int room_y,const V6Player *,unsigned buttons,
    V6TeleporterDestination *travel);
#endif
