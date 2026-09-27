/* Session lifecycle checks; movement equivalence is tested separately. */
#include <assert.h>
#include <stdio.h>
#include "slice.h"
int main(void)
{
    uint16_t tiles[1200] = {0};
    V6Room room = {tiles, 1, 1};
    V6Slice s;
    unsigned events;
    int i;
    v6_slice_init(&s, 80, 80, 21);
    assert(s.player.x == 76 && s.player.y == 73 && s.player.gravity == 0);
    v6_slice_step(&s, &room, 0, 0);
    assert(s.checkpoint_pending && !s.checkpoint_active);
    assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_SAVE);
    events = v6_slice_step(&s, &room, 0, 1);
    assert(events & V6_EVENT_DEATH);
    assert(s.deaths == 1 && s.death_timer == 29);
    for (i = 0; i < 28; ++i) {
        assert(!(v6_slice_step(&s, &room, V6_RIGHT, 0) & V6_EVENT_RESPAWN));
    }
    assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_RESPAWN);
    assert(s.player.x == 76 && s.player.y == 73 && s.life_timer == 10);
    for (i = 0; i < 5; ++i) {
        v6_slice_step(&s, &room, V6_RIGHT, 0);
        assert(s.player.x == 76);
    }
    v6_slice_step(&s, &room, V6_RIGHT, 0);
    assert(s.player.x > 76);
    v6_slice_init(&s, 224, 96, 20);
    assert(s.player.x == 220 && s.player.y == 94 && s.player.gravity == 1);
    s.player.x = 310;
    assert(v6_slice_step(&s, &room, 0, 0) & V6_EVENT_EXIT);
    assert(s.exits == 1 && s.respawns == 1 && s.deaths == 0);
    assert(s.player.x == 220 && s.player.y == 94);
    puts("PASS: checkpoint, death delay, respawn controls, ceiling spawn, slice exit");
    return 0;
}
