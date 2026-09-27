#include "disappearing.h"
/* Life stays in 0..12; the narrow modulo uses 68000 DIVS, not libgcc. */
void v6_disappearing_init(V6Disappearing *p)
{ *p=(V6Disappearing){0,0,0,1,0}; }
void v6_disappearing_contact(V6Disappearing *p,int overlapping)
{ if(p->on_entity>0 && overlapping) p->state=p->on_entity; }
unsigned v6_disappearing_step(V6Disappearing *p)
{
    if(p->state==1) {
        p->life=12;p->state=2;p->on_entity=0;
        return V6_DISAPPEAR_SOUND;
    }
    if(p->state==2) {
        --p->life;
        if((short)p->life%3==0) ++p->walking_frame;
        if(p->life<=0) {
            p->state=3;p->invisible=1;
            return V6_DISAPPEAR_DISABLE;
        }
    } else if(p->state==4) {
        p->invisible=0;--p->walking_frame;p->state=5;p->on_entity=1;
        return V6_DISAPPEAR_CREATE;
    } else if(p->state==5) {
        p->life+=3;
        if((short)p->life%3==0) --p->walking_frame;
        if(p->life>=12) {p->life=12;p->state=0;++p->walking_frame;}
    }
    return 0;
}
unsigned v6_disappearing_death(V6Disappearing *p)
{
    unsigned events=0;
    if(p->state==3) p->state=4;
    else if(p->state==2) {
        while(p->state==2) events|=v6_disappearing_step(p);
        p->state=4;
    }
    return events;
}
