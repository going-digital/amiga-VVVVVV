#include "music_control.h"
#include "music_area.h"
/* Products are bounded by 128*60000; every quotient fits 16 bits. Narrow
 * operands use native MULU and DIVU on 68000, with no libgcc runtime. */
static unsigned scaled(unsigned gain,unsigned elapsed,unsigned duration)
{
 uint32_t product=(uint32_t)(uint16_t)gain*(uint16_t)elapsed;
#ifdef __m68k__
 uint16_t divisor=(uint16_t)duration;
 __asm volatile("divu.w %1,%0":"+d"(product):"d"(divisor):"cc");
 return (uint16_t)product;
#else
 return product/duration;
#endif
}
static int valid(const V6MusicControl *m,const V6MusicPlan *p)
{
 return m && p && m->current>=-1 && m->current<16 && m->halted_song>=-1 && m->halted_song<16 &&
 m->queued>=-1 && m->queued<16 && m->volume>=0 && m->volume<=128 &&
 m->available>=0 && m->available<=65535 && m->duration>=0 && m->duration<=60000 &&
 m->elapsed>=0 && m->elapsed<=61000 && m->start>=0 && m->start<=128 && m->end>=0 && m->end<=128 &&
 (unsigned)m->nice<=1 && (unsigned)m->quick<=1 && (unsigned)m->safe<=1 &&
 (unsigned)m->fade_in<=1 && (unsigned)m->fade_out<=1 &&
 (unsigned)m->present<=1 && (unsigned)m->paused<=1 && !(m->fade_in && m->fade_out);
}
static void emit(V6MusicPlan *p,int kind,int track,int value)
{V6MusicOp *o=&p->ops[p->count++];o->kind=kind;o->track=track;o->value=value;}
static int halted(const V6MusicControl *m){return m->paused || !m->present;}
static void pause_music(V6MusicControl *m,V6MusicPlan *p)
{if(m->present){m->paused=1;emit(p,V6_MUSIC_STOP_CLOCK,-1,0);}}
static void halt_music(V6MusicControl *m,int from_fade,V6MusicPlan *p)
{
 pause_music(m,p);m->halted_song=m->current;m->current=-1;m->fade_in=m->fade_out=0;
 if(!from_fade){m->nice=0;m->queued=-1;}
}
static void resume_music(V6MusicControl *m,V6MusicPlan *p)
{
 if(m->current==-1){m->current=m->halted_song;m->halted_song=-1;}
 if(m->present){m->paused=0;emit(p,V6_MUSIC_RESUME_CLOCK,-1,0);}
}
static void fade_in(V6MusicControl *m,int ms,V6MusicPlan *p)
{
 if(halted(m))return;
 m->fade_in=1;m->fade_out=0;m->volume=0;
 emit(p,V6_MUSIC_GAIN,-1,0);m->elapsed=0;m->duration=ms;m->start=0;m->end=128;
}
static void fade_out(V6MusicControl *m,int ms)
{
 if(halted(m))return;
 m->fade_in=0;m->fade_out=1;m->elapsed=0;m->duration=(int32_t)scaled((unsigned)m->volume,(unsigned)ms,128);
 m->start=m->volume;m->end=0;
}
static void play(V6MusicControl *m,int track,V6MusicPlan *p)
{
 m->safe=1;if(m->current==track && !m->fade_out)return;
 m->current=track;m->halted_song=-1;if(track==-1)return;
 if(track==0 || track==7) {
  if(m->available&(1U<<track)) {
   m->present=1;m->paused=0;emit(p,V6_MUSIC_START,track,0);
   m->fade_in=m->fade_out=0;m->volume=128;emit(p,V6_MUSIC_GAIN,-1,128);
  }
 } else if(m->fade_out) {
  m->queued=track;m->nice=1;m->current=-1;
  if(m->quick)fade_out(m,500);else m->quick=1;
 } else if(m->available&(1U<<track)) {
  m->present=1;m->paused=0;emit(p,V6_MUSIC_START,track,1);
  m->fade_in=m->fade_out=0;fade_in(m,3000,p);
 }
}
int v6_music_init(V6MusicControl *m,unsigned available)
{
 if(!m || available>65535)return 0;
 m->current=m->halted_song=m->queued=-1;m->quick=1;
 m->nice=m->safe=m->fade_in=m->fade_out=m->volume=m->present=0;m->paused=1;
 m->available=(int32_t)available;m->start=m->end=m->duration=m->elapsed=0;return 1;
}
int v6_music_command(V6MusicControl *m,unsigned command,int arg,V6MusicPlan *p)
{
 if(!valid(m,p) || command>V6_MUSIC_SILENCE ||
 (command==V6_MUSIC_PLAY && (arg< -1 || arg>15)) ||
 (command==V6_MUSIC_NICEPLAY && (arg<0 || arg>15)) ||
 (command==V6_MUSIC_FADE_OUT && (arg<0 || arg>1)) ||
 ((command==V6_MUSIC_RESUME_FADE || command==V6_MUSIC_FADE_IN) && (arg<0 || arg>60000)))return 0;
 p->count=0;
 switch(command) {
 case V6_MUSIC_PLAY:play(m,arg,p);break;
 case V6_MUSIC_NICEPLAY:
  if(m->current!=arg){if(m->current!=-1){fade_out(m,2000);m->quick=0;}m->nice=1;}
  m->queued=arg;break;
 case V6_MUSIC_PAUSE:pause_music(m,p);break;
 case V6_MUSIC_HALT:halt_music(m,0,p);break;
 case V6_MUSIC_RESUME:resume_music(m,p);break;
 case V6_MUSIC_RESUME_FADE:resume_music(m,p);fade_in(m,arg,p);break;
 case V6_MUSIC_FADE_OUT:fade_out(m,arg?500:2000);m->quick=arg;break;
 case V6_MUSIC_FADE_IN:fade_in(m,arg,p);break;
 case V6_MUSIC_SILENCE:m->volume=0;m->fade_in=m->fade_out=0;emit(p,V6_MUSIC_GAIN,-1,0);break;
 }
 return 1;
}
int v6_music_tick(V6MusicControl *m,unsigned ms,V6MusicPlan *p)
{
 int finished=0,old;
 if(!valid(m,p) || ms>1000)return 0;
 p->count=0;if(!m->safe)return 1;
 if(m->fade_in || m->fade_out) {
  old=m->volume;
  if(!m->duration || m->start==m->end || m->elapsed>=m->duration) {
   m->volume=m->end;m->elapsed=0;finished=1;
  } else {
   int delta=m->end-m->start;
   int change=(int)scaled((unsigned)(delta<0?-delta:delta),(unsigned)m->elapsed,(unsigned)m->duration);
   m->volume=m->start+(delta<0?-change:change);m->elapsed+=(int32_t)ms;
  }
  if(old!=m->volume)emit(p,V6_MUSIC_GAIN,-1,m->volume);
  if(finished){if(m->fade_out)halt_music(m,1,p);else m->fade_in=0;}
 }
 if(m->nice && halted(m)){play(m,m->queued,p);m->queued=-1;m->nice=0;}
 return 1;
}

int v6_music_change_area(V6MusicControl *m,int x,int y,int script_running,
    int flip_mode,int time_trial,V6MusicPlan *p)
{
 int track;
 if(!valid(m,p) || !v6_music_area_track(x,y,script_running,flip_mode,time_trial,&track))return 0;
 if(track==-1){p->count=0;return 1;}
 return v6_music_command(m,V6_MUSIC_NICEPLAY,track,p);
}

int v6_music_enter_room(V6MusicControl *m,int x,int y,int final_mode,
    int custom_mode,int script_running,int flip_mode,int time_trial,V6MusicPlan *p)
{
 int track;
 if(!valid(m,p) || !v6_music_entry_track(x,y,final_mode,custom_mode,script_running,flip_mode,time_trial,&track))return 0;
 if(track==-1){p->count=0;return 1;}
 return v6_music_command(m,V6_MUSIC_NICEPLAY,track,p);
}
