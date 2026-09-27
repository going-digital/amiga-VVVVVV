/* A bounded static-room session. Checkpoint offsets and 30/10-tick death/life
 * timing follow Entity.cpp and Logic.cpp. This is not the campaign state machine. */
#include "slice.h"

static void respawn(V6Slice *s)
{
    int flips = s->player.flips;
    v6_player_init(&s->player, s->save_x, s->save_y, s->save_gravity);
    s->player.dir = s->save_dir;
    s->player.flips = flips;
    s->life_timer = 10;
    s->death_timer = -1;
    ++s->respawns;
}

void v6_slice_init(V6Slice *s, int x, int y, int tile)
{
    s->checkpoint_x = x; s->checkpoint_y = y; s->checkpoint_tile = tile;
    s->save_x = x - 4;
    s->save_y = y - (tile == 20 ? 2 : 7);
    s->save_gravity = tile == 20;
    s->save_dir = 1;
    v6_player_init(&s->player, s->save_x, s->save_y, s->save_gravity);
    s->checkpoint_active = s->checkpoint_pending = 0;
    s->death_timer = -1; s->life_timer = 0;
    s->deaths = s->respawns = s->exits = 0;
    s->frame = s->walking_frame = s->frame_delay = 0;
}

unsigned v6_slice_step(V6Slice *s, const V6Room *room, unsigned input, int restart)
{
    unsigned events = 0;
    if (restart && s->death_timer < 0) s->death_timer = 30;
    if (s->death_timer >= 0) {
        if (s->death_timer == 30) { ++s->deaths; events |= V6_EVENT_DEATH; }
        s->frame = 12 + (s->player.dir ? 0 : 1) + (s->player.gravity ? 2 : 0);
        if (--s->death_timer <= 0) { respawn(s); events |= V6_EVENT_RESPAWN; }
        return events;
    }
    if (s->checkpoint_pending) {
        s->checkpoint_pending = 0; s->checkpoint_active = 1;
        s->save_dir = s->player.dir;
        events |= V6_EVENT_SAVE;
    }
    if (s->life_timer > 5) input |= V6_NO_CONTROL;
    if (s->life_timer > 0) --s->life_timer;
    events |= v6_player_step(&s->player, room, input);
    if (!s->checkpoint_active && v6_player_overlaps(&s->player,
            s->checkpoint_x, s->checkpoint_y, 16, 16)) s->checkpoint_pending = 1;
    if (v6_player_hurt(&s->player, room)) s->death_timer = 30;
    /* Returning to the checkpoint at an unsupported exit is explicit slice
     * behavior, not a substitute for campaign room-transition rules. */
    if (s->player.x < -14 || s->player.x >= 308 || s->player.y < -2 || s->player.y >= 238) {
        ++s->exits; respawn(s); events |= V6_EVENT_EXIT | V6_EVENT_RESPAWN;
    }
    --s->frame_delay;
    s->frame = s->player.dir ? 0 : 3;
    if (s->player.ground > 0 || s->player.roof > 0) {
        if (s->player.vx) {
            if (s->frame_delay <= 1) { s->frame_delay = 4; s->walking_frame ^= 1; }
            s->frame += s->walking_frame + 1;
        }
        if (s->player.roof > 0) s->frame += 6;
        if (s->player.ground > 0 && s->player.roof > 0 && !s->player.gravity) s->frame -= 6;
    } else s->frame += 1 + (s->player.gravity ? 6 : 0);
    return events;
}
