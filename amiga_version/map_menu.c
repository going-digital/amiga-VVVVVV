#include "map_menu.h"
void v6_map_menu_init(V6MapMenu *m)
{
    m->open=m->mapheld=m->jumpheld=m->saved=m->failed=m->save_pending=0;
    m->page=0;
}
unsigned v6_map_menu_tick(V6MapMenu *m,unsigned b,int enabled,
    int transitioning,int script_running,int special)
{
    unsigned result=V6_MAP_NONE;
    int old;
    if(!m->open) {
        if(transitioning) {m->mapheld=1;return result;}
        if(!(b&V6_MAP_ENTER))m->mapheld=0;
        if(enabled && (b&V6_MAP_ENTER) && !m->mapheld) {
            m->open=m->mapheld=1;m->page=script_running?3:0;
            m->saved=m->failed=m->save_pending=0;
            return V6_MAP_OPENED;
        }
        return result;
    }
    if(transitioning) {m->mapheld=m->jumpheld=1;return result;}
    if(!(b&(V6_MAP_ACTION|V6_MAP_LEFT|V6_MAP_RIGHT)))m->jumpheld=0;
    if(!(b&V6_MAP_ENTER))m->mapheld=0;
    if(!m->mapheld && (b&V6_MAP_ENTER)) {
        m->open=0;result=V6_MAP_CLOSED;
    }
    old=m->page;
    if(!m->jumpheld) {
        if(b&(V6_MAP_ACTION|V6_MAP_LEFT|V6_MAP_RIGHT|V6_MAP_ENTER))m->jumpheld=1;
        if(!(script_running && m->page==3)) {
            if(b&V6_MAP_LEFT)--m->page;
            else if(b&V6_MAP_RIGHT)++m->page;
        }
        /* Source invokes the action before wrapping tabs. */
        if((b&V6_MAP_ACTION) && m->page==3 && !special &&
           !m->saved && !m->failed && !m->save_pending) {
            m->save_pending=1;result=V6_MAP_SAVE;
        }
        if(m->page<0)m->page=3;
        if(m->page>3)m->page=0;
    }
    if(result==V6_MAP_NONE && old!=m->page)result=V6_MAP_CHANGED;
    return result;
}
void v6_map_menu_save_result(V6MapMenu *m,int success)
{
    if(!m->save_pending)return;
    m->save_pending=0;m->saved=success!=0;m->failed=success==0;
}
