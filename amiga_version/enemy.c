/* Adapted from Entity.cpp moving behaviours 0..3, updateentitylogic,
 * entitymapcollision, checkwall and Ent.cpp outside. See ../LICENSE.md. */
#include "enemy.h"

static int outside(V6Enemy *e)
{
    if (e->x < e->x1) { e->x = e->x1; return 1; }
    if (e->y < e->y1) { e->y = e->y1; return 1; }
    if (e->x + e->w > e->x2) { e->x = e->x2 - e->w; return 1; }
    if (e->y + e->h > e->y2) { e->y = e->y2 - e->h; return 1; }
    return 0;
}

static void behavior(V6Enemy *e)
{
    if (!e->state) e->state = e->behavior == 1 ? 2 : 3;
    if (e->state == 1) {
        if (outside(e)) e->state = e->onwall;
    } else if (e->state == 2 || e->state == 3) {
        int velocity = e->state == 2 ? -e->speed : e->speed;
        if (e->behavior == 2) velocity = -velocity;
        if (e->behavior < 2) e->vy = velocity; else e->vx = velocity;
        e->onwall = e->state == 2 ? 3 : 2;
        e->state = 1;
    }
}

int v6_enemy_init(V6Enemy *e, int x, int y, int kind, int speed,
                  int x1, int y1, int x2, int y2, int cx, int cy, int w, int h)
{
    if (kind < 0 || kind > 3 || speed < -16 || speed > 16 ||
        w < 1 || w > 32 || h < 1 || h > 32 ||
        x1 < -64 || y1 < -64 || x2 > 384 || y2 > 304 ||
        x2-x1 < w || y2-y1 < h || x < -64 || x > 384 || y < -64 || y > 304 ||
        cx < 0 || cy < 0 || cx > 32 || cy > 32) return 0;
    e->x = e->old_x = x; e->y = e->old_y = y;
    e->vx = e->vy = 0; e->behavior = kind; e->speed = speed;
    e->state = e->onwall = 0;
    e->x1 = x1; e->y1 = y1; e->x2 = x2; e->y2 = y2;
    e->cx = cx; e->cy = cy; e->w = w; e->h = h;
    behavior(e); /* createentity invokes updateentities immediately. */
    return 1;
}

static int solid(const V6Room *r, int x, int y)
{
    if (r->terrain) return v6_terrain_solid(r->terrain,x,y);
    int tile, height = 29+r->extra_row;
    if (x == -1) x = 0;
    if (x == 40) x = 39;
    if (y == -1) y = 0;
    if (y == height) y = height-1;
    if (x < 0 || x >= 40 || y < 0 || y >= height) return 0;
    tile = r->tiles[y*40+x];
    if (r->tileset == 2) return tile >= 12 && tile <= 27;
    return tile == 1 || (tile >= 80 && tile < 680) ||
        (tile == 59 && r->tileset == 0) || (tile == 740 && r->tileset == 1);
}

static int wall(const V6Enemy *e, const V6Room *r, const V6EnemyBlock *blocks,
                unsigned count, int x, int y)
{
    int left = x+e->cx, top = y+e->cy, right = left+e->w, bottom = top+e->h;
    int l = left/8, t = top/8, rr = (right-1)/8, b = (bottom-1)/8, offset;
    unsigned i;
    for (i=0; i<count; ++i) {
        const V6EnemyBlock *p = &blocks[i];
        /* Rule 1 supplies dx=dy=0 even while moving. Thus only directional
         * triggers 1 and 3 block an enemy; this is intentional source behavior. */
        if (v6_block_hit(p,left,top,e->w,e->h,0,0,1)) return 1;
    }
    if (solid(r,l,t) || solid(r,rr,t) || solid(r,l,b) || solid(r,rr,b)) return 1;
    for (offset=6; offset<=18 && e->h>=offset+6; offset+=6) {
        int row=(top+offset)/8;
        if (row != t && row != b && (solid(r,l,row) || solid(r,rr,row))) return 1;
    }
    if (e->w>=12) {
        int column=(left+6)/8;
        if (column != l && column != rr && (solid(r,column,t) || solid(r,column,b))) return 1;
    }
    return 0;
}

void v6_enemy_step(V6Enemy *e, const V6Room *r, const V6EnemyBlock *blocks, unsigned count)
{
    behavior(e);
    v6_enemy_move(e,r,blocks,count);
}

void v6_enemy_move(V6Enemy *e,const V6Room *r,const V6EnemyBlock *blocks,unsigned count)
{
    int next;
    e->old_x = e->x; e->old_y = e->y;
    next = e->x+e->vx;
    while (wall(e,r,blocks,count,next,e->y)) {
        if (e->vx > 1) --e->vx;
        else if (e->vx < -1) ++e->vx;
        else { e->vx = 0; e->state = e->onwall; break; }
        next = e->x+e->vx;
    }
    if (e->vx) e->x = next;
    next = e->y+e->vy;
    while (wall(e,r,blocks,count,e->x,next)) {
        if (e->vy > 1) --e->vy;
        else if (e->vy < -1) ++e->vy;
        else { e->vy = 0; e->state = e->onwall; break; }
        next = e->y+e->vy;
    }
    if (e->vy) e->y = next;
}
