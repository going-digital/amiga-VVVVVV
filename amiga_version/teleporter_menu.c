/* Adapted from Logic.cpp readiness and Input.cpp normal TELEPORTERMODE.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "teleporter_menu.h"
void v6_teleporter_menu_init(V6TeleporterMenu *m)
{
    m->ready=m->open=m->selected=m->held=0;m->room_x=m->room_y=0;
}
void v6_teleporter_menu_ready(V6TeleporterMenu *m,const V6TeleporterRegion *r,
    const V6Player *p,int enabled)
{
    if(m->open)return;
    if(enabled && r->active && v6_player_overlaps(p,r->x,r->y,r->w,r->h)) {
        m->ready+=25;if(m->ready>255)m->ready=255;
    } else m->ready=m->ready>50?m->ready-50:0;
}
unsigned v6_teleporter_menu_tick(V6TeleporterMenu *m,const V6TeleporterDestination *d,
    unsigned count,int rx,int ry,const V6Player *p,unsigned buttons,
    V6TeleporterDestination *travel)
{
    unsigned i,j,current=count;
    if(!d || !count || !p || !travel || (buttons&~15u))return V6_TELE_MENU_NONE;
    for(i=0;i<count;++i) {
        if(d[i].room_x<100 || d[i].room_x>=120 || d[i].room_y<100 || d[i].room_y>=120)
            return V6_TELE_MENU_NONE;
        for(j=0;j<i;++j)
            if(d[i].room_x==d[j].room_x && d[i].room_y==d[j].room_y)return V6_TELE_MENU_NONE;
        if(d[i].room_x==rx && d[i].room_y==ry)current=i;
    }
    if(current==count || (m->open && (m->selected>=count || m->room_x!=rx || m->room_y!=ry)))
        return V6_TELE_MENU_NONE;
    if(!buttons){m->held=0;return V6_TELE_MENU_NONE;}
    if(m->held)return V6_TELE_MENU_NONE;
    m->held=1;
    if(!m->open) {
        if(!(buttons&V6_TELE_MENU_CONFIRM) || m->ready<=20 ||
           p->vx<=-2*V6_ONE || p->vx>=2*V6_ONE || p->vy<=-V6_ONE || p->vy>=V6_ONE)
            return V6_TELE_MENU_NONE;
        m->open=1;m->selected=current;m->room_x=rx;m->room_y=ry;
        return V6_TELE_MENU_OPENED;
    }
    if(buttons&V6_TELE_MENU_CANCEL){m->open=0;return V6_TELE_MENU_CLOSED;}
    if(buttons&V6_TELE_MENU_LEFT)m->selected=m->selected?m->selected-1:count-1;
    else if(buttons&V6_TELE_MENU_RIGHT)m->selected=m->selected+1==count?0:m->selected+1;
    if(buttons&V6_TELE_MENU_CONFIRM) {
        m->open=0;
        if(m->selected==current)return V6_TELE_MENU_CLOSED;
        *travel=d[m->selected];return V6_TELE_MENU_TRAVEL;
    }
    return buttons&(V6_TELE_MENU_LEFT|V6_TELE_MENU_RIGHT)?V6_TELE_MENU_CHANGED:V6_TELE_MENU_NONE;
}
