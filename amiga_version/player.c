/* Adapted from VVVVVV Entity.cpp, Input.cpp, Logic.cpp and Map.cpp.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md.
 * Preserve input -> contact probes -> velocity -> X collision -> Y collision.
 */
#include "player.h"

/* Keep the original binary32 rounding without a floating-point runtime.
 * All supported player velocities/accelerations fit in signed 8.24. The
 * compiler expands constant power-of-two scaling to shifts on the 68000. */
static int32_t velocity_round(int32_t value)
{
    uint32_t magnitude = value < 0 ? -value : value;
    uint32_t reduced = magnitude, step = 1, rounded, tail;
    while (reduced >= (1UL << 24)) { reduced >>= 1; step <<= 1; }
    rounded = magnitude & ~(step - 1);
    tail = magnitude & (step - 1);
    if (step > 1 && (tail > step / 2 || (tail == step / 2 && (rounded & step)))) rounded += step;
    return value < 0 ? -(int32_t)rounded : (int32_t)rounded;
}

static int position(int x, int32_t velocity)
{
    int64_t value = (int64_t)x * V6_ONE + velocity;
    uint64_t magnitude = value < 0 ? -value : value;
    uint64_t reduced = magnitude, step = 1, rounded, tail;
    while (reduced >= (1UL << 24)) { reduced >>= 1; step <<= 1; }
    rounded = magnitude & ~(step - 1);
    tail = magnitude & (step - 1);
    if (step > 1 && (tail > step / 2 || (tail == step / 2 && (rounded & step)))) rounded += step;
    return value < 0 ? -(int)(rounded >> 24) : (int)(rounded >> 24);
}

static int overlap(int ax, int ay, int aw, int ah, int bx, int by, int bw, int bh)
{
    return ax < bx + bw && ax + aw > bx && ay < by + bh && ay + ah > by;
}

int v6_player_overlaps(const V6Player *p, int x, int y, int w, int h)
{
    return overlap(p->x + 6, p->y + 2, 12, 21, x, y, w, h);
}

static int solid(const V6Room *room, int x, int y)
{
    int tile, height = 29 + room->extra_row;
    /* Map::collide duplicates the edge tile for exactly one tile outside. */
    if (x == -1) x = 0;
    if (x == 40) x = 39;
    if (y == -1) y = 0;
    if (y == height) y = height - 1;
    if (x < 0 || y < 0 || x >= 40 || y >= height) return 0;
    tile = room->tiles[y * 40 + x];
    if (room->tileset == 2) return tile >= 12 && tile <= 27;
    return tile == 1 || (tile == 59 && room->tileset == 0) ||
        (tile >= 80 && tile < 680) || (tile == 740 && room->tileset == 1);
}

static int wall(const V6Room *room, int x, int y, int32_t dx, int32_t dy)
{
    int left = x + 6, top = y + 2, right = left + 11, bottom = top + 20;
    int tx, ty, gy;
    /* Deliberately /8, not >>3: original getgridpoint truncates toward zero. */
    int l = left / 8, r = right / 8, t = top / 8, b = bottom / 8;
    for (ty = t < 0 ? 0 : t; ty <= b && ty < 29 + room->extra_row; ++ty)
        for (tx = l < 0 ? 0 : l; tx <= r && tx < 40; ++tx) {
            int tile = room->tiles[ty * 40 + tx];
            if (((tile == 14 && dy > 0) || (tile == 15 && dy <= 0) ||
                 (tile == 16 && dx > 0) || (tile == 17 && dx <= 0)) &&
                overlap(left, top, 12, 21, tx * 8, ty * 8, 8, 8)) return 1;
        }
    if (solid(room, l, t) || solid(room, r, t) ||
        solid(room, l, b) || solid(room, r, b)) return 1;
    for (gy = 6; gy <= 12; gy += 6)
        if (solid(room, l, (top + gy) / 8) || solid(room, r, (top + gy) / 8)) return 1;
    return solid(room, (left + 6) / 8, t) || solid(room, (left + 6) / 8, b);
}

void v6_player_init(V6Player *p, int x, int y, int gravity)
{
    p->x = p->old_x = x;
    p->y = p->old_y = y;
    p->vx = p->vy = p->ay = 0;
    p->ground = p->roof = p->tap_left = p->tap_right = 0;
    p->held = p->buffer = p->flips = 0;
    p->gravity = gravity;
    p->dir = 1;
}

unsigned v6_player_step(V6Player *p, const V6Room *room, unsigned input)
{
    int32_t ax = 0, next;
    const int32_t friction = 18454938; /* exact binary32 1.1f, scaled by 2^24 */
    unsigned event = 0;
    if (!(input & V6_NO_CONTROL)) {
    if (input & V6_LEFT) { ax = -3 * V6_ONE; p->dir = 0; }
    else if (input & V6_RIGHT) { ax = 3 * V6_ONE; p->dir = 1; }
    if (input & V6_LEFT) ++p->tap_left;
    else {
        if (p->tap_left > 0 && p->tap_left <= 4 && p->vx < 0) p->vx = 0;
        p->tap_left = 0;
    }
    if (input & V6_RIGHT) ++p->tap_right;
    else {
        if (p->tap_right > 0 && p->tap_right <= 4 && p->vx > 0) p->vx = 0;
        p->tap_right = 0;
    }
    if (!(input & V6_FLIP)) { p->buffer = 0; p->held = 0; }
    if ((input & V6_FLIP) && !p->held) { p->buffer = 5; p->held = 1; }
    if (p->buffer > 0 && !(input & V6_NO_CONTROL)) {
        --p->buffer;
        if (p->ground > 0 && !p->gravity) {
            p->gravity = 1; p->vy = -4 * V6_ONE; p->ay = -3 * V6_ONE;
            p->buffer = 0; ++p->flips; event = V6_EVENT_FLIP;
        }
        /* Separate if, as in Input.cpp (also significant if wedged). */
        if (p->roof > 0 && p->gravity) {
            p->gravity = 0; p->vy = 4 * V6_ONE; p->ay = 3 * V6_ONE;
            p->buffer = 0; ++p->flips; event = V6_EVENT_FLIP;
        }
    }
    }
    p->ground = wall(room, p->x, p->y + 1, 0, 0) ? 2 : p->ground - 1;
    p->roof = wall(room, p->x, p->y - 1, 0, 0) ? 2 : p->roof - 1;
    p->old_x = p->x; p->old_y = p->y;
    p->vx = velocity_round(p->vx + ax); p->vy = velocity_round(p->vy + p->ay);
    p->ay = p->gravity ? -3 * V6_ONE : 3 * V6_ONE;
    /* Sequential tests, not if/else: friction may cross zero. */
    if (p->vx > 0) p->vx = velocity_round(p->vx - friction);
    if (p->vx < 0) p->vx = velocity_round(p->vx + friction);
    if (p->vy > 0) p->vy -= V6_ONE / 4;
    if (p->vy < 0) p->vy += V6_ONE / 4;
    if (p->vx > 6 * V6_ONE) p->vx = 6 * V6_ONE;
    if (p->vx < -6 * V6_ONE) p->vx = -6 * V6_ONE;
    if (p->vy > 10 * V6_ONE) p->vy = 10 * V6_ONE;
    if (p->vy < -10 * V6_ONE) p->vy = -10 * V6_ONE;
    if (p->vx > -friction && p->vx < friction) p->vx = 0;
    if (p->vy > -V6_ONE/4 && p->vy < V6_ONE/4) p->vy = 0;
    next = position(p->x, p->vx);
    while (wall(room, next, p->y, p->vx, 0)) {
        if (p->vx > V6_ONE) p->vx = velocity_round(p->vx - V6_ONE);
        else if (p->vx < -V6_ONE) p->vx = velocity_round(p->vx + V6_ONE);
        else { p->vx = 0; break; }
        next = position(p->x, p->vx);
    }
    if (p->vx) p->x = next;
    next = position(p->y, p->vy);
    while (wall(room, p->x, next, 0, p->vy)) {
        if (p->vy > V6_ONE) p->vy -= V6_ONE;
        else if (p->vy < -V6_ONE) p->vy += V6_ONE;
        else { p->vy = 0; break; }
        next = position(p->y, p->vy);
    }
    if (p->vy) p->y = next;
    return event;
}

int v6_player_hurt(const V6Player *p, const V6Room *room)
{
    int tx, ty;
    int left = (p->x + 6) / 8, right = (p->x + 17) / 8;
    int top = (p->y + 2) / 8, bottom = (p->y + 22) / 8;
    for (ty = top < 0 ? 0 : top; ty <= bottom && ty < 29 + room->extra_row; ++ty)
        for (tx = left < 0 ? 0 : left; tx <= right && tx < 40; ++tx) {
            int tile = room->tiles[ty * 40 + tx], dy = -1, height = 4;
            if (room->tileset == 1) {
                if ((tile >= 63 && tile <= 74) || (tile >= 6 && tile <= 9)) {
                    int adjusted = tile < 10 ? tile + 1 : tile;
                    dy = (adjusted & 1) ? 4 : 0;
                }
                if (tile >= 49 && tile <= 62) { dy = 3; height = 2; }
            } else {
                if (tile == 6 || tile == 8) dy = 4;
                if (tile == 7 || tile == 9) dy = 0;
                if (room->tileset == 0 && (tile == 49 || tile == 50)) { dy = 3; height = 2; }
            }
            if (dy >= 0 && v6_player_overlaps(p, tx * 8, ty * 8 + dy, 8, height)) return 1;
        }
    return 0;
}
