/* Adapted from VVVVVV Entity.cpp, Input.cpp, Logic.cpp and Map.cpp.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md.
 * Preserve input -> contact probes -> velocity -> X collision -> Y collision.
 */
#include "player.h"

void v6_player_tower_room(V6Room *room,const V6TowerTiles *source)
{
    room->tiles=(const uint16_t *)(const void *)source;
    room->tileset=V6_TILE_SOURCE_TOWER;room->extra_row=0;room->terrain=0;
    room->blocks=0;room->block_count=0;
}
static int tower_tile(const V6Room *room,int x,int y)
{
    const V6TowerTiles *source=(const void *)room->tiles;
    return source->read(source->context,x,y);
}

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
    /* In bounded tower coordinates an integer plus a quarter-pixel velocity is exactly
     * representable in binary32. Avoid 64-bit rounding for these common cases. */
    if (x >= -16384 && x <= 16384 && (velocity & (V6_ONE/4-1)) == 0)
        return (x*4 + velocity/(V6_ONE/4))/4;
    if(x>=-16384 && x<=16384 && velocity>=-10*V6_ONE && velocity<=10*V6_ONE) {
        /* Split the exact sum before rounding so it fits 32-bit registers.
         * The integral part determines binary32 spacing; rounding the
         * fractional magnitude can carry across the next pixel boundary. */
        int whole=x+velocity/V6_ONE,negative;
        int32_t fraction=velocity%V6_ONE;
        uint32_t magnitude,reduced,step=1,rounded,tail;
        if(whole>0 && fraction<0) { --whole;fraction+=V6_ONE; }
        else if(whole<0 && fraction>0) { ++whole;fraction-=V6_ONE; }
        negative=whole<0 || (!whole && fraction<0);
        magnitude=fraction<0?(uint32_t)-fraction:(uint32_t)fraction;
        reduced=whole<0?(unsigned)-whole:(unsigned)whole;
        while(reduced) { reduced>>=1;step<<=1; }
        rounded=magnitude&~(step-1);tail=magnitude&(step-1);
        if(step>1 && (tail>step/2 || (tail==step/2 && (rounded&step)))) rounded+=step;
        whole=whole<0?-whole:whole;
        if(rounded>=V6_ONE) ++whole;
        return negative?-whole:whole;
    }
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
    if(room->tileset==V6_TILE_SOURCE_TOWER) {
        const V6TowerTiles *source=(const void *)room->tiles;
        int tile=tower_tile(room,x,y);
        return (tile>=12 && tile<=27) || (source->invincible && tile>=6 && tile<=11);
    }
    if (room->terrain) return v6_terrain_solid(room->terrain,x,y);
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

static inline __attribute__((always_inline)) int wall_mode(const V6Room *room, int x, int y, int32_t dx, int32_t dy, int skip_directional)
{
    int left = x + 6, top = y + 2, right = left + 11, bottom = top + 20;
    int tx, ty, gy, previous_row;
    unsigned i;
    for(i=0;i<room->block_count;++i)
        if((!skip_directional || room->blocks[i].type!=V6_DIRECTIONAL) && v6_block_hit(&room->blocks[i],left,top,12,21,dx,dy,0)) return 1;
    if(room->tileset==V6_TILE_SOURCE_TOWER) {
        const V6TowerTiles *source=(const void *)room->tiles;
        if(source->walls) return source->walls(source->context,x,y,source->invincible);
    }
    /* Deliberately /8, not >>3: original getgridpoint truncates toward zero. */
    int l = left / 8, r = right / 8, t = top / 8, b = bottom / 8;
    if (solid(room, l, t) || solid(room, r, t) ||
        solid(room, l, b) || solid(room, r, b)) return 1;
    previous_row=t;
    for (gy = 6; gy <= 12; gy += 6) {
        int row=(top+gy)/8;
        if (row != t && row != b && row != previous_row &&
            (solid(room,l,row) || solid(room,r,row))) return 1;
        previous_row=row;
    }
    tx=(left+6)/8;
    if(tx != l && tx != r && (solid(room,tx,t) || solid(room,tx,b))) return 1;
    if(room->terrain && room->tileset==2) {
        /* Tiles 14..17 are solid in tileset 2. All edge cells have already
         * been sampled, so only an unsampled interior directional block can
         * add a collision. The 12-pixel body spans at most three columns. */
        if(!skip_directional && room->terrain->directional && r-l==2)
            for(ty=t+1;ty<b;++ty) if(ty>=0 && ty<29+room->extra_row && l+1>=0 && l+1<40) {
                int tile=room->tiles[ty*40+l+1];
                if((tile==14 && dy>0) || (tile==15 && dy<=0) ||
                   (tile==16 && dx>0) || (tile==17 && dx<=0)) return 1;
            }
        return 0;
    }
    if (room->tileset!=V6_TILE_SOURCE_TOWER && !skip_directional && (!room->terrain || room->terrain->directional))
    for (ty = t < 0 ? 0 : t; ty <= b && ty < 29 + room->extra_row; ++ty)
        for (tx = l < 0 ? 0 : l; tx <= r && tx < 40; ++tx) {
            int tile = room->tiles[ty * 40 + tx];
            if (((tile == 14 && dy > 0) || (tile == 15 && dy <= 0) ||
                 (tile == 16 && dx > 0) || (tile == 17 && dx <= 0)) &&
                overlap(left, top, 12, 21, tx * 8, ty * 8, 8, 8)) return 1;
        }
    return 0;
}
static int wall(const V6Room *room, int x, int y, int32_t dx, int32_t dy)
{ return wall_mode(room,x,y,dx,dy,0); }

/* Separate probe keeps the normal collision path free of directional-skip
 * branches. Like testwallsx, retries change velocity but never commit X. */
void v6_player_unstick(V6Player *p,const V6Room *room)
{
    int next=p->x;
    while (wall_mode(room,next,p->y,p->vx,0,1)) {
        if(p->vx>V6_ONE) p->vx=velocity_round(p->vx-V6_ONE);
        else if(p->vx<-V6_ONE) p->vx=velocity_round(p->vx+V6_ONE);
        else {
            p->vx=0;
            p->y+=p->gravity ? 3 : -3;
            return;
        }
        next=position(p->x,p->vx);
    }
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

unsigned v6_player_input(V6Player *p, unsigned input, V6PlayerMotion *motion)
{
    int32_t ax = 0;
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
    }
    /* Input.cpp tracks flip edges even while player control is locked. */
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
    motion->ax=ax;
    return event;
}

void v6_player_physics(V6Player *p,const V6Room *room,V6PlayerMotion *motion,V6ContactHook hook,void *context)
{
    const int32_t friction = 18454938; /* binary32 1.1f in 8.24 */
    p->ground = wall(room, p->x, p->y + 1, 0, 0) ? 2 : p->ground - 1;
    p->roof = wall(room, p->x, p->y - 1, 0, 0) ? 2 : p->roof - 1;
    if (hook) hook(p, context);
    p->old_x = p->x; p->old_y = p->y;
    p->vx = velocity_round(p->vx + motion->ax); motion->ax=0; p->vy = velocity_round(p->vy + p->ay);
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
    motion->pending_y=v6_player_map_move(p,room,position(p->x,p->vx),position(p->y,p->vy));
}

int v6_player_hurt(const V6Player *p, const V6Room *room)
{
    int tx, ty;
    int left = (p->x + 6) / 8, right = (p->x + 17) / 8;
    int top = (p->y + 2) / 8, bottom = (p->y + 22) / 8;
    if(room->tileset==V6_TILE_SOURCE_TOWER) {
        const V6TowerTiles *source=(const void *)room->tiles;
        int rows[4] = {top,bottom,(p->y+8)/8,(p->y+14)/8},i;
        if(source->invincible) return 0;
        for(i=0;i<4;++i) {
            if(i>=2 && (rows[i]==top || rows[i]==bottom ||
                (i==3 && rows[3]==rows[2]))) continue;
            int a=tower_tile(room,left,rows[i]),b=tower_tile(room,right,rows[i]);
            if((a>=6 && a<=11) || (b>=6 && b<=11)) return 1;
        }
        return 0;
    }
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

unsigned v6_player_step_hook(V6Player *p,const V6Room *room,unsigned input,V6ContactHook hook,void *context)
{
    V6PlayerMotion motion={0,p->y};
    unsigned events=v6_player_input(p,input,&motion);
    v6_player_physics(p,room,&motion,hook,context);
    return events;
}

unsigned v6_player_step(V6Player *p, const V6Room *room, unsigned input)
{ return v6_player_step_hook(p,room,input,0,0); }
int v6_player_contacts(const V6Player *p, const V6Room *room)
{ return wall(room,p->x,p->y+1,0,0) | (wall(room,p->x,p->y-1,0,0)<<1); }

int v6_player_map_move(V6Player *p,const V6Room *room,int target_x,int target_y)
{
    int next=target_x, allowed=1;
    while (wall(room, next, p->y, p->vx, 0)) {
        if (p->vx > V6_ONE) p->vx = velocity_round(p->vx - V6_ONE);
        else if (p->vx < -V6_ONE) p->vx = velocity_round(p->vx + V6_ONE);
        else { p->vx = 0; allowed=0; break; }
        next = position(p->x, p->vx);
    }
    if (allowed) p->x = next;
    if (v6_player_test_y(p,room,&target_y)) p->y=target_y;
    return target_y;
}

int v6_player_test_y(V6Player *p,const V6Room *room,int *target_y)
{
    int next=*target_y;
    while (wall(room, p->x, next, 0, p->vy)) {
        if (p->vy > V6_ONE) p->vy -= V6_ONE;
        else if (p->vy < -V6_ONE) p->vy += V6_ONE;
        else { p->vy = 0; return 0; }
        next = position(p->y, p->vy);
        *target_y=next;
    }
    return 1;
}
