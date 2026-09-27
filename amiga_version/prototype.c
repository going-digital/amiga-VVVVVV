/* VVVVVV A500 playable static-room slice. Original tiles and player rules.
 * The full campaign, moving entities and scripts are pending.
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
#define SCREEN_BYTES (4 * PLANE_BYTES)
#define BACKGROUND_BYTES (4 * BACKGROUND_PLANE_BYTES)
#define BACKGROUND_CACHE_BYTES (SLICE_ROOM_COUNT * BACKGROUND_BYTES)
#define COPPER_BYTES 256
#define HUD_PLANE_BYTES (40 * 40)
#define HUD_BYTES (4 * HUD_PLANE_BYTES)
#define MASK_BYTES (32 * 6)
#define CHIP_BYTES (2 * SCREEN_BYTES + BACKGROUND_CACHE_BYTES + COPPER_BYTES + sizeof(flip_sound) + 4 + HUD_BYTES + MASK_BYTES)

/* Located by the host smoke test in a RAM dump. Fixed-width big-endian fields. */
static volatile struct {
    ULONG magic, version, frames, ticks, renders, max_work_lines, missed_frames;
    ULONG flips, scroll_mode, chip_free, other_free, chip_allocated, error, status;
    LONG player_x, player_y, player_vx, player_vy, gravity, death_timer;
    ULONG deaths, respawns, checkpoint, exits;
    ULONG room_index, transitions, max_load_lines, load_frames;
} diagnostics = {.magic = 0x56364447, .version = 3, .chip_allocated = CHIP_BYTES};

static volatile ULONG frames;
static UBYTE *chip, *screen[2], *background, *sample, *hud;
static UWORD *sprite_masks;
static UWORD *copper, *plane_words, *silence;
static UWORD room_tiles[SLICE_ROOM_COUNT][1200];
static UWORD *room = room_tiles[0];
static V6Slice slice;
static V6Room current_room = {room_tiles[0], 1, 1};
static UWORD saved_dma, saved_ints, saved_adk;
static APTR saved_irq;
static struct View *saved_view;

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
    UWORD p;
    for (p = 0; p < 4; ++p) {
        ULONG address = (ULONG)(data + p * PLANE_BYTES);
        plane_words[p * 4 + 1] = address >> 16;
        plane_words[p * 4 + 3] = address;
    }
}

static void create_copper(void)
{
    UWORD *p = copper;
    UWORD i;
    p = move_reg(p, 0x100, 0x4200); /* four planes, color */
    p = move_reg(p, 0x102, 0);
    p = move_reg(p, 0x104, 0);
    p = move_reg(p, 0x108, 0);
    p = move_reg(p, 0x10a, 0);
    p = move_reg(p, 0x08e, 0x3481); /* PAL: y=52, x=129 */
    p = move_reg(p, 0x090, 0x24c1); /* y=292, x=449 */
    p = move_reg(p, 0x092, 0x0038);
    p = move_reg(p, 0x094, 0x00d0);
    /* The CPU publishes completed buffer pointers just after the VBL IRQ.
     * Delay Copper pointer reads until line 44, before the visible line 52. */
    *p++ = 0x2c01; *p++ = 0xfffe;
    plane_words = p;
    for (i = 0; i < 4; ++i) {
        p = move_reg(p, 0x0e0 + 4 * i, 0);
        p = move_reg(p, 0x0e2 + 4 * i, 0);
    }
    for (i = 0; i < 16; ++i) p = move_reg(p, 0x180 + i * 2, palette[i]);
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
    hw->dmacon = DMAF_SETCLR | DMAF_MASTER | DMAF_RASTER | DMAF_COPPER | DMAF_BLITTER;
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
        for (plane = 0; plane < 4; ++plane) for (row = 0; row < 8; ++row)
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

/* Word-aligned damaged rectangle. Each back buffer tracks its own old player. */
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
    for (plane = 0; plane < 4; ++plane) {
        ULONG offset = plane * PLANE_BYTES + y * 40 + left_word * 2;
        wait_blit();
        hw->bltcon0 = 0x09f0; hw->bltcon1 = 0;
        hw->bltafwm = hw->bltalwm = 0xffff;
        hw->bltamod = hw->bltdmod = 40 - words * 2;
        hw->bltapt = background + offset;
        hw->bltdpt = dst + offset;
        hw->bltsize = ((bottom-y) << 6) | words;
    }
    wait_blit();
}

static void draw_player(UBYTE *dst, int x, int y, UWORD frame)
{
    UWORD plane, row, shift = x & 15;
    int left_word = x < 0 ? (x-15)/16 : x/16;
    int skip_words = left_word < 0 ? -left_word : 0;
    int width = (shift ? 3 : 2) - skip_words;
    int skip_rows = y < 0 ? -y : 0, rows = 32 - skip_rows;
    UWORD *mask;
    if (left_word < 0) left_word = 0;
    if (left_word + width > 20) width = 20 - left_word;
    if (y < 0) y = 0;
    if (y + rows > 240) rows = 240-y;
    if (width <= 0 || rows <= 0) return;
    wait_blit();
    for (row = 0; row < 32; ++row) {
        ULONG bits = sprite_rows[frame][row], upper = bits >> shift;
        sprite_masks[row*3] = upper >> 16;
        sprite_masks[row*3+1] = upper;
        sprite_masks[row*3+2] = shift ? (UWORD)bits << (16-shift) : 0;
    }
    mask = sprite_masks + skip_rows*3 + skip_words;
    for (plane = 0; plane < 4; ++plane) {
        UBYTE *target = dst + plane * PLANE_BYTES + y * 40 + left_word * 2;
        wait_blit();
        /* Set cyan index 14 under opaque mask; preserve the background. */
        hw->bltcon0 = plane ? 0x0bfa : 0x0b0a; /* A | C or ~A & C */
        hw->bltcon1 = 0;
        hw->bltafwm = hw->bltalwm = 0xffff;
        hw->bltamod = 6 - width * 2;
        hw->bltcmod = hw->bltdmod = 40 - width * 2;
        hw->bltapt = (APTR)mask;
        hw->bltcpt = target;
        hw->bltdpt = target;
        hw->bltsize = (rows << 6) | width;
    }
    wait_blit();
}

static void text(UWORD x, UWORD y, const char *s)
{
    UWORD row, plane;
    while (*s && x < 40) {
        const UBYTE *glyph = font_rows[(UBYTE)*s++ & 127];
        for (plane = 0; plane < 4; ++plane) for (row = 0; row < 8; ++row)
            hud[plane * HUD_PLANE_BYTES + (y + row) * 40 + x] = glyph[row];
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

static void overlay_hud(UBYTE *dst)
{
    UWORD plane;
    for (plane = 0; plane < 4; ++plane) {
        blit_rows(hud + plane * HUD_PLANE_BYTES, dst + plane * PLANE_BYTES, 16);
        blit_rows(hud + plane * HUD_PLANE_BYTES + 16 * 40,
                  dst + plane * PLANE_BYTES + 216 * 40, 24);
    }
    wait_blit();
}

static void draw_checkpoint(void)
{
    UWORD row, plane, color = slice.checkpoint_active ? 13 : 15;
    UWORD shift = slice.checkpoint_x & 15;
    for (row = 0; row < 32; ++row) {
        ULONG bits = sprite_rows[slice.checkpoint_tile][row];
        ULONG shifted = bits >> shift;
        UWORD first = shifted >> 16, second = shifted;
        UWORD tail = shift ? bits << (16-shift) : 0;
        UWORD *p = (UWORD *)(background + (slice.checkpoint_y + row) * 40
            + (slice.checkpoint_x / 16) * 2);
        for (plane = 0; plane < 4; ++plane) {
            if (color & (1 << plane)) {
                p[0] |= first; p[1] |= second;
                if (shift) p[2] |= tail;
            } else {
                p[0] &= ~first; p[1] &= ~second;
                if (shift) p[2] &= ~tail;
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
    WORD old_x[2], old_y[2];
    UWORD checkpoint_dirty[2] = {0,0}, room_dirty[2] = {0,0};
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
    screen[0] = chip; screen[1] = chip + SCREEN_BYTES;
    background = chip + SCREEN_BYTES * 2;
    copper = (UWORD *)(background + BACKGROUND_CACHE_BYTES);
    sample = (UBYTE *)copper + COPPER_BYTES;
    silence = (UWORD *)(sample + sizeof(flip_sound));
    hud = (UBYTE *)(silence + 2);
    sprite_masks = (UWORD *)(hud + HUD_BYTES);
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
        background = chip + SCREEN_BYTES * 2 + i * BACKGROUND_BYTES;
        draw_room();
    }
    room = room_tiles[0]; background = chip + SCREEN_BYTES * 2;
    diagnostics.chip_free = AvailMem(MEMF_CHIP);
    diagnostics.other_free = AvailMem(MEMF_FAST);
    v6_slice_init_world(&slice, room_setups, SLICE_ROOM_COUNT, 0);
    old_x[0] = old_x[1] = slice.player.x;
    old_y[0] = old_y[1] = slice.player.y;
    draw_checkpoint();
    text(1, 0, "VVVVVV AMIGA - PLAYABLE ROOM");
    text(1, 8, "100,110 - TWO ROOM SLICE");
    text(1, 16, "DEATHS       FLIPS       LINES");
    text(1, 32, "JOY L/R FIRE FLIP RMB RESET LMB EXIT");
    create_copper();
    take_system();
    restore_rectangle(screen[0], 0, 0, 320, 240);
    restore_rectangle(screen[1], 0, 0, 320, 240);
    observed = frames;
    diagnostics.status = 1;
    while (*(volatile UBYTE *)0xbfe001 & 0x40) { /* left mouse exits */
        ULONG current, delta, start, work;
        UWORD loading;
        UWORD joy, fire, right_mouse, input = 0;
        while (frames == observed) {}
        current = frames;
        delta = current - observed;
        observed = current;
        if (delta > 1) diagnostics.missed_frames += delta - 1;
        if (ready) { set_screen(screen[back]); back ^= 1; ready = 0; }
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
        while (elapsed_us >= 34000) {
            elapsed_us -= 34000;
            ++diagnostics.ticks;
            {
                unsigned events;
#ifdef V6_TRANSITION_REPLAY
                input = diagnostics.ticks <= sizeof(transition_replay)
                    ? transition_replay[diagnostics.ticks - 1] : 0;
                if (diagnostics.ticks == 100) restart_pending = 1;
#endif
                current_room.tiles = room_tiles[slice.room_index];
                events = v6_slice_step(&slice, &current_room, input, restart_pending);
                restart_pending = 0;
                if (events & V6_EVENT_FLIP) sound();
                if (events & V6_EVENT_ROOM) {
                    background = chip + SCREEN_BYTES * 2 + slice.room_index * BACKGROUND_BYTES;
                    room = room_tiles[slice.room_index];
                    room_dirty[0] = room_dirty[1] = 1;
                    checkpoint_dirty[0] = checkpoint_dirty[1] = 0;
                    draw_checkpoint();
                    text(1, 8, slice.room_index ? "119,110 - TWO ROOM SLICE           " : "100,110 - TWO ROOM SLICE           ");
                }
                if (events & V6_EVENT_SAVE) {
                    draw_checkpoint(); checkpoint_dirty[0] = checkpoint_dirty[1] = 1;
                }
                if (events & V6_EVENT_EXIT) {
                    exit_notice = 60;
                    text(1, 8, "ROOM EXIT: BACK TO SLICE CHECKPOINT");
                }
            }
            if (exit_notice && --exit_notice == 0) text(1, 8, slice.room_index ? "119,110 - TWO ROOM SLICE           " : "100,110 - TWO ROOM SLICE           ");
        }
        loading = room_dirty[back];
        if (loading) {
            restore_rectangle(screen[back], 0, 0, 320, 240);
            room_dirty[back] = 0;
        } else restore_rectangle(screen[back], old_x[back], old_y[back], 32, 32);
        if (checkpoint_dirty[back]) {
            restore_rectangle(screen[back], slice.checkpoint_x, slice.checkpoint_y, 32, 32);
            checkpoint_dirty[back] = 0;
        }
        draw_player(screen[back], slice.player.x, slice.player.y, slice.frame);
        if (shown_deaths != slice.deaths) { shown_deaths = slice.deaths; number(8,16,shown_deaths); }
        if (shown_flips != slice.player.flips) { shown_flips = slice.player.flips; number(20,16,shown_flips); }
        if (shown_work != (LONG)diagnostics.max_work_lines) { shown_work = diagnostics.max_work_lines; number(32,16,shown_work); }
        overlay_hud(screen[back]);
        old_x[back] = slice.player.x;
        old_y[back] = slice.player.y;
        work = beam_clock() - start;
        if (loading) {
            if (work > diagnostics.max_load_lines) diagnostics.max_load_lines = work;
            diagnostics.load_frames += frames - observed;
            /* Explicit slice loading pause; never feed rendering backlog into
             * a burst of player updates. Full-game timing remains a later gate. */
            observed = frames; elapsed_us = 0;
        }
        if (!loading && work > diagnostics.max_work_lines) diagnostics.max_work_lines = work;
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
