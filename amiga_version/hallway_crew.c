#include "hallway_crew.h"
int v6_hallway_crew_visible(int x,int y,const V6HallwayStory *s)
{
    return s && x==110 && y==104 && (!s->time_trial || s->translator_exploring)
        && s->companion==0 && !s->rescue_triggered && !s->red_rescued;
}
