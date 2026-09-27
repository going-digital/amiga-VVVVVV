#ifndef V6_BLOCKS_H
#define V6_BLOCKS_H
#include <stdint.h>
enum { V6_BLOCK, V6_SAFE, V6_DIRECTIONAL };
typedef struct { int x, y, w, h, type, trigger; } V6Block;
/* Disable every matching origin; moving restores only the first matching
 * block, preserving source order even when origins overlap. */
void v6_blocks_disable_at(V6Block *, unsigned count, int x, int y);
int v6_blocks_move(V6Block *, unsigned count, int old_x, int old_y,
                   int x, int y, int w, int h);
/* Matches Entity::checkblocks for player/enemy rules. Empty rectangles never
 * collide (including temporarily disabled platform blocks). */
static inline int v6_block_hit(const V6Block *b, int x, int y, int w, int h,
                               int32_t dx, int32_t dy, int enemy)
{
    int blocking=b->type==V6_BLOCK || (b->type==V6_SAFE && enemy) ||
        (b->type==V6_DIRECTIONAL &&
         ((b->trigger==0 && dy>0) || (b->trigger==1 && dy<=0) ||
          (b->trigger==2 && dx>0) || (b->trigger==3 && dx<=0)));
    return blocking && b->w>0 && b->h>0 && w>0 && h>0 &&
        x<b->x+b->w && x+w>b->x && y<b->y+b->h && y+h>b->y;
}
#endif
