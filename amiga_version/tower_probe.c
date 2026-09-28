/* Standalone PAL tower display experiment; left mouse exits. */
#include <proto/exec.h>
#include <proto/graphics.h>
#include <graphics/gfxbase.h>
#include <exec/execbase.h>
#include <hardware/custom.h>
#include <hardware/dmabits.h>
#include <hardware/intbits.h>
#include "tower_draw.h"
#include "tower_copper.h"
#include "tower_camera.h"
#include "tower_session.h"
#include "tower_assets.h"
#include "tower_map.h"
#include "tower_background_map.h"
#include "tower_backdrop.h"
struct ExecBase *SysBase;
struct GfxBase *GfxBase;
static volatile struct Custom * const hw=(void *)0xdff000;
/* Test-only fixed camera; negative selects the moving seam route. */
#ifndef V6_TOWER_HOLD
#define V6_TOWER_HOLD -1
#endif
/* Synthetic stress step, not the desktop camera controller. */
#ifndef V6_TOWER_STEP
#define V6_TOWER_STEP 1
#endif
#if V6_TOWER_STEP != 1 && V6_TOWER_STEP != 4 && V6_TOWER_STEP != 8 && V6_TOWER_STEP != 12 && V6_TOWER_STEP != 16
#error Unsupported tower stress step
#endif
#ifdef V6_TOWER_FULL_ROUTE
#define CAMERA_MIN 0
#else
#define CAMERA_MIN 5344
#endif
#define CAMERA_MAX 5856
#define LIST_WORDS 64
#define LAYER_BYTES (V6_TOWER_RING_BYTES+V6_TOWER_PLANE_BYTES)
#define CHIP_BYTES (2*LAYER_BYTES+2*LIST_WORDS*2)
static V6TowerStream stream,background_stream;
static V6TowerDraw draw[2],background_draw[2];
static UBYTE *rings[2];
static unsigned prepared_camera[2];
static volatile ULONG frames;
/* Big-endian ULONG record, discoverable in emulator RAM dumps. */
static volatile struct {
    ULONG magic,version,status,frames,camera,max_work_lines,missed,error,chip_bytes;
    ULONG forward_wraps,reverse_wraps,max_rows,max_copied;
    ULONG step,route_min,route_max,visited_min,visited_max;
    ULONG logic_ticks,logic_frames,logic_remainder;
    ULONG camera_mode,recovery_calls,recovery_life,recovery_delay,recovery_seek_frames;
} diag={0x56365450,6,0,0,0,0,0,0,CHIP_BYTES,0,0,0,0,
    V6_TOWER_STEP,CAMERA_MIN,CAMERA_MAX,CAMERA_MAX,0,0,0,0,0,0,0,0,0};
#ifdef V6_TOWER_RECOVERY
/* Test-only bounded trace: all camera fields plus callback state. Stored
 * outside the Chip allocation; count is published after a complete record. */
#define CAMERA_TRACE_TICKS 128
static volatile struct {
    ULONG magic,version,count,capacity;
    int16_t records[CAMERA_TRACE_TICKS][13];
    int32_t players[CAMERA_TRACE_TICKS][12];
} camera_trace={0x56364354,2,0,CAMERA_TRACE_TICKS,{{0}},{{0}}};
static void trace_camera(const V6TowerCamera *c,int life,int delay)
{
    volatile int16_t *r;
    if(camera_trace.count>=CAMERA_TRACE_TICKS) return;
    r=camera_trace.records[camera_trace.count];
    r[0]=c->y;r[1]=c->old_y;r[2]=c->mode;r[3]=c->seek;
    r[4]=c->seek_frames;r[5]=c->spike_top;r[6]=c->spike_bottom;
    r[7]=c->old_spike_top;r[8]=c->old_spike_bottom;r[9]=c->colour_superstate;
    r[10]=life;r[11]=delay;r[12]=(int16_t)diag.recovery_calls;
    ++camera_trace.count;
}
static V6TowerSession session;
#endif
static UWORD beam(void) { return (*(volatile ULONG *)0xdff004>>8)&511; }
static ULONG clock_lines(void) {
    ULONG a,b; UWORD y;
    do { a=frames;y=beam();b=frames; } while(a!=b);
    return a*312+y;
}
static void blank(void) {
    while(beam()==311) {} while(beam()!=311) {}
}
static void __attribute__((interrupt)) irq(void) {
    ++frames;hw->intreq=INTF_VERTB;hw->intreq=INTF_VERTB;
}
static UWORD *move(UWORD *p,UWORD reg,UWORD value) {
    *p++=reg;*p++=value;return p;
}
/* Copy matching cached rows from the read-only front ring. Each blit is
 * complete before its cache tag is published or CPU rendering begins. */
static void wait_blit(void)
{
    (void)hw->dmaconr;
    while(hw->dmaconr&DMAF_BLTDONE) {}
}
static unsigned reuse_rows(V6TowerDraw *dst_cache,const V6TowerDraw *src_cache,
    UBYTE *dst,const UBYTE *src,int top,unsigned planes)
{
    int row;unsigned copied=0;
    for(row=top;row<top+31;++row) {
        unsigned slot=(unsigned)row&31,plane;
        ULONG bit=1UL<<slot;
        if((dst_cache->valid&bit) && dst_cache->tags[slot]==row) continue;
        if(!(src_cache->valid&bit) || src_cache->tags[slot]!=row) continue;
        for(plane=0;plane<planes;++plane) {
            unsigned offset=slot*320+plane*V6_TOWER_PLANE_BYTES;
            wait_blit();
            hw->bltcon0=0x09f0;hw->bltcon1=0;
            hw->bltafwm=hw->bltalwm=0xffff;
            hw->bltamod=hw->bltdmod=0;
            hw->bltapt=(APTR)(src+offset);hw->bltdpt=dst+offset;
            hw->bltsize=(8<<6)|20;
        }
        wait_blit();
        dst_cache->tags[slot]=(int16_t)row;dst_cache->valid|=bit;++copied;
    }
    return copied;
}
static int prepare(UBYTE *ring,UWORD *list,unsigned index,unsigned camera,unsigned *drawn) {
    UWORD *p=list;unsigned i,background_rows,copied;
    copied=0;
    /* Small advances cost less to redraw than to scan and copy from peer. */
    if(camera>prepared_camera[index]+8 || prepared_camera[index]>camera+8) {
        copied=reuse_rows(&draw[index],&draw[index^1],ring,rings[index^1],camera>>3,2);
        copied+=reuse_rows(&background_draw[index],&background_draw[index^1],
            ring+V6_TOWER_RING_BYTES,rings[index^1]+V6_TOWER_RING_BYTES,camera>>4,1);
    }
    prepared_camera[index]=camera;
    if(drawn && copied>diag.max_copied) diag.max_copied=copied;
    if(!v6_tower_draw_prepare(&draw[index],ring,&stream,camera>>3,
        tower_tiles,TOWER_TILE_COUNT,0,drawn)) return 0;
    if(!v6_tower_draw_mono_prepare(&background_draw[index],ring+V6_TOWER_RING_BYTES,
        &background_stream,camera>>4,tower_backdrop,TOWER_TILE_COUNT,&background_rows)) return 0;
    if(drawn) *drawn+=background_rows;
    p=move(p,0x100,0x3600);p=move(p,0x102,0);p=move(p,0x104,0);
    p=move(p,0x108,0);p=move(p,0x10a,0);
    p=move(p,0x08e,0x3481);p=move(p,0x090,0x24c1);
    p=move(p,0x092,0x0038);p=move(p,0x094,0x00d0);
    for(i=0;i<4;++i) p=move(p,0x180+i*2,tower_palette[i]);
    p=move(p,0x192,0x223);
    return v6_tower_dual_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
        camera&255,(camera>>1)&255)!=0;
}
static int run(void) {
    UBYTE *chip;UWORD *lists[2];
    UWORD dma,ints,adk;APTR old_irq;struct View *view;
    /* Keep logical coordinates continuous across the 700-row source seam.
     * Only the stream wraps source rows; physical ring slots use logical rows.
     * A bounded back-and-forth route exercises both directions indefinitely. */
    unsigned back=1,camera=V6_TOWER_HOLD>=0?V6_TOWER_HOLD:CAMERA_MIN,drawn;int direction=1;
    ULONG start,work,previous;
#ifdef V6_TOWER_CONTROLLER
    static V6TowerCamera controller;
    ULONG logic_frame,elapsed=0;
#ifdef V6_TOWER_RECOVERY
    v6_tower_session_init(&session,144,300,1,0);
    session.player.x=80;session.player.y=450;session.player.gravity=0;
    session.player.vx=V6_ONE;session.player.vy=-V6_ONE;
    session.player.old_x=79;session.player.old_y=451;
#endif
    camera=0;diag.step=0;diag.route_min=0;diag.route_max=5368;
    (void)direction;
#endif
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    if(SysBase->AttnFlags&AFF_68010) return 20;
    GfxBase=(struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    if(!GfxBase) return 20;
    if(!(GfxBase->DisplayFlags&PAL)) { CloseLibrary((struct Library *)GfxBase);return 20; }
    chip=AllocMem(CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    if(!chip) { CloseLibrary((struct Library *)GfxBase);return 20; }
    rings[0]=chip;rings[1]=chip+LAYER_BYTES;
    lists[0]=(UWORD *)(chip+2*LAYER_BYTES);lists[1]=lists[0]+LIST_WORDS;
    if(!v6_tower_open(&stream,tower_map,sizeof(tower_map)) ||
       !v6_tower_open(&background_stream,tower_background_map,sizeof(tower_background_map)) ||
       !prepare(rings[0],lists[0],0,camera,0)) {
        FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
    }
    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
    OwnBlitter();WaitBlit();Forbid();Disable();
    dma=hw->dmaconr;ints=hw->intenar;adk=hw->adkconr;
    hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l 0x6c.w,%0":"=r"(old_irq));
    __asm volatile("move.l %0,0x6c.w"::"r"((APTR)irq):"memory");
    blank();hw->cop1lc=(ULONG)lists[0];hw->copjmp1=0;
    hw->dmacon=DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER;
    hw->intena=INTF_SETCLR|INTF_INTEN|INTF_VERTB;Enable();diag.status=1;
    /* Warm the second ring before measuring incremental row work. */
    if(!prepare(rings[1],lists[1],1,camera,0)) diag.error=1;
    blank();previous=frames;
#ifdef V6_TOWER_CONTROLLER
    logic_frame=frames;
#endif
    while((*(volatile UBYTE *)0xbfe001&0x40) && !diag.error) {
        start=clock_lines();
#ifdef V6_TOWER_CONTROLLER
        {
            ULONG now=frames,delta=now-logic_frame;
            logic_frame=now;elapsed+=delta*19968UL;diag.logic_frames+=delta;
            while(elapsed>=34000) {
                elapsed-=34000;
#ifdef V6_TOWER_RECOVERY
                if(diag.logic_ticks==60) v6_tower_session_die(&session);
                v6_tower_session_tick(&session,1,0,0);
                diag.recovery_calls=session.life_calls;
                diag.recovery_life=session.life_timer;diag.recovery_delay=session.resume_delay;
                diag.recovery_seek_frames=session.camera.seek_frames;
                if(camera_trace.count<CAMERA_TRACE_TICKS) {
                    volatile int32_t *r=camera_trace.players[camera_trace.count];
                    r[0]=session.player.x;r[1]=session.player.y;r[2]=session.player.vx;r[3]=session.player.vy;
                    r[4]=session.player.gravity;r[5]=session.player.dir;r[6]=session.death_timer;
                    r[7]=session.invisible;r[8]=session.deaths;r[9]=session.respawns;
                    r[10]=session.player.old_x;r[11]=session.player.old_y;
                }
                trace_camera(&session.camera,session.life_timer,session.resume_delay);
                /* Trace owns real player state; no externally supplied life count. */
                controller.y=session.camera.y;controller.mode=session.camera.mode;
#else
                v6_tower_camera_tick(&controller,0,0,1,0,0);
#endif
                diag.camera_mode=controller.mode;
                ++diag.logic_ticks;
            }
            camera=controller.y;diag.camera=camera;diag.logic_remainder=elapsed;
        }
#else
        if(V6_TOWER_HOLD<0) {
            if(camera==CAMERA_MAX) direction=-1;
            if(camera==CAMERA_MIN) direction=1;
            if(direction>0) {
                if(camera<5600 && camera+V6_TOWER_STEP>=5600) ++diag.forward_wraps;
                camera+=V6_TOWER_STEP;
                if(camera>CAMERA_MAX) camera=CAMERA_MAX;
            } else {
                if(camera>=5600 && camera-V6_TOWER_STEP<5600) ++diag.reverse_wraps;
                camera=camera<CAMERA_MIN+V6_TOWER_STEP?CAMERA_MIN:camera-V6_TOWER_STEP;
            }
        }
#endif
        if(!prepare(rings[back],lists[back],back,camera,&drawn)) { diag.error=2;break; }
        if(drawn>diag.max_rows) diag.max_rows=drawn;
        work=clock_lines()-start;if(work>diag.max_work_lines) diag.max_work_lines=work;
        blank();
        if(frames-previous>1) diag.missed+=frames-previous-1;
        previous=frames;
        /* Completed inactive list becomes next frame's list before vertical restart. */
        hw->cop1lc=(ULONG)lists[back];back^=1;
        diag.camera=camera;diag.frames=frames;
        if(camera<diag.visited_min) diag.visited_min=camera;
        if(camera>diag.visited_max) diag.visited_max=camera;
    }
    Disable();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l %0,0x6c.w"::"r"(old_irq):"memory");
    hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
    hw->adkcon=adk|0x8000;hw->dmacon=dma|0x8000;hw->intena=ints|0x8000;
    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=2;
    FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return diag.error?20:0;
}
int __attribute__((used,section(".text.unlikely"))) _start(void) { return run(); }
