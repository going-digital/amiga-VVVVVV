/* Native hardware fixture for the first station terminal; not campaign admission.
 * Original room/actors/scripts: Terry Cavanagh; see ../LICENSE.md. */
#include <proto/exec.h>
#include <proto/graphics.h>
#include <proto/cia.h>
#include <graphics/gfxbase.h>
#include <exec/execbase.h>
#include <hardware/custom.h>
#include <hardware/dmabits.h>
#include <hardware/intbits.h>
#include "activity.h"
#include "terminal.h"
#include "terminal_read.h"
#include "keyboard.h"
#include "map_menu.h"
#include "enemy.h"
#include "sprites.h"
#include "audio.h"
#include "terminal_fixture_assets.h"
#include "terminal_station_program.h"
struct ExecBase *SysBase;
struct GfxBase *GfxBase;
static struct Custom *const hw=(struct Custom *)0xdff000;
static struct Library *cia;
static volatile ULONG frames;
static V6Keyboard keys;
static V6TerminalRead reader;
static V6Terminal terminal;
static V6Player player;
static V6Enemy enemies[2];
static V6Terrain terrain;
static V6Block activity={248,200,20,16,V6_ACTIVITY,6};
static V6Room room;
static V6Audio audio;
static volatile struct {ULONG magic,version,status,frames,ticks,max_work,missed,error,chip_bytes,
    opens,closes,touch_cues,read_cues,audio_starts,audio_completed,clipped,visible,bars,phase,buttons;
    LONG enemy_x[2],enemy_y[2];ULONG ui_bitmap,list,sprite_dma,samples,period,sample_bytes;} diag={.magic=0x5636544e,.version=1};
#define BITMAP_BYTES 28800
#define DMA_BYTES (8*V6_SPRITE_WORDS*2)
#define LIST_BYTES 256
#define CHIP_BYTES (4*BITMAP_BYTES+2*DMA_BYTES+2*LIST_BYTES+FIXTURE_AUDIO_BYTES)
static UWORD beam(void){UWORD a,b,c;do{a=hw->vposr;b=hw->vhposr;c=hw->vposr;}while((a^c)&1);return ((a&1)<<8)|(b>>8);}
static void blank(void){while(beam()==311){}while(beam()!=311){}}
static void __attribute__((interrupt)) irq(void){++frames;hw->intreq=INTF_VERTB;hw->intreq=INTF_VERTB;}
static ULONG clock_lines(void){ULONG a,b;UWORD y,p;do{a=frames;y=beam();p=y<4?(hw->intreqr&INTF_VERTB):0;b=frames;}while(a!=b || p);return a*312+y;}
static void poll(void){
    if(SetICR(cia,8)&8){UBYTE serial=*(volatile UBYTE *)0xbfec01;volatile UBYTE *cra=(volatile UBYTE *)0xbfee01;
        UBYTE old=*cra;UWORD y;unsigned i;*cra=old|0x40;
        for(i=0;i<3;++i){y=beam();while(beam()==y){}}
        *cra=(*cra&0xbf)|(old&0x40);v6_keyboard_receive(&keys,serial);}
}
static UWORD *reg(UWORD *p,unsigned r,unsigned v){*p++=(UWORD)r;*p++=(UWORD)v;return p;}
static void apply(const V6AudioPlan *p){unsigned i;for(i=0;i<p->count;++i)*(volatile UWORD *)((ULONG)hw+p->writes[i].reg)=(UWORD)p->writes[i].value;}
static void cue(UBYTE *samples,unsigned which){
    V6AudioPlan p;V6AudioSample s;
    s.address=(ULONG)(samples+(which?sizeof(fixture_sound0):0));s.bytes=which?sizeof(fixture_sound1):sizeof(fixture_sound0);s.period=FIXTURE_PERIOD;s.volume=64;
    if(!v6_audio_request(&audio,&s,&p)){diag.error=3;return;}apply(&p);
    diag.samples=s.address;diag.period=s.period;diag.sample_bytes=s.bytes;
}
static void sprite_occlude(UWORD *d){
    unsigned start=((d[0]>>8)|((d[1]&4)<<6)),stop=((d[1]>>8)|((d[1]&2)<<7));
    int x=(d[0]&255)*2+(d[1]&1)-128;unsigned y;
    if(!d[0] && !d[1])return;
    for(y=start;y<stop;++y){unsigned bits=0;
        if(y>=52 && y<292 && x>=0 && x<320){
            const UBYTE *row=fixture_cover+(y-52)*40;
            unsigned at=(unsigned)x>>3,shift=(unsigned)x&7;
            ULONG packed=(ULONG)row[at]<<16;
            if(at<39)packed|=(ULONG)row[at+1]<<8;
            if(at<38)packed|=row[at+2];
            bits=(packed>>(8-shift))&65535U;
        }
        if(bits){unsigned at=2+(y-start)*2,old=d[at]|d[at+1];d[at]&=(UWORD)~bits;d[at+1]&=(UWORD)~bits;
            if(old&bits)++diag.clipped;}
    }
}
typedef uint32_t AliasU32 __attribute__((may_alias));
static uint32_t bar_mask(unsigned position,unsigned x,int bottom)
{
    int n=bottom?(int)x*32+32-(360-(int)position):(int)position-(int)x*32;
    if(n<=0)return 0;
    if(n>=32)return 0xffffffffUL;
    return bottom?0xffffffffUL>>(32-n):0xffffffffUL<<(32-n);
}
static void bars(UBYTE *bitmap,unsigned position,unsigned previous)
{
    unsigned x,y,p,b;
    for(b=0;b<2;++b)for(x=0;x<10;++x){
        uint32_t mask=bar_mask(position,x,b);
        if(mask==bar_mask(previous,x,b))continue;
        for(p=0;p<2;++p)for(y=0;y<16;++y){
            unsigned a=p*2400+(b?224+y:y)*10+x;
            ((AliasU32 *)bitmap)[a]=((const AliasU32 *)fixture_world)[a]&~mask;
        }
    }
}
static unsigned small_div(unsigned n,unsigned d){unsigned q=0;while(n>=d){n-=d;++q;}return q;}
static int picture(UWORD *list,UWORD *dma,UBYTE *world,UBYTE *reading,unsigned frame){
    V6Sprites batch;unsigned i,grey=v6_terminal_box_gray(&reader.boxes[0]),visible=reader.boxes[0].visible;
    UWORD *p=list;ULONG bitmap=(ULONG)(visible?reading:world);
    v6_sprites_begin(&batch,dma);for(i=0;i<8;++i)batch.colours[i]=0;
    if(v6_sprites_add_rect(&batch,fixture_masks[0],player.x,player.y,6,16,32,0x6ff)<V6_SPRITE_CLIPPED ||
       v6_sprites_add_rect(&batch,fixture_masks[1],252,200,0,16,16,terminal.active?0xfff:0x888)<V6_SPRITE_CLIPPED ||
       v6_sprites_add_rect(&batch,fixture_masks[3],24,168,0,16,16,0x888)<V6_SPRITE_CLIPPED ||
       v6_sprites_add_rect(&batch,fixture_masks[2],280,48,0,16,16,0x888)<V6_SPRITE_CLIPPED)return 0;
    for(i=0;i<2;++i)if(v6_sprites_add_rect(&batch,fixture_masks[4+frame],enemies[i].x,enemies[i].y,0,32,16,0x9f9)<V6_SPRITE_CLIPPED)return 0;
    if(visible)for(i=0;i<batch.count;++i)sprite_occlude(dma+i*V6_SPRITE_WORDS);
    p=reg(p,0x100,0x3200);p=reg(p,0x102,0);p=reg(p,0x104,0x24);p=reg(p,0x108,0);p=reg(p,0x10a,0);
    p=reg(p,0x08e,0x3481);p=reg(p,0x090,0x24c1);p=reg(p,0x092,0x38);p=reg(p,0x094,0xd0);
    *p++=0x1401;*p++=0xfffe;
    for(i=0;i<8;++i){ULONG a=(ULONG)(dma+i*V6_SPRITE_WORDS);p=reg(p,0x120+i*4,a>>16);p=reg(p,0x122+i*4,a);p=reg(p,v6_sprite_colour_register(i),batch.colours[i]);}
    *p++=0x2c01;*p++=0xfffe;
    for(i=0;i<3;++i){ULONG a=bitmap+i*9600;p=reg(p,0xe0+i*4,a>>16);p=reg(p,0xe2+i*4,a);}
    for(i=0;i<8;++i){unsigned c=fixture_palette[i];if(i==5)c=small_div(small_div(grey,6)+8,17)*0x111;if(i==7)c=small_div(grey+8,17)*0x111;p=reg(p,0x180+i*2,c);}
    *p++=0xffff;*p++=0xfffe;
    diag.ui_bitmap=bitmap;diag.list=(ULONG)list;diag.sprite_dma=(ULONG)dma;
    return (unsigned)(p-list)<=LIST_BYTES/2;
}
int __attribute__((used,section(".text.unlikely"))) _start(void){
    UBYTE *chip,*samples;UWORD *lists[2],*dma[2];UWORD saved_dma,saved_ints,saved_adk;
    APTR old_irq;struct View *view;ULONG previous,elapsed=0;unsigned back=1,held=0,pending=0,barpos=0,walk=0,delay=0;
    unsigned bar_cache[4]={0,0,361,361};
    V6AudioPlan plan;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    if(SysBase->AttnFlags&AFF_68010)return 20;
    cia=(struct Library *)OpenResource((CONST_STRPTR)"ciaa.resource");
    GfxBase=(struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    if(!GfxBase)return 20;
    if(!cia){CloseLibrary((struct Library *)GfxBase);return 20;}
    if(!(GfxBase->DisplayFlags&PAL)){CloseLibrary((struct Library *)GfxBase);return 20;}
    chip=AllocMem(CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);if(!chip){CloseLibrary((struct Library *)GfxBase);return 20;}
    diag.chip_bytes=CHIP_BYTES;
    {unsigned i;for(i=0;i<BITMAP_BYTES;++i){chip[i]=chip[BITMAP_BYTES+i]=fixture_world[i];chip[2*BITMAP_BYTES+i]=chip[3*BITMAP_BYTES+i]=fixture_read[i];}}
    bars(chip+2*BITMAP_BYTES,361,0);bars(chip+3*BITMAP_BYTES,361,0);
    dma[0]=(UWORD *)(chip+4*BITMAP_BYTES);dma[1]=(UWORD *)((UBYTE *)dma[0]+DMA_BYTES);
    lists[0]=(UWORD *)((UBYTE *)dma[1]+DMA_BYTES);lists[1]=(UWORD *)((UBYTE *)lists[0]+LIST_BYTES);
    samples=(UBYTE *)lists[1]+LIST_BYTES;
    {unsigned i;for(i=0;i<sizeof(fixture_sound0);++i)samples[i]=fixture_sound0[i];for(i=0;i<sizeof(fixture_sound1);++i)samples[sizeof(fixture_sound0)+i]=fixture_sound1[i];}
    if(!v6_audio_init(&audio,(ULONG)(samples+FIXTURE_AUDIO_BYTES-2))){FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;}
    room.tiles=fixture_tiles;room.tileset=0;room.extra_row=0;room.terrain=0;room.blocks=&activity;room.block_count=1;
    v6_terrain_build(&terrain,&room);room.terrain=&terrain;
    v6_player_init(&player,248,193,0);player.ground=2;player.dir=1;
    v6_terminal_init(&terminal,252,200,1,0,1);v6_keyboard_init(&keys);
    v6_enemy_init(&enemies[0],80,88,3,3,0,0,320,240,0,0,32,16);
    v6_enemy_init(&enemies[1],208,128,2,3,0,0,320,240,0,0,32,16);
    picture(lists[0],dma[0],chip,chip+2*BITMAP_BYTES,0);
    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();OwnBlitter();WaitBlit();Forbid();Disable();
    if((hw->dmaconr&15)||(hw->intenar&0x780)){Enable();Permit();DisownBlitter();LoadView(view);FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;}
    saved_dma=hw->dmaconr;saved_ints=hw->intenar;saved_adk=hw->adkconr;
    hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l 0x6c.w,%0":"=r"(old_irq));__asm volatile("move.l %0,0x6c.w"::"r"((APTR)irq):"memory");
    blank();hw->cop1lc=(ULONG)lists[0];hw->copjmp1=0;hw->dmacon=0x83a0;hw->intena=0xc020;Enable();diag.status=1;
    while(!frames){}previous=frames;
    while((*(volatile UBYTE *)0xbfe001&0x40) && !(keys.down[0x45>>3]&(1U<<(0x45&7))) && !diag.error){
        ULONG start=clock_lines(),work;unsigned buttons,edges;
        poll();buttons=v6_keyboard_map_buttons(&keys);edges=buttons&~held;held=buttons;pending|=edges;diag.buttons=buttons;
        v6_audio_tick(&audio,(hw->intreqr&INTF_AUD0)!=0,&plan);apply(&plan);
        elapsed+=19968;
        if(elapsed>=34000){unsigned old_cues=reader.cues,old_active=reader.active;
            V6ActivitySignals s={(pending&V6_MAP_ENTER)!=0,1,0,0,0,0};V6ActivityResult result;
            elapsed-=34000;++diag.ticks;
            /* Retain edges until a gameplay update, rather than losing a
               keyboard press on a render-only field. See pending below. */
            result=v6_activity_input(&activity,1,v6_activity_find(&activity,1,&player),&player,&s);
            if(!reader.active && result.action==V6_INTERACT_ACTIVITY){if(!v6_terminal_read_start(&reader,&v6_station_terminal_program))diag.error=2;else ++diag.opens;}
            v6_terminal_read_tick(&reader,&(V6TerminalReadSignals){(int)barpos,(pending&V6_MAP_ACTION)!=0});
            pending=0;
            if(reader.bars){barpos=barpos+25>361?361:barpos+25;}else barpos=barpos<25?0:barpos-25;
            if(reader.cues!=old_cues){++diag.read_cues;cue(samples,1);}
            if(old_active && !reader.active)++diag.closes;
            v6_terminal_read_animate(&reader);
            if(v6_terminal_tick(&terminal)){++diag.touch_cues;cue(samples,0);}v6_terminal_contact(&terminal,&player);
            v6_enemy_step(&enemies[1],&room,room.blocks,room.block_count);v6_enemy_step(&enemies[0],&room,room.blocks,room.block_count);
            if(!delay){walk=(walk+1)&3;delay=8;}--delay;
        }
        {unsigned bank=back+(reader.boxes[0].visible?2:0);
            if(bar_cache[bank]!=barpos){bars(chip+bank*BITMAP_BYTES,barpos,bar_cache[bank]);bar_cache[bank]=barpos;}}
        if(!picture(lists[back],dma[back],chip+back*BITMAP_BYTES,chip+(2+back)*BITMAP_BYTES,walk))diag.error=1;
        work=clock_lines()-start;if(work>diag.max_work)diag.max_work=work;
        diag.frames=frames;diag.audio_starts=audio.starts;diag.audio_completed=audio.completed;diag.visible=reader.boxes[0].visible;diag.bars=barpos;diag.phase=reader.phase;
        diag.enemy_x[0]=enemies[0].x;diag.enemy_x[1]=enemies[1].x;diag.enemy_y[0]=enemies[0].y;diag.enemy_y[1]=enemies[1].y;
        if(audio.error)diag.error=4;
        blank();hw->cop1lc=(ULONG)lists[back];back^=1;while(frames==previous){}if(frames-previous!=1)diag.missed+=frames-previous-1;previous=frames;
    }
    v6_audio_stop(&audio,&plan);apply(&plan);Disable();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l %0,0x6c.w"::"r"(old_irq):"memory");hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
    hw->adkcon=saved_adk|0x8000;hw->dmacon=saved_dma|0x8000;hw->intena=saved_ints|0x8000;SetICR(cia,0);
    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=2;FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return diag.error?20:0;
}
