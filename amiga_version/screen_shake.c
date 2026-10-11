#include "screen_shake.h"
void v6_screen_shake_init(V6ScreenShake *state)
{
    if(state)state->x=state->y=0;
}
int v6_screen_shake_pre(V6ScreenShake *state,int timer,const uint16_t samples[2])
{
    if(!state)return 0;
    if(timer<=0)return 1;
    if(!samples)return 0;
    /* Signed division truncates toward zero, as the source's Sint32 cast. */
    state->x=(int16_t)(((int32_t)samples[0]*7-262144)/65536);
    state->y=(int16_t)(((int32_t)samples[1]*7-262144)/65536);
    return 1;
}
int v6_screen_shake_plan(const V6ScreenShake *state,int timer,int noflashing,
    int flip,V6ScreenShakePlan *out)
{
    V6ScreenShakePlan plan;
    int x=0,y=0;
    if(!state || !out || state->x < -4 || state->x > 2 ||
        state->y < -4 || state->y > 2)return 0;
    if(timer>0 && !noflashing) {
        x=state->x;y=flip?-state->y:state->y;
    }
    plan.x=(int16_t)x;plan.y=(int16_t)y;
    plan.source_x=(uint16_t)(x<0?-x:0);
    plan.source_y=(uint16_t)(y<0?-y:0);
    plan.destination_x=(uint16_t)(x>0?x:0);
    plan.destination_y=(uint16_t)(y>0?y:0);
    plan.width=(uint16_t)(320-(x<0?-x:x));
    plan.height=(uint16_t)(240-(y<0?-y:y));
    *out=plan;return 1;
}
