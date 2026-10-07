#include "save_controls.h"
unsigned v6_save_controls_tick(V6SaveControls *s,int right,int fire)
{
    unsigned action=0;
    if(!fire)s->suppress_fire=0;
    if(right && fire)s->suppress_fire=1;
    if(right && !s->right_down)action=fire?V6_SAVE_ACTION_LOAD:V6_SAVE_ACTION_SAVE;
    s->right_down=right!=0;return action;
}
unsigned v6_save_controls_filter(const V6SaveControls *s,unsigned input)
{ return s->suppress_fire?input&~V6_FLIP:input; }
