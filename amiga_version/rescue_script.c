#include "rescue_script.h"
int v6_rescue_start(V6RescueScript *v,const V6RescueProgram *normal,const V6RescueProgram *skip,int enabled)
{
    if(!v || !normal || !skip || !normal->ops || !skip->ops || !normal->count || !skip->count) return 0;
    v->normal=normal;v->skip=skip;v->program=normal;v->draft=v->speech=0;
    v->pc=v->error=v->delay=v->waiting=v->bars=v->following=0;
    v->ui_serial=v->cues=v->flips=0;v->active=v->control=v->mood=1;
    v->tile=0;v->tile_serial=0;
    v->skip_enabled=enabled!=0;v->fade=v->position=v->cue_speaker=0;
    return 1;
}
static void tick(V6RescueScript *v,int *rescued,int *companion,const V6RescueSignals *s)
{
    unsigned budget=64,bars_changed=0,fade_changed=0;
    if(!v || !v->active || !rescued || !companion || !s) return;
    if(v->delay) { --v->delay;return; }
    if(v->waiting) {
        if(!s->advance) return;
        v->waiting=0;
    }
    while(budget--) {
        const V6RescueOp *op;
        if(v->pc==v->program->count) { v->active=0;return; }
        if(v->pc>v->program->count) break;
        op=&v->program->ops[v->pc++];
        switch(op->op) {
        case V6_R_IF_SKIP:
            if(v->skip_enabled) { v->program=v->skip;v->pc=0; }
            break;
        case V6_R_BARS:bars_changed=v->bars!=(unsigned)(op->value!=0);v->bars=op->value!=0;break;
        case V6_R_FLOOR:
            if(s->onroof) { ++v->flips;return; }
            break;
        case V6_R_MOOD:v->mood=(unsigned)op->value;break;
        case V6_R_WAIT_BARS:
            if(bars_changed || !s->bars_ready) { --v->pc;return; }
            break;
        case V6_R_RESCUED:*rescued=1;break;
        case V6_R_CUE:v->cue_speaker=op->value;++v->cues;break;
        case V6_R_TEXT:
            if(!op->speech || !op->speech->count || op->speech->count>V6_RESCUE_MAX_LINES) goto failed;
            v->draft=op->speech;break;
        case V6_R_POSITION:v->position=op->value;break;
        case V6_R_SHOW:
            if(!v->draft) goto failed;
            v->speech=v->draft;v->waiting=1;v->control=0;++v->ui_serial;return;
        case V6_R_HIDE:v->speech=0;v->control=1;++v->ui_serial;break;
        case V6_R_FADE:fade_changed=v->fade!=op->value;v->fade=op->value;break;
        case V6_R_WAIT_FADE:
            if(fade_changed || !s->fade_ready) { --v->pc;return; }
            break;
        case V6_R_DELAY:
            if(op->value<0 || op->value>32767) goto failed;
            if(op->value) { v->delay=(unsigned)op->value-1;return; }
            break;
        case V6_R_COMPANION:*companion=op->value;break;
        case V6_R_FOLLOW:v->following=1;break;
        case V6_R_TILE:
            if(op->value<0 || op->value>255)goto failed;
            v->tile=op->value;++v->tile_serial;break;
        default:goto failed;
        }
    }
failed:
    v->error=1;v->active=v->waiting=0;v->speech=0;v->control=1;
}

void v6_rescue_tick(V6RescueScript *v,V6HallwayStory *story,const V6RescueSignals *s)
{ if(story)tick(v,&story->red_rescued,&story->companion,s); }
void v6_station_rescue_tick(V6RescueScript *v,V6StationStory *story,const V6RescueSignals *s)
{ if(story)tick(v,&story->yellow_rescued,&story->companion,s); }
