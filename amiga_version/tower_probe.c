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
#include "tower_assets.h"
#include "tower_map.h"
struct ExecBase *SysBase;
struct GfxBase *GfxBase;
static volatile struct Custom * const hw=(void *)0xdff000;
#define LIST_WORDS 64
#define CHIP_BYTES (2*V6_TOWER_RING_BYTES+2*LIST_WORDS*2)
static V6TowerStream stream;
static V6TowerDraw draw[2];
static volatile ULONG frames;
/* Big-endian ULONG record, discoverable in emulator RAM dumps. */
static volatile struct {
    ULONG magic,version,status,frames,camera,max_work_lines,missed,error,chip_bytes;
} diag={0x56365450,1,0,0,0,0,0,0,CHIP_BYTES};
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
static int prepare(UBYTE *ring,UWORD *list,unsigned index,unsigned camera) {
    UWORD *p=list;unsigned i;
    if(!v6_tower_draw_prepare(&draw[index],ring,&stream,camera>>3,
        tower_tiles,TOWER_TILE_COUNT,0,0)) return 0;
    p=move(p,0x100,0x2200);p=move(p,0x102,0);p=move(p,0x104,0);
    p=move(p,0x108,0);p=move(p,0x10a,0);
    p=move(p,0x08e,0x3481);p=move(p,0x090,0x24c1);
    p=move(p,0x092,0x0038);p=move(p,0x094,0x00d0);
    for(i=0;i<4;++i) p=move(p,0x180+i*2,tower_palette[i]);
    return v6_tower_copper(p,(ULONG)ring,camera&255)!=0;
}
static int run(void) {
    UBYTE *chip,*rings[2];UWORD *lists[2];
    UWORD dma,ints,adk;APTR old_irq;struct View *view;
    unsigned back=1,camera=0;ULONG start,work,previous;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    if(SysBase->AttnFlags&AFF_68010) return 20;
    GfxBase=(struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    if(!GfxBase) return 20;
    if(!(GfxBase->DisplayFlags&PAL)) { CloseLibrary((struct Library *)GfxBase);return 20; }
    chip=AllocMem(CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    if(!chip) { CloseLibrary((struct Library *)GfxBase);return 20; }
    rings[0]=chip;rings[1]=chip+V6_TOWER_RING_BYTES;
    lists[0]=(UWORD *)(chip+2*V6_TOWER_RING_BYTES);lists[1]=lists[0]+LIST_WORDS;
    if(!v6_tower_open(&stream,tower_map,sizeof(tower_map)) ||
       !prepare(rings[0],lists[0],0,0)) {
        FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
    }
    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
    OwnBlitter();WaitBlit();Forbid();Disable();
    dma=hw->dmaconr;ints=hw->intenar;adk=hw->adkconr;
    hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l 0x6c.w,%0":"=r"(old_irq));
    __asm volatile("move.l %0,0x6c.w"::"r"((APTR)irq):"memory");
    blank();hw->cop1lc=(ULONG)lists[0];hw->copjmp1=0;
    hw->dmacon=DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER;
    hw->intena=INTF_SETCLR|INTF_INTEN|INTF_VERTB;Enable();diag.status=1;
    /* Warm the second ring before measuring incremental row work. */
    if(!prepare(rings[1],lists[1],1,0)) diag.error=1;
    blank();previous=frames;
    while((*(volatile UBYTE *)0xbfe001&0x40) && !diag.error) {
        start=clock_lines();
        ++camera;if(camera==5600) camera=0;
        if(!prepare(rings[back],lists[back],back,camera)) { diag.error=2;break; }
        work=clock_lines()-start;if(work>diag.max_work_lines) diag.max_work_lines=work;
        blank();
        if(frames-previous>1) diag.missed+=frames-previous-1;
        previous=frames;
        /* Completed inactive list becomes next frame's list before vertical restart. */
        hw->cop1lc=(ULONG)lists[back];back^=1;
        diag.camera=camera;diag.frames=frames;
    }
    Disable();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l %0,0x6c.w"::"r"(old_irq):"memory");
    hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
    hw->adkcon=adk|0x8000;hw->dmacon=dma|0x8000;hw->intena=ints|0x8000;
    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=2;
    FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return diag.error?20:0;
}
int __attribute__((used,section(".text.unlikely"))) _start(void) { return run(); }
