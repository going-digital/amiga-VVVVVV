#ifndef V6_MAP_DRAW_H
#define V6_MAP_DRAW_H
#include <stdint.h>
#include "teleporter_admission.h"
#include "save_page.h"
#define V6_MAP_PLANE_BYTES 9600
#define V6_MAP_BITMAP_BYTES (5*V6_MAP_PLANE_BYTES)
/* Normal 20x20 world: original 240x180 image at (40,21), 12x9 fog,
 * alpha textbox border, room title and four source-positioned tabs.
 * colours: black, background, textbox fill, border, text, dark text.
 * Output is one row, five consecutive 40-byte planes. Raw assets must contain
 * only indices 0..31; arguments are validated before writing.
 * Caller copies rows to an inactive/hidden Chip bitmap. Legends are excluded. */
int v6_map_draw_row(uint8_t out[200],unsigned row,const V6Exploration *,
    const uint8_t minimap[43200],const uint8_t fog[108],const uint8_t font[128][8],
    const uint8_t border[8][8],const uint8_t colours[6],const char *roomname);
/* Equivalent lossless run/count stream, with 181 row offsets. The requested
 * image row must decode to exactly 240 indices in 0..31; malformed input
 * leaves output unchanged. The private converter validates the complete asset. */
int v6_map_draw_row_rle(uint8_t out[200],unsigned row,const V6Exploration *,
    const uint8_t *runs,unsigned bytes,const uint16_t offsets[181],const uint8_t fog[108],
    const uint8_t font[128][8],const uint8_t border[8][8],const uint8_t colours[6],const char *roomname);
/* Native fast path: offline source-equivalent full-map template, encoded in
 * display-row order (five consecutive 40-byte planes). Fog masks are the
 * original 12x9 tile packed into high 12 bits, nine rows by five planes.
 * The requested template row must decode to exactly 200 bytes. */
int v6_map_draw_template_row(uint8_t out[200],unsigned row,const V6Exploration *,
    const uint8_t *runs,unsigned bytes,const uint16_t offsets[241],const uint16_t fog[9][5]);
/* Normal non-tower current-room marker. Mode 1: white double outline;
 * mode 2: cyan inner outline. Zero hides. The caller advances the source timer;
 * delay is normalized to 30..59 in state 2, preserving its /15 blink phase.
 * Rows are source-format 32-bit sprite masks; only 12x9 are used. */
void v6_map_cursor_tick(unsigned *state,unsigned *delay);
unsigned v6_map_cursor_mode(unsigned state,unsigned delay,int noflashing);
int v6_map_cursor_rows(uint32_t rows[32],unsigned mode,int room_x,int room_y,int *x,int *y);
/* Full-screen five-plane Copper list. Bitmap addresses are even/24-bit;
 * caller supplies Chip memory and an inactive list. Palette[17] is cursor.
 * Blank sprite pointers supplied by caller; optional sprite 0 overrides it.
 * 140 words are sufficient. Invalid arguments leave output untouched. */
#define V6_MAP_COPPER_WORDS 140
/* Same list for admitted three/five-plane menus; capacity remains 140. */
unsigned v6_menu_copper(uint16_t *,uint32_t,const uint16_t palette[32],uint32_t,uint32_t,unsigned);
unsigned v6_map_copper(uint16_t *,uint32_t bitmap,const uint16_t palette[32],uint32_t blank,uint32_t cursor);
/* Source Save page prompt or failure message, Latin 8px font,
 * normal orientation and glow zero. Receipt, restricted modes, last summary, script-only and ship tabs are not admitted.
 * colours extend the map semantics with white and muted (RGB12 99b).
 * Action is a caller-owned printable ASCII label; output unchanged on error. */
int v6_save_draw_row(uint8_t out[200],unsigned row,const V6SavePage *,
    const uint8_t font[128][8],const uint8_t border[8][8],
    const uint8_t colours[8],const char *roomname,const char *action);
#endif
