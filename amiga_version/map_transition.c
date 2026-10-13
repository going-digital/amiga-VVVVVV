#include "map_transition.h"
void v6_map_transition_init(V6MapTransition *t)
{
    t->active=t->closing=0;t->previous=t->offset=240;
}
void v6_map_transition_open(V6MapTransition *t)
{
    t->active=1;t->closing=0;t->previous=t->offset=240;
}
void v6_map_transition_close(V6MapTransition *t)
{
    if(t->active)t->closing=1;
}
unsigned v6_map_transition_tick(V6MapTransition *t)
{
    if(!t->active)return 0;
    t->previous=t->offset;
    if(t->closing) {
        t->offset+=25;
        if(t->offset>=240) {
            t->offset=240;t->active=t->closing=0;return 1;
        }
    } else if(t->offset>0) {
        t->offset=t->offset>25?t->offset-25:0;
    }
    return 0;
}
unsigned v6_map_transition_offset(const V6MapTransition *t,unsigned remainder)
{
    unsigned short weighted;
    if(remainder>34)remainder=34;
    /* Nonnegative weighted endpoints preserve source float-to-int truncation
       during both directions (including the final 15-pixel step). */
    weighted=(unsigned short)(t->previous*(34-remainder)+t->offset*remainder);
    return weighted/34;
}
unsigned v6_map_transition_input_locked(const V6MapTransition *t)
{
    return t->active && (t->closing || t->offset!=0);
}
