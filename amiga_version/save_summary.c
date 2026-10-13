#include "save_summary.h"
static int valid(const V6SaveClock *c)
{return c && c->minutes<60 && c->seconds<60 && c->frames<30;}
void v6_save_clock_init(V6SaveClock *c)
{c->hours=c->minutes=c->seconds=c->frames=0;}
int v6_save_clock_tick(V6SaveClock *c,int countdown)
{
    if(!valid(c))return 0;
    if(countdown>0)return 1;
    if(c->hours==65535 && c->minutes==59 && c->seconds==59 && c->frames==29)return 0;
    if(++c->frames>=30) {
        c->frames-=30;
        if(++c->seconds>=60) {
            c->seconds-=60;
            if(++c->minutes>=60) {c->minutes-=60;++c->hours;}
        }
    }
    return 1;
}
static char *digits(char *p,uint16_t value,int two)
{
    char reverse[5];unsigned n=0;
    do {reverse[n++]=(char)('0'+value%10);value/=10;}while(value);
    if(two && n==1)*p++='0';
    while(n)*p++=reverse[--n];
    return p;
}
int v6_save_clock_text(char out[12],const V6SaveClock *c)
{
    char *p=out;
    if(!out || !valid(c))return 0;
    if(c->hours) {p=digits(p,c->hours,0);*p++=':';}
    p=digits(p,c->minutes,c->hours!=0);*p++=':';
    p=digits(p,c->seconds,1);*p=0;return 1;
}
int v6_save_summary_capture(V6SaveSummary *out,const V6SaveClock *c,
    int x,int y,const V6Collect *collected,unsigned crew)
{
    unsigned i,count=0;
    if(!out || !valid(c) || !collected || (collected->bits[12]&0xf0) || crew>63 ||
       x<100 || x>119 || y<100 || y>119)return 0;
    for(i=0;i<100;++i)if(collected->bits[i>>3]&(1U<<(i&7)))++count;
    out->clock.hours=c->hours;out->clock.minutes=c->minutes;
    out->clock.seconds=c->seconds;out->clock.frames=c->frames;
    out->room_x=(int16_t)x;out->room_y=(int16_t)y;
    out->trinkets=(uint16_t)count;out->crew_mask=(uint16_t)crew;out->exists=1;return 1;
}
int v6_save_summary_publish(V6SaveSummary *out,const V6SaveSummary *candidate,int success)
{
    if(!out || !candidate || !success || candidate->exists!=1 ||
       !valid(&candidate->clock) || candidate->room_x<100 || candidate->room_x>119 ||
       candidate->room_y<100 || candidate->room_y>119 || candidate->trinkets>100 || candidate->crew_mask>63)return 0;
    out->clock.hours=candidate->clock.hours;out->clock.minutes=candidate->clock.minutes;
    out->clock.seconds=candidate->clock.seconds;out->clock.frames=candidate->clock.frames;
    out->room_x=candidate->room_x;out->room_y=candidate->room_y;
    out->trinkets=candidate->trinkets;out->crew_mask=candidate->crew_mask;out->exists=1;return 1;
}
