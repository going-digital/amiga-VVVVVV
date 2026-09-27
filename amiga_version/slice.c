/* A bounded static-room session. Checkpoint offsets and 30/10-tick death/life
 * timing follow Entity.cpp and Logic.cpp. This is not the campaign state machine. */
#include "slice.h"

static void enter_room(V6Slice *s, int index)
{
    const V6RoomSetup *r = &s->rooms[index];
    s->room_index = index;
    s->checkpoint_x = r->checkpoint_x; s->checkpoint_y = r->checkpoint_y;
    s->checkpoint_tile = r->checkpoint_tile;
    s->checkpoint_pending = 0;
    s->checkpoint_active = index == s->save_room;
}

static void respawn(V6Slice *s)
{
    int flips = s->player.flips;
    if (s->rooms && s->room_index != s->save_room) {
        enter_room(s, s->save_room);
        v6_player_init(&s->player, s->save_x, s->save_y, s->save_gravity);
    } else {
        /* Map::resetplayer retains contact counters, input latches and old
         * positions when the existing player stays in the same room. */
        s->player.x = s->save_x; s->player.y = s->save_y;
        s->player.vx = s->player.vy = s->player.ay = 0;
        s->player.gravity = s->save_gravity;
    }
    s->player.dir = s->save_dir;
    s->player.flips = flips;
    s->life_timer = 10;
    s->death_timer = -1;
    ++s->respawns;
}

void v6_slice_init(V6Slice *s, int x, int y, int tile)
{
    s->rooms = 0; s->room_count = 0; s->room_index = s->save_room = 0; s->transitions = 0;
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

void v6_slice_init_world(V6Slice *s, const V6RoomSetup *rooms, int count, int initial)
{
    const V6RoomSetup *r = &rooms[initial];
    v6_slice_init(s, r->checkpoint_x, r->checkpoint_y, r->checkpoint_tile);
    s->rooms = rooms; s->room_count = count;
    s->room_index = s->save_room = initial;
}

/* Logic.cpp: normal vertical transition first, then horizontal. Map.cpp:
 * main-world coordinates wrap in [100,119]. Unsupported slice rooms explicitly
 * return to the checkpoint; they are never silently treated as empty rooms. */
unsigned v6_slice_transition(V6Slice *s)
{
    unsigned events = 0;
    int axis;
    for (axis = 0; axis < 2; ++axis) {
        int dx = 0, dy = 0, x, y, index;
        if (!axis) {
            if (s->player.y >= 238) dy = 1;
            else if (s->player.y < -2) dy = -1;
        } else {
            if (s->player.x < -14) dx = -1;
            else if (s->player.x >= 308) dx = 1;
        }
        if (!dx && !dy) continue;
        if (!s->rooms) goto unsupported;
        x = s->rooms[s->room_index].x + dx;
        y = s->rooms[s->room_index].y + dy;
        if (x < 100) x = 119;
        if (x > 119) x = 100;
        if (y < 100) y = 119;
        if (y > 119) y = 100;
        for (index = 0; index < s->room_count; ++index)
            if (s->rooms[index].x == x && s->rooms[index].y == y) break;
        if (index == s->room_count) goto unsupported;
        s->player.x -= dx * 320; s->player.y -= dy * 240;
        enter_room(s, index); ++s->transitions;
        s->player.old_x = s->player.x; s->player.old_y = s->player.y;
        events |= V6_EVENT_ROOM;
        continue;
unsupported:
        index = s->room_index;
        ++s->exits; respawn(s);
        return events | V6_EVENT_EXIT | V6_EVENT_RESPAWN |
            (index != s->room_index ? V6_EVENT_ROOM : 0);
    }
    return events;
}

static inline __attribute__((always_inline)) unsigned step(V6Slice *s, const V6Room *room, unsigned input, int restart, V6ContactHook hook, V6SliceMovement movement, void *context,int external_checkpoints)
{
    unsigned events = 0;
    int previous_room = s->room_index;
    if (restart && s->death_timer < 0) s->death_timer = 30;
    if (s->death_timer >= 0) {
        V6PlayerMotion locked_motion = {0, s->player.y};
        v6_player_input(&s->player, input | V6_NO_CONTROL, &locked_motion);
        if (s->death_timer == 30) { ++s->deaths; events |= V6_EVENT_DEATH; }
        s->frame = 12 + (s->player.dir ? 0 : 1) + (s->player.gravity ? 2 : 0);
        if (--s->death_timer <= 0) { respawn(s); events |= V6_EVENT_RESPAWN;
            if (previous_room != s->room_index) events |= V6_EVENT_ROOM; }
        return events;
    }
    if (!external_checkpoints && s->checkpoint_pending) {
        s->checkpoint_pending = 0; s->checkpoint_active = 1;
        s->save_dir = s->player.dir;
        s->save_room = s->room_index;
        s->save_x = s->checkpoint_x - 4;
        s->save_y = s->checkpoint_y - (s->checkpoint_tile == 20 ? 2 : 7);
        s->save_gravity = s->checkpoint_tile == 20;
        events |= V6_EVENT_SAVE;
    }
    if (s->life_timer > 5) input |= V6_NO_CONTROL;
    if (s->life_timer > 0) --s->life_timer;
    events |= movement ? movement(&s->player,room,input,s->life_timer,context) :
        v6_player_step_hook(&s->player, room, input, hook, context);
    if (!external_checkpoints && !s->checkpoint_active && v6_player_overlaps(&s->player,
            s->checkpoint_x, s->checkpoint_y, 16, 16)) s->checkpoint_pending = 1;
    if (v6_player_hurt(&s->player, room)) s->death_timer = 30;
    events |= v6_slice_transition(s);
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

unsigned v6_slice_step_hook(V6Slice *s,const V6Room *room,unsigned input,int restart,V6ContactHook hook,void *context)
{ return step(s,room,input,restart,hook,0,context,0); }

unsigned v6_slice_step_movement(V6Slice *s,const V6Room *room,unsigned input,int restart,V6SliceMovement movement,void *context)
{ return step(s,room,input,restart,0,movement,context,0); }

unsigned v6_slice_step(V6Slice *s, const V6Room *room, unsigned input, int restart)
{ return v6_slice_step_hook(s,room,input,restart,0,0); }

void v6_slice_apply_save(V6Slice *s,const V6CheckpointSave *save)
{
    /* The activation belongs to the current room, not a remote save load. */
    s->save_room=s->room_index;
    s->save_x=save->x;s->save_y=save->y;
    s->save_gravity=save->gravity;s->save_dir=save->dir;
    s->checkpoint_x=save->x+4;
    s->checkpoint_y=save->y+(save->gravity?2:7);
    s->checkpoint_tile=save->gravity?20:21;
    s->checkpoint_active=1;s->checkpoint_pending=0;
}
unsigned v6_slice_step_entities(V6Slice *s,const V6Room *room,unsigned input,
                                int restart,V6SliceMovement movement,void *context)
{ return step(s,room,input,restart,0,movement,context,1); }
