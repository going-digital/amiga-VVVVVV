/* Adapted from Entity.cpp teleporter animation; see ../LICENSE.md. */
#include "teleporter_animation.h"
int v6_teleporter_animate(V6TeleporterAnimation *a,int tile,int noflashing,unsigned choice)
{
    if(!a || choice>5) return 0;
    if(tile==1 || noflashing) a->frame=tile;
    else if(tile==2 || tile==6) {
        if(--a->delay<=0) {
            a->delay=tile==2?1:2;a->walking=(int)choice;
            if(a->walking>=4) {a->walking=tile==2?-1:-5;a->delay=4;}
        }
        a->frame=tile+a->walking;
    }
    return 1;
}
