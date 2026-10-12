#ifndef V6_MAP_MENU_H
#define V6_MAP_MENU_H
/* Normal campaign's four map tabs only. Caller pauses gameplay while open,
 * renders the transition, performs SAVE, and reports its result. Ship warp,
 * pause/quit pages and special modes are deliberately outside this core. */
typedef struct {
    unsigned open,mapheld,jumpheld,saved,failed,save_pending;
    int page;
} V6MapMenu;
enum { V6_MAP_ENTER=1,V6_MAP_LEFT=2,V6_MAP_RIGHT=4,V6_MAP_ACTION=8 };
enum { V6_MAP_NONE=0,V6_MAP_OPENED=1,V6_MAP_CHANGED=2,
       V6_MAP_CLOSED=3,V6_MAP_SAVE=4 };
void v6_map_menu_init(V6MapMenu *);
/* enabled: normal campaign and no higher-priority interaction consumed ENTER.
 * transitioning gates menu input exactly as desktop menuoffset does.
 * script_running locks navigation on the Save tab, matching Input.cpp.
 * special disables saving. Opening never emits SAVE. */
unsigned v6_map_menu_tick(V6MapMenu *,unsigned buttons,int enabled,
    int transitioning,int script_running,int special);
/* A completed attempt (including failure) cannot repeat until next opening. */
void v6_map_menu_save_result(V6MapMenu *,int success);
#endif
