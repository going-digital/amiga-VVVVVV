/* Standalone PAL tower display experiment; left mouse exits. */
#include <proto/exec.h>
#if defined(V6_TOWER_PERSIST) || defined(V6_TOWER_UI_SAVE) || defined(V6_BUILDING_SAVE)
#include <proto/dos.h>
#include "campaign_dos.h"
#include "campaign_route.h"
struct DosLibrary *DOSBase;
#ifdef V6_BUILDING_SAVE
static V6CheckpointSave building_saved;
static unsigned building_stage;
static volatile struct {ULONG magic,version,values[12];} building_save_diag={0x56364253,1,{0}};
static int checkpoint_bank_valid(const V6CheckpointSave *);
#endif
#ifdef V6_TOWER_PERSIST
static V6CheckpointSave persisted_checkpoint;
static V6HallwayStory persisted_story;
static unsigned persist_stage;
static volatile struct { ULONG magic,version,values[18]; } persist_diag={0x56365356,1,{0}};
#endif
#if defined(V6_TOWER_BUILDING) && defined(V6_TOWER_UI_SAVE)
#define V6_TOWER_TELE_MENU
#include "teleporter_menu.h"
static V6TeleporterMenu tele_menu;
static unsigned tele_menu_fire;
static const V6TeleporterDestination tele_destinations[1]={{111,104}};
static volatile struct {ULONG magic,version,values[10];} tele_menu_diag={0x5636544d,1,{0}};
#endif
#ifdef V6_TOWER_UI_SAVE
static const char save_name[]="DF1:campaign.v6cs";
static const char save_temp[]="DF1:campaign.tmp";
static const char save_backup[]="DF1:campaign.bak";
#include "save_controls.h"
#ifndef V6_TOWER_RESCUE
#include "dialogue.h"
#include "dialogue_font.h"
#endif
#include "rescue_script.h"
static V6SaveControls save_controls;
static unsigned ui_status,ui_fields;
static UBYTE *ui_captions;
static volatile struct { ULONG magic,version,values[18]; } ui_diag={0x56365549,1,{0}};
#ifdef V6_TOWER_TELE_MENU
#define UI_MESSAGE_COUNT 6
#else
#define UI_MESSAGE_COUNT 5
#endif
static const V6RescueSpeech ui_messages[UI_MESSAGE_COUNT]={
#ifdef V6_TOWER_TELE_MENU
    {0,1,3,{"Down + fire: teleporter menu","Right: save; fire + right: load","Left mouse: exit"}},
#else
    {0,1,3,{"Right mouse: save","Hold fire + right mouse: load","Left mouse: exit"}},
#endif
    {1,1,2,{"Checkpoint saved","Continue playing"}},
    {2,1,2,{"Checkpoint loaded","Continue playing"}},
    {3,1,3,{"Save/load failed","Current game retained","Check the save disk"}},
#ifdef V6_TOWER_TELE_MENU
    {4,1,2,{"Finish loading or close the menu","Then try save/load again"}}
#else
    {4,1,2,{"Finish dialogue or loading first","Then try save/load again"}}
#endif
#ifdef V6_TOWER_TELE_MENU
    ,{5,1,3,{"Building Apport","Left/right: select; fire: confirm","Down + fire: cancel"}}
#endif
};
static volatile struct { ULONG magic,version,count,capacity,records[8][10]; } ui_trace={0x56364954,1,0,8,{{0}}};
#ifdef V6_TOWER_UI_REPLAY
static unsigned ui_test_phase,ui_test_tick;
#endif
static int checkpoint_bank_valid(const V6CheckpointSave *);
#else
#ifdef V6_BUILDING_SAVE
static const char save_name[]="DF1:campaign.v6cs";
static const char save_temp[]="DF1:campaign.tmp";
static const char save_backup[]="DF1:campaign.bak";
#else
static const char save_name[]="DF0:campaign.v6cs";
static const char save_temp[]="DF0:campaign.tmp";
static const char save_backup[]="DF0:campaign.bak";
#endif
#endif
#endif
#include <proto/graphics.h>
#include <graphics/gfxbase.h>
#include <exec/execbase.h>
#include <hardware/custom.h>
#include <hardware/dmabits.h>
#include <hardware/intbits.h>
#include "tower_draw.h"
#include "tower_copper.h"
#include "tower_camera.h"
#include "tower_session.h"
#ifdef V6_TOWER_ROUTE
#include "tower_route.h"
#endif
#ifdef V6_TOWER_WORLD
#define V6_TOWER_PAIRS
#endif
#ifdef V6_TOWER_PAIRS
#include "tower_pairs.h"
#include "tower_background_pairs.h"
#endif
#ifdef V6_TOWER_PLAY
#include "sprites.h"
#include "animation.h"
#include "tower_player_assets.h"
#ifdef V6_TOWER_WORLD
#include "tower_checkpoints.h"
#if defined(V6_TOWER_COMPANION_ROUTE)
#include "../tools/amiga/tower_upper_replay.h"
#elif defined(V6_TOWER_TRIGGER_REPLAY)
#include "../tools/amiga/tower_trigger_replay.h"
#elif defined(V6_TOWER_UPPER_REPLAY)
#include "../tools/amiga/tower_upper_replay.h"
#elif defined(V6_TOWER_ROUTE_REPLAY)
#include "../tools/amiga/tower_route_replay.h"
#elif defined(V6_TOWER_WRAP_REPLAY)
#include "../tools/amiga/tower_wrap_replay.h"
#else
#include "../tools/amiga/tower_world_replay.h"
#endif
static V6TowerGameplay world;
#ifdef V6_TOWER_ROUTE
#include "tower_route_data.h"
#include "hallway_crew.h"
#if !defined(V6_TOWER_HALLWAY_HOLD) || defined(V6_TOWER_CREW_HOLD)
#ifdef V6_TOWER_TRIGGER_REPLAY
static V6HallwayStory hallway_story={0,0,0,0,0};
#include "hallway_trigger.h"
static V6HallwayTrigger hallway_trigger;
static int trigger_crew_visible;
#ifdef V6_TOWER_RESCUE
#include "rescue_programs.h"
#include "dialogue.h"
#include "dialogue_font.h"
#include "companion.h"
#ifdef V6_TOWER_AUDIO
#include "audio.h"
#include "cue_samples.h"
static V6Audio cue_audio;
static unsigned cue_consumed;
static UBYTE *cue_chip;
static volatile struct { ULONG magic,version,values[7]; } cue_diag={0x56364155,1,{0}};
static void audio_apply(const V6AudioPlan *p)
{
    unsigned i;
    for(i=0;i<p->count;++i) *(volatile UWORD *)(0xdff000UL+p->writes[i].reg)=(UWORD)p->writes[i].value;
}
static void audio_record(void)
{
    cue_diag.values[0]=cue_audio.state;cue_diag.values[1]=cue_audio.starts;
    cue_diag.values[2]=cue_audio.completed;cue_diag.values[3]=cue_audio.replaced;
    cue_diag.values[4]=cue_audio.error;cue_diag.values[5]=cue_audio.interrupts;
    cue_diag.values[6]=cue_consumed;
}
#endif
static V6Companion companion;
static V6Terrain hallway_terrain[2];
static V6RescueScript rescue_vm={.control=1,.mood=1};
static int rescue_bars,rescue_fade,rescue_fade_mode,rescue_fire;
static UBYTE *rescue_captions;
static unsigned rescue_flips_applied;
static volatile struct { ULONG magic,version,count,capacity,records[128][18]; }
    rescue_trace={0x56365256,1,0,128,{{0}}};
static volatile struct { ULONG magic,version,values[18]; }
    rescue_diag={0x56365241,1,{0}};
static volatile struct { ULONG magic,version,count,capacity,records[128][14]; }
    companion_trace={0x56364354,1,0,128,{{0}}};
static volatile struct { ULONG magic,version,values[14]; }
    companion_diag={0x56364346,1,{0}};
static void companion_record(void)
{
    unsigned i;
    ULONG values[14]={companion.visible,companion.following,companion.mood,companion.frame,
        companion.body.x,companion.body.y,companion.body.vx,companion.body.vy,companion.body.dir,
        companion.animation.delay,companion.animation.walk,companion.spawns,companion.steps,companion.follow_steps};
    for(i=0;i<14;++i) companion_diag.values[i]=values[i];
    if(companion_trace.count<128) {
        volatile ULONG *record=companion_trace.records[companion_trace.count];
        for(i=0;i<14;++i) record[i]=values[i];
        ++companion_trace.count;
    }
}
static void rescue_record(void)
{
    unsigned i;
    ULONG values[18]={rescue_vm.pc,rescue_vm.active,rescue_vm.error,rescue_vm.delay,
        rescue_vm.waiting,rescue_vm.bars,rescue_vm.control,rescue_vm.mood,rescue_vm.following,
        rescue_vm.ui_serial,rescue_vm.cues,rescue_vm.flips,(ULONG)rescue_vm.fade,
        rescue_vm.speech?rescue_vm.speech->index+1:0,hallway_story.red_rescued,
        hallway_story.companion,rescue_bars,rescue_fade};
    for(i=0;i<18;++i) rescue_diag.values[i]=values[i];
    if(rescue_trace.count<128) {
        volatile ULONG *record=rescue_trace.records[rescue_trace.count];
        for(i=0;i<18;++i) record[i]=values[i];
        ++rescue_trace.count;
    }
}
static void rescue_animate(void)
{
    if(rescue_vm.bars) { rescue_bars+=25;if(rescue_bars>361) rescue_bars=361; }
    else { rescue_bars-=25;if(rescue_bars<0) rescue_bars=0; }
    if(rescue_vm.fade!=rescue_fade_mode) {
        rescue_fade_mode=rescue_vm.fade;rescue_fade=rescue_fade_mode<0?416:0;
    } else if(rescue_fade_mode>0) {
        rescue_fade+=24;if(rescue_fade>432) rescue_fade=432;
    } else if(rescue_fade_mode<0) {
        rescue_fade-=24;if(rescue_fade<0) rescue_fade=0;
    }
}
static UWORD rescue_colour(unsigned c)
{
    static const UBYTE factors[52]={
16,15,15,15,14,14,14,13,13,13,12,12,12,12,11,11,11,10,10,10,9,9,9,8,8,8,8,7,7,7,6,6,6,5,5,5,4,4,4,4,3,3,3,2,2,2,1,1,1,0,0,0};
    unsigned factor;
    if(!rescue_fade) return (UWORD)c;
    if(rescue_fade>=416) return 0;
    factor=factors[(unsigned)rescue_fade>>3];
    return (UWORD)(((((c>>8)&15)*factor)>>4)<<8 |
                  ((((c>>4)&15)*factor)>>4)<<4 | (((c&15)*factor)>>4));
}
#define DISPLAY_COLOUR(c) rescue_colour(c)
#else
#define DISPLAY_COLOUR(c) (c)
#endif
static volatile struct { ULONG magic,version,count,capacity,records[128][7]; }
    trigger_trace={0x56364854,1,0,128,{{0}}};
static volatile struct { ULONG magic,version,values[7]; }
    trigger_diag={0x56364851,1,{0}};
static void record_trigger(void)
{
    unsigned i;
    trigger_diag.values[0]=hallway_story.rescue_triggered;
    trigger_diag.values[1]=hallway_story.red_rescued;
    trigger_diag.values[2]=hallway_story.companion;
    trigger_diag.values[3]=hallway_trigger.active;
    trigger_diag.values[4]=hallway_trigger.pending;
    trigger_diag.values[5]=hallway_trigger.requests;
    trigger_diag.values[6]=trigger_crew_visible;
    if(trigger_trace.count<128) {
        for(i=0;i<7;++i) trigger_trace.records[trigger_trace.count][i]=trigger_diag.values[i];
        ++trigger_trace.count;
    }
}
#else
static const V6HallwayStory hallway_story={0,0,0,0,0};
#endif
#endif
static V6TowerRoute route;
static unsigned route_loading,route_budget;
static volatile struct { ULONG magic,version,index,transitions,returns,loading_frames,error; }
    route_diag={0x56365254,1,0,0,0,0,0};
#endif
#endif
static V6Sprites player_sprites[2];
static V6CollisionAnimation player_animation;
static V6Room player_room;
static V6TowerTiles player_tiles;
static int player_frame;
#endif
#ifndef DISPLAY_COLOUR
#define DISPLAY_COLOUR(c) (c)
#endif
#include "tower_assets.h"
#include "tower_map.h"
#include "tower_background_map.h"
#include "tower_backdrop.h"
#ifdef V6_TOWER_BUILDING
#include "terrain.h"
#include "teleporter_animation.h"
#include "teleporter_draw.h"
#include "teleporter_assets.h"
#ifdef V6_TOWER_RESCUE
#error Building route renderer currently reserves six channels plus player; crew sharing is pending
#endif
static UWORD *building_dma;
static UWORD building_prepared[10][6*V6_TELEPORTER_DMA_WORDS];
static int building_frames[2]={-1,-1};
static V6TeleporterAnimation building_animation;
static V6Terrain building_terrain;
#ifdef V6_TOWER_ENERGIZE
#include "energize_assets.h"
static V6Terrain energize_terrain;
static UWORD energize_prepared[10][6*V6_TELEPORTER_DMA_WORDS];
#define FG_OFFSETS (route.index==5?energize_pair_offsets:tower_pair_offsets)
#define FG_PAIRS (route.index==5?energize_pairs:tower_pairs)
#define FG_WORDS (route.index==5?ENERGIZE_PAIR_WORDS:TOWER_PAIR_WORDS)
#define FG_COUNT (route.index==5?ENERGIZE_TILE_COUNT:TOWER_TILE_COUNT)
#define FG_PALETTE (route.index==5?energize_palette:tower_palette)
#else
#define FG_OFFSETS tower_pair_offsets
#define FG_PAIRS tower_pairs
#define FG_WORDS TOWER_PAIR_WORDS
#define FG_COUNT TOWER_TILE_COUNT
#define FG_PALETTE tower_palette
#endif
#ifdef V6_TOWER_ARRIVAL
#ifndef V6_ENERGIZE_CAPTURE
#error Arrival fixture requires Energize capture
#endif
#include "teleporter_arrival.h"
static V6TeleporterArrival arrival;
static int arrival_flash;
static volatile struct {ULONG magic,version,count,records[128][14];}
    arrival_trace={0x56364152,1,0,{{0}}};
#ifdef V6_TOWER_ROUNDTRIP
#include "teleporter_departure.h"
static V6TeleporterDeparture departure;
static unsigned travel_leg;
static volatile struct {ULONG magic,version,count,records[128][8];}
    departure_trace={0x56364452,1,0,{{0}}};
#endif
static int arrival_phase(V6TowerRoute *r,void *context)
{
    V6TowerSession *s=r->session;
    return v6_teleporter_arrival_tick((V6TeleporterArrival *)context,&s->player,
        &s->motion,&s->invisible,r->rooms[r->index].teleporter,&r->tele_region);
}
#endif
#ifdef V6_TOWER_ROUNDTRIP
static int travel_phase(V6TowerRoute *r,void *context)
{
    (void)context;
    if(departure.state || departure.travel)
        return v6_teleporter_departure_tick(&departure,&r->session->invisible,
            r->rooms[r->index].teleporter);
    return arrival_phase(r,&arrival);
}
#endif
static ULONG building_random=1;
#define BUILDING_DMA_BYTES (2*6*V6_TELEPORTER_DMA_WORDS*2)
static volatile struct {ULONG magic,version,count,records[128][12];}
    building_trace={0x56364252,1,0,{{0}}};
#else
#define BUILDING_DMA_BYTES 0
#define FG_OFFSETS tower_pair_offsets
#define FG_PAIRS tower_pairs
#define FG_WORDS TOWER_PAIR_WORDS
#define FG_COUNT TOWER_TILE_COUNT
#define FG_PALETTE tower_palette
#endif
#ifdef V6_TELEPORTER_LIVE
#if !defined(V6_TOWER_TELEPORTER_HOLD) || !defined(V6_TOWER_CONTROLLER)
#error Live teleporter fixture requires a teleporter hold and the gameplay clock
#endif
#include "teleporter.h"
#include "teleporter_animation.h"
#include "teleporter_draw.h"
#include "sprites.h"
#include "animation.h"
#include "tower_player_assets.h"
static V6Teleporter tele;
static V6TeleporterRegion tele_region;
static V6TeleporterAnimation tele_animation;
static V6Player tele_player;
static V6Room tele_room;
static V6CheckpointSave tele_save;
static V6CollisionAnimation tele_player_animation;
static UWORD tele_prepared[10][6*V6_TELEPORTER_DMA_WORDS];
static int tele_bank_frame[2]={-1,-1};
static V6Sprites tele_player_sprites[2];
static ULONG tele_random=1;
static unsigned tele_saves,tele_messages,tele_player_frame;
static volatile struct {ULONG magic,version,count,records[256][12];}
    tele_trace={0x5636544c,1,0,{{0}}};
#define TELE_BANK_BYTES (6*V6_TELEPORTER_DMA_WORDS*2+8*V6_SPRITE_WORDS*2)
#endif
#ifdef V6_TOWER_TELEPORTER_HOLD
#include "teleporter_draw.h"
#include "teleporter_assets.h"
#include "building_display.h"
#ifdef V6_TOWER_PLAY
#error Teleporter hold is a static visual fixture, not a gameplay route
#endif
#ifndef V6_TELEPORTER_TINT
#define V6_TELEPORTER_TINT 0x444
#endif
#ifdef V6_TELEPORTER_LIVE
#define TELE_DMA_BYTES (2*TELE_BANK_BYTES)
#else
#define TELE_DMA_BYTES (V6_TELEPORTER_CHANNELS*V6_TELEPORTER_DMA_WORDS*2+4)
#endif
static UWORD *tele_dma;
#else
#define TELE_DMA_BYTES 0
#endif
struct ExecBase *SysBase;
struct GfxBase *GfxBase;
static volatile struct Custom * const hw=(void *)0xdff000;
/* Test-only fixed camera; negative selects the moving seam route. */
#ifndef V6_TOWER_HOLD
#define V6_TOWER_HOLD -1
#endif
/* Synthetic stress step, not the desktop camera controller. */
#ifndef V6_TOWER_STEP
#define V6_TOWER_STEP 1
#endif
#if V6_TOWER_STEP != 1 && V6_TOWER_STEP != 4 && V6_TOWER_STEP != 8 && V6_TOWER_STEP != 12 && V6_TOWER_STEP != 16
#error Unsupported tower stress step
#endif
#ifdef V6_TOWER_FULL_ROUTE
#define CAMERA_MIN 0
#else
#define CAMERA_MIN 5344
#endif
#define CAMERA_MAX 5856
#ifdef V6_TOWER_PLAY
#if defined(V6_TOWER_RESCUE) || defined(V6_TOWER_BUILDING)
#define LIST_WORDS 192
#else
#define LIST_WORDS 128
#endif
#define PLAYER_DMA_BYTES (2*V6_SPRITE_CHANNELS*V6_SPRITE_WORDS*2)
#else
#ifdef V6_TOWER_TELEPORTER_HOLD
#define LIST_WORDS 192
#else
#define LIST_WORDS 64
#endif
#define PLAYER_DMA_BYTES 0
#endif
#define LAYER_BYTES (V6_TOWER_RING_BYTES+V6_TOWER_PLANE_BYTES)
#ifdef V6_TOWER_RESCUE
#define CAPTION_DMA_BYTES (V6_RESCUE_SPEECHES*V6_DIALOGUE_BYTES)
#else
#define CAPTION_DMA_BYTES 0
#endif
#ifdef V6_TOWER_AUDIO
#define AUDIO_DMA_BYTES CUE_DMA_BYTES
#else
#define AUDIO_DMA_BYTES 0
#endif
#ifdef V6_TOWER_UI_SAVE
#define UI_DMA_BYTES (UI_MESSAGE_COUNT*V6_DIALOGUE_BYTES)
#else
#define UI_DMA_BYTES 0
#endif
#define CHIP_BYTES (BUILDING_DMA_BYTES+TELE_DMA_BYTES+UI_DMA_BYTES+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES+AUDIO_DMA_BYTES)
static V6TowerStream stream,background_stream;
static V6TowerDraw draw[2],background_draw[2];
static UBYTE *rings[2];
static unsigned prepared_camera[2];
#ifdef V6_TOWER_ROUTE
static int route_source(void)
{
    const UBYTE *data=tower_map;unsigned bytes=sizeof(tower_map),i;
    if(route.index==2) { data=hallway0_display;bytes=sizeof(hallway0_display); }
    if(route.index==3) { data=hallway1_display;bytes=sizeof(hallway1_display); }
#ifdef V6_TOWER_BUILDING
    if(route.index==4) {
        data=building_display;bytes=sizeof(building_display);
        building_animation.frame=1;building_animation.delay=building_animation.walking=0;
        building_frames[0]=building_frames[1]=-1;
        route.room.terrain=&building_terrain;
    }
#endif
#ifdef V6_TOWER_ENERGIZE
    if(route.index==5) {
        data=energize_display;bytes=sizeof(energize_display);
        building_animation.frame=1;building_animation.delay=building_animation.walking=0;
        building_frames[0]=building_frames[1]=-1;route.room.terrain=&energize_terrain;
    }
#endif
    /* All three resident maps were opened and fully pair-validated before
     * takeover. Rebind only these identical immutable bytes; a repeated
     * 700-entry directory scan would consume the transition frame. */
    stream.data=data;stream.size=bytes;stream.height=route.index<2?700:30;stream.valid=0;
    for(i=0;i<2;++i) {
        v6_tower_draw_reset(&draw[i]);v6_tower_draw_reset(&background_draw[i]);
        prepared_camera[i]=(unsigned)route.session->camera.y;
    }
#ifdef V6_TOWER_TRIGGER_REPLAY
    v6_hallway_trigger_enter(&hallway_trigger,route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
    trigger_crew_visible=v6_hallway_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
#endif
#ifdef V6_TOWER_RESCUE
    if(hallway_story.companion==9)
        v6_companion_enter(&companion,9,route.index<2,route.rooms[route.index].x,&route.session->player);
    else v6_companion_idle(&companion,trigger_crew_visible);
    if(route.index>=2) route.room.terrain=&hallway_terrain[route.index-2];
#endif
    route_loading=2;route_budget=1;return 1;
}
static volatile struct { ULONG magic,version,count,records[128][3]; }
    route_trace={0x56365252,1,0,{{0}}};
#endif
static volatile ULONG frames;
/* Big-endian ULONG record, discoverable in emulator RAM dumps. */
static volatile struct {
    ULONG magic,version,status,frames,camera,max_work_lines,missed,error,chip_bytes;
    ULONG forward_wraps,reverse_wraps,max_rows,max_copied;
    ULONG step,route_min,route_max,visited_min,visited_max;
    ULONG logic_ticks,logic_frames,logic_remainder;
    ULONG camera_mode,recovery_calls,recovery_life,recovery_delay,recovery_seek_frames;
} diag={0x56365450,6,0,0,0,0,0,0,CHIP_BYTES,0,0,0,0,
    V6_TOWER_STEP,CAMERA_MIN,CAMERA_MAX,CAMERA_MAX,0,0,0,0,0,0,0,0,0};
#ifdef V6_TOWER_PLAY
static volatile struct {
    ULONG magic,version,max_logic,max_render,peak_logic,peak_render,peak_tick,peak_rows;
} profile={0x56365046,1,0,0,0,0,0,0};
#endif
#ifdef V6_TOWER_WORLD
static volatile struct { ULONG magic,version,values[13]; }
    world_diag={0x56365747,1,{0}};
static volatile struct {
    ULONG magic,version,count,capacity;
    ULONG records[128][12];
} world_trace={0x56365754,1,0,128,{{0}}};
static void record_world(void)
{
    unsigned i;
    world_diag.values[0]=world.save.id;world_diag.values[1]=world.save.x;
    world_diag.values[2]=world.save.y;world_diag.values[3]=world.save.gravity;
    world_diag.values[4]=world.save.dir;world_diag.values[5]=world.activations;
    world_diag.values[6]=world.active_mask;world_diag.values[7]=world.pending_mask;
    world_diag.values[8]=world.wrap_left;world_diag.values[9]=world.wrap_right;
    world_diag.values[10]=world.exit.room_x;world_diag.values[11]=world.exit.room_y;
#ifdef V6_TOWER_ROUTE
    route_diag.index=route.index;route_diag.transitions=route.transitions;
    route_diag.returns=route.returns;route_diag.error=route.error;
    if(route_trace.count<128) {
        route_trace.records[route_trace.count][0]=route.index;
        route_trace.records[route_trace.count][1]=route.transitions;
        route_trace.records[route_trace.count][2]=route.returns;
        ++route_trace.count;
    }
#endif
    if(world_trace.count<128) {
        for(i=0;i<12;++i) world_trace.records[world_trace.count][i]=world_diag.values[i];
        ++world_trace.count;
    }
}
#endif
#ifdef V6_TOWER_RECOVERY
/* Test-only bounded trace: all camera fields plus callback state. Stored
 * outside the Chip allocation; count is published after a complete record. */
#define CAMERA_TRACE_TICKS 128
static volatile struct {
    ULONG magic,version,count,capacity;
    int16_t records[CAMERA_TRACE_TICKS][13];
    int32_t players[CAMERA_TRACE_TICKS][12];
} camera_trace={0x56364354,2,0,CAMERA_TRACE_TICKS,{{0}},{{0}}};
static void trace_camera(const V6TowerCamera *c,int life,int delay)
{
    volatile int16_t *r;
    if(camera_trace.count>=CAMERA_TRACE_TICKS) return;
    r=camera_trace.records[camera_trace.count];
    r[0]=c->y;r[1]=c->old_y;r[2]=c->mode;r[3]=c->seek;
    r[4]=c->seek_frames;r[5]=c->spike_top;r[6]=c->spike_bottom;
    r[7]=c->old_spike_top;r[8]=c->old_spike_bottom;r[9]=c->colour_superstate;
    r[10]=life;r[11]=delay;r[12]=(int16_t)diag.recovery_calls;
    ++camera_trace.count;
}
static V6TowerSession session;
#endif
static UWORD beam(void) { return (*(volatile ULONG *)0xdff004>>8)&511; }
static ULONG clock_lines(void) {
    ULONG a,b; UWORD y,pending;
    /* The beam may wrap before the VBlank handler increments frames.
     * Retry that pending-IRQ window instead of returning a clock in the
     * previous field (which would underflow unsigned phase timings). */
    do {
        a=frames;y=beam();pending=y<4?(hw->intreqr&INTF_VERTB):0;b=frames;
    } while(a!=b || pending);
    return a*312+y;
}
static void blank(void) {
    while(beam()==311) {} while(beam()!=311) {}
}
static void __attribute__((interrupt)) irq(void) {
    ++frames;hw->intreq=INTF_VERTB;hw->intreq=INTF_VERTB;
}
static UWORD *move(UWORD *p,UWORD reg,UWORD value) {
#ifdef V6_TOWER_ARRIVAL
    /* Graphics::flashlight fills the complete viewport with RGB 0xBB. */
    if(arrival_flash && reg>=0x180 && reg<=0x1be)value=0xbbb;
#endif
    *p++=reg;*p++=value;return p;
}
/* Copy matching cached rows from the read-only front ring. Each blit is
 * complete before its cache tag is published or CPU rendering begins. */
static void wait_blit(void)
{
    (void)hw->dmaconr;
    while(hw->dmaconr&DMAF_BLTDONE) {}
}
static unsigned reuse_rows(V6TowerDraw *dst_cache,const V6TowerDraw *src_cache,
    UBYTE *dst,const UBYTE *src,int top,unsigned planes)
{
    int row,first,end;unsigned copied=0;ULONG bit;
    v6_tower_draw_span(dst_cache,top,&first,&end);
    for(row=first,bit=1UL<<((unsigned)first&31);row<end;
        ++row,bit=(bit<<1)|(bit>>31)) {
        unsigned slot=(unsigned)row&31,plane;
        if((dst_cache->valid&bit) && dst_cache->tags[slot]==row) continue;
        if(!(src_cache->valid&bit) || src_cache->tags[slot]!=row) continue;
        for(plane=0;plane<planes;++plane) {
            unsigned offset=slot*320+plane*V6_TOWER_PLANE_BYTES;
            wait_blit();
            hw->bltcon0=0x09f0;hw->bltcon1=0;
            hw->bltafwm=hw->bltalwm=0xffff;
            hw->bltamod=hw->bltdmod=0;
            hw->bltapt=(APTR)(src+offset);hw->bltdpt=dst+offset;
            hw->bltsize=(8<<6)|20;
        }
        wait_blit();
        dst_cache->tags[slot]=(int16_t)row;dst_cache->valid|=bit;++copied;
    }
    return copied;
}
static unsigned background_camera(unsigned camera)
{
#ifdef V6_TOWER_TELEPORTER_HOLD
    (void)camera;return 200;
#endif
#ifdef V6_TOWER_ROUTE
    /* Desktop background modes 7/8 both use backat(...,200). */
    if(route.rooms[route.index].packed) return 200;
#endif
    return camera>>1;
}
static int prepare(UBYTE *ring,UWORD *list,unsigned index,unsigned camera,unsigned *drawn) {
    UWORD *p=list;unsigned i,background_rows,copied,bg_camera=background_camera(camera);
    copied=0;
    /* Small advances cost less to redraw than to scan and copy from peer. */
    if(camera>prepared_camera[index]+8 || prepared_camera[index]>camera+8) {
        copied=reuse_rows(&draw[index],&draw[index^1],ring,rings[index^1],camera>>3,2);
        copied+=reuse_rows(&background_draw[index],&background_draw[index^1],
            ring+V6_TOWER_RING_BYTES,rings[index^1]+V6_TOWER_RING_BYTES,bg_camera>>3,1);
    }
    prepared_camera[index]=camera;
    if(drawn && copied>diag.max_copied) diag.max_copied=copied;
#ifdef V6_TOWER_PAIRS
    if(!v6_tower_draw_pair_prepare_verified(&draw[index],ring,&stream,camera>>3,
        FG_OFFSETS,FG_PAIRS,FG_WORDS,FG_COUNT,2,drawn)) return 0;
    if(!v6_tower_draw_pair_prepare_verified(&background_draw[index],ring+V6_TOWER_RING_BYTES,
        &background_stream,bg_camera>>3,tower_background_pair_offsets,tower_background_pairs,
        TOWER_BACKGROUND_PAIR_WORDS,TOWER_TILE_COUNT,1,&background_rows)) return 0;
#else
    if(!v6_tower_draw_prepare(&draw[index],ring,&stream,camera>>3,
        tower_tiles,TOWER_TILE_COUNT,0,drawn)) return 0;
    if(!v6_tower_draw_mono_prepare(&background_draw[index],ring+V6_TOWER_RING_BYTES,
        &background_stream,bg_camera>>3,tower_backdrop,TOWER_TILE_COUNT,&background_rows)) return 0;
#endif
    if(drawn) *drawn+=background_rows;
    p=move(p,0x100,0x3600);p=move(p,0x102,0);p=move(p,0x104,0x24);
    p=move(p,0x108,0);p=move(p,0x10a,0);
    p=move(p,0x08e,0x3481);p=move(p,0x090,0x24c1);
    p=move(p,0x092,0x0038);p=move(p,0x094,0x00d0);
    for(i=0;i<4;++i) p=move(p,0x180+i*2,DISPLAY_COLOUR(FG_PALETTE[i]));
    p=move(p,0x192,DISPLAY_COLOUR(0x223));
#ifdef V6_TOWER_ROUTE
    if(route.rooms[route.index].packed) {
        /* Source banks 15 (Divot) and 10 (Seeing Red) use two dark
         * OCS colours in the background tiles: tinted base and grey detail. */
        p=move(p,0x180,DISPLAY_COLOUR(route.index==2?0x011:0x010));
        p=move(p,0x192,DISPLAY_COLOUR(0x111));
    }
#endif
#ifdef V6_TOWER_TELEPORTER_HOLD
    p=move(p,0x180,0x010);p=move(p,0x192,0x111);
#ifdef V6_TELEPORTER_LIVE
    {
        UWORD *bank=tele_dma+index*(TELE_BANK_BYTES/2);
        int frame=tele_animation.frame;
        if(frame>9)frame=8;
        if(frame<1)frame=1;
        if(tele_bank_frame[index]!=frame) {
            unsigned word;
            for(word=0;word<6*V6_TELEPORTER_DMA_WORDS;word+=8) {
                bank[word]=tele_prepared[frame][word];bank[word+1]=tele_prepared[frame][word+1];
                bank[word+2]=tele_prepared[frame][word+2];bank[word+3]=tele_prepared[frame][word+3];
                bank[word+4]=tele_prepared[frame][word+4];bank[word+5]=tele_prepared[frame][word+5];
                bank[word+6]=tele_prepared[frame][word+6];bank[word+7]=tele_prepared[frame][word+7];
            }
            tele_bank_frame[index]=frame;
        }
        v6_sprites_begin(&tele_player_sprites[index],bank+6*V6_TELEPORTER_DMA_WORDS);
        tele_player_sprites[index].count=6;
        if(v6_sprites_add_wide(&tele_player_sprites[index],tower_player_rows[tele_player_frame],
            tele_player.x,tele_player.y,0,32,0x6ff)<0)return 0;
    }
#endif
    for(i=0;i<8;++i) {
#ifdef V6_TELEPORTER_LIVE
        ULONG address=(ULONG)(i<6?tele_dma+index*(TELE_BANK_BYTES/2)+i*V6_TELEPORTER_DMA_WORDS:
            tele_player_sprites[index].dma+i*V6_SPRITE_WORDS);
#else
        ULONG address=(ULONG)(tele_dma+(i<6?i*V6_TELEPORTER_DMA_WORDS:6*V6_TELEPORTER_DMA_WORDS));
#endif
        p=move(p,0x120+i*4,address>>16);p=move(p,0x122+i*4,address);
    }
#ifdef V6_TELEPORTER_LIVE
    p=move(p,0x1ba,0x6ff);p=move(p,0x1be,0x6ff);
#endif
    for(i=0;i<3;++i) {
        p=move(p,0x1a2+i*8,0x111);
        p=move(p,0x1a4+i*8,V6_TELEPORTER_TINT);
        p=move(p,0x1a6+i*8,V6_TELEPORTER_TINT);
    }
#endif
#ifdef V6_TOWER_PLAY
    v6_sprites_begin(&player_sprites[index],player_sprites[index].dma);
#ifdef V6_TOWER_BUILDING
    if(route.rooms[route.index].teleporter) {
        const UWORD (*prepared)[6*V6_TELEPORTER_DMA_WORDS]=building_prepared;
#ifdef V6_TOWER_ENERGIZE
        if(route.index==5)prepared=energize_prepared;
#endif
        UWORD *bank=building_dma+index*(6*V6_TELEPORTER_DMA_WORDS);
        unsigned word;int frame=building_animation.frame;
        if(frame<1)frame=1;
        if(frame>9)frame=8;
        if(building_frames[index]!=frame) {
            for(word=0;word<6*V6_TELEPORTER_DMA_WORDS;word+=8) {
                bank[word]=prepared[frame][word];bank[word+1]=prepared[frame][word+1];
                bank[word+2]=prepared[frame][word+2];bank[word+3]=prepared[frame][word+3];
                bank[word+4]=prepared[frame][word+4];bank[word+5]=prepared[frame][word+5];
                bank[word+6]=prepared[frame][word+6];bank[word+7]=prepared[frame][word+7];
            }
            building_frames[index]=frame;
        }
        player_sprites[index].count=6;
        for(i=0;i<3;++i) {
            unsigned tint=route.rooms[route.index].teleporter->tile==1?0x444:0xaaf;
            p=move(p,0x1a2+i*8,0x111);p=move(p,0x1a4+i*8,tint);p=move(p,0x1a6+i*8,tint);
        }
    }
#endif
    if(!session.invisible)
        v6_sprites_add(&player_sprites[index],tower_player_rows[player_frame],
                      session.player.x,session.player.y-(int)camera,6,0x6ff);
#ifdef V6_TOWER_WORLD
    for(i=0;i<world.count;++i) {
        V6Checkpoint *c=&world.checkpoints[i];
        int y=c->y-(int)camera;
        if(y>=216 || y+16<=16) continue;
        if(v6_sprites_add_rect(&player_sprites[index],tower_player_rows[c->tile],
            c->x,y,0,16,16,c->active?0x6f6:0x888)<0) return 0;
    }
#if defined(V6_TOWER_ROUTE) && (!defined(V6_TOWER_HALLWAY_HOLD) || defined(V6_TOWER_CREW_HOLD))
#ifdef V6_TOWER_TRIGGER_REPLAY
    if(
#ifdef V6_TOWER_RESCUE
       companion.visible
#else
       trigger_crew_visible
#endif
#ifdef V6_TOWER_CAPTION_HOLD
       && 0
#endif
       )
#else
    if(v6_hallway_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story))
#endif
        if(v6_sprites_add(&player_sprites[index],
#ifdef V6_TOWER_RESCUE
            companion.mood?tower_crew_rows:tower_player_rows[companion.frame>=144?companion.frame-144:companion.frame],
#else
            tower_crew_rows,
#endif
#ifdef V6_TOWER_RESCUE
            companion.body.x,companion.body.y,6,0xf44)<0) return 0;
#else
            264,185,6,0xf44)<0) return 0;
#endif
#endif
    if(player_sprites[index].count>world_diag.values[12]) world_diag.values[12]=player_sprites[index].count;
#endif
    for(i=0;i<8;++i) {
        ULONG address=(ULONG)(player_sprites[index].dma+i*V6_SPRITE_WORDS);
#ifdef V6_TOWER_BUILDING
        if(route.rooms[route.index].teleporter && i<6)address=(ULONG)(building_dma+(index*6+i)*V6_TELEPORTER_DMA_WORDS);
#endif
        p=move(p,0x120+i*4,address>>16);p=move(p,0x122+i*4,address);
    }
#ifdef V6_TOWER_WORLD
    for(i=
#ifdef V6_TOWER_BUILDING
        route.rooms[route.index].teleporter?6:
#endif
        0;i<player_sprites[index].count;++i) p=move(p,v6_sprite_colour_register(i),DISPLAY_COLOUR(player_sprites[index].colours[i]));
#else
    p=move(p,0x1a2,0x6ff);
#endif
#endif
#ifdef V6_TOWER_RESCUE
    if(rescue_vm.speech || rescue_bars) {
        unsigned speech=rescue_vm.speech?rescue_vm.speech->index:0;
        unsigned tint=rescue_vm.speech?(rescue_vm.speech->speaker?0x6ff:0xf44):0;
        return v6_tower_caption_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
            camera&255,bg_camera&255,(ULONG)(rescue_captions+speech*V6_DIALOGUE_BYTES),
            DISPLAY_COLOUR(tint),DISPLAY_COLOUR(FG_PALETTE[1]),DISPLAY_COLOUR(FG_PALETTE[3]))!=0;
    }
#endif
#ifdef V6_TOWER_UI_SAVE
    if(ui_fields
#ifdef V6_TOWER_TELE_MENU
       || tele_menu.open
#endif
      )return v6_tower_caption_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
        camera&255,bg_camera&255,(ULONG)(ui_captions+
#ifdef V6_TOWER_TELE_MENU
        (tele_menu.open?5:ui_status)*V6_DIALOGUE_BYTES
#else
        ui_status*V6_DIALOGUE_BYTES
#endif
        ),
        0x6ff,DISPLAY_COLOUR(FG_PALETTE[1]),DISPLAY_COLOUR(FG_PALETTE[3]))!=0;
#endif
    return v6_tower_dual_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
        camera&255,bg_camera&255)!=0;
}
#ifdef V6_TOWER_UI_SAVE
static void ui_copy(void *out,const void *in,unsigned n)
{
    volatile UBYTE *d=out;const volatile UBYTE *p=in;
    while(n--)*d++=*p++;
}
static ULONG ui_game_hash(void)
{
    ULONG hash=0;
#define HASH(v) hash=(hash<<5)-hash+(ULONG)(v)
    HASH(session.player.x);HASH(session.player.y);HASH(session.player.old_x);HASH(session.player.old_y);
    HASH(session.player.vx);HASH(session.player.vy);HASH(session.player.gravity);HASH(session.player.dir);HASH(session.player.flips);
    HASH(session.deaths);HASH(session.respawns);HASH(session.death_timer);HASH(session.life_timer);HASH(session.camera.y);
    HASH(world.save.x);HASH(world.save.y);HASH(world.save.gravity);HASH(world.save.dir);
    HASH(world.save.room_x);HASH(world.save.room_y);HASH(world.save.id);
    HASH(hallway_story.companion);HASH(hallway_story.rescue_triggered);HASH(hallway_story.red_rescued);
#ifdef V6_TOWER_RESCUE
    HASH(companion.body.x);HASH(companion.body.y);HASH(companion.body.vx);HASH(companion.body.vy);
    HASH(companion.follow_steps);HASH(rescue_vm.pc);HASH(rescue_vm.active);
#endif
#ifdef V6_TOWER_BUILDING
    HASH(building_teleporter.tile);HASH(building_teleporter.state);
    HASH(route.tele_region.active);HASH(building_animation.frame);
    HASH(building_animation.delay);HASH(building_animation.walking);
#endif
#undef HASH
    return hash;
}
static int ui_load_checked(V6CheckpointSave *out,V6HallwayStory *story)
{
    int a=v6_campaign_dos.exists(save_name),k=v6_campaign_dos.exists(save_backup),result;
    V6CheckpointSave c,b;V6HallwayStory s,bs;
    if(a<0 || k<0)return V6_SAVE_IO;
    result=v6_campaign_read(&v6_campaign_dos,a?save_name:save_backup,&c,&s);
    if(result)return result;
    if(!checkpoint_bank_valid(&c))return V6_SAVE_CORRUPT;
#if defined(V6_TOWER_BUILDING) && !defined(V6_TOWER_RESCUE)
    if(s.companion || s.rescue_triggered || s.red_rescued)return V6_SAVE_CORRUPT;
#endif
    if(a && k) {
        result=v6_campaign_read(&v6_campaign_dos,save_backup,&b,&bs);
        if(result)return result;
        if(!checkpoint_bank_valid(&b))return V6_SAVE_CORRUPT;
#if defined(V6_TOWER_BUILDING) && !defined(V6_TOWER_RESCUE)
        if(bs.companion || bs.rescue_triggered || bs.red_rescued)return V6_SAVE_CORRUPT;
#endif
    }
    return v6_campaign_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story);
}
static int ui_save_checked(void)
{
    V6CheckpointSave c;V6HallwayStory story;int result;
    int a,k;
    if(!checkpoint_bank_valid(&world.save))return V6_SAVE_INVALID;
    a=v6_campaign_dos.exists(save_name);k=v6_campaign_dos.exists(save_backup);
    if(a<0 || k<0)return V6_SAVE_IO;
    /* Existing records need source-bank validation before replacement recovery
     * can discard a backup, just as an explicit load does. */
    if(a || k) {result=ui_load_checked(&c,&story);if(result)return result;}
    return v6_campaign_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story);
}
static int ui_apply_load(const V6CheckpointSave *c,const V6HallwayStory *story)
{
    ui_copy(&world.save,c,sizeof(*c));
#ifdef V6_TOWER_RESCUE
    ui_copy(&hallway_story,story,sizeof(*story));
#else
    (void)story;
#endif
    v6_tower_session_init(&session,c->x,c->y,c->gravity,c->dir);
    if(!v6_tower_route_load(&route,c->room_x,c->room_y,1))return 0;
    session.player.old_x=session.player.x;session.player.old_y=session.player.y;

#ifdef V6_TOWER_RESCUE
    { unsigned i;for(i=0;i<sizeof(rescue_vm);++i)((volatile UBYTE *)&rescue_vm)[i]=0; }
    rescue_vm.control=1;rescue_vm.following=story->companion==9;rescue_vm.mood=story->companion==9?0:1;
    rescue_bars=rescue_fade=rescue_fade_mode=rescue_fire=0;rescue_flips_applied=cue_consumed=0;
    v6_companion_init(&companion);
#endif
    player_animation.delay=player_animation.walk=0;player_frame=c->dir?0:3;
#ifdef V6_TOWER_TELE_MENU
    v6_teleporter_menu_init(&tele_menu);tele_menu_fire=0;
#endif
    return route_source();
}
#endif
static int run(void) {
    UBYTE *chip;UWORD *lists[2];
    UWORD dma,ints,adk;APTR old_irq;struct View *view;
    /* Keep logical coordinates continuous across the 700-row source seam.
     * Only the stream wraps source rows; physical ring slots use logical rows.
     * A bounded back-and-forth route exercises both directions indefinitely. */
    unsigned back=1,camera=V6_TOWER_HOLD>=0?V6_TOWER_HOLD:CAMERA_MIN,drawn;int direction=1;
#ifdef V6_TOWER_ROUTE
    int publish;
#endif
    ULONG start,work,previous;
#ifdef V6_TOWER_UI_SAVE
    int ui_os_paused=0;
#endif
#ifdef V6_TOWER_PLAY
    ULONG logic_work,render_work;
#endif
#ifdef V6_TOWER_CONTROLLER
    static V6TowerCamera controller;
    ULONG logic_frame,elapsed=0;
#ifdef V6_TOWER_RECOVERY
#ifdef V6_TOWER_PLAY
#ifdef V6_TOWER_WORLD
    /* Original ceiling checkpoint. The replay starts with it inactive, so
     * ordinary contact must arm it before its next entity update can save. */
    v6_tower_session_init(&session,140,1822,1,1);
    session.camera.y=session.camera.old_y=1702;
    world.checkpoints=tower_checkpoints;world.count=TOWER_CHECKPOINT_COUNT;
    world.save.x=140;world.save.y=1822;world.save.gravity=1;world.save.dir=1;
    world.save.room_x=109;world.save.room_y=109;world.save.id=-1;
    if(!v6_tower_gameplay_init(&world,tower_checkpoints,TOWER_CHECKPOINT_COUNT,&world.save)) return 20;
#ifdef V6_TOWER_ROUTE_REPLAY
    v6_tower_session_init(&session,44,5449,0,1);
    session.camera.y=session.camera.old_y=5329;
    world.save.x=44;world.save.y=5449;world.save.gravity=0;world.save.dir=1;
    world.save.id=505007;
    if(!v6_tower_gameplay_init(&world,tower_checkpoints,TOWER_CHECKPOINT_COUNT,&world.save)) return 20;
#endif
#else
    /* Player-only regression fixture, not a literal checkpoint reset. */
    v6_tower_session_init(&session,140,1817,0,1);
    session.camera.y=session.camera.old_y=1697;
#endif
#ifdef V6_TOWER_UPPER_REPLAY
    /* Start beside the upper exit; movement and checkpoint contact are live. */
    v6_tower_session_init(&session,280,80,0,1);
    world.save.id=505147;
    if(!v6_tower_gameplay_init(&world,tower_checkpoints,TOWER_CHECKPOINT_COUNT,&world.save)) return 20;
#endif
#if defined(V6_TOWER_TRIGGER_REPLAY) && !defined(V6_TOWER_COMPANION_ROUTE)
    v6_tower_session_init(&session,180,185,0,1);
    world.save.id=505147;
    if(!v6_tower_gameplay_init(&world,tower_checkpoints,TOWER_CHECKPOINT_COUNT,&world.save)) return 20;
#endif
    player_tiles.read=v6_tower_tile;player_tiles.context=&stream;
#ifdef V6_TOWER_WORLD
    player_tiles.walls=v6_tower_walls;
#endif
    v6_player_tower_room(&player_room,&player_tiles);
#ifdef V6_TOWER_ROUTE
    if(!v6_tower_route_init(&route,&session,&world,tower_route_rooms,TOWER_ROUTE_COUNT,109,109,&player_tiles)) return 20;
#ifdef V6_TOWER_BUILDING
    v6_tower_session_init(&session,280,185,0,1);
    if(!v6_tower_route_load(&route,110,104,0))return 20;
#ifdef V6_ENERGIZE_CAPTURE
#ifdef V6_TOWER_ROUNDTRIP
    if(!v6_tower_route_load(&route,111,104,0))return 20;
    v6_player_init(&session.player,156,92,0);
    if(!v6_tower_route_step(&route,0) || !v6_tower_route_step(&route,0))return 20;
    v6_teleporter_departure_init(&departure);
    if(!v6_teleporter_departure_start(&departure,&building_teleporter,&route.tele_region))return 20;
#else
    if(!v6_tower_route_load(&route,111,104,0) || !v6_tower_route_teleport(&route,110,105))return 20;
#endif
    building_animation.frame=1;
#ifdef V6_TOWER_ARRIVAL
    v6_teleporter_arrival_init(&arrival);
#ifndef V6_TOWER_ROUNDTRIP
    if(!v6_teleporter_arrival_start(&arrival))return 20;
    session.invisible=1;
#endif
#endif
#endif
#ifdef V6_BUILDING_SAVE
    if(building_stage==2) {
        world.save.x=building_saved.x;world.save.y=building_saved.y;
        world.save.gravity=building_saved.gravity;world.save.dir=building_saved.dir;
        world.save.room_x=building_saved.room_x;world.save.room_y=building_saved.room_y;world.save.id=building_saved.id;
        if(!v6_tower_route_load(&route,building_saved.room_x,building_saved.room_y,1))return 20;
        building_save_diag.values[9]=session.player.x;building_save_diag.values[10]=session.player.y;
        building_animation.frame=1;
    }
#endif
#endif
#ifdef V6_TOWER_TRIGGER_REPLAY
#ifdef V6_TOWER_COMPANION_ROUTE
    hallway_story.companion=9;hallway_story.rescue_triggered=hallway_story.red_rescued=1;
    rescue_vm.following=1;rescue_vm.mood=0;
#else
    if(!v6_tower_route_load(&route,110,104,0)) return 20;
#endif
#ifdef V6_TOWER_PERSIST
    if(persist_stage==2) {
        world.save=persisted_checkpoint;hallway_story=persisted_story;
        if(!v6_tower_route_load(&route,world.save.room_x,world.save.room_y,1))return 20;
        rescue_vm.following=hallway_story.companion==9;rescue_vm.mood=hallway_story.companion==9?0:1;
        persist_diag.values[4]=1;
        persist_diag.values[6]=session.player.x;persist_diag.values[7]=session.player.y;
        persist_diag.values[8]=session.player.gravity;persist_diag.values[9]=session.player.dir;
    }
#endif
    v6_hallway_trigger_init(&hallway_trigger);
    v6_hallway_trigger_enter(&hallway_trigger,route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
    trigger_crew_visible=v6_hallway_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
#ifdef V6_TOWER_RESCUE
    v6_companion_init(&companion);
#ifdef V6_TOWER_COMPANION_ROUTE
    v6_companion_enter(&companion,9,1,109,&session.player);
#else
#ifdef V6_TOWER_PERSIST
    if(persist_stage==2 && hallway_story.companion==9)
        v6_companion_enter(&companion,9,route.index<2,route.rooms[route.index].x,&session.player);
    else
#endif
    v6_companion_idle(&companion,trigger_crew_visible);
#endif
    {
        unsigned i;
        for(i=0;i<2;++i) {
            V6Room collision;
            collision.tiles=tower_route_rooms[i+2].decoded;
            collision.tileset=2;collision.extra_row=0;collision.terrain=0;
            collision.blocks=0;collision.block_count=0;
            v6_terrain_build(&hallway_terrain[i],&collision);
        }
        if(route.index>=2)route.room.terrain=&hallway_terrain[route.index-2];
    }
#endif
#endif
#ifdef V6_TOWER_HALLWAY_HOLD
    if(!v6_tower_route_load(&route,V6_TOWER_HALLWAY_HOLD?110:108,V6_TOWER_HALLWAY_HOLD?104:109,0)) return 20;
    session.player.x=0;session.player.y=-2000;session.invisible=1;world.count=0;
#endif
#endif
#else
    v6_tower_session_init(&session,144,300,1,0);
    session.player.x=80;session.player.y=450;session.player.gravity=0;
    session.player.vx=V6_ONE;session.player.vy=-V6_ONE;
    session.player.old_x=79;session.player.old_y=451;
#endif
#endif
#ifdef V6_TOWER_CAPTION_HOLD
    rescue_vm.speech=&v6_rescue_speeches[V6_TOWER_CAPTION_HOLD];
#endif
    camera=0;
#ifdef V6_TOWER_PLAY
    camera=session.camera.y;
    controller.y=session.camera.y;controller.old_y=session.camera.old_y;
#endif
    diag.step=0;diag.route_min=0;diag.route_max=5368;
    (void)direction;
#endif
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    if(SysBase->AttnFlags&AFF_68010) return 20;
    GfxBase=(struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    if(!GfxBase) return 20;
    if(!(GfxBase->DisplayFlags&PAL)) { CloseLibrary((struct Library *)GfxBase);return 20; }
#ifdef V6_TOWER_AUDIO
    /* This takeover fixture cannot resume another client's write-only audio
     * pointers. Start only with all audio DMA and our audio IRQs idle. */
    if((hw->dmaconr&15) || (hw->intenar&(INTF_AUD0|INTF_AUD1))) {
        CloseLibrary((struct Library *)GfxBase);return 20;
    }
#endif
    chip=AllocMem(CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    if(!chip) { CloseLibrary((struct Library *)GfxBase);return 20; }
    rings[0]=chip;rings[1]=chip+LAYER_BYTES;
    lists[0]=(UWORD *)(chip+2*LAYER_BYTES);lists[1]=lists[0]+LIST_WORDS;
#ifdef V6_TOWER_PLAY
    player_sprites[0].dma=(UWORD *)(lists[1]+LIST_WORDS);
    player_sprites[1].dma=player_sprites[0].dma+8*V6_SPRITE_WORDS;
#endif
#ifdef V6_TOWER_RESCUE
    {
        unsigned i;
        rescue_captions=chip+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES;
        for(i=0;i<V6_RESCUE_SPEECHES;++i)
            if(!v6_dialogue_draw(rescue_captions+i*V6_DIALOGUE_BYTES,dialogue_font,&v6_rescue_speeches[i])) {
                FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
            }
    }
#endif
#ifdef V6_TOWER_BUILDING
    {
        unsigned frame;V6Room collision;
        building_dma=(UWORD *)(chip+CHIP_BYTES-BUILDING_DMA_BYTES);
        collision.tiles=building_tiles;collision.tileset=2;collision.extra_row=0;
        collision.terrain=0;collision.blocks=0;collision.block_count=0;
        v6_terrain_build(&building_terrain,&collision);
        if(route.index==4)route.room.terrain=&building_terrain;
#ifdef V6_TOWER_ENERGIZE
        collision.tiles=energize_tiles;collision.tileset=0;v6_terrain_build(&energize_terrain,&collision);
        if(route.index==5)route.room.terrain=&energize_terrain;
        for(frame=1;frame<10;++frame)
            if(!v6_teleporter_draw(energize_prepared[frame],teleporter_masks[0],teleporter_masks[frame],36,68)) {
                FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
            }
#endif
        for(frame=1;frame<10;++frame)
            if(!v6_teleporter_draw(building_prepared[frame],teleporter_masks[0],teleporter_masks[frame],112,48)) {
                FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
            }
    }
#endif
#ifdef V6_TOWER_TELEPORTER_HOLD
    tele_dma=(UWORD *)(chip+CHIP_BYTES-TELE_DMA_BYTES);
#ifdef V6_TELEPORTER_LIVE
    {
        unsigned frame;
        for(frame=1;frame<10;++frame)
            if(!v6_teleporter_draw(tele_prepared[frame],teleporter_masks[0],teleporter_masks[frame],112,48)) {
                FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
            }
    }
    v6_teleporter_init(&tele,112,48,0);tele_animation.frame=1;
    v6_player_init(&tele_player,80,80,0);tele_player.dir=1;
    tele_room.tiles=building_tiles;tele_room.tileset=2;tele_room.extra_row=0;
    tele_room.terrain=0;tele_room.blocks=0;tele_room.block_count=0;
#else
    {
        int frame=V6_TOWER_TELEPORTER_HOLD;
        if(frame>9)frame=8;
        if(frame<1)frame=1;
        if(!v6_teleporter_draw(tele_dma,teleporter_masks[0],teleporter_masks[frame],112,48)) {
            FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
        }
        tele_dma[6*V6_TELEPORTER_DMA_WORDS]=tele_dma[6*V6_TELEPORTER_DMA_WORDS+1]=0;
    }
#endif
#endif
    if(
#ifdef V6_TOWER_ENERGIZE
       !v6_tower_open(&stream,energize_display,sizeof(energize_display)) ||
       !v6_tower_pairs_validate(&stream,energize_pair_offsets,ENERGIZE_PAIR_WORDS,ENERGIZE_TILE_COUNT,2) ||
#endif
#ifdef V6_TOWER_ROUTE
       #ifdef V6_TOWER_BUILDING
       !v6_tower_open(&stream,building_display,sizeof(building_display)) ||
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
#endif
       !v6_tower_open(&stream,hallway0_display,sizeof(hallway0_display)) ||
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
       !v6_tower_open(&stream,hallway1_display,sizeof(hallway1_display)) ||
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
#endif
       !v6_tower_open(&stream,tower_map,sizeof(tower_map)) ||
       !v6_tower_open(&background_stream,tower_background_map,sizeof(tower_background_map)) ||
#ifdef V6_TOWER_PAIRS
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
       !v6_tower_pairs_validate(&background_stream,tower_background_pair_offsets,TOWER_BACKGROUND_PAIR_WORDS,TOWER_TILE_COUNT,1) ||
#endif
#ifdef V6_TOWER_HALLWAY_HOLD
       !v6_tower_open(&stream,V6_TOWER_HALLWAY_HOLD?hallway1_display:hallway0_display,
           V6_TOWER_HALLWAY_HOLD?sizeof(hallway1_display):sizeof(hallway0_display)) ||
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
#endif
#if defined(V6_TOWER_TRIGGER_REPLAY) && !defined(V6_TOWER_COMPANION_ROUTE)
       !v6_tower_open(&stream,hallway1_display,sizeof(hallway1_display)) ||
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
#endif
#ifdef V6_TOWER_TELEPORTER_HOLD
       !v6_tower_open(&stream,building_display,sizeof(building_display)) ||
#ifdef V6_TOWER_PAIRS
       !v6_tower_pairs_validate(&stream,tower_pair_offsets,TOWER_PAIR_WORDS,TOWER_TILE_COUNT,2) ||
#endif
#endif
#ifdef V6_TOWER_BUILDING
       !v6_tower_open(&stream,
#ifdef V6_BUILDING_SAVE
           building_stage==2?building_display:
#endif

#ifdef V6_TOWER_ROUNDTRIP
           building_display,
#elif defined(V6_ENERGIZE_CAPTURE)
           energize_display,
#else
           hallway1_display,
#endif
#ifdef V6_BUILDING_SAVE
           building_stage==2?sizeof(building_display):
#endif

#ifdef V6_TOWER_ROUNDTRIP
           sizeof(building_display)) ||
#elif defined(V6_ENERGIZE_CAPTURE)
           sizeof(energize_display)) ||
#else
           sizeof(hallway1_display)) ||
#endif
#endif
       !prepare(rings[0],lists[0],0,camera,0)) {
        FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
    }
#ifdef V6_TOWER_AUDIO
    {
        unsigned i;
        cue_chip=chip+CHIP_BYTES-CUE_DMA_BYTES;
        for(i=0;i<CUE_CREW6_BYTES;++i)cue_chip[i]=cue_crew6[i];
        for(i=0;i<CUE_CREW1_BYTES;++i)cue_chip[CUE_CREW6_BYTES+i]=cue_crew1[i];
        if(!v6_audio_init(&cue_audio,(ULONG)(cue_chip+CUE_DMA_BYTES-2))) {
            FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
        }
    }
#endif
#ifdef V6_TOWER_UI_SAVE
    {
        unsigned i;ui_captions=chip+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES;
        for(i=0;i<UI_MESSAGE_COUNT;++i)if(!v6_dialogue_draw(ui_captions+i*V6_DIALOGUE_BYTES,dialogue_font,&ui_messages[i])) {
            FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
        }
        ui_fields=250;ui_status=0;
    }
#endif
    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
    OwnBlitter();WaitBlit();Forbid();Disable();
#ifdef V6_TOWER_AUDIO
    /* Recheck while scheduling and interrupts are stopped: allocation and
     * display preparation ran with the OS enabled after the early check. */
    if((hw->dmaconr&15) || (hw->intenar&(INTF_AUD0|INTF_AUD1))) {
        Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();
        FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
    }
#endif
    dma=hw->dmaconr;ints=hw->intenar;adk=hw->adkconr;
    hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l 0x6c.w,%0":"=r"(old_irq));
    __asm volatile("move.l %0,0x6c.w"::"r"((APTR)irq):"memory");
    blank();hw->cop1lc=(ULONG)lists[0];hw->copjmp1=0;
    hw->dmacon=DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER
#if defined(V6_TOWER_PLAY) || defined(V6_TOWER_TELEPORTER_HOLD)
        |DMAF_SPRITE
#endif
        ;
    hw->intena=INTF_SETCLR|INTF_INTEN|INTF_VERTB;Enable();diag.status=1;
    /* Warm the second ring before measuring incremental row work. */
    if(!prepare(rings[1],lists[1],1,camera,0)) diag.error=1;
    blank();previous=frames;
#ifdef V6_TOWER_CONTROLLER
    logic_frame=frames;
#endif
    while((*(volatile UBYTE *)0xbfe001&0x40) && !diag.error
#ifdef V6_TOWER_WORLD
          && !world.exit.room_x
#endif
#ifdef V6_TOWER_PERSIST
          && (persist_stage==2?diag.logic_ticks<64:
              !(hallway_story.red_rescued && !rescue_vm.active && companion.follow_steps>=64 && cue_audio.state==0))
#endif
#ifdef V6_TOWER_UI_REPLAY
          && (ui_test_phase<4 || diag.logic_ticks<ui_test_tick+32)
#endif
#ifdef V6_BUILDING_SAVE
          && diag.logic_ticks<128
#endif
          ) {
        start=clock_lines();
#ifdef V6_TOWER_UI_SAVE
        {
            int right=(hw->potinp&0x0400)==0,fire=(*(volatile UBYTE *)0xbfe001&0x80)==0;
            unsigned action;
#ifdef V6_TOWER_UI_REPLAY
            right=fire=0;
            if(ui_test_phase==0) {right=fire=1;ui_test_phase=1;}
            else if(ui_test_phase==1 && diag.logic_ticks>=20 && rescue_vm.active) {right=1;ui_test_phase=2;}
            else if(ui_test_phase==2 && !rescue_vm.active && companion.follow_steps>=64 && !cue_audio.state) {
                right=1;ui_test_phase=3;ui_test_tick=diag.logic_ticks;
            } else if(ui_test_phase==3 && diag.logic_ticks>=ui_test_tick+16) {
                right=fire=1;ui_test_phase=4;ui_test_tick=diag.logic_ticks;
            }
            ui_diag.values[17]=ui_test_phase;
#endif
            action=v6_save_controls_tick(&save_controls,right,fire);
            if(ui_fields)--ui_fields;
            if(action) {
                ULONG before_hash=ui_game_hash(),before_frames=frames,before_ticks=diag.logic_ticks;
                int result=5;
                ++ui_diag.values[0];ui_diag.values[7]=action;
                if(route_loading || session.death_timer!=-1
#ifdef V6_TOWER_TELE_MENU
                   || tele_menu.open
#endif
#ifdef V6_TOWER_RESCUE
                   || rescue_vm.active
#endif
#ifdef V6_TOWER_AUDIO
                   || cue_audio.state
#endif
                  ) {
                    ++ui_diag.values[4];ui_status=4;ui_fields=200;
                } else {
                    V6CheckpointSave c;V6HallwayStory story;
#ifdef V6_TOWER_AUDIO
                    { V6AudioPlan plan;v6_audio_stop(&cue_audio,&plan);audio_apply(&plan);audio_record(); }
#endif
                    Disable();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
                    __asm volatile("move.l %0,0x6c.w"::"r"(old_irq):"memory");
                    hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
                    hw->adkcon=adk|0x8000;hw->dmacon=dma|0x8000;hw->intena=ints|0x8000;
                    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=3;ui_os_paused=1;
                    ++ui_diag.values[5];
                    if(action==V6_SAVE_ACTION_SAVE)
                        result=ui_save_checked();
                    else {
                        result=ui_load_checked(&c,&story);
                        if(!result && !ui_apply_load(&c,&story)){result=V6_SAVE_INVALID;diag.error=12;}
                        if(!result){ui_diag.values[15]=session.player.x;ui_diag.values[16]=session.player.y;}
                    }
                    /* DOS may acknowledge cached changes before physical
                     * disk writes finish. Complete them before Forbid/IRQ
                     * takeover can suspend the filesystem's background work. */
                    if(!v6_campaign_dos_flush("DF1:")) {
                        ui_diag.values[8]=V6_SAVE_IO;diag.error=12;diag.status=2;break;
                    }
                    if(result){++ui_diag.values[3];ui_status=3;}else{++ui_diag.values[action];ui_status=action;}
                    ui_fields=200;camera=session.camera.y;ui_copy(&controller,&session.camera,sizeof(controller));
                    /* Refill both banks while the OS owns the display. No DOS
                     * time is added to the private VBlank clock or accumulator. */
                    { unsigned i;for(i=0;i<2;++i) {
                        v6_tower_draw_reset(&draw[i]);v6_tower_draw_reset(&background_draw[i]);
                        prepared_camera[i]=camera;
                        if(!prepare(rings[i],lists[i],i,camera,0))diag.error=12;
                    } }
                    route_loading=0;back=1;
                    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
                    OwnBlitter();WaitBlit();Forbid();Disable();
                    if((hw->dmaconr&15) || (hw->intenar&(INTF_AUD0|INTF_AUD1))) {
                        Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();
                        diag.error=12;diag.status=2;break;
                    }
                    ui_os_paused=0;
                    dma=hw->dmaconr;ints=hw->intenar;adk=hw->adkconr;
                    hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
                    __asm volatile("move.l 0x6c.w,%0":"=r"(old_irq));
                    __asm volatile("move.l %0,0x6c.w"::"r"((APTR)irq):"memory");
                    blank();hw->cop1lc=(ULONG)lists[0];hw->copjmp1=0;
                    hw->dmacon=DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER|DMAF_SPRITE;
                    hw->intena=INTF_SETCLR|INTF_INTEN|INTF_VERTB;Enable();diag.status=1;
                    blank();previous=frames;logic_frame=frames;++ui_diag.values[6];
                }
                ui_diag.values[8]=result;ui_diag.values[9]=before_hash;ui_diag.values[10]=ui_game_hash();
                ui_diag.values[11]=before_frames;ui_diag.values[12]=frames;
                ui_diag.values[13]=before_ticks;ui_diag.values[14]=diag.logic_ticks;
                if(ui_trace.count<8) {
                    volatile ULONG *r=ui_trace.records[ui_trace.count++];
                    r[0]=action;r[1]=result;r[2]=before_hash;r[3]=ui_game_hash();r[4]=before_frames;r[5]=frames;
                    r[6]=before_ticks;r[7]=diag.logic_ticks;r[8]=session.player.x;r[9]=session.player.y;
                }
                if(result!=5)continue;
            }
        }
#endif
#ifdef V6_TOWER_AUDIO
        {
            V6AudioPlan plan;
            v6_audio_tick(&cue_audio,(hw->intreqr&INTF_AUD0)!=0,&plan);
            audio_apply(&plan);audio_record();
        }
#endif
#ifdef V6_TOWER_CONTROLLER
        {
            ULONG now=frames,delta=now-logic_frame;
            logic_frame=now;
#ifdef V6_TOWER_ROUTE
            if(route_loading) delta=0;
#endif
#ifdef V6_ENERGIZE_CAPTURE
#ifndef V6_ENERGIZE_CAPTURE_TICKS
#define V6_ENERGIZE_CAPTURE_TICKS 128
#endif
            if(diag.logic_ticks>=V6_ENERGIZE_CAPTURE_TICKS)delta=0; /* Hold the verified scene for capture. */
#endif
            elapsed+=delta*19968UL;diag.logic_frames+=delta;
            while(elapsed>=34000) {
                elapsed-=34000;
#ifdef V6_TELEPORTER_LIVE
                {
                    unsigned events,input=diag.logic_ticks<40?V6_RIGHT:diag.logic_ticks<80?V6_LEFT:0;
                    if(diag.logic_ticks==180)tele.state=2; /* arrival fixture */
                    events=v6_teleporter_update(&tele,&tele_region,0,0,&tele_player,111,104,0,0,&tele_save);
                    tele_saves+=(events&V6_TELEPORTER_SAVED)!=0;
                    tele_messages+=(events&V6_TELEPORTER_MESSAGE)!=0;
                    v6_player_step(&tele_player,&tele_room,input);
                    v6_teleporter_collide(&tele,&tele_player);
                    tele_random^=tele_random<<13;tele_random^=tele_random>>17;tele_random^=tele_random<<5;
                    v6_teleporter_animate(&tele_animation,tele.tile,0,(UWORD)(tele_random>>16)%6);
                    tele_player_frame=v6_collision_frame(&tele_player_animation,&tele_player,tele_player.ground,tele_player.roof,-1);
                    if(tele_trace.count<256) {
                        volatile ULONG *r=tele_trace.records[tele_trace.count++];
                        r[0]=tele_player.x;r[1]=tele_player.y;r[2]=tele.tile;r[3]=tele.state;
                        r[4]=tele_animation.frame;r[5]=tele_animation.delay;r[6]=tele_animation.walking;
                        r[7]=tele_saves;r[8]=tele_messages;r[9]=tele_save.x;r[10]=tele_save.y;r[11]=tele_region.active;
                    }
                    controller.y=controller.old_y=0;
                }
#else
#ifdef V6_TOWER_RECOVERY
#ifdef V6_TOWER_PLAY
                unsigned input=0;
#ifdef V6_TOWER_PLAY_REPLAY
#ifdef V6_TOWER_WORLD
                input=diag.logic_ticks<sizeof(tower_world_replay)?tower_world_replay[diag.logic_ticks]:0;
#else
                input=diag.logic_ticks<16?V6_RIGHT:0;
                if(diag.logic_ticks>=16 && diag.logic_ticks<20) input|=V6_FLIP;
#endif
#if defined(V6_TOWER_RESCUE) && !defined(V6_TOWER_COMPANION_ROUTE)
                if(diag.logic_ticks>=8) {
                    input=rescue_vm.waiting && (UWORD)diag.logic_ticks%30==0?V6_FLIP:0;
                    if(!rescue_vm.active && hallway_story.companion==9) {
                        unsigned phase=(UWORD)(companion.follow_steps+1)%96;
                        input=phase<12 || (phase>=36 && phase<48)?V6_LEFT:phase<36?V6_RIGHT:0;
                        if(session.player.x>270 && input==V6_RIGHT)input=V6_LEFT;
                        if(session.player.x<140 && input==V6_LEFT)input=V6_RIGHT;
                    }
                }
#endif
#else
                UWORD joy=hw->joy1dat;
                if(joy&0x0200) input|=V6_LEFT;
                if(joy&0x0002) input|=V6_RIGHT;
                if(!(*(volatile UBYTE *)0xbfe001&0x80)) input|=V6_FLIP;
#endif
#ifdef V6_TOWER_BUILDING_REPLAY
                input=(diag.logic_ticks<40?V6_RIGHT:diag.logic_ticks<80?V6_LEFT:0);
                if(diag.logic_ticks==30)input|=V6_FLIP;
#ifdef V6_TELE_MENU_CAPTURE
                if(diag.logic_ticks>=42)input=0;
#endif
#ifdef V6_BUILDING_SAVE
                if(building_stage==2)input=0;
#endif
#endif
#ifdef V6_ENERGIZE_CAPTURE
                input=0;
#endif
#ifdef V6_TOWER_PERSIST
                if(persist_stage==2) input=0;
#endif
#ifdef V6_TOWER_UI_REPLAY
                if(ui_test_phase==4)input=0;
#endif
#ifdef V6_TOWER_UI_SAVE
                input=v6_save_controls_filter(&save_controls,input);
#endif
#ifdef V6_TOWER_TELE_MENU
                {
                    UWORD joy=hw->joy1dat;
                    int fire=(*(volatile UBYTE *)0xbfe001&0x80)==0;
                    int down=((joy&0x0100)!=0)!=((joy&1)!=0);
                    unsigned buttons=0,was_open=tele_menu.open,event;
                    ULONG before=ui_game_hash();V6TeleporterDestination target;
                    if(!fire)tele_menu_fire=0;
                    else if(was_open)tele_menu_fire=1;
                    if(tele_menu.open) {
                        if(joy&0x0200)buttons|=V6_TELE_MENU_LEFT;
                        if(joy&0x0002)buttons|=V6_TELE_MENU_RIGHT;
                        if(fire)buttons|=down?V6_TELE_MENU_CANCEL:V6_TELE_MENU_CONFIRM;
                    } else if(fire && !save_controls.suppress_fire && (down || tele_menu_fire)) {
                        buttons=V6_TELE_MENU_CONFIRM;tele_menu_fire=1;
                    }
                    v6_teleporter_menu_ready(&tele_menu,&route.tele_region,&session.player,
                        route.index==4 && session.death_timer==-1 && !route_loading);
                    event=v6_teleporter_menu_tick(&tele_menu,tele_destinations,1,
                        route.rooms[route.index].x,route.rooms[route.index].y,&session.player,buttons,&target);
                    if(event==V6_TELE_MENU_OPENED){
                        if(!tele_menu_diag.values[0])tele_menu_diag.values[8]=session.player.flips;
                        ++tele_menu_diag.values[0];tele_menu_fire=1;tele_menu_diag.values[6]=before;
                    }
                    tele_menu_diag.values[9]=session.player.flips;
                    if(event==V6_TELE_MENU_CHANGED)++tele_menu_diag.values[1];
                    if(event==V6_TELE_MENU_CLOSED){++tele_menu_diag.values[2];ui_fields=0;}
                    /* Only the current resident teleporter is offered. A future
                     * destination must add a validated arrival path first. */
                    if(event==V6_TELE_MENU_TRAVEL){++tele_menu_diag.values[3];diag.error=13;}
                    tele_menu_diag.values[4]=tele_menu.selected;
                    if(tele_menu_fire || was_open || tele_menu.open)input&=~V6_FLIP;
                    if(was_open || tele_menu.open) {
                        ++tele_menu_diag.values[5];tele_menu_diag.values[7]=ui_game_hash();
                        if(tele_menu_diag.values[6]!=tele_menu_diag.values[7])diag.error=13;
                        goto tele_menu_paused;
                    }
                }
#endif
#ifdef V6_TOWER_RESCUE
                V6RescueSignals rescue_signals;
                v6_companion_step(&companion,&session.player,&route.room,session.death_timer);
                rescue_animate();
                rescue_signals.bars_ready=rescue_vm.bars?rescue_bars>=360:rescue_bars==0;
                rescue_signals.fade_ready=rescue_vm.fade>0?rescue_fade>416:rescue_fade==0;
                rescue_signals.onroof=session.player.roof>0;
                rescue_signals.advance=(input&V6_FLIP) && !rescue_fire;
                rescue_fire=(input&V6_FLIP)!=0;
                if(rescue_vm.active) {
                    input&=~V6_FLIP;
                    if(!rescue_vm.control) input|=V6_NO_CONTROL;
                }
                if(rescue_vm.flips!=rescue_flips_applied) {
                    input|=V6_FLIP;rescue_flips_applied=rescue_vm.flips;
                }
#endif
#ifdef V6_TOWER_WORLD
#ifdef V6_TOWER_ROUTE
                unsigned index=route.index;
#ifndef V6_TOWER_HALLWAY_HOLD
#ifdef V6_TOWER_ARRIVAL
#ifdef V6_TOWER_ROUNDTRIP
                departure.events=arrival.events=0;
                if(travel_leg==1 && !arrival.state && !departure.state) {
                    if(!v6_teleporter_departure_start(&departure,route.rooms[route.index].teleporter,&route.tele_region))diag.error=14;
                }
                if(departure.state || !arrival.control)input|=V6_NO_CONTROL;
                if(!v6_tower_route_step_phase(&route,input,travel_phase,0))diag.error=6;
                if(departure.travel) {
                    int x=travel_leg==0?110:111,y=travel_leg==0?105:104;
                    if(!v6_tower_route_teleport(&route,x,y))diag.error=14;
                    else {
                        departure.travel=0;++travel_leg;
                        v6_teleporter_arrival_init(&arrival);
                        arrival.flash=departure.flash;arrival.shake=departure.shake;
                        if(!v6_teleporter_arrival_start(&arrival))diag.error=14;
                    }
                }
                arrival_flash=departure.state?departure.flash:arrival.flash;
                if(departure_trace.count<128) {
                    volatile ULONG *d=departure_trace.records[departure_trace.count++];
                    d[0]=departure.state;d[1]=departure.delay;d[2]=departure.control;
                    d[3]=departure.flash;d[4]=departure.shake;d[5]=departure.events;
                    d[6]=departure.travel;d[7]=travel_leg;
                }
                if(departure.flash>0)--departure.flash;
                if(departure.shake>0)--departure.shake;
#else
                if(!arrival.control)input|=V6_NO_CONTROL;
                if(!v6_tower_route_step_phase(&route,input,arrival_phase,&arrival))diag.error=6;
                arrival_flash=arrival.flash;
#endif
                if(arrival_trace.count<128) {
                    volatile ULONG *a=arrival_trace.records[arrival_trace.count++];
                    a[0]=arrival.state;a[1]=arrival.delay;a[2]=arrival.control;
                    a[3]=arrival.flash;a[4]=arrival.shake;a[5]=arrival.events;
                    a[6]=session.invisible;a[7]=session.player.vx;a[8]=session.player.vy;
                    a[9]=session.player.ay;a[10]=session.player.old_x;a[11]=session.player.old_y;
                    a[12]=session.player.dir;a[13]=session.death_timer;
                }
                /* Graphics::renderfixedpost effect counters decay once per tick. */
                if(arrival.flash>0)--arrival.flash;
                if(arrival.shake>0)--arrival.shake;
#else
                if(!v6_tower_route_step(&route,input)) diag.error=6;
#endif
#else
                (void)input;
#endif
                if(route.index!=index && !route_source()) diag.error=7;
#ifdef V6_TOWER_BUILDING
                if(route.rooms[route.index].teleporter) {
                    building_random^=building_random<<13;building_random^=building_random>>17;building_random^=building_random<<5;
                    v6_teleporter_animate(&building_animation,route.rooms[route.index].teleporter->tile,0,(UWORD)(building_random>>16)%6);
                }
                if(building_trace.count<128) {
                    volatile ULONG *r=building_trace.records[building_trace.count++];
                    r[0]=route.index;r[1]=session.player.x;r[2]=session.player.y;
                    V6Teleporter *t=&building_teleporter;
#ifdef V6_TOWER_ENERGIZE
                    if(route.index==5)t=&energize_teleporter;
#endif
                    r[3]=t->tile;r[4]=t->state;r[5]=route.tele_events;
                    r[6]=building_animation.frame;r[7]=world.save.x;r[8]=world.save.y;
                    r[9]=world.save.room_x;r[10]=world.save.room_y;r[11]=route.tele_region.active;
                }
#endif
#ifdef V6_TOWER_TRIGGER_REPLAY
                /* Trigger-only fixture retains the handoff; rescue builds consume it. */
                v6_hallway_trigger_step(&hallway_trigger,&hallway_story,&session.player);
#ifdef V6_TOWER_RESCUE
                if(hallway_trigger.pending && !rescue_vm.active) {
                    if(v6_hallway_trigger_take(&hallway_trigger)!=V6_SCRIPT_RESCUE_RED ||
                       !v6_rescue_start(&rescue_vm,&v6_rescuered_program,&v6_skipred_program,
#ifdef V6_TOWER_RESCUE_SKIP
                           1
#else
                           0
#endif
                           )) diag.error=9;
                }
                v6_rescue_tick(&rescue_vm,&hallway_story,&rescue_signals);
                if(rescue_vm.error) diag.error=10;
#ifdef V6_TOWER_AUDIO
                if(rescue_vm.cues!=cue_consumed) {
                    V6AudioPlan plan;V6AudioSample sample;
                    sample.address=(ULONG)(cue_chip+(rescue_vm.cue_speaker?CUE_CREW6_BYTES:0));
                    sample.bytes=rescue_vm.cue_speaker?CUE_CREW1_BYTES:CUE_CREW6_BYTES;
                    sample.period=CUE_PERIOD;sample.volume=64;
                    if(!v6_audio_request(&cue_audio,&sample,&plan)) { cue_audio.error=1;diag.error=11; }
                    else audio_apply(&plan);
                    cue_consumed=rescue_vm.cues;audio_record();
                }
#endif
                companion.mood=rescue_vm.mood;companion.following=rescue_vm.following;
                companion_record();
                rescue_record();
#endif
                record_trigger();
#endif
#else
                v6_tower_session_play_world(&session,&player_room,input,&world);
#endif
                record_world();
#else
                v6_tower_session_play(&session,&player_room,input,0,0);
#endif
                player_frame=v6_collision_frame(&player_animation,&session.player,
                    session.player.ground,session.player.roof,session.death_timer);
#else
                if(diag.logic_ticks==60) v6_tower_session_die(&session);
                v6_tower_session_tick(&session,1,0,0);
#endif
                diag.recovery_calls=session.life_calls;
                diag.recovery_life=session.life_timer;diag.recovery_delay=session.resume_delay;
                diag.recovery_seek_frames=session.camera.seek_frames;
                if(camera_trace.count<CAMERA_TRACE_TICKS) {
                    volatile int32_t *r=camera_trace.players[camera_trace.count];
                    r[0]=session.player.x;r[1]=session.player.y;r[2]=session.player.vx;r[3]=session.player.vy;
                    r[4]=session.player.gravity;r[5]=session.player.dir;r[6]=session.death_timer;
                    r[7]=session.invisible;r[8]=session.deaths;r[9]=session.respawns;
                    r[10]=session.player.old_x;r[11]=session.player.old_y;
                }
                trace_camera(&session.camera,session.life_timer,session.resume_delay);
                /* Trace owns real player state; no externally supplied life count. */
                controller.y=session.camera.y;controller.mode=session.camera.mode;
#else
                v6_tower_camera_tick(&controller,0,0,1,0,0);
#endif
#endif
#ifdef V6_TOWER_TELE_MENU
tele_menu_paused:
#endif
                diag.camera_mode=controller.mode;
                ++diag.logic_ticks;
#ifdef V6_TOWER_ROUTE
                if(route_loading || diag.error) break;
#endif
            }
            camera=controller.y;diag.camera=camera;diag.logic_remainder=elapsed;
        }
#else
        if(V6_TOWER_HOLD<0) {
            if(camera==CAMERA_MAX) direction=-1;
            if(camera==CAMERA_MIN) direction=1;
            if(direction>0) {
                if(camera<5600 && camera+V6_TOWER_STEP>=5600) ++diag.forward_wraps;
                camera+=V6_TOWER_STEP;
                if(camera>CAMERA_MAX) camera=CAMERA_MAX;
            } else {
                if(camera>=5600 && camera-V6_TOWER_STEP<5600) ++diag.reverse_wraps;
                camera=camera<CAMERA_MIN+V6_TOWER_STEP?CAMERA_MIN:camera-V6_TOWER_STEP;
            }
        }
#endif
#ifdef V6_TOWER_PLAY
        logic_work=clock_lines()-start;
#endif
#ifdef V6_TOWER_ROUTE
        publish=1;drawn=0;
        if(route_loading) {
            unsigned fg_rows,bg_rows=0;
            /* A crossing also pays for physics and bank rebinding. Keep its
             * fill small; paused frames have room for twice the row work. */
            unsigned budget=route_budget;
            int fg=v6_tower_draw_pair_prepare_budget(&draw[back],rings[back],&stream,camera>>3,
                FG_OFFSETS,FG_PAIRS,FG_WORDS,FG_COUNT,2,&fg_rows,budget);
            int bg=1;
            bg=v6_tower_draw_pair_prepare_budget(&background_draw[back],rings[back]+V6_TOWER_RING_BYTES,
                    &background_stream,background_camera(camera)>>3,tower_background_pair_offsets,tower_background_pairs,
                    TOWER_BACKGROUND_PAIR_WORDS,TOWER_TILE_COUNT,1,&bg_rows,budget);
            drawn=fg_rows+bg_rows;++route_diag.loading_frames;
#ifdef V6_TOWER_BUILDING
            /* Leave room for the six-channel DMA copy on final cold fields. */
            route_budget=route.rooms[route.index].teleporter?1:2;
#else
            route_budget=2;
#endif
            if(!fg || !bg) { diag.error=8;break; }
            publish=fg==1 && bg==1;
            if(publish) {
                unsigned final_rows;
                if(!prepare(rings[back],lists[back],back,camera,&final_rows)) { diag.error=2;break; }
                drawn+=final_rows;--route_loading;
            }
        } else
#endif
        if(!prepare(rings[back],lists[back],back,camera,&drawn)) { diag.error=2;break; }
        if(drawn>diag.max_rows) diag.max_rows=drawn;
        work=clock_lines()-start;
#ifdef V6_TOWER_PLAY
        render_work=work-logic_work;
        if(logic_work>profile.max_logic) profile.max_logic=logic_work;
        if(render_work>profile.max_render) profile.max_render=render_work;
        if(work>diag.max_work_lines) {
            profile.peak_logic=logic_work;profile.peak_render=render_work;
            profile.peak_tick=diag.logic_ticks;profile.peak_rows=drawn;
        }
#endif
        if(work>diag.max_work_lines) diag.max_work_lines=work;
        blank();
        if(frames-previous>1) diag.missed+=frames-previous-1;
        previous=frames;
        /* Completed inactive list becomes next frame's list before vertical restart. */
#ifdef V6_TOWER_ROUTE
        if(publish)
#endif
        { hw->cop1lc=(ULONG)lists[back];back^=1; }
        diag.camera=camera;diag.frames=frames;
        if(camera<diag.visited_min) diag.visited_min=camera;
        if(camera>diag.visited_max) diag.visited_max=camera;
    }
#ifdef V6_TOWER_UI_SAVE
    if(!ui_os_paused) {
#endif
#ifdef V6_TOWER_AUDIO
    { V6AudioPlan plan;v6_audio_stop(&cue_audio,&plan);audio_apply(&plan);audio_record(); }
#endif
    Disable();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
    __asm volatile("move.l %0,0x6c.w"::"r"(old_irq):"memory");
    hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
    hw->adkcon=adk|0x8000;hw->dmacon=dma|0x8000;hw->intena=ints|0x8000;
    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=2;
#ifdef V6_TOWER_UI_SAVE
    }
#endif
    FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return diag.error?20:0;
}
#if defined(V6_TOWER_PERSIST) || defined(V6_TOWER_UI_SAVE) || defined(V6_BUILDING_SAVE)
static int checkpoint_bank_valid(const V6CheckpointSave *c)
{
    return v6_campaign_route_checkpoint_valid(c,tower_route_rooms,
        sizeof(tower_route_rooms)/sizeof(tower_route_rooms[0]));
}
#endif
int __attribute__((used,section(".text.unlikely"))) _start(void) {
#ifdef V6_BUILDING_SAVE
    int result,a,k;V6HallwayStory story;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    a=v6_campaign_dos.exists(save_name);k=v6_campaign_dos.exists(save_backup);
    result=V6_SAVE_OK;building_stage=(a || k)?2:1;building_save_diag.values[0]=building_stage;
    if(a<0 || k<0)result=V6_SAVE_IO;
    if(!result && building_stage==2) {
        result=v6_campaign_read(&v6_campaign_dos,a?save_name:save_backup,&building_saved,&story);
        if(!result && (!checkpoint_bank_valid(&building_saved) || building_saved.room_x!=111 || building_saved.room_y!=104 || story.companion || story.rescue_triggered || story.red_rescued))result=V6_SAVE_CORRUPT;
        if(!result && a && k) {
            V6CheckpointSave backup;V6HallwayStory bs;
            result=v6_campaign_read(&v6_campaign_dos,save_backup,&backup,&bs);
            if(!result && (!checkpoint_bank_valid(&backup) || backup.room_x!=111 || backup.room_y!=104 || bs.companion || bs.rescue_triggered || bs.red_rescued))result=V6_SAVE_CORRUPT;
        }
        if(!result)result=v6_campaign_recover(&v6_campaign_dos,save_name,save_temp,save_backup,&building_saved,&story);
        if(!result && !v6_campaign_dos_flush("DF1:"))result=V6_SAVE_IO;
    }
    if(result) {building_save_diag.values[1]=result;building_save_diag.values[2]=1;CloseLibrary((struct Library *)DOSBase);return 20;}
    result=run();
    if(!result && building_stage==1) {
        if(!checkpoint_bank_valid(&world.save))result=V6_SAVE_INVALID;
        else result=v6_campaign_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story);
        if(!v6_campaign_dos_flush("DF1:"))result=V6_SAVE_IO;
    }
    building_save_diag.values[1]=result;building_save_diag.values[3]=world.save.x;
    building_save_diag.values[4]=world.save.y;building_save_diag.values[5]=world.save.dir;
    building_save_diag.values[6]=world.save.room_x;building_save_diag.values[7]=world.save.room_y;
    building_save_diag.values[8]=world.save.id;building_save_diag.values[11]=building_stage==2;
    CloseLibrary((struct Library *)DOSBase);return result?20:0;
#elif defined(V6_TOWER_PERSIST)
    int result,exists,temp_exists,backup_exists;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    exists=v6_campaign_dos.exists(save_name);
    temp_exists=v6_campaign_dos.exists(save_temp);backup_exists=v6_campaign_dos.exists(save_backup);
    if(exists<0 || temp_exists<0 || backup_exists<0){persist_diag.values[1]=V6_SAVE_IO;CloseLibrary((struct Library *)DOSBase);return 20;}
    persist_stage=(exists || backup_exists || temp_exists)?2:1;persist_diag.values[0]=persist_stage;
    if(persist_stage==2) {
        result=v6_campaign_read(&v6_campaign_dos,exists?save_name:save_backup,&persisted_checkpoint,&persisted_story);
        persist_diag.values[1]=result;
        if(result!=V6_SAVE_OK || !checkpoint_bank_valid(&persisted_checkpoint)) {
            persist_diag.values[3]=1;CloseLibrary((struct Library *)DOSBase);return 20;
        }
        /* Validate source semantics before recovery can remove either record. */
        if(exists && backup_exists) {
            V6CheckpointSave c;V6HallwayStory s;
            result=v6_campaign_read(&v6_campaign_dos,save_backup,&c,&s);
            if(result || !checkpoint_bank_valid(&c)) {
                persist_diag.values[1]=result;persist_diag.values[3]=1;
                CloseLibrary((struct Library *)DOSBase);return 20;
            }
        }
        result=v6_campaign_recover(&v6_campaign_dos,save_name,save_temp,save_backup,&persisted_checkpoint,&persisted_story);
        persist_diag.values[1]=result;
        if(result){persist_diag.values[3]=1;CloseLibrary((struct Library *)DOSBase);return 20;}
    }
    result=run();
    if(!result && !rescue_vm.active && checkpoint_bank_valid(&world.save)) {
        if(persist_stage==1) {
            result=v6_campaign_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story);
#ifdef V6_TOWER_REPLACE_TEST
            if(!result) {
                V6CheckpointSave newer=world.save;newer.dir=0;
#if V6_TOWER_REPLACE_TEST == 1
                result=v6_campaign_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&newer,&hallway_story);
#else
                /* Construct each rename-boundary interruption using real DOS
                 * files, then leave it for a fresh boot to recover. */
                if(!Rename((CONST_STRPTR)save_name,(CONST_STRPTR)save_backup))result=V6_SAVE_IO;
#if V6_TOWER_REPLACE_TEST == 2
                if(!result)result=v6_campaign_write_new(&v6_campaign_dos,save_temp,"DF0:campaign.stage",&newer,&hallway_story);
#elif V6_TOWER_REPLACE_TEST == 3
                if(!result)result=v6_campaign_write_new(&v6_campaign_dos,save_name,save_temp,&newer,&hallway_story);
#else
#error Unsupported replacement fixture
#endif
#endif
            }
#endif
            persist_diag.values[2]=result;
        }
        if(!result)persist_diag.values[5]=1;
    } else {persist_diag.values[3]=1;result=20;}
    persist_diag.values[10]=world.save.id;persist_diag.values[11]=hallway_story.companion;
    persist_diag.values[12]=hallway_story.rescue_triggered;persist_diag.values[13]=hallway_story.red_rescued;
    persist_diag.values[14]=hallway_trigger.requests;persist_diag.values[15]=cue_audio.starts;
    persist_diag.values[16]=companion.visible;persist_diag.values[17]=rescue_vm.following;
    CloseLibrary((struct Library *)DOSBase);return result?20:0;
#elif defined(V6_TOWER_UI_SAVE)
    int result;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    result=run();CloseLibrary((struct Library *)DOSBase);return result;
#else
    return run();
#endif
}
