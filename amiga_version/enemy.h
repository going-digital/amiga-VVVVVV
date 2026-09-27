#ifndef V6_ENEMY_H
#define V6_ENEMY_H
#include "player.h"
/* Movement-only subset: ordinary bouncing enemies (behaviours 0..3), integer
 * speeds -16..16, hitboxes up to 32x32. No gravity, emitters or platforms.
 * Rendering and player hit detection are deliberately outside this API. */
typedef struct {
    int32_t x, y, old_x, old_y, vx, vy;
    int32_t behavior, speed, state, onwall;
    int32_t x1, y1, x2, y2, cx, cy, w, h;
} V6Enemy;
enum { V6_ENEMY_BLOCK=V6_BLOCK, V6_ENEMY_SAFE=V6_SAFE, V6_ENEMY_DIRECTIONAL=V6_DIRECTIONAL };
typedef V6Block V6EnemyBlock;
int v6_enemy_init(V6Enemy *, int x, int y, int behavior, int speed,
                  int x1, int y1, int x2, int y2, int cx, int cy, int w, int h);
void v6_enemy_step(V6Enemy *, const V6Room *, const V6EnemyBlock *, unsigned count);
/* Movement/collision stage after a caller-supplied behaviour update. */
void v6_enemy_move(V6Enemy *,const V6Room *,const V6EnemyBlock *,unsigned count);
#endif
