/* Adapted from Game.cpp pickup states and Input.cpp text advancement.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "trinket_screen.h"
void v6_trinket_screen_init(V6TrinketScreen *s)
{
    s->state=0;s->delay=0;s->control=1;s->stopped=0;
    s->bars=0;s->advance=0;s->visible=0;s->count=0;
}
unsigned v6_trinket_screen_begin(V6TrinketScreen *s,const V6Collect *bank,int music)
{
    int i;
    s->count=0;
    for(i=0;i<V6_COLLECT_COUNT;++i)if(v6_collect_has(bank,i))++s->count;
    s->state=1000;
    return V6_TRINKET_CUE | (music ? V6_TRINKET_SILENCE : 0);
}
int v6_trinket_screen_input(V6TrinketScreen *s,int action,int held)
{
    if(s->advance && action && !held) {++s->state;return 1;}
    return 0;
}
unsigned v6_trinket_screen_tick(V6TrinketScreen *s,int music)
{
    if(s->delay>0)--s->delay;
    if(s->delay>0)return 0;
    switch(s->state) {
    case 1000:
        s->bars=1;s->control=0;s->stopped=1;s->state=1001;s->delay=15;
        break;
    case 1001:
        s->advance=1;s->state=1002;s->visible=1;
        return V6_TRINKET_SHOW;
    case 1002:
        if(!s->advance)++s->state;
        break;
    case 1003:
        s->visible=0;s->control=1;s->advance=0;s->stopped=0;s->state=0;s->bars=0;
        return V6_TRINKET_HIDE | (music ? V6_TRINKET_FADE_IN : 0);
    }
    return 0;
}
