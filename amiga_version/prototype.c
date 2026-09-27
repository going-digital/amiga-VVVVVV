/* VVVVVV A500 playable room slices. Original tiles and player rules.
 * The full campaign, general entity handling and scripts are pending.
 * Native display/blitter/Paula code; no SDL and no runtime asset decompression
 * beyond the bounded room RLE decoder. All OS calls occur outside takeover.
 */
#include <proto/exec.h>
#include <proto/dos.h>
#include <proto/graphics.h>
#include <graphics/gfxbase.h>
#include <exec/execbase.h>
#include <hardware/custom.h>
#include <hardware/dmabits.h>
#include <hardware/intbits.h>
#include "room_codec.h"
#include "slice.h"
#include "enemy.h"
#include "platform.h"
#include "pixel_collision.h"
#include "animation.h"
#include "sprites.h"
#include "prototype_room.h"
#include "prototype_assets.h"
#ifdef V6_TRANSITION_REPLAY
#include "../tools/amiga/transition_replay.h"
#endif

struct ExecBase *SysBase;
struct GfxBase *GfxBase;
struct DosLibrary *DOSBase;
static volatile struct Custom * const hw = (void *)0xdff000;
#define BACKGROUND_PLANE_BYTES 9600
#define PLANE_BYTES BACKGROUND_PLANE_BYTES
#define SCREEN_BYTES (V6_PLANES * PLANE_BYTES)
#define BACKGROUND_BYTES (V6_PLANES * BACKGROUND_PLANE_BYTES)
#define DISPLAY_BUFFER_COUNT (2 * SLICE_ROOM_COUNT)
#define COPPER_BYTES 320
#define HUD_PLANE_BYTES (40 * 40)
#define HUD_BYTES HUD_PLANE_BYTES
#define MASK_BYTES (2 * V6_SPRITE_CHANNELS * V6_SPRITE_WORDS * 2)
#define CHIP_BYTES (DISPLAY_BUFFER_COUNT * SCREEN_BYTES + COPPER_BYTES + sizeof(flip_sound) + 4 + HUD_BYTES + MASK_BYTES)

/* Located by the host smoke test in a RAM dump. Fixed-width big-endian fields. */
static volatile struct {
    ULONG magic, version, frames, ticks, renders, max_work_lines, missed_frames;
    ULONG flips, peak_tick, chip_free, other_free, chip_allocated, error, status;
    LONG player_x, player_y, player_vx, player_vy, gravity, death_timer;
    ULONG deaths, respawns, checkpoint, exits;
    ULONG room_index, transitions, max_load_lines, load_frames;
    LONG enemy_x, enemy_y;
    ULONG enemy_ticks, enemy_hits;
    ULONG sprite_channels, max_sprite_channels;
} diagnostics = {.magic = 0x56364447, .version = 5, .chip_allocated = CHIP_BYTES};

#ifdef V6_PROFILE
/* Separate profiling builds only: phase costs at the highest-work update. */
static volatile struct { ULONG magic, phase[6]; } profile = {0x56365046,{0}};
static ULONG profile_marks[7];
#define PROFILE_MARK(n) (profile_marks[n]=beam_clock())
#else
#define PROFILE_MARK(n) ((void)0)
#endif

static volatile ULONG frames;
static UBYTE *chip, *screen[DISPLAY_BUFFER_COUNT], *background, *sample, *hud;
static ULONG hud_generation = 1, hud_versions[DISPLAY_BUFFER_COUNT];
static ULONG hud_rows[5], hud_row_versions[DISPLAY_BUFFER_COUNT][5];
static UBYTE room_backgrounds[SLICE_ROOM_COUNT][BACKGROUND_BYTES];
static V6Sprites sprites[2];
static UWORD *sprite_words, *sprite_colour_words;
static UWORD *copper, *plane_words, *color_words, *silence;
static UWORD room_tiles[SLICE_ROOM_COUNT][1200];
static UWORD *room = room_tiles[0];
static V6Slice slice;
static V6Terrain terrain[SLICE_ROOM_COUNT];
static V6Room current_room = {room_tiles[0], SLICE_TILESET, SLICE_EXTRA_ROW, 0, 0, 0};
#ifdef V6_ENEMY_SCENE
static V6Enemy drones[ENEMY_COUNT];
static UWORD drone_frame = ENEMY_TILE, drone_walk, drone_delay;
static ULONG enemy_hits, enemy_ticks;
static V6CollisionAnimation collision_animation;
static int visual_ground, visual_roof, collision_frame;
static void collision_contact(const V6Player *p, void *context)
{
    (void)context;
    /* Input leaves position unchanged: reuse the same static contact probes
     * that gamerenderfixed would perform before input, avoiding duplicate work. */
    visual_ground=p->ground==2?2:visual_ground-1;
    visual_roof=p->roof==2?2:visual_roof-1;
    collision_frame=v6_collision_frame(&collision_animation,p,visual_ground,visual_roof,slice.death_timer);
}
static void reset_drone(void)
{
    unsigned n;
    for(n=0;n<ENEMY_COUNT;++n)
        v6_enemy_init(&drones[n],enemy_setup[n][0],enemy_setup[n][1],enemy_setup[n][2],enemy_setup[n][3],
                      0,0,320,240,0,0,ENEMY_WIDTH,ENEMY_HEIGHT);
    drone_frame=ENEMY_TILE; drone_walk=drone_delay=0;
}
#endif
#ifdef V6_PLATFORM_SCENE
static V6Platform platforms[PLATFORM_COUNT];
static V6Block platform_blocks[PLATFORM_COUNT];
static V6PlayerMotion platform_motion;
static V6PlatformPush platform_push;
static ULONG platform_ticks, platform_pushes;
static void reset_platforms(void)
{
    unsigned i;
    for(i=0;i<PLATFORM_COUNT;++i) {
        v6_platform_init(&platforms[i],platform_setup[i][0],platform_setup[i][1],
                         0,3,100,70,320,160);
        platform_blocks[i]=(V6Block){platforms[i].x,platforms[i].y,32,8,V6_BLOCK,0};
    }
    current_room.blocks=platform_blocks;current_room.block_count=PLATFORM_COUNT;
    platform_motion=(V6PlayerMotion){0,slice.player.y};
    platform_push=(V6PlatformPush){slice.player.y,0,0};
}
static unsigned platform_movement(V6Player *p,const V6Room *r,unsigned input,
                                  int life_timer,void *context)
{
    int before;
    unsigned events;
    (void)context;
    events=v6_player_input(p,input,&platform_motion);
    platform_push.pending_y=platform_motion.pending_y;
    before=p->y;
    v6_platform_transport(p,r,platforms,PLATFORM_COUNT,platform_blocks,PLATFORM_COUNT,
                           V6_PLATFORMS_VERTICAL,life_timer,&platform_push);
    if(p->y!=before) ++platform_pushes;
    v6_player_physics(p,r,&platform_motion,0,0);
    v6_platform_disable_overlaps(p,platforms,PLATFORM_COUNT,platform_blocks,PLATFORM_COUNT);
    v6_player_unstick(p,r);
    ++platform_ticks;
    return events;
}
#endif
static UWORD saved_dma, saved_ints, saved_adk;
static APTR saved_irq;
static struct View *saved_view;

static const char *room_caption(void)
{
#if defined(V6_ENEMY_SCENE) || defined(V6_PLATFORM_SCENE)
    return SLICE_CAPTION;
#else
    return slice.room_index ? "119,110 - TWO ROOM SLICE           " : "100,110 - TWO ROOM SLICE           ";
#endif
}

static void wait_blit(void)
{
    (void)hw->dmaconr;
    while (hw->dmaconr & DMAF_BLTDONE) {}
}

static UWORD beam(void)
{
    return (*(volatile ULONG *)0xdff004 >> 8) & 511;
}

static ULONG beam_clock(void)
{
    ULONG a, b;
    UWORD y;
    do { a = frames; y = beam(); b = frames; } while (a != b);
    return a * 312 + y;
}

static void wait_pal_blank(void)
{
    while (beam() == 311) {}
    while (beam() != 311) {}
}

static void __attribute__((interrupt)) vblank(void)
{
    ++frames;
    hw->intreq = INTF_VERTB;
    hw->intreq = INTF_VERTB;
}

static UWORD *move_reg(UWORD *p, UWORD reg, UWORD value)
{
    *p++ = reg; *p++ = value;
    return p;
}

static void set_screen(UBYTE *data)
{
#if V6_PLANES == 2
    color_words[3] = room_colors[slice.room_index];
#endif
    UWORD p;
    UWORD buffer = data == screen[slice.room_index*2] ? 0 : 1;
    for (p = 0; p < V6_SPRITE_CHANNELS; ++p) {
        ULONG address = (ULONG)(sprites[buffer].dma + p*V6_SPRITE_WORDS);
        sprite_colour_words[p*2+1] = sprites[buffer].colours[p];
        sprite_words[p*4+1] = address >> 16; sprite_words[p*4+3] = address;
    }
    for (p = 0; p < V6_PLANES; ++p) {
        ULONG address = (ULONG)(data + p * PLANE_BYTES);
        plane_words[p * 4 + 1] = address >> 16;
        plane_words[p * 4 + 3] = address;
    }
}

static void create_copper(void)
{
    UWORD *p = copper;
    UWORD i;
    p = move_reg(p, 0x100, (V6_PLANES << 12) | 0x0200); /* planar color display */
    p = move_reg(p, 0x102, 0);
    p = move_reg(p, 0x104, 0x24);
    p = move_reg(p, 0x108, 0);
    p = move_reg(p, 0x10a, 0);
    p = move_reg(p, 0x08e, 0x3481); /* PAL: y=52, x=129 */
    p = move_reg(p, 0x090, 0x24c1); /* y=292, x=449 */
    p = move_reg(p, 0x092, 0x0038);
    p = move_reg(p, 0x094, 0x00d0);
    /* Publish after the CPU VBL handoff but before sprite DMA control fetch. */
    *p++ = 0x1401; *p++ = 0xfffe;
    sprite_words = p;
    for (i = 0; i < 8; ++i) {
        ULONG address = (ULONG)silence;
        p = move_reg(p, 0x120 + i*4, address >> 16);
        p = move_reg(p, 0x122 + i*4, address);
    }
    sprite_colour_words = p;
    for (i = 0; i < V6_SPRITE_CHANNELS; ++i)
        p = move_reg(p, v6_sprite_colour_register(i), 0);
    /* The CPU publishes completed buffer pointers just after the VBL IRQ.
     * Delay Copper pointer reads until line 44, before the visible line 52. */
    *p++ = 0x2c01; *p++ = 0xfffe;
    plane_words = p;
    for (i = 0; i < V6_PLANES; ++i) {
        p = move_reg(p, 0x0e0 + 4 * i, 0);
        p = move_reg(p, 0x0e2 + 4 * i, 0);
    }
    color_words = p;
    for (i = 0; i < (1 << V6_PLANES); ++i) p = move_reg(p, 0x180 + i * 2, palette[i]);
    *p++ = 0xffff; *p = 0xfffe;
    set_screen(screen[0]);
}

static void take_system(void)
{
    saved_view = GfxBase->ActiView;
    LoadView(0);
    WaitTOF(); WaitTOF();
    OwnBlitter(); WaitBlit();
    Forbid();
    Disable();
    saved_dma = hw->dmaconr;
    saved_ints = hw->intenar;
    saved_adk = hw->adkconr;
    hw->intena = 0x7fff;
    hw->intreq = 0x7fff;
    hw->dmacon = 0x7fff;
    hw->adkcon = 0x7fff;
    __asm volatile ("move.l 0x6c.w,%0" : "=r"(saved_irq));
    __asm volatile ("move.l %0,0x6c.w" : : "r"((APTR)vblank) : "memory");
    wait_pal_blank();
    hw->cop1lc = (ULONG)copper;
    hw->copjmp1 = 0;
    hw->dmacon = DMAF_SETCLR | DMAF_MASTER | DMAF_RASTER | DMAF_COPPER | DMAF_BLITTER | DMAF_SPRITE;
    hw->intena = INTF_SETCLR | INTF_INTEN | INTF_VERTB;
    Enable();
}

static void free_system(void)
{
    wait_blit();
    Disable();
    hw->intena = 0x7fff;
    hw->intreq = 0x7fff;
    hw->dmacon = 0x7fff;
    hw->adkcon = 0x7fff;
    __asm volatile ("move.l %0,0x6c.w" : : "r"(saved_irq) : "memory");
    hw->aud[0].ac_vol = 0;
    hw->cop1lc = (ULONG)GfxBase->copinit;
    hw->cop2lc = (ULONG)GfxBase->LOFlist;
    hw->copjmp1 = 0;
    hw->adkcon = saved_adk | 0x8000;
    hw->dmacon = saved_dma | 0x8000;
    hw->intena = saved_ints | 0x8000;
    Enable();
    Permit();
    DisownBlitter();
    LoadView(saved_view);
    WaitTOF(); WaitTOF();
}

static void draw_room(void)
{
    UWORD x, y, plane, row;
    for (y = 0; y < 30; ++y) for (x = 0; x < 40; ++x) {
        UWORD tile = room[y * 40 + x];
        UWORD mapped = tile_mapping[tile];
        for (plane = 0; plane < V6_PLANES; ++plane) for (row = 0; row < 8; ++row)
            background[plane * BACKGROUND_PLANE_BYTES + (y * 8 + row) * 40 + x] =
                tile_planes[mapped][plane * 8 + row];
    }
}

static void blit_rows(const UBYTE *src, UBYTE *dst, UWORD rows)
{
    if (!rows) return;
    wait_blit();
    hw->bltcon0 = 0x09f0; /* A to D, all bits, no shift */
    hw->bltcon1 = 0;
    hw->bltafwm = hw->bltalwm = 0xffff;
    hw->bltamod = hw->bltdmod = 0;
    hw->bltapt = (APTR)src;
    hw->bltdpt = dst;
    hw->bltsize = (rows << 6) | 20;
}

/* Word-aligned checkpoint damage; each back buffer tracks its dirty state. */
static void restore_rectangle(UBYTE *dst, int x, int y, int width, int height)
{
    int right = x + width, bottom = y + height, left_word, words;
    UWORD plane;
    if (x < 0) x = 0;
    if (y < 0) y = 0;
    if (right > 320) right = 320;
    if (bottom > 240) bottom = 240;
    if (right <= x || bottom <= y) return;
    left_word = x / 16;
    words = (right + 15) / 16 - left_word;
    /* Backgrounds live in non-DMA RAM. Copy only the damaged words with the
     * CPU; retain each room's screen pair instead of copying a whole room on
     * entry. 68000 longword accesses need only word alignment. */
    wait_blit();
    for (plane = 0; plane < V6_PLANES; ++plane) {
        int row;
        ULONG offset = plane * PLANE_BYTES + y * 40 + left_word * 2;
        for (row = y; row < bottom; ++row) {
            const UWORD *src = (const UWORD *)(background + offset);
            UWORD *target = (UWORD *)(dst + offset);
            int count = words;
            while (count >= 2) {
                *(ULONG *)target = *(const ULONG *)src;
                target += 2; src += 2; count -= 2;
            }
            if (count) *target = *src;
            offset += 40;
        }
    }
}

static void text(UWORD x, UWORD y, const char *s)
{
    UWORD row;
    ++hud_generation;
    ++hud_rows[y/8];
    while (*s && x < 40) {
        const UBYTE *glyph = font_rows[(UBYTE)*s++ & 127];
        for (row = 0; row < 8; ++row)
            hud[(y + row) * 40 + x] = glyph[row];
        ++x;
    }
}

static void number(UWORD x, UWORD y, UWORD value)
{
    char s[6];
    UWORD i;
    s[5] = 0;
    for (i = 5; i; --i) { s[i-1] = '0' + value % 10; value /= 10; }
    text(x, y, s);
}

static void overlay_hud(UBYTE *dst, UWORD buffer)
{
    UWORD plane, row;
    for(row=0;row<5;++row) {
        if(hud_versions[buffer] && hud_row_versions[buffer][row]==hud_rows[row]) continue;
        for(plane=0;plane<V6_PLANES;++plane)
            blit_rows(hud+row*8*40, dst+plane*PLANE_BYTES+
                      (row<2?row*8:216+(row-2)*8)*40,8);
        hud_row_versions[buffer][row]=hud_rows[row];
    }
    wait_blit();
}

static void draw_checkpoint(void)
{
    UWORD row, plane, color = slice.checkpoint_active ? CHECKPOINT_COLOR : TEXT_COLOR;
    UWORD shift = slice.checkpoint_x & 15;
    /* Asset conversion verifies a 16x16 mask: even shifted, two words suffice. */
    for (row = 0; row < 16; ++row) {
        ULONG bits = sprite_rows[slice.checkpoint_tile][row];
        ULONG shifted = bits >> shift;
        UWORD first = shifted >> 16, second = shifted;
        UWORD *p = (UWORD *)(background + (slice.checkpoint_y + row) * 40
            + (slice.checkpoint_x / 16) * 2);
        for (plane = 0; plane < V6_PLANES; ++plane) {
            if (color & (1 << plane)) {
                p[0] |= first; p[1] |= second;
            } else {
                p[0] &= ~first; p[1] &= ~second;
            }
            p += PLANE_BYTES / 2;
        }
    }
}

static void sound(void)
{
    UWORD line;
    hw->dmacon = DMAF_AUD0;
    hw->aud[0].ac_ptr = (UWORD *)sample;
    hw->aud[0].ac_len = sizeof(flip_sound) / 2;
    hw->aud[0].ac_per = 322; /* PAL ~11015 Hz */
    hw->aud[0].ac_vol = 48;
    hw->intreq = INTF_AUD0;
    hw->dmacon = DMAF_SETCLR | DMAF_AUD0;
    /* Let initial DMA fetch latch the sample, then arrange a silent reload. */
    line = beam(); while (beam() == line) {}
    line = beam(); while (beam() == line) {}
    hw->aud[0].ac_ptr = silence;
    hw->aud[0].ac_len = 1;
}

static int run(void)
{
    UWORD back = 1, ready = 0, last_right = 0, restart_pending = 0;
    UWORD checkpoint_dirty[DISPLAY_BUFFER_COUNT] = {0};
    LONG shown_deaths = -1, shown_flips = -1, shown_work = -1;
    UWORD exit_notice = 0;
    ULONG observed = 0, elapsed_us = 0;
    UWORD i;
    __asm volatile ("move.l 4.w,%0" : "=r"(SysBase));
    /* This harness owns the 68000 vector table and uses PAL scanline timing. */
    if (SysBase->AttnFlags & AFF_68010) return 20;
    GfxBase = (struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library", 0);
    if (!GfxBase) return 20;
    DOSBase = (struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library", 0);
    if (!DOSBase) { CloseLibrary((struct Library *)GfxBase); return 20; }
    if (!(GfxBase->DisplayFlags & PAL)) {
        static const char message[] = "PAL required for this prototype.\n";
        Write(Output(), (APTR)message, sizeof(message) - 1);
        CloseLibrary((struct Library *)DOSBase);
        CloseLibrary((struct Library *)GfxBase);
        return 20;
    }
    chip = AllocMem(CHIP_BYTES, MEMF_CHIP | MEMF_CLEAR);
    if (!chip) {
        CloseLibrary((struct Library *)DOSBase);
        CloseLibrary((struct Library *)GfxBase);
        return 20;
    }
    for (i = 0; i < DISPLAY_BUFFER_COUNT; ++i) screen[i] = chip + i * SCREEN_BYTES;
    copper = (UWORD *)(chip + DISPLAY_BUFFER_COUNT * SCREEN_BYTES);
    sample = (UBYTE *)copper + COPPER_BYTES;
    silence = (UWORD *)(sample + sizeof(flip_sound));
    hud = (UBYTE *)(silence + 2);
    for (i=0;i<2;++i) v6_sprites_begin(&sprites[i],
        (UWORD *)(hud + HUD_BYTES) + i*V6_SPRITE_CHANNELS*V6_SPRITE_WORDS);
    for (i = 0; i < sizeof(flip_sound); ++i) sample[i] = flip_sound[i];
    for (i = 0; i < SLICE_ROOM_COUNT; ++i) {
        if (!v6_unpack_room(packed_rooms[i], packed_sizes[i], room_tiles[i], 1200)) {
            diagnostics.error = 1;
            FreeMem(chip, CHIP_BYTES);
            CloseLibrary((struct Library *)DOSBase);
            CloseLibrary((struct Library *)GfxBase);
            return 20;
        }
        room = room_tiles[i];
        background = room_backgrounds[i];
        draw_room();
        restore_rectangle(screen[i*2], 0, 0, 320, 240);
        restore_rectangle(screen[i*2+1], 0, 0, 320, 240);
    }
    room = room_tiles[0]; background = room_backgrounds[0];
    diagnostics.chip_free = AvailMem(MEMF_CHIP);
    diagnostics.other_free = AvailMem(MEMF_FAST);
    v6_slice_init_world(&slice, room_setups, SLICE_ROOM_COUNT, 0);
    for (i = 0; i < DISPLAY_BUFFER_COUNT; ++i) {
        checkpoint_dirty[i] = 1;
    }
    draw_checkpoint();
#ifdef V6_ENEMY_SCENE
    reset_drone();
#endif
#ifdef V6_PLATFORM_SCENE
    reset_platforms();
#endif
    text(1, 0, "VVVVVV AMIGA - PLAYABLE ROOM");
    text(1, 8, room_caption());
    text(1, 16, "DEATHS       FLIPS       LINES");
    text(1, 32, "JOY L/R FIRE FLIP RMB RESET LMB EXIT");
    number(8,16,0); number(20,16,0); number(32,16,0);
    shown_deaths=shown_flips=shown_work=0;
    for(i=0;i<SLICE_ROOM_COUNT;++i) {
        V6Room source={room_tiles[i],SLICE_TILESET,SLICE_EXTRA_ROW,0,0,0};
        v6_terrain_build(&terrain[i],&source);
    }
    create_copper();
    take_system();
    for (i=0;i<2;++i) {
        restore_rectangle(screen[i],slice.checkpoint_x,slice.checkpoint_y,16,16);
        overlay_hud(screen[i],i); hud_versions[i]=hud_generation;
        checkpoint_dirty[i]=0;
    }

    observed = frames;
    diagnostics.status = 1;
    while (*(volatile UBYTE *)0xbfe001 & 0x40) { /* left mouse exits */
        ULONG current, delta, start, work;
        UWORD loading = 0, buffer;
        UWORD joy, fire, right_mouse, input = 0;
        while (frames == observed) {}
        current = frames;
        delta = current - observed;
        observed = current;
        if (delta > 1) diagnostics.missed_frames += delta - 1;
        if (ready) { set_screen(screen[slice.room_index * 2 + back]); back ^= 1; ready = 0; }
        joy = hw->joy1dat;
        fire = !(*(volatile UBYTE *)0xbfe001 & 0x80);
        right_mouse = !(hw->potinp & 0x0400);
        if (right_mouse && !last_right) restart_pending = 1;
        last_right = right_mouse;
        if (joy & 0x0200) input |= V6_LEFT;
        if (joy & 0x0002) input |= V6_RIGHT;
        if (fire) input |= V6_FLIP;
        /* PAL frame is 312*227 / 3546895 seconds. Rounded to nearest us here;
         * full port will use the platform clock. Logic retains 34ms ticks. */
        elapsed_us += delta * 19968UL;
        if (elapsed_us < 34000) continue;
        start = beam_clock();
        PROFILE_MARK(0);
        while (elapsed_us >= 34000) {
            elapsed_us -= 34000;
            ++diagnostics.ticks;
            {
                unsigned events;
#ifdef V6_PLATFORM_REPLAY
                /* Walk off the checkpoint ledge, then flip onto the third
                 * platform. This deterministic capture also exercises respawn. */
                input=diagnostics.ticks<=50?V6_LEFT:0;
                if(diagnostics.ticks==50) input|=V6_FLIP;
#endif
#ifdef V6_TRANSITION_REPLAY
                input = diagnostics.ticks <= sizeof(transition_replay)
                    ? transition_replay[diagnostics.ticks - 1] : 0;
                if (diagnostics.ticks == 100) restart_pending = 1;
#endif
                current_room.tiles = room_tiles[slice.room_index];
                current_room.terrain = &terrain[slice.room_index];
#ifdef V6_ENEMY_SCENE
                /* Fixed rendering advances the enemy frame before gamelogic. */
                if (!drone_delay || --drone_delay == 0) {
                    drone_delay=8; drone_walk=(drone_walk+1)&3;
                }
                drone_frame=ENEMY_TILE+drone_walk;
                { int n; for(n=ENEMY_COUNT-1;n>=0;--n)
                    v6_enemy_step(&drones[n], &current_room, 0, 0); }
                ++enemy_ticks;
#endif
                PROFILE_MARK(1);
#ifdef V6_PLATFORM_SCENE
                events=v6_slice_step_movement(&slice,&current_room,input,restart_pending,platform_movement,0);
                if(events & V6_EVENT_RESPAWN) {
                    /* Same-room respawn preserves platform positions and blocks. */
                    platform_motion=(V6PlayerMotion){0,slice.player.y};
                    platform_push=(V6PlatformPush){slice.player.y,0,0};
                }
#elif defined(V6_ENEMY_SCENE)
                events = v6_slice_step_hook(&slice, &current_room, input, restart_pending,collision_contact,0);
#else
                events = v6_slice_step(&slice, &current_room, input, restart_pending);
#endif
#ifdef V6_ENEMY_SCENE
                if (events & V6_EVENT_RESPAWN) {
                    reset_drone(); collision_animation.delay=collision_animation.walk=0;
                    visual_ground=visual_roof=0;
                }
                else if (slice.death_timer < 0) {
                    int n;
                    for(n=ENEMY_COUNT-1;n>=0;--n) {
                        const V6Enemy *e=&drones[n];
                        if (v6_player_overlaps(&slice.player,e->x+e->cx,e->y+e->cy,e->w,e->h) &&
                            v6_pixel_hit(collision_rows[collision_frame],slice.player.x,slice.player.y,
                                         collision_rows[drone_frame],e->x,e->y)) {
                            slice.death_timer=30; ++enemy_hits; break;
                        }
                    }
                }
                if (!(events & V6_EVENT_RESPAWN)) {
                    slice.frame=slice.death_timer<0?collision_frame:
                        (slice.player.dir?12:13)+(slice.player.gravity?2:0);
                }
#endif
                PROFILE_MARK(2);
                restart_pending = 0;
                if (events & V6_EVENT_FLIP) sound();
                if (events & V6_EVENT_ROOM) {
                    background = room_backgrounds[slice.room_index];
                    room = room_tiles[slice.room_index];
                    loading = 1;
                    checkpoint_dirty[slice.room_index*2] = checkpoint_dirty[slice.room_index*2+1] = 1;
                    draw_checkpoint();
                    text(1, 8, room_caption());
                }
                if (events & V6_EVENT_SAVE) {
                    draw_checkpoint();
                    checkpoint_dirty[slice.room_index*2] = checkpoint_dirty[slice.room_index*2+1] = 1;
                }
                if (events & V6_EVENT_EXIT) {
                    exit_notice = 60;
                    text(1, 8, "ROOM EXIT: BACK TO SLICE CHECKPOINT");
                }
            }
            if (exit_notice && --exit_notice == 0) text(1, 8, room_caption());
        }
        PROFILE_MARK(3);
        buffer = slice.room_index * 2 + back;
        if (checkpoint_dirty[buffer]) {
            restore_rectangle(screen[buffer], slice.checkpoint_x, slice.checkpoint_y, 16, 16);
            checkpoint_dirty[buffer] = 0;
            if (slice.checkpoint_y < 16 || slice.checkpoint_y+16 > 216) hud_versions[buffer] = 0;
        }
        PROFILE_MARK(4);
        v6_sprites_begin(&sprites[back],sprites[back].dma);
        if (v6_sprites_add(&sprites[back],sprite_rows[slice.frame],
                slice.player.x,slice.player.y,6,0x6ff) < V6_SPRITE_CLIPPED) {
            diagnostics.error=4; break;
        }
#ifdef V6_ENEMY_SCENE
        {
            unsigned n;
            for(n=0;n<ENEMY_COUNT;++n)
                if (v6_sprites_add_wide(&sprites[back],sprite_rows[drone_frame],
                        drones[n].x,drones[n].y,0,ENEMY_DRAW_WIDTH,ENEMY_COLOUR) < V6_SPRITE_CLIPPED) {
                    diagnostics.error=4; break;
                }
            if(diagnostics.error) break;
        }
        diagnostics.enemy_x=drones[0].x; diagnostics.enemy_y=drones[0].y;
        diagnostics.enemy_ticks=enemy_ticks; diagnostics.enemy_hits=enemy_hits;
#endif
#ifdef V6_PLATFORM_SCENE
        {
            unsigned n;
            for(n=0;n<PLATFORM_COUNT;++n)
                if(v6_sprites_add_rect(&sprites[back],platform_rows,platforms[n].x,
                        platforms[n].y,0,32,8,0xf6b)<V6_SPRITE_CLIPPED) {
                    diagnostics.error=4;break;
                }
            if(diagnostics.error) break;
        }
        /* Version-5 actor slots describe platforms in this separate scene. */
        diagnostics.enemy_x=platforms[0].x;diagnostics.enemy_y=platforms[0].y;
        diagnostics.enemy_ticks=platform_ticks;diagnostics.enemy_hits=platform_pushes;
#endif
        PROFILE_MARK(5);
        diagnostics.sprite_channels=sprites[back].count;
        if(sprites[back].count>diagnostics.max_sprite_channels)
            diagnostics.max_sprite_channels=sprites[back].count;
        if (shown_deaths != slice.deaths) { shown_deaths = slice.deaths; number(8,16,shown_deaths); }
        if (shown_flips != slice.player.flips) { shown_flips = slice.player.flips; number(20,16,shown_flips); }
        if ((diagnostics.ticks & 31) == 0 && shown_work != (LONG)diagnostics.max_work_lines) { shown_work = diagnostics.max_work_lines; number(32,16,shown_work); }
        if (hud_versions[buffer] != hud_generation) {
            overlay_hud(screen[buffer],buffer); hud_versions[buffer]=hud_generation;
        }
        PROFILE_MARK(6);
        work = beam_clock() - start;
        if (loading) {
            if (work > diagnostics.max_load_lines) diagnostics.max_load_lines = work;
            diagnostics.load_frames += frames - observed;

        }
        if (!loading && work > diagnostics.max_work_lines) {
#ifdef V6_PROFILE
            { unsigned n; for(n=0;n<6;++n) profile.phase[n]=profile_marks[n+1]-profile_marks[n]; }
#endif
            diagnostics.max_work_lines = work; diagnostics.peak_tick = diagnostics.ticks;
        }
        ++diagnostics.renders;
        diagnostics.frames = frames;
        diagnostics.flips = slice.player.flips;
        diagnostics.player_x = slice.player.x; diagnostics.player_y = slice.player.y;
        diagnostics.player_vx = slice.player.vx; diagnostics.player_vy = slice.player.vy;
        diagnostics.gravity = slice.player.gravity;
        diagnostics.death_timer = slice.death_timer;
        diagnostics.deaths = slice.deaths; diagnostics.respawns = slice.respawns;
        diagnostics.checkpoint = slice.checkpoint_active; diagnostics.exits = slice.exits;
        diagnostics.room_index = slice.room_index; diagnostics.transitions = slice.transitions;
        ready = 1;
    }
    free_system();
    diagnostics.status = 2;
    {
        static const char message[] = "VVVVVV prototype: hardware restored.\n";
        Write(Output(), (APTR)message, sizeof(message) - 1);
    }
    FreeMem(chip, CHIP_BYTES);
    CloseLibrary((struct Library *)DOSBase);
    CloseLibrary((struct Library *)GfxBase);
    return 0;
}

/* Bartman ELF-to-Hunk entry: preserve the AmigaDOS caller and return normally.
 * No C++ constructors or libc are needed by this hardware harness. */
int __attribute__((used, section(".text.unlikely"))) _start(void)
{
    return run();
}
