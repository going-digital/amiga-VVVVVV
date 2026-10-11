#if defined(V6_TOWER_COLLECTION_SAVE) && (!defined(V6_TOWER_PRIZE) || !defined(V6_STATION_MENU))
#error Collection saves require the Prize route and station menu
#endif
#if defined(V6_STATION_TRAVEL_CAPTURE) && (!defined(V6_STATION_MENU) || !defined(V6_TELE_MENU_CAPTURE) || defined(V6_STATION_CAPTURE))
#error Station travel capture requires the interactive station menu fixture
#endif
#if defined(V6_STATION_MENU) && (!defined(V6_TOWER_STATION) || !defined(V6_TOWER_MENU_TRAVEL) || defined(V6_STATION_SAVE))
#error Station menu requires interactive station travel without the isolated save path
#endif
#if defined(V6_TOWER_STATION) && defined(V6_TOWER_UI_SAVE) && !defined(V6_STATION_MENU)
#error Station UI saves require the station menu path
#endif
#if defined(V6_STATION_SAVE) && !defined(V6_TOWER_STATION)
#error Station save requires the station room slice
#endif
#if defined(V6_STATION_COMPANION_CAPTURE) && (!defined(V6_STATION_CAPTURE) || !defined(V6_TOWER_STATION) || defined(V6_STATION_SAVE))
#error Companion capture requires the isolated station capture without saves
#endif
#ifdef V6_TOWER_STATION
#if !defined(V6_TOWER_BUILDING) || !defined(V6_TOWER_ENERGIZE) || !defined(V6_TOWER_RESCUE) || !defined(V6_TOWER_TRIGGER_REPLAY)
#error Station slice requires room/rescue cores
#endif
#endif
/* Standalone PAL tower display experiment; left mouse exits. */
#include <proto/exec.h>
#ifdef V6_TOWER_MENU_TRAVEL
#if !defined(V6_TOWER_BUILDING) || !defined(V6_TOWER_UI_SAVE) || !defined(V6_TOWER_ENERGIZE) || !defined(V6_TOWER_ARRIVAL) || !defined(V6_TOWER_ROUNDTRIP) || defined(V6_ENERGIZE_CAPTURE)
#error Menu travel requires interactive Building/Energize and normal travel cores
#endif
#endif
#ifdef V6_MENU_EXPLORED_CAPTURE
#if !defined(V6_TOWER_MENU_TRAVEL) || !defined(V6_TELE_MENU_CAPTURE)
#error Exploration seeding is only for the bounded physical menu capture
#endif
#endif
#ifdef V6_MENU_EFFECT_HOLD
#if !defined(V6_TOWER_MENU_TRAVEL) || !defined(V6_TELE_MENU_CAPTURE) || !defined(V6_TOWER_SHAKE) || V6_MENU_EFFECT_HOLD < 1 || V6_MENU_EFFECT_HOLD > 64
#error Effect pixel hold is only for the bounded interactive shake capture
#endif
#endif
#if defined(V6_MENU_SHAKE_REFERENCE) && !defined(V6_MENU_EFFECT_HOLD)
#error Unshifted effect reference requires the pixel hold fixture
#endif
#ifdef V6_TOWER_ARRIVAL_SAVE
#if !defined(V6_BUILDING_SAVE) || !defined(V6_TOWER_ROUNDTRIP) || !defined(V6_TOWER_ENERGIZE) || !defined(V6_ENERGIZE_CAPTURE) || !defined(V6_TOWER_ARRIVAL)
#error Arrival save requires the Building save and staged roundtrip fixtures
#endif
#if V6_ENERGIZE_CAPTURE_TICKS == 64
#define V6_SAVE_ROOM_X 110
#define V6_SAVE_ROOM_Y 105
#elif V6_ENERGIZE_CAPTURE_TICKS == 128
#define V6_SAVE_ROOM_X 111
#define V6_SAVE_ROOM_Y 104
#else
#error Arrival save must stop at a completed arrival (64 or 128 ticks)
#endif
#define V6_SAVE_TICKS V6_ENERGIZE_CAPTURE_TICKS
#define V6_SAVE_DIAG_VALUES 20
#else
#define V6_SAVE_ROOM_X 111
#define V6_SAVE_ROOM_Y 104
#define V6_SAVE_TICKS 128
#define V6_SAVE_DIAG_VALUES 12
#endif
#ifdef V6_TOWER_ARRIVAL_SAVE_EARLY
#ifndef V6_TOWER_ARRIVAL_SAVE
#error Early save rejection is only an arrival persistence test
#endif
#define V6_SAVE_STOP_TICKS 23
#else
#define V6_SAVE_STOP_TICKS V6_SAVE_TICKS
#endif
#if defined(V6_TOWER_PERSIST) || defined(V6_TOWER_UI_SAVE) || defined(V6_BUILDING_SAVE) || defined(V6_STATION_SAVE)
#include <proto/dos.h>
#include "campaign_dos.h"
#include "campaign_route.h"
struct DosLibrary *DOSBase;
#ifdef V6_STATION_SAVE
static V6CheckpointSave station_saved;
static V6HallwayStory station_saved_red;
static V6StationStory station_saved_yellow;
static V6Exploration station_exploration;
static unsigned station_stage;
static volatile struct {ULONG magic,version,values[18];} station_save_diag={0x56365350,1,{0}};
static int checkpoint_bank_valid(const V6CheckpointSave *);
#endif
#ifdef V6_BUILDING_SAVE
static V6CheckpointSave building_saved;
static unsigned building_stage;
static volatile struct {ULONG magic,version,values[V6_SAVE_DIAG_VALUES];} building_save_diag={0x56364253,1,{0}};
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
#include "teleporter_admission.h"
static V6TeleporterMenu tele_menu;
static unsigned tele_menu_fire;
static V6Exploration tele_exploration;
static V6TeleporterDestination tele_destinations[2];
static unsigned tele_destination_count;
#ifdef V6_TOWER_MENU_TRAVEL
static V6Exploration ui_loaded_exploration;
#ifdef V6_STATION_MENU
static V6StationStory ui_loaded_yellow;
#ifdef V6_TOWER_COLLECTION_SAVE
static V6Collect ui_loaded_collection;
#endif
#endif
static const V6TeleporterDestination tele_residents[2]={{111,104},{110,105}};
static V6TeleporterDestination menu_target;
static unsigned menu_save_pending,menu_travel_active,menu_exit_pending;
static volatile struct {ULONG magic,version,count;LONG snapshot[23],records[128][36];}
    menu_travel_trace={0x56364d54,1,0,{0},{{0}}};
static volatile struct {ULONG magic,version,values[6];}
    menu_effect_diag={0x56364d45,1,{0}};
#else
static const V6TeleporterDestination tele_residents[1]={{111,104}};
#endif
static int tele_note_room(int x,int y)
{
    return v6_exploration_visit(&tele_exploration,x,y) &&
        v6_teleporter_admit(&tele_exploration,tele_residents,
            sizeof(tele_residents)/sizeof(tele_residents[0]),tele_destinations,2,&tele_destination_count);
}
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
#ifdef V6_TOWER_MENU_TRAVEL
#define UI_MESSAGE_COUNT 7
#else
#define UI_MESSAGE_COUNT 6
#endif
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
#ifdef V6_TOWER_MENU_TRAVEL
    {4,1,2,{"Save/load is busy","Wait for travel or close the menu"}}
#else
    {4,1,2,{"Finish loading or close the menu","Then try save/load again"}}
#endif
#else
    {4,1,2,{"Finish dialogue or loading first","Then try save/load again"}}
#endif
#ifdef V6_TOWER_TELE_MENU
    ,{5,1,3,{"Building Apport","Left/right: select; fire: confirm","Down + fire: cancel"}}
#ifdef V6_TOWER_MENU_TRAVEL
    ,{6,1,3,{"Energize","Left/right: select; fire: confirm","Down + fire: cancel"}}
#endif
#endif
};
static volatile struct { ULONG magic,version,count,capacity,records[8][10]; } ui_trace={0x56364954,1,0,8,{{0}}};
#ifdef V6_TOWER_UI_REPLAY
static unsigned ui_test_phase,ui_test_tick;
#endif
static int checkpoint_bank_valid(const V6CheckpointSave *);
#else
#ifdef V6_STATION_SAVE
static const char save_name[]="DF1:station.v6cs";
static const char save_temp[]="DF1:station.tmp";
static const char save_backup[]="DF1:station.bak";
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
#ifdef V6_TOWER_STATION
#include "station_rescue_programs.h"
static V6StationStory station_story;
static V6StationTrigger station_trigger;
#define v6_rescuered_program v6_rescueyellow_program
#define v6_skipred_program v6_skipyellow_program
#define v6_rescue_speeches v6_station_rescue_speeches
#define V6_RESCUE_SPEECHES V6_STATION_RESCUE_SPEECHES
#else
#include "rescue_programs.h"
#endif
#include "dialogue.h"
#include "dialogue_font.h"
#include "companion.h"
#ifdef V6_TOWER_AUDIO
#include "audio.h"
#ifdef V6_TOWER_STATION
#include "station_cue_samples.h"
#else
#include "cue_samples.h"
#endif
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
#ifdef V6_STATION_MENU
static volatile struct {ULONG magic,version,count,bytes;LONG snapshot[sizeof(V6Companion)/4],records[64][14];}
    station_travel_trace={0x56365943,1,0,sizeof(V6Companion),{0},{{0}}};
#endif

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
#ifdef V6_STATION_MENU
    if(station_travel_trace.count<64 && station_travel_trace.count<menu_travel_trace.count) {
        for(i=0;i<14;++i)station_travel_trace.records[station_travel_trace.count][i]=values[i];
        ++station_travel_trace.count;
    }
#endif
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
        rescue_vm.speech?rescue_vm.speech->index+1:0,
#ifdef V6_TOWER_STATION
        station_story.yellow_rescued,station_story.companion,
#else
        hallway_story.red_rescued,hallway_story.companion,
#endif
        rescue_bars,rescue_fade};
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
#ifdef V6_TOWER_MUSIC_TRACE
#include "music_control.h"
static V6MusicControl route_music;
typedef char music_state_trace_size[(sizeof(V6MusicControl)==64 && sizeof(V6MusicPlan)==52)?1:-1];
static unsigned music_entry_pending;
static volatile struct {ULONG magic,version,count,entries;int32_t records[128][32];}
    music_trace={0x56364d55,1,0,0,{{0}}};
static int music_trace_enter(void)
{
    V6MusicPlan p;
    if(!v6_music_enter_room(&route_music,route.rooms[route.index].x,route.rooms[route.index].y,
       0,0,0,0,0,&p))return 0;
    ++music_trace.entries;music_entry_pending=1;return 1;
}
static int music_trace_tick(void)
{
    V6MusicPlan p;unsigned i;volatile int32_t *r;
    const UBYTE *src;volatile UBYTE *dst;
    /* Volatile byte stores avoid freestanding aggregate-init memset calls. */
    dst=(volatile UBYTE *)&p;for(i=0;i<sizeof(p);++i)dst[i]=0;
    if(!v6_music_tick(&route_music,34,&p) || music_trace.count>=128)return 0;
    r=music_trace.records[music_trace.count];
    src=(const UBYTE *)&route_music;dst=(volatile UBYTE *)r;
    for(i=0;i<sizeof(route_music);++i)dst[i]=src[i];
    src=(const UBYTE *)&p;dst=(volatile UBYTE *)(r+16);
    for(i=0;i<sizeof(p);++i)dst[i]=src[i];
    r[29]=route.rooms[route.index].x;r[30]=route.rooms[route.index].y;r[31]=music_entry_pending;
    music_entry_pending=0;++music_trace.count;return 1;
}
#endif
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
#if defined(V6_TOWER_RESCUE) && !defined(V6_TOWER_STATION)
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
#ifdef V6_TOWER_STATION
#include "frown_assets.h"
#include "shenanigan_assets.h"
#ifdef V6_TOWER_SHENANIGAN
#include "platform.h"
static V6Terrain shenanigan_terrain;
static V6Platform station_conveyors[2];
static V6Block station_conveyor_blocks[2];
static unsigned station_conveyor_phase,station_conveyor_delay;
#ifdef V6_SHENANIGAN_CAPTURE
static volatile struct {ULONG magic,version,count;LONG records[160][14];}
    shenanigan_trace={0x5636534e,1,0,{{0}}};
static unsigned shenanigan_ui_stage;
#endif
#endif
#ifdef V6_TOWER_PRIZE
#if !defined(V6_TOWER_STATION) || !defined(V6_TOWER_SHENANIGAN)
#error Prize route requires the resident station and Shenanigan rooms
#endif
#include "prize.h"
#include "prize_assets.h"
static V6Terrain prize_terrain;
static V6Prize station_prize;
static V6Collect station_collected;
#ifdef V6_TOWER_PICKUP_SCREEN
#ifndef V6_TOWER_UI_SAVE
#error Pickup screen requires the caption/menu allocation
#endif
#include "trinket_screen.h"
#include "pickup_draw.h"
#include "pickup_copper.h"
#include "pickup_assets.h"
static V6TrinketScreen pickup_screen;
typedef char PickupActorWordSize[(sizeof(V6Prize)%sizeof(ULONG))==0?1:-1];
static V6PickupDraw pickup_draw;
static UBYTE *pickup_banks,*pickup_zero;
static UWORD pickup_mask[V6_PICKUP_PLANE_BYTES/2] __attribute__((aligned(4)));
static UWORD pickup_ink[V6_PICKUP_PLANE_BYTES/2] __attribute__((aligned(4)));
static unsigned pickup_rows[2],pickup_bar_rows[2];
static unsigned pickup_bar_room[2],pickup_bar_camera[2];
static unsigned pickup_bar_position[2],pickup_render_bars;
static volatile struct {ULONG magic,version,count,records[96][7];}
    pickup_interpolation={0x56365049,1,0,{{0}}};
static UWORD pickup_bar_masks[2][2][20];
static UWORD pickup_copper_cache[2][V6_PICKUP_COPPER_WORDS];
static unsigned pickup_copper_key[2],pickup_copper_words[2];
static const UWORD pickup_blank[20] __attribute__((aligned(4)))={0};
static ULONG pickup_world_hash,pickup_actor_snapshot[sizeof(V6Prize)/sizeof(ULONG)];
static unsigned pickup_hash_valid;
static volatile struct {ULONG magic,version,count,values[8],records[256][5];}
    pickup_presentation={0x56365042,1,0,{0},{{0}}};
static unsigned pickup_held,pickup_pause_ticks;
static volatile struct {ULONG magic,version,values[12];}
    pickup_diag={0x56365053,1,{0}};
#endif
static volatile struct {ULONG magic,version,room_index,pickups,visible;UBYTE bits[16];}
    collection_diag={0x56364342,1,0,0,0,{0}};
static unsigned prize_pickups,prize_patches,prize_sounds;
static unsigned prize_audio_pending;
static int prize_gate_drawn[2][3];
static unsigned prize_drawn_patch[2];
#ifdef V6_PRIZE_ROUTE_CAPTURE
static volatile struct {ULONG magic,version,count,records[128][8];}
    pickup_frame_trace={0x56365058,1,0,{{0}}};
static volatile struct {ULONG magic,version,count;LONG records[224][24];}
    prize_route_trace={0x56365052,1,0,{{0}}};
static unsigned prize_ui_stage,prize_pickup_release;
#endif
#define PRIZE_FG(value,fallback) (route.index==8?(value):(fallback))
#else
#define PRIZE_FG(value,fallback) (fallback)
#endif
static V6Terrain frown_terrain;
#define FG_OFFSETS PRIZE_FG(prize_pair_offsets, (route.index==7?shenanigan_pair_offsets:route.index==6?frown_pair_offsets:route.index==5?energize_pair_offsets:tower_pair_offsets))
#define FG_PAIRS PRIZE_FG(prize_pairs, (route.index==7?shenanigan_pairs:route.index==6?frown_pairs:route.index==5?energize_pairs:tower_pairs))
#define FG_WORDS PRIZE_FG(PRIZE_PAIR_WORDS, (route.index==7?SHENANIGAN_PAIR_WORDS:route.index==6?FROWN_PAIR_WORDS:route.index==5?ENERGIZE_PAIR_WORDS:TOWER_PAIR_WORDS))
#define FG_COUNT PRIZE_FG(PRIZE_TILE_COUNT, (route.index==7?SHENANIGAN_TILE_COUNT:route.index==6?FROWN_TILE_COUNT:route.index==5?ENERGIZE_TILE_COUNT:TOWER_TILE_COUNT))
#define FG_PALETTE PRIZE_FG(prize_palette, (route.index==7?shenanigan_palette:route.index==6?frown_palette:route.index==5?energize_palette:tower_palette))
#else
#define FG_OFFSETS (route.index==5?energize_pair_offsets:tower_pair_offsets)
#define FG_PAIRS (route.index==5?energize_pairs:tower_pairs)
#define FG_WORDS (route.index==5?ENERGIZE_PAIR_WORDS:TOWER_PAIR_WORDS)
#define FG_COUNT (route.index==5?ENERGIZE_TILE_COUNT:TOWER_TILE_COUNT)
#define FG_PALETTE (route.index==5?energize_palette:tower_palette)
#endif
#else
#define FG_OFFSETS tower_pair_offsets
#define FG_PAIRS tower_pairs
#define FG_WORDS TOWER_PAIR_WORDS
#define FG_COUNT TOWER_TILE_COUNT
#define FG_PALETTE tower_palette
#endif
#ifdef V6_TOWER_SHENANIGAN
static int station_conveyor_tick(V6TowerRoute *r,void *context)
{
    V6PlatformPush push;
    (void)context;
#ifdef V6_TOWER_PRIZE
    if(r->index==8) {
        v6_prize_platform(&station_prize,&r->room,&r->session->player,
                         r->session->life_timer,r->session->motion.pending_y);
        return 1;
    }
#endif
    if(r->index!=7)return 1;
    push.pending_y=r->session->motion.pending_y;push.visual_ground=push.visual_roof=0;
    v6_platform_transport(&r->session->player,&r->room,station_conveyors,2,
        station_conveyor_blocks,2,V6_PLATFORMS_HORIZONTAL,r->session->life_timer,&push);
    if(!station_conveyor_delay) {station_conveyor_phase=(station_conveyor_phase+1)&3;station_conveyor_delay=3;}
    --station_conveyor_delay;
    return 1;
}
#endif
#ifdef V6_TOWER_PRIZE
static int prize_events(V6TowerRoute *r,unsigned events)
{
    if(events&V6_PRIZE_FULL)return 0;
    if(events&V6_PRIZE_PICKUP) {
        ++prize_pickups;prize_audio_pending|=8;
#ifdef V6_TOWER_PICKUP_SCREEN
        /* No tracker is playing yet; only the source effect is requested. */
        v6_trinket_screen_begin(&pickup_screen,&station_collected,0);
        /* The candidate's sole pending trinket is known before gameplay.
         * Prepare its template at boot/load while the OS owns the display. */
        if(pickup_draw.count!=(unsigned)pickup_screen.count)return 0;
        pickup_rows[0]=pickup_rows[1]=0;
        pickup_hash_valid=0;
        pickup_held=r->session->player.held;pickup_pause_ticks=0;
        ++pickup_diag.values[0];
        pickup_diag.values[6]=r->session->player.flips;
#endif
    }
    if(events&V6_PRIZE_SOUND){++prize_sounds;prize_audio_pending|=4;}
    if(events&V6_PRIZE_TILE) {
        int changed=v6_terrain_set_tile(&prize_terrain,prize_tiles,0,0,18,9,59);
        if(changed<0)return 0;
        if(changed)++prize_patches;
    }
    (void)r;
    return 1;
}
static int prize_entities(V6TowerRoute *r,void *context)
{
    (void)context;
    return r->index!=8 || prize_events(r,v6_prize_entities(&station_prize,&r->room,&station_collected));
}
static int prize_contacts(V6TowerRoute *r,void *context)
{
    (void)context;
    if(r->index==8)v6_prize_collide(&station_prize,&r->session->player);
    return 1;
}
static int prize_death(V6TowerRoute *r,void *context)
{
    (void)context;
    return r->index!=8 || prize_events(r,v6_prize_death(&station_prize,&r->room));
}
static int station_route_step(V6TowerRoute *r,unsigned input,V6TowerRoutePhase phase,void *context)
{
    V6TowerRouteHooks hooks={phase,prize_entities,prize_contacts,prize_death};
    return v6_tower_route_step_hooks(r,input,&hooks,context);
}
#else
#define station_route_step v6_tower_route_step_phase
#endif
#ifdef V6_TOWER_ARRIVAL
#if !defined(V6_ENERGIZE_CAPTURE) && !defined(V6_TOWER_MENU_TRAVEL)
#error Arrival fixture requires Energize capture
#endif
#include "teleporter_arrival.h"
static V6TeleporterArrival arrival;
static int arrival_flash;
static volatile struct {ULONG magic,version,count,records[128][14];}
    arrival_trace={0x56364152,1,0,{{0}}};
#ifdef V6_TOWER_ROUNDTRIP
#include "teleporter_departure.h"
#include "teleporter_colour.h"
#ifdef V6_TOWER_SHAKE
#include "screen_shake_dma.h"
#include "screen_shake_display.h"
#if !defined(V6_TOWER_ROUNDTRIP) || (defined(V6_TOWER_RESCUE) && !defined(V6_STATION_MENU)) || (defined(V6_TOWER_UI_SAVE) && !defined(V6_TOWER_MENU_TRAVEL))
#error Shake supports the staged roundtrip or interactive normal teleporter travel
#endif
static V6ScreenShake shake;
static V6ScreenShakePlan shake_plan;
static ULONG shake_random=19;
static int shake_timer;
static UBYTE *shake_mask;
static unsigned shake_heads[2];
static struct { ULONG magic,version,count; LONG records[128][3]; } shake_trace={0x56365348,1,0,{{0}}};
#ifdef V6_TOWER_MENU_TRAVEL
static volatile struct {ULONG magic,version,count,seed;LONG records[64][3];}
    menu_shake_trace={0x56364d48,1,0,0,{{0}}};
#endif
#endif
#ifdef V6_TOWER_TRAVEL_AUDIO
#include "paula_voice.h"
#include "audio_policy.h"
#ifndef V6_TRAVEL_SFX_MASK
#define V6_TRAVEL_SFX_MASK 15
#endif
#if defined(V6_TOWER_AUDIO) && (V6_TRAVEL_SFX_MASK & 3)
#error Travel effects must reserve dialogue channels zero and one
#endif
static unsigned travel_priority[4],travel_started[4],travel_stolen;
static volatile struct {ULONG magic,version,mask,stolen,violations;}
    travel_policy_diag={0x56364150,1,V6_TRAVEL_SFX_MASK,0,0};
#include "teleporter_samples.h"
#ifdef V6_TOWER_PRIZE
#include "prize_samples.h"
#define PRIZE_AUDIO_BYTES (PRIZE_VANISH_BYTES+PRIZE_TRINKET_BYTES)
static volatile struct {ULONG magic,version,values[5],records[32][4];}
    prize_audio_diag={0x56365041,1,{0},{{0}}};
#else
#define PRIZE_AUDIO_BYTES 0
#endif
static V6PaulaVoice travel_voices[4];
static UBYTE *travel_audio_chip;
static unsigned travel_audio_requests,travel_audio_dropped,travel_audio_peak;
static volatile struct {ULONG magic,version,values[8],records[8][4];}
    travel_audio_diag={0x56365441,1,{0},{{0}}};
static void travel_audio_apply(const V6AudioPlan *p)
{
    unsigned i;
    for(i=0;i<p->count;++i) {
        unsigned reg=p->writes[i].reg,value=p->writes[i].value;
        if((reg==0x96 && (value&15)&~V6_TRAVEL_SFX_MASK) ||
           (reg==0x9c && ((value>>7)&15)&~V6_TRAVEL_SFX_MASK) ||
           (reg>=0xa0 && reg<0xe0 && !(V6_TRAVEL_SFX_MASK&(1U<<((reg-0xa0)/16))))) {
            ++travel_policy_diag.violations;continue;
        }
        *(volatile UWORD *)(0xdff000UL+reg)=(UWORD)value;
    }
}
static void travel_audio_record(void)
{
    unsigned i,active=0,starts=0,completed=0,interrupts=0;
    for(i=0;i<4;++i) {
        active+=travel_voices[i].audio.state!=V6_AUDIO_IDLE;
        starts+=travel_voices[i].audio.starts;completed+=travel_voices[i].audio.completed;
        interrupts+=travel_voices[i].audio.interrupts;
    }
    if(active>travel_audio_peak)travel_audio_peak=active;
    travel_audio_diag.values[0]=active;travel_audio_diag.values[1]=starts;
    travel_audio_diag.values[2]=completed;travel_audio_diag.values[3]=interrupts;
    travel_audio_diag.values[4]=travel_audio_requests;travel_audio_diag.values[5]=travel_audio_dropped;
    travel_audio_diag.values[6]=travel_audio_peak;
    travel_policy_diag.stolen=travel_stolen;
}
#ifdef V6_TOWER_MENU_TRAVEL
static unsigned travel_audio_busy(void)
{
    unsigned i,n=0;
    for(i=0;i<4;++i)if(V6_TRAVEL_SFX_MASK&(1U<<i))n+=travel_voices[i].audio.state!=V6_AUDIO_IDLE;
    return n;
}
#endif
#ifdef V6_TOWER_COEXIST_AUDIO
#include "music_gain.h"
#include "music_registers.h"
static UBYTE *coexist_sample;
static unsigned coexist_fields,coexist_stage;
static volatile struct {ULONG magic,version,count,violations;ULONG records[7][6];}
    coexist_diag={0x56364d58,1,0,0,{{0}}};
static int coexist_apply(const V6AudioPlan *p)
{
    unsigned i;
    for(i=0;i<p->count;++i) {
        unsigned r=p->writes[i].reg,v=p->writes[i].value;
        if((r==0x96 && (v&15)&3) || (r==0x9c && (v&0x780)&0x180) ||
           (r!=0x96 && r!=0x9c && (r<0xc0 || r>0xd8))) {
            ++coexist_diag.violations;return 0;
        }
    }
    for(i=0;i<p->count;++i)*(volatile UWORD *)(0xdff000UL+p->writes[i].reg)=(UWORD)p->writes[i].value;
    return 1;
}
static int coexist_tick(ULONG hardware_frame)
{
    V6AudioPlan raw,guarded,gain;unsigned i,period[4]={161,161,161,241};
    unsigned instruments[4]={64,64,48,32},control=128,mute=0;
    ++coexist_fields;
    /* Raw audio IRQ acknowledgements deliberately include the SFX channels.
     * Run before SFX polling: filtering must preserve their pending IRQs. */
    raw.count=1;raw.writes[0].reg=0x9c;raw.writes[0].value=0x780;
    if(!v6_music_register_plan(&raw,12,3,&guarded) || !coexist_apply(&guarded))return 0;
    if(coexist_fields!=1 && coexist_fields!=80 && coexist_fields!=120 &&
       coexist_fields!=160 && coexist_fields!=200 && coexist_fields!=240 && coexist_fields!=280)return 1;
    if(coexist_fields==1) {
        raw.count=0;
        for(i=0;i<4;++i) {
            unsigned b=0xa0+16*i;ULONG address=(ULONG)coexist_sample;
            raw.writes[raw.count].reg=b;raw.writes[raw.count++].value=address>>16;
            raw.writes[raw.count].reg=b+2;raw.writes[raw.count++].value=address&65535;
            raw.writes[raw.count].reg=b+4;raw.writes[raw.count++].value=32;
            raw.writes[raw.count].reg=b+6;raw.writes[raw.count++].value=period[i];
        }
        if(!v6_music_register_plan(&raw,12,3,&guarded) || !coexist_apply(&guarded))return 0;
    }
    if(coexist_fields==80 || coexist_fields==120 || coexist_fields==160)control=64;
    if(coexist_fields==120)mute=1;
    if(coexist_fields>=240){period[2]=251;period[3]=181;}
    if(coexist_fields==240) {
        raw.count=4;
        for(i=0;i<4;++i){raw.writes[i].reg=0xa6+16*i;raw.writes[i].value=period[i];}
        if(!v6_music_register_plan(&raw,12,3,&guarded) || !coexist_apply(&guarded))return 0;
    }
    if(coexist_fields==280)control=0;
    if(!v6_music_gain_plan(12,3,instruments,control,256,0,mute,&gain) ||
       !v6_music_register_plan(&gain,12,3,&guarded) || !coexist_apply(&guarded))return 0;
    if(coexist_fields==1 || coexist_fields==280) {
        raw.count=1;raw.writes[0].reg=0x96;raw.writes[0].value=coexist_fields==1?0x800f:15;
        if(!v6_music_register_plan(&raw,12,3,&guarded) || !coexist_apply(&guarded))return 0;
    }
    {
        volatile ULONG *r=coexist_diag.records[coexist_stage++];
        r[0]=coexist_fields;r[1]=hardware_frame;r[2]=period[2];r[3]=period[3];
        r[4]=gain.writes[0].value;r[5]=gain.writes[1].value;coexist_diag.count=coexist_stage;
    }
    return 1;
}
#endif

#endif
static V6TeleporterDeparture departure;
static unsigned travel_leg;
static ULONG colour_random=7;
static UWORD teleporter_tint=0xccd,player_tint=0xccd;
static volatile struct {ULONG magic,version,count,records[128][2];}
    colour_trace={0x5636434c,1,0,{{0}}};
static UWORD flashing_colour(int noflashing)
{
    UWORD samples[4];unsigned i;
    for(i=0;i<4;++i) {
        colour_random^=colour_random<<13;colour_random^=colour_random>>17;colour_random^=colour_random<<5;
        samples[i]=(UWORD)(colour_random>>16);
    }
    return v6_teleporter_flash_colour(samples,noflashing);
}
static volatile struct {ULONG magic,version,count,records[128][8];}
    departure_trace={0x56364452,1,0,{{0}}};
#endif
static int arrival_phase(V6TowerRoute *r,void *context)
{
    V6TowerSession *s=r->session;
#ifdef V6_TOWER_SHENANIGAN
    if(!station_conveyor_tick(r,0))return 0;
#endif
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
#if defined(V6_TOWER_SHAKE) && defined(V6_TOWER_UI_SAVE)
#ifdef V6_TOWER_PICKUP_SCREEN
#define LIST_WORDS 384
#else
#define LIST_WORDS 256
#endif
#else
#define LIST_WORDS 192
#endif
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
#define CUE_AUDIO_BYTES CUE_DMA_BYTES
#else
#define CUE_AUDIO_BYTES 0
#endif
#ifdef V6_TOWER_TRAVEL_AUDIO
#ifdef V6_TOWER_COEXIST_AUDIO
#define COEXIST_BYTES 64
#else
#define COEXIST_BYTES 0
#endif
#define TRAVEL_AUDIO_BYTES (TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_AUDIO_BYTES+2)
#else
#define TRAVEL_AUDIO_BYTES 0
#endif
#define AUDIO_DMA_BYTES (CUE_AUDIO_BYTES+TRAVEL_AUDIO_BYTES)
#if defined(V6_TOWER_AUDIO) && !defined(V6_TOWER_TRAVEL_AUDIO)
#define AUDIO_IRQ_MASK (INTF_AUD0|INTF_AUD1)
#else
#define AUDIO_IRQ_MASK (INTF_AUD0|INTF_AUD1|INTF_AUD2|INTF_AUD3)
#endif
#ifdef V6_TOWER_UI_SAVE
#ifdef V6_TOWER_PICKUP_SCREEN
#define PICKUP_DMA_BYTES V6_PICKUP_DMA_BYTES
#else
#define PICKUP_DMA_BYTES 0
#endif
#define UI_DMA_BYTES (UI_MESSAGE_COUNT*V6_DIALOGUE_BYTES+PICKUP_DMA_BYTES)
#else
#define UI_DMA_BYTES 0
#endif
#ifdef V6_TOWER_SHAKE
#define SHAKE_DMA_BYTES V6_SHAKE_MASK_BYTES
#else
#define SHAKE_DMA_BYTES 0
#endif
#define CHIP_BYTES (SHAKE_DMA_BYTES+BUILDING_DMA_BYTES+TELE_DMA_BYTES+UI_DMA_BYTES+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES+AUDIO_DMA_BYTES)
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
#ifdef V6_TOWER_STATION
#ifdef V6_STATION_SAVE
    if(!v6_exploration_visit(&station_exploration,route.rooms[route.index].x,route.rooms[route.index].y))return 0;
#endif
    if(route.index==6){data=frown_display;bytes=sizeof(frown_display);route.room.terrain=&frown_terrain;}
#ifdef V6_TOWER_SHENANIGAN
    if(route.index==7) {
        data=shenanigan_display;bytes=sizeof(shenanigan_display);route.room.terrain=&shenanigan_terrain;
        for(i=0;i<2;++i) {
            if(!v6_conveyor_init(&station_conveyors[i],i?104:16,i?184:104,8+i,4,64))return 0;
            station_conveyor_blocks[i]=(V6Block){i?104:16,i?184:104,32,8,V6_BLOCK,0};
        }
        route.room.blocks=station_conveyor_blocks;route.room.block_count=2;
        station_conveyor_phase=station_conveyor_delay=0;
    }
#endif
#endif
#ifdef V6_TOWER_PRIZE
    if(route.index==8) {
        data=prize_display;bytes=sizeof(prize_display);
        route.room.terrain=&prize_terrain;
        v6_prize_init(&station_prize,&route.room,&station_collected,world.save.id,route.session->player.y);
        for(i=0;i<3;++i)prize_gate_drawn[0][i]=prize_gate_drawn[1][i]=-2;
        prize_drawn_patch[0]=prize_drawn_patch[1]=~prize_patches;
    }
#endif
    /* Resident maps were opened and fully pair-validated before
     * takeover. Rebind only these identical immutable bytes; a repeated
     * 700-entry directory scan would consume the transition frame. */
    stream.data=data;stream.size=bytes;stream.height=route.index<2?700:30;stream.valid=0;
    for(i=0;i<2;++i) {
        v6_tower_draw_reset(&draw[i]);v6_tower_draw_reset(&background_draw[i]);
        prepared_camera[i]=(unsigned)route.session->camera.y;
    }
#ifdef V6_TOWER_TRIGGER_REPLAY
    #ifdef V6_TOWER_STATION
    v6_station_trigger_enter(&station_trigger,route.rooms[route.index].x,route.rooms[route.index].y,&station_story);
    trigger_crew_visible=v6_station_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&station_story);
#else
    v6_hallway_trigger_enter(&hallway_trigger,route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
    trigger_crew_visible=v6_hallway_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
#endif
#endif
#ifdef V6_TOWER_RESCUE
#ifdef V6_TOWER_STATION
    if(station_story.companion==7)
        v6_station_companion_enter(&companion,7,route.rooms[route.index].x,route.rooms[route.index].y,&route.session->player);
    else v6_station_companion_idle(&companion,trigger_crew_visible);
#else
    if(hallway_story.companion==9)
        v6_companion_enter(&companion,9,route.index<2,route.rooms[route.index].x,&route.session->player);
    else v6_companion_idle(&companion,trigger_crew_visible);
#endif
    if(route.index>=2 && route.index<4) route.room.terrain=&hallway_terrain[route.index-2];
#endif
#ifdef V6_TOWER_MUSIC_TRACE
    if(!music_trace_enter())return 0;
#endif
    route_loading=2;route_budget=1;
#ifdef V6_TOWER_TELE_MENU
    if(!tele_note_room(route.rooms[route.index].x,route.rooms[route.index].y))return 0;
#endif
    return 1;
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
#ifdef V6_STATION_COMPANION_CAPTURE
static volatile struct { ULONG magic,version,copies,words; } dma_copy_diag={0x56364443,1,0,0};
static int verify_dma_copy(void)
{
    enum { WORDS=V6_TELEPORTER_CHANNELS*V6_TELEPORTER_DMA_WORDS };
    static UWORD source[WORDS+4] __attribute__((aligned(4)));
    UWORD *dest=AllocMem((WORDS+4)*2,MEMF_CHIP);
    unsigned bank,frame,so,offset,i;int ok=1;
    if(!dest)return 0;
    for(bank=0;bank<2 && ok;++bank)for(frame=1;frame<10 && ok;++frame)
        for(so=1;so<=2 && ok;++so)for(offset=1;offset<=2 && ok;++offset) {
            const UWORD *prepared=bank?energize_prepared[frame]:building_prepared[frame];
            for(i=0;i<WORDS+4;++i){source[i]=0xbeef;dest[i]=0xdead;}
            for(i=0;i<WORDS;++i)source[so+i]=prepared[i];
            v6_teleporter_copy_dma(dest+offset,source+so);
            for(i=0;i<WORDS;++i)if(dest[offset+i]!=prepared[i] || source[so+i]!=prepared[i])ok=0;
            for(i=0;i<offset;++i)if(dest[i]!=0xdead)ok=0;
            for(i=offset+WORDS;i<WORDS+4;++i)if(dest[i]!=0xdead)ok=0;
            if(ok){++dma_copy_diag.copies;dma_copy_diag.words+=WORDS;}
        }
    FreeMem(dest,(WORDS+4)*2);return ok;
}
#endif
#if defined(V6_TOWER_AUDIO) && defined(V6_TOWER_RESCUE)
static void rescue_audio_tick(void)
{
    if(rescue_vm.cues!=cue_consumed) {
        V6AudioPlan plan;V6AudioSample sample;
        sample.address=(ULONG)(cue_chip+(rescue_vm.cue_speaker?CUE_CREW_BYTES:0));
        sample.bytes=rescue_vm.cue_speaker?CUE_CREW1_BYTES:CUE_CREW_BYTES;
        sample.period=CUE_PERIOD;sample.volume=64;
        if(!v6_audio_request(&cue_audio,&sample,&plan)) { cue_audio.error=1;diag.error=11; }
        else audio_apply(&plan);
        cue_consumed=rescue_vm.cues;audio_record();
    }
}

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
#ifdef V6_TOWER_PRIZE
    { unsigned i;
      collection_diag.room_index=route.index;collection_diag.pickups=prize_pickups;
      collection_diag.visible=route.index==8?station_prize.trinket.visible:0;
      for(i=0;i<V6_COLLECT_BYTES;++i)collection_diag.bits[i]=station_collected.bits[i]; }
#endif

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
#ifdef V6_TOWER_SHAKE
    if(shake_timer && !session.noflashing && reg==0x180)value=0;
#endif
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
#ifdef V6_TOWER_PICKUP_SCREEN
static void pickup_draw_tick(void)
{
    v6_pickup_draw_tick(&pickup_draw,pickup_screen.bars);
    if((pickup_draw.bars || pickup_draw.old_bars) && pickup_presentation.count<256) {
        volatile ULONG *r=pickup_presentation.records[pickup_presentation.count++];
        r[0]=pickup_screen.state;r[1]=pickup_draw.bars;r[2]=pickup_draw.old_bars;
        r[3]=pickup_screen.visible;r[4]=diag.logic_ticks;
    }
    pickup_presentation.values[0]=pickup_draw.bars;
    pickup_presentation.values[1]=pickup_draw.old_bars;
    pickup_presentation.values[6]=pickup_draw.count;
    pickup_presentation.values[7]=pickup_draw.length;
}
static int pickup_prepare(UBYTE *ring,unsigned index,unsigned camera)
{
    unsigned n,row,x,b,fo=camera&255,was_warm,position;
    UBYTE *bank;
    pickup_render_bars=v6_pickup_bar_position(&pickup_draw,diag.logic_remainder);
    if(!pickup_banks)return 1;
    bank=pickup_banks+index*V6_PICKUP_BANK_BYTES;
    if(pickup_bar_room[index]!=route.index || pickup_bar_camera[index]!=fo) {
        pickup_bar_room[index]=route.index;pickup_bar_camera[index]=fo;pickup_bar_rows[index]=0;
        pickup_bar_position[index]=0xffffffffUL;
        for(b=0;b<2;++b)for(x=0;x<20;++x)pickup_bar_masks[index][b][x]=0;
    }
    if(route.index!=8 && !pickup_draw.bars && !pickup_screen.visible)return 1;
    if(route_loading && !pickup_draw.bars)return 1;
    /* Warm the unmasked bar strips before pickup. During animation only the
     * words at the moving edge need changing. Prize's rim terrain is static. */
    n=pickup_draw.bars?32:4;
    was_warm=pickup_bar_rows[index]==32;
    while(n-- && pickup_bar_rows[index]<32) {
        row=pickup_bar_rows[index]++;b=row>=16;
        row&=15;
        v6_pickup_compose_row((UWORD *)(bank+(b?V6_PICKUP_BOTTOM_OFFSET:0)+row*40),
            V6_PICKUP_BAR_PLANE_BYTES/2,(const UWORD *)(ring+((fo+(b?224:0)+row)&255)*40),
            V6_TOWER_PLANE_BYTES/2,pickup_blank,pickup_blank);
    }
    position=pickup_draw.bars?pickup_render_bars:25;
    if((pickup_draw.bars || pickup_draw.old_bars) && pickup_interpolation.count<96 &&
       (!pickup_interpolation.count || pickup_interpolation.records[pickup_interpolation.count-1][5]!=pickup_render_bars)) {
        volatile ULONG *r=pickup_interpolation.records[pickup_interpolation.count++];
        r[0]=diag.logic_ticks;r[1]=frames;r[2]=pickup_draw.old_bars;r[3]=pickup_draw.bars;
        r[4]=diag.logic_remainder;r[5]=pickup_render_bars;r[6]=index;
    }
    if(pickup_bar_rows[index]==32 && (was_warm || pickup_draw.bars) &&
       pickup_bar_position[index]!=position)for(b=0;b<2;++b) {
        UWORD mask[20];UBYTE *strip=bank+(b?V6_PICKUP_BOTTOM_OFFSET:0);
        if(!v6_pickup_bar_row((UBYTE *)mask,position,b))return 0;
        for(x=0;x<20;++x)if(mask[x]!=pickup_bar_masks[index][b][x]) {
            unsigned y=(fo+(b?224:0))&255,rows=y>240?256-y:16;
            v6_pickup_bar_column((UWORD *)strip+x,(const UWORD *)(ring+y*40)+x,mask[x],rows);
            if(rows<16)v6_pickup_bar_column((UWORD *)(strip+rows*40)+x,
                (const UWORD *)ring+x,mask[x],16-rows);
            pickup_bar_masks[index][b][x]=mask[x];
        }
        if(b==1)pickup_bar_position[index]=position;
    }
    if(pickup_screen.state && pickup_pause_ticks) {
        /* Two inactive banks are prepared in the source's 15-tick delay.
         * The mask preserves room art in the gap and around both boxes. */
        for(n=0;n<7 && pickup_rows[index]<V6_PICKUP_HEIGHT;++n) {
            row=pickup_rows[index]++;
            v6_pickup_compose_row((UWORD *)(bank+V6_PICKUP_TEXT_OFFSET+row*40),
                V6_PICKUP_PLANE_BYTES/2,(const UWORD *)(ring+((fo+V6_PICKUP_TOP+row)&255)*40),
                V6_TOWER_PLANE_BYTES/2,pickup_mask+row*20,pickup_ink+row*20);
        }
        if(pickup_screen.visible && pickup_rows[index]!=V6_PICKUP_HEIGHT)return 0;
    }
    pickup_presentation.values[2]=pickup_rows[0];pickup_presentation.values[3]=pickup_rows[1];
    pickup_presentation.values[4]=pickup_bar_rows[0];pickup_presentation.values[5]=pickup_bar_rows[1];
    return 1;
}
#endif
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
#ifdef V6_TOWER_SHENANIGAN
    if(route.index==7) {
        unsigned n,row,plane;
        for(n=0;n<2;++n) {
            unsigned frame=n?4+station_conveyor_phase:((4-station_conveyor_phase)&3);
            for(plane=0;plane<2;++plane)for(row=0;row<8;++row) {
                UBYTE bits=shenanigan_treads[frame][plane*8+row];
                UBYTE *dest=ring+plane*V6_TOWER_PLANE_BYTES+(station_conveyors[n].y+row)*40+station_conveyors[n].x/8;
                dest[0]=dest[1]=dest[2]=dest[3]=bits;
                dest[4]=dest[5]=dest[6]=dest[7]=bits;
            }
        }
    }
#endif
#ifdef V6_TOWER_PRIZE
    if(route.index==8) {
        unsigned n,row,plane;
        for(n=0;n<3;++n) {
            int y=n==0?72:n==1?112:128;
            int frame=station_prize.disappearing[n].walking_frame;
            const UBYTE *patch=(n==0 && prize_tiles[9*40+18]==59)?prize_death_tile:0;
            if(station_prize.disappearing[n].invisible || frame<0 || frame>=PRIZE_GATE_FRAMES)frame=-1;
            if(prize_gate_drawn[index][n]==frame && prize_drawn_patch[index]==prize_patches)continue;
            for(plane=0;plane<2;++plane)for(row=0;row<8;++row) {
                UBYTE mask=frame>=0?prize_gate_masks[frame][row]:0;
                UBYTE bits=frame>=0?prize_gate_planes[frame][plane*8+row]:0;
                UBYTE *dest=ring+plane*V6_TOWER_PLANE_BYTES+(y+row)*40+15;
                dest[0]=dest[1]=dest[2]=bits;
                dest[3]=patch?(patch[plane*8+row]&~mask)|bits:bits;
            }
            prize_gate_drawn[index][n]=frame;
        }
        prize_drawn_patch[index]=prize_patches;
    }
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
#ifdef V6_TOWER_SHAKE
    if(arrival_flash && shake_timer && !session.noflashing) {
        /* Flash replaces the whole scene before translation. Its opaque mask
         * already supplies every visible pixel; sprite work is unnecessary.
         * Leave cached animation frames untouched so the next scene restores
         * the current frame normally. Publish terminated inactive sprites. */
        v6_sprites_begin(&player_sprites[index],player_sprites[index].dma);
        for(i=0;i<8;++i) {
            ULONG address=(ULONG)(player_sprites[index].dma+i*V6_SPRITE_WORDS);
            p=move(p,0x120+i*4,address>>16);p=move(p,0x122+i*4,address);
        }
    } else
#endif
    {
    v6_sprites_begin(&player_sprites[index],player_sprites[index].dma);
#ifdef V6_TOWER_BUILDING
    if(route.rooms[route.index].teleporter) {
#ifdef V6_TOWER_SHAKE
        /* This bounded fixture restores only teleporter heads. Its six
         * sprite strips must remain away from clipping edges at every offset. */
        if(route.rooms[route.index].teleporter->x<4 || route.rooms[route.index].teleporter->x>222 ||
           route.rooms[route.index].teleporter->y<4 || route.rooms[route.index].teleporter->y>142)return 0;
#endif
        const UWORD (*prepared)[6*V6_TELEPORTER_DMA_WORDS]=building_prepared;
#ifdef V6_TOWER_ENERGIZE
        if(route.index==5)prepared=energize_prepared;
#endif
        UWORD *bank=building_dma+index*(6*V6_TELEPORTER_DMA_WORDS);
        int frame=building_animation.frame;
        if(frame<1)frame=1;
        if(frame>9)frame=8;
        if(building_frames[index]!=frame) {
            v6_teleporter_copy_dma(bank,prepared[frame]);
            building_frames[index]=frame;
#ifdef V6_TOWER_SHAKE
            shake_heads[index]=0;
#endif
        }
#ifdef V6_TOWER_SHAKE
        /* The fixture teleporter is away from viewport edges. Restore heads
         * after each translation; the bounds check excludes pixel clipping. */
        if(shake_heads[index] || shake_plan.x || shake_plan.y)
            v6_screen_shake_heads(bank,prepared[frame],V6_TELEPORTER_DMA_WORDS,shake_plan.x,shake_plan.y);
        shake_heads[index]=shake_plan.x || shake_plan.y;
#endif
        player_sprites[index].count=6;
        for(i=0;i<3;++i) {
            unsigned tint=route.rooms[route.index].teleporter->tile==1?0x444:0xaaf;
#ifdef V6_TOWER_ROUNDTRIP
            tint=teleporter_tint;
#endif
            p=move(p,0x1a2+i*8,0x111);p=move(p,0x1a4+i*8,tint);p=move(p,0x1a6+i*8,tint);
        }
    }
#endif
    if(!session.invisible)
        v6_sprites_add(&player_sprites[index],tower_player_rows[player_frame],
                      session.player.x,session.player.y-(int)camera,6,
#ifdef V6_TOWER_ROUNDTRIP
                      player_tint);
#else
                      0x6ff);
#endif
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
            companion.mood?
#ifdef V6_TOWER_STATION
            station_crew_rows:
#else
            tower_crew_rows:
#endif
            tower_player_rows[companion.frame>=144?companion.frame-144:companion.frame],
#else
            tower_crew_rows,
#endif
#ifdef V6_TOWER_RESCUE
            companion.body.x,companion.body.y,6,
#ifdef V6_TOWER_STATION
            0xff4
#else
            0xf44
#endif
            )<V6_SPRITE_CLIPPED) return 0;
#else
            264,185,6,0xf44)<V6_SPRITE_CLIPPED) return 0;
#endif
#endif
#ifdef V6_TOWER_PRIZE
    if(route.index==8) {
        if(v6_sprites_add_rect(&player_sprites[index],prize_waiting_rows,
            station_prize.waiting.x,station_prize.waiting.y,0,32,8,0xfff)<V6_SPRITE_CLIPPED)return 0;
        if(station_prize.trinket.visible &&
           v6_sprites_add_rect(&player_sprites[index],tower_player_rows[22],192,128,0,16,16,0xfff)<V6_SPRITE_CLIPPED)return 0;
    }
#endif
    if(player_sprites[index].count>world_diag.values[12]) world_diag.values[12]=player_sprites[index].count;
#endif
    for(i=0;i<8;++i) {
        UWORD *sprite=player_sprites[index].dma+i*V6_SPRITE_WORDS;
        unsigned sprite_words=V6_SPRITE_WORDS;
        ULONG address=(ULONG)sprite;
#ifdef V6_TOWER_BUILDING
        if(route.rooms[route.index].teleporter && i<6) {
            sprite=building_dma+(index*6+i)*V6_TELEPORTER_DMA_WORDS;
            sprite_words=V6_TELEPORTER_DMA_WORDS;address=(ULONG)sprite;
        }
#endif
#ifdef V6_TOWER_SHAKE
        if((shake_plan.x || shake_plan.y) &&
#ifdef V6_TOWER_BUILDING
           !(route.rooms[route.index].teleporter && i<6) &&
#endif
           !v6_screen_shake_sprite(sprite,sprite_words,shake_plan.x,shake_plan.y))return 0;
#else
        (void)sprite_words;
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
    }
#endif
#ifdef V6_TOWER_PICKUP_SCREEN
    if(!pickup_prepare(ring,index,camera))return 0;
    if(pickup_screen.visible || pickup_draw.bars) {
        unsigned key=(camera&255)|((bg_camera&255)<<8)|
            (pickup_screen.visible<<16)|((pickup_render_bars>40)<<17)|
            ((pickup_render_bars>0)<<18);
        /* Bar width changes bitmap words, but its Copper segment changes
         * only when a strip appears/disappears or a ring offset changes. */
        if(!pickup_copper_words[index] || pickup_copper_key[index]!=key) {
            pickup_copper_words[index]=v6_pickup_copper(pickup_copper_cache[index],
                (ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),camera&255,bg_camera&255,
                (ULONG)(pickup_banks+index*V6_PICKUP_BANK_BYTES),(ULONG)pickup_zero,
                pickup_screen.visible,pickup_render_bars);
            pickup_copper_key[index]=key;
        }
        if(!pickup_copper_words[index])return 0;
        for(i=0;i<pickup_copper_words[index];++i)*p++=pickup_copper_cache[index][i];
        return 1;
    }
#endif
#ifdef V6_TOWER_RESCUE
    if(rescue_vm.speech || rescue_bars) {
        unsigned speech=rescue_vm.speech?rescue_vm.speech->index:0;
        unsigned tint=rescue_vm.speech?(rescue_vm.speech->speaker?0x6ff:
#ifdef V6_TOWER_STATION
            0xff4
#else
            0xf44
#endif
            ):0;
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
      ) {
        ULONG caption=(ULONG)(ui_captions+
#ifdef V6_TOWER_TELE_MENU
        (tele_menu.open?
#ifdef V6_TOWER_MENU_TRAVEL
          (tele_destinations[tele_menu.selected].room_x==110?6:5):
#else
          5:
#endif
          ui_status)*V6_DIALOGUE_BYTES
#else
        ui_status*V6_DIALOGUE_BYTES
#endif
        );
#ifdef V6_TOWER_SHAKE
        if(shake_timer && !session.noflashing) {
            p=move(p,0x194,DISPLAY_COLOUR(0x010));p=move(p,0x196,DISPLAY_COLOUR(0x111));
            return v6_screen_shake_caption(p,&shake_plan,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
                (ULONG)shake_mask,camera&255,bg_camera&255,arrival_flash,caption,
                0x6ff,DISPLAY_COLOUR(FG_PALETTE[1]),DISPLAY_COLOUR(FG_PALETTE[3]))!=0;
        }
#endif
        return v6_tower_caption_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
            camera&255,bg_camera&255,caption,0x6ff,DISPLAY_COLOUR(FG_PALETTE[1]),DISPLAY_COLOUR(FG_PALETTE[3]))!=0;
    }
#endif
#ifdef V6_TOWER_SHAKE
    if(shake_timer && !session.noflashing) {
        p=move(p,0x194,DISPLAY_COLOUR(0x010));p=move(p,0x196,DISPLAY_COLOUR(0x111));
        return v6_screen_shake_display(p,&shake_plan,(ULONG)ring,
            (ULONG)(ring+V6_TOWER_RING_BYTES),(ULONG)shake_mask,camera&255,bg_camera&255,arrival_flash)!=0;
    }
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
#ifdef V6_STATION_MENU
    HASH(station_story.companion);HASH(station_story.rescue_triggered);HASH(station_story.yellow_rescued);
    { unsigned i;ULONG map_hash=0;
      for(i=0;i<sizeof(tele_exploration);++i) {
          map_hash=(map_hash<<1)^((const UBYTE *)&tele_exploration)[i];
      }
      HASH(map_hash); }
#endif
#endif
#ifdef V6_TOWER_BUILDING
    HASH(building_teleporter.tile);HASH(building_teleporter.state);
    HASH(route.tele_region.active);HASH(building_animation.frame);
    HASH(building_animation.delay);HASH(building_animation.walking);
#ifdef V6_TOWER_MENU_TRAVEL
    HASH(energize_teleporter.tile);HASH(energize_teleporter.state);HASH(route.index);
    HASH(departure.state);HASH(departure.delay);HASH(departure.flash);HASH(departure.shake);
    HASH(arrival.state);HASH(arrival.delay);HASH(arrival.control);HASH(arrival.flash);HASH(arrival.shake);
    HASH(session.invisible);HASH(session.motion.ax);HASH(session.motion.pending_y);
    HASH(building_random);HASH(colour_random);
#ifdef V6_TOWER_SHAKE
    HASH(shake_random);HASH(shake_timer);HASH(shake_plan.x);HASH(shake_plan.y);
#endif
#endif
#endif
#ifdef V6_TOWER_PRIZE
    { unsigned i;for(i=0;i<V6_COLLECT_BYTES;++i)HASH(station_collected.bits[i]); }
#endif
#undef HASH
    return hash;
}
#ifdef V6_STATION_MENU
static int ui_station_checkpoint_valid(const V6CheckpointSave *c,const V6HallwayStory *s)
{
    /* Only resident station rooms run the yellow slice; red progress is retained,
     * but its active companion requires the separate red runtime. */
    return checkpoint_bank_valid(c) && !s->companion &&
        ((c->room_x==111 && (c->room_y==104 || c->room_y==105 || c->room_y==106
#ifdef V6_TOWER_COLLECTION_SAVE
            || c->room_y==107
#endif
        )) ||
         (c->room_x==110 && c->room_y==105));
}
#endif
static int ui_load_checked(V6CheckpointSave *out,V6HallwayStory *story)
{
    int a=v6_campaign_dos.exists(save_name),k=v6_campaign_dos.exists(save_backup),result;
    V6CheckpointSave c,b;V6HallwayStory s,bs;
#ifdef V6_TOWER_MENU_TRAVEL
    V6Exploration map,bmap;
#ifdef V6_STATION_MENU
    V6StationStory yellow,byellow;
#ifdef V6_TOWER_COLLECTION_SAVE
    V6Collect collected,bcollected;
#endif
#endif
#endif
    if(a<0 || k<0)return V6_SAVE_IO;
#ifdef V6_TOWER_COLLECTION_SAVE
    result=v6_campaign_collection_read(&v6_campaign_dos,a?save_name:save_backup,&c,&s,&yellow,&map,&collected);
#elif defined(V6_STATION_MENU)
    result=v6_campaign_progress_read(&v6_campaign_dos,a?save_name:save_backup,&c,&s,&yellow,&map);
#elif defined(V6_TOWER_MENU_TRAVEL)
    result=v6_campaign_state_read(&v6_campaign_dos,a?save_name:save_backup,&c,&s,&map);
#else
    result=v6_campaign_read(&v6_campaign_dos,a?save_name:save_backup,&c,&s);
#endif
    if(result)return result;
    if(!checkpoint_bank_valid(&c))return V6_SAVE_CORRUPT;
#ifdef V6_STATION_MENU
    if(!ui_station_checkpoint_valid(&c,&s))return V6_SAVE_CORRUPT;
#endif
#if defined(V6_TOWER_BUILDING) && !defined(V6_TOWER_RESCUE)
    if(s.companion || s.rescue_triggered || s.red_rescued)return V6_SAVE_CORRUPT;
#endif
    if(a && k) {
#ifdef V6_TOWER_COLLECTION_SAVE
        result=v6_campaign_collection_read(&v6_campaign_dos,save_backup,&b,&bs,&byellow,&bmap,&bcollected);
#elif defined(V6_STATION_MENU)
        result=v6_campaign_progress_read(&v6_campaign_dos,save_backup,&b,&bs,&byellow,&bmap);
#elif defined(V6_TOWER_MENU_TRAVEL)
        result=v6_campaign_state_read(&v6_campaign_dos,save_backup,&b,&bs,&bmap);
#else
        result=v6_campaign_read(&v6_campaign_dos,save_backup,&b,&bs);
#endif
        if(result)return result;
        if(!checkpoint_bank_valid(&b))return V6_SAVE_CORRUPT;
#ifdef V6_STATION_MENU
        if(!ui_station_checkpoint_valid(&b,&bs))return V6_SAVE_CORRUPT;
#endif
#if defined(V6_TOWER_BUILDING) && !defined(V6_TOWER_RESCUE)
        if(bs.companion || bs.rescue_triggered || bs.red_rescued)return V6_SAVE_CORRUPT;
#endif
    }
#ifdef V6_TOWER_COLLECTION_SAVE
    return v6_campaign_collection_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_yellow,&ui_loaded_exploration,&ui_loaded_collection);
#elif defined(V6_STATION_MENU)
    return v6_campaign_progress_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_yellow,&ui_loaded_exploration);
#elif defined(V6_TOWER_MENU_TRAVEL)
    return v6_campaign_state_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_exploration);
#else
    return v6_campaign_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story);
#endif
}
static int ui_save_checked(void)
{
    V6CheckpointSave c;V6HallwayStory story;int result;
    int a,k;
#if defined(V6_TOWER_PRIZE) && !defined(V6_TOWER_COLLECTION_SAVE)
    /* The legacy menu cannot represent collected flags. Retain the existing
     * disk until V4 is wired, including when the checkpoint is in another room. */
    { unsigned i;for(i=0;i<V6_COLLECT_BYTES;++i)
        if(station_collected.bits[i])return V6_SAVE_INVALID; }
#endif
    if(!checkpoint_bank_valid(&world.save))return V6_SAVE_INVALID;
#ifdef V6_STATION_MENU
    if(!ui_station_checkpoint_valid(&world.save,&hallway_story))return V6_SAVE_INVALID;
#ifdef V6_TOWER_COLLECTION_SAVE
    { uint8_t bytes[V6_CAMPAIGN_COLLECTION_BYTES];
      if(!v6_campaign_collection_encode(bytes,sizeof(bytes),&world.save,&hallway_story,&station_story,&tele_exploration,&station_collected))return V6_SAVE_INVALID; }
#else
    { uint8_t bytes[V6_CAMPAIGN_STATE_BYTES];
      if(!v6_campaign_progress_encode(bytes,sizeof(bytes),&world.save,&hallway_story,&station_story,&tele_exploration))return V6_SAVE_INVALID; }
#endif
#elif defined(V6_TOWER_MENU_TRAVEL)
    { uint8_t bytes[V6_CAMPAIGN_STATE_BYTES];
      if(!v6_campaign_state_encode(bytes,sizeof(bytes),&world.save,&hallway_story,&tele_exploration))return V6_SAVE_INVALID; }
#endif
    a=v6_campaign_dos.exists(save_name);k=v6_campaign_dos.exists(save_backup);
    if(a<0 || k<0)return V6_SAVE_IO;
    /* Existing records need source-bank validation before replacement recovery
     * can discard a backup, just as an explicit load does. */
    if(a || k) {result=ui_load_checked(&c,&story);if(result)return result;}
#ifdef V6_TOWER_COLLECTION_SAVE
    return v6_campaign_collection_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&station_story,&tele_exploration,&station_collected);
#elif defined(V6_STATION_MENU)
    return v6_campaign_progress_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&station_story,&tele_exploration);
#elif defined(V6_TOWER_MENU_TRAVEL)
    return v6_campaign_state_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&tele_exploration);
#else
    return v6_campaign_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story);
#endif
}
static int ui_apply_load(const V6CheckpointSave *c,const V6HallwayStory *story)
{
#ifdef V6_TOWER_PICKUP_SCREEN
    v6_trinket_screen_init(&pickup_screen);pickup_held=0;pickup_pause_ticks=0;
    v6_pickup_draw_init(&pickup_draw);pickup_rows[0]=pickup_rows[1]=0;
    pickup_bar_rows[0]=pickup_bar_rows[1]=0;
    pickup_bar_room[0]=pickup_bar_room[1]=0xffffffffUL;
#endif
#ifdef V6_TOWER_COLLECTION_SAVE
    ui_copy(&station_collected,&ui_loaded_collection,sizeof(station_collected));
#elif defined(V6_TOWER_PRIZE)
    /* Accepted V1..V3 records migrate with an empty collection bank. */
    v6_collect_clear(&station_collected);
#endif
    ui_copy(&world.save,c,sizeof(*c));
#ifdef V6_TOWER_PICKUP_SCREEN
    {
        unsigned count=0,i;
        for(i=0;i<V6_COLLECT_COUNT;++i)count+=v6_collect_has(&station_collected,i);
        if(!v6_collect_has(&station_collected,6))++count;
        if(!v6_pickup_draw_count(&pickup_draw,count))return 0;
        for(i=0;i<V6_PICKUP_HEIGHT;++i)
            if(!v6_pickup_text_row(&pickup_draw,i,(UBYTE *)pickup_mask+i*40,
                (UBYTE *)pickup_ink+i*40,dialogue_font,pickup_border))return 0;
    }
#endif
#ifdef V6_TOWER_RESCUE
    ui_copy(&hallway_story,story,sizeof(*story));
#ifdef V6_STATION_MENU
    ui_copy(&station_story,&ui_loaded_yellow,sizeof(station_story));
#endif
#else
    (void)story;
#endif
    v6_tower_session_init(&session,c->x,c->y,c->gravity,c->dir);
    if(!v6_tower_route_load(&route,c->room_x,c->room_y,1))return 0;
    session.player.old_x=session.player.x;session.player.old_y=session.player.y;

#ifdef V6_TOWER_RESCUE
    { unsigned i;for(i=0;i<sizeof(rescue_vm);++i)((volatile UBYTE *)&rescue_vm)[i]=0; }
    rescue_vm.control=1;rescue_vm.following=story->companion==9;rescue_vm.mood=story->companion==9?0:1;
#ifdef V6_STATION_MENU
    rescue_vm.following=station_story.companion==7;rescue_vm.mood=rescue_vm.following?0:1;
#endif
    rescue_bars=rescue_fade=rescue_fade_mode=rescue_fire=0;rescue_flips_applied=cue_consumed=0;
    v6_companion_init(&companion);
#endif
    player_animation.delay=player_animation.walk=0;player_frame=c->dir?0:3;
#ifdef V6_TOWER_TELE_MENU
    v6_teleporter_menu_init(&tele_menu);tele_menu_fire=0;
#ifdef V6_TOWER_MENU_TRAVEL
    v6_teleporter_departure_init(&departure);v6_teleporter_arrival_init(&arrival);
    menu_save_pending=menu_travel_active=0;arrival_flash=0;session.invisible=0;
#ifdef V6_TOWER_SHAKE
    shake_timer=0;v6_screen_shake_init(&shake);v6_screen_shake_plan(&shake,0,0,0,&shake_plan);
#endif
#endif
#endif
#ifdef V6_TOWER_MENU_TRAVEL
    ui_copy(&tele_exploration,&ui_loaded_exploration,sizeof(tele_exploration));
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
#ifdef V6_TOWER_ARRIVAL_SAVE
    if(building_stage==1)
#endif
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
#ifdef V6_TOWER_ARRIVAL_SAVE
        /* Fresh boot has no previous scene to interpolate from. */
        session.player.old_x=session.player.x;session.player.old_y=session.player.y;
#endif
        building_save_diag.values[9]=session.player.x;building_save_diag.values[10]=session.player.y;
#ifdef V6_TOWER_ARRIVAL_SAVE
        building_save_diag.values[12]=session.player.old_x;building_save_diag.values[13]=session.player.old_y;
        building_save_diag.values[14]=session.player.vx;building_save_diag.values[15]=session.player.vy;
        building_save_diag.values[16]=session.player.gravity;building_save_diag.values[17]=session.player.dir;
        building_save_diag.values[18]=departure.state;building_save_diag.values[19]=arrival.state;
#endif
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
#ifdef V6_TOWER_STATION
    v6_tower_session_init(&session,188,86,1,0);
    world.save.x=188;world.save.y=86;world.save.gravity=1;world.save.dir=0;
    world.save.room_x=111;world.save.room_y=105;world.save.id=441490;
    if(!v6_tower_route_load(&route,111,105,1))return 20;
#ifdef V6_STATION_SAVE
    if(station_stage==2) {
        world.save=station_saved;hallway_story=station_saved_red;station_story=station_saved_yellow;
        if(!v6_tower_route_load(&route,world.save.room_x,world.save.room_y,1))return 20;
        rescue_vm.following=station_story.companion==7;rescue_vm.mood=!rescue_vm.following;
    }
    if(!v6_exploration_visit(&station_exploration,111,105))return 20;
    station_save_diag.values[3]=session.player.x;station_save_diag.values[4]=session.player.y;
    station_save_diag.values[5]=session.player.gravity;station_save_diag.values[6]=session.player.dir;
    station_save_diag.values[7]=world.save.room_x;station_save_diag.values[8]=world.save.room_y;
    station_save_diag.values[9]=world.save.id;
    station_save_diag.values[10]=station_story.rescue_triggered;station_save_diag.values[11]=station_story.yellow_rescued;
    station_save_diag.values[12]=station_story.companion;
#endif
#ifdef V6_PRIZE_ROUTE_CAPTURE
    station_story.rescue_triggered=station_story.yellow_rescued=1;station_story.companion=7;
    rescue_vm.following=1;rescue_vm.mood=0;
    v6_player_init(&session.player,234,219,0);
#endif
#ifdef V6_SHENANIGAN_CAPTURE
    station_story.rescue_triggered=station_story.yellow_rescued=1;station_story.companion=7;
    rescue_vm.following=1;rescue_vm.mood=0;
    v6_player_init(&session.player,234,219,0);
#endif
#ifdef V6_STATION_COMPANION_CAPTURE
    station_story.rescue_triggered=station_story.yellow_rescued=1;station_story.companion=7;
    rescue_vm.following=1;rescue_vm.mood=0;
    if(!v6_tower_route_load(&route,110,105,0))return 20;
    v6_player_init(&session.player,64,86,1);
#endif
#ifdef V6_STATION_TRAVEL_CAPTURE
    /* Completed rescue and visited destinations are fixture setup only. */
    station_story.rescue_triggered=station_story.yellow_rescued=1;station_story.companion=7;
    rescue_vm.following=1;rescue_vm.mood=0;
    world.save.x=156;world.save.y=92;world.save.gravity=0;world.save.dir=0;
    world.save.room_x=111;world.save.room_y=104;world.save.id=0;
    v6_tower_session_init(&session,156,92,0,0);
    if(!v6_tower_route_load(&route,111,104,1))return 20;
#endif
    v6_station_trigger_init(&station_trigger);
#endif
    v6_hallway_trigger_init(&hallway_trigger);
    #ifdef V6_TOWER_STATION
    v6_station_trigger_enter(&station_trigger,route.rooms[route.index].x,route.rooms[route.index].y,&station_story);
    trigger_crew_visible=v6_station_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&station_story);
#else
    v6_hallway_trigger_enter(&hallway_trigger,route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
    trigger_crew_visible=v6_hallway_crew_visible(route.rooms[route.index].x,route.rooms[route.index].y,&hallway_story);
#endif
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
#ifdef V6_TOWER_STATION
#if defined(V6_STATION_SAVE) || defined(V6_STATION_COMPANION_CAPTURE) || defined(V6_STATION_TRAVEL_CAPTURE)
    if(station_story.companion==7)v6_station_companion_enter(&companion,7,route.rooms[route.index].x,route.rooms[route.index].y,&session.player);
    else
#endif
    v6_station_companion_idle(&companion,trigger_crew_visible);
#else
    v6_companion_idle(&companion,trigger_crew_visible);
#endif
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
        if(route.index>=2 && route.index<4)route.room.terrain=&hallway_terrain[route.index-2];
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
#ifdef V6_TOWER_MUSIC_TRACE
    {
        V6MusicPlan p;
        /* Trace-only virtual backend: seed Passion for Exploring, then apply
         * the current room's source dispatch. No operations touch Paula. */
        if(!v6_music_init(&route_music,65535) ||
           !v6_music_command(&route_music,V6_MUSIC_PLAY,4,&p) || !music_trace_enter())return 20;
    }
#endif
    camera=0;
#ifdef V6_TOWER_PLAY
    camera=session.camera.y;
    controller.y=session.camera.y;controller.old_y=session.camera.old_y;
#endif
#ifdef V6_TOWER_TELE_MENU
    v6_exploration_init(&tele_exploration);
#ifdef V6_MENU_EXPLORED_CAPTURE
    /* Capture setup represents a previously visited resident room. The normal
     * executable starts with current-room exploration only. */
    if(!v6_exploration_visit(&tele_exploration,110,105))return 20;
#endif
#ifdef V6_STATION_TRAVEL_CAPTURE
    if(!v6_exploration_visit(&tele_exploration,111,105) || !v6_exploration_visit(&tele_exploration,110,105))return 20;
#endif
    if(!tele_note_room(route.rooms[route.index].x,route.rooms[route.index].y))return 20;
#endif
#ifdef V6_TOWER_MENU_TRAVEL
    v6_teleporter_departure_init(&departure);v6_teleporter_arrival_init(&arrival);
#endif
    diag.step=0;diag.route_min=0;diag.route_max=5368;
    (void)direction;
#endif
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    if(SysBase->AttnFlags&AFF_68010) return 20;
    GfxBase=(struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    if(!GfxBase) return 20;
    if(!(GfxBase->DisplayFlags&PAL)) { CloseLibrary((struct Library *)GfxBase);return 20; }
#if defined(V6_TOWER_AUDIO) || defined(V6_TOWER_TRAVEL_AUDIO)
    /* This takeover fixture cannot resume another client's write-only audio
     * pointers. Start only with all audio DMA and our audio IRQs idle. */
    if((hw->dmaconr&15) || (hw->intenar&AUDIO_IRQ_MASK)) {
        CloseLibrary((struct Library *)GfxBase);return 20;
    }
#endif
    chip=AllocMem(CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);
    if(!chip) { CloseLibrary((struct Library *)GfxBase);return 20; }
    rings[0]=chip+SHAKE_DMA_BYTES;rings[1]=rings[0]+LAYER_BYTES;
#ifdef V6_TOWER_SHAKE
    { unsigned i;shake_mask=chip;for(i=0;i<V6_SHAKE_MASK_BYTES/2;++i)((UWORD *)shake_mask)[i]=0xffff; }
    v6_screen_shake_init(&shake);v6_screen_shake_plan(&shake,0,0,0,&shake_plan);
#endif
    lists[0]=(UWORD *)(rings[0]+2*LAYER_BYTES);lists[1]=lists[0]+LIST_WORDS;
#ifdef V6_TOWER_PLAY
    player_sprites[0].dma=(UWORD *)(lists[1]+LIST_WORDS);
    player_sprites[1].dma=player_sprites[0].dma+8*V6_SPRITE_WORDS;
#endif
#ifdef V6_TOWER_RESCUE
    {
        unsigned i;
        rescue_captions=rings[0]+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES;
        for(i=0;i<V6_RESCUE_SPEECHES;++i)
            if(!v6_dialogue_draw(rescue_captions+i*V6_DIALOGUE_BYTES,dialogue_font,&v6_rescue_speeches[i])) {
                FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
            }
    }
#endif
#ifdef V6_TOWER_BUILDING
    {
        unsigned frame;V6Room collision;
        building_dma=(UWORD *)(chip+CHIP_BYTES-BUILDING_DMA_BYTES-AUDIO_DMA_BYTES);
        collision.tiles=building_tiles;collision.tileset=2;collision.extra_row=0;
        collision.terrain=0;collision.blocks=0;collision.block_count=0;
        v6_terrain_build(&building_terrain,&collision);
        if(route.index==4)route.room.terrain=&building_terrain;
#ifdef V6_TOWER_ENERGIZE
        collision.tiles=energize_tiles;collision.tileset=0;v6_terrain_build(&energize_terrain,&collision);
        if(route.index==5)route.room.terrain=&energize_terrain;
#ifdef V6_TOWER_STATION
        collision.tiles=frown_tiles;v6_terrain_build(&frown_terrain,&collision);
#ifdef V6_TOWER_SHENANIGAN
        collision.tiles=shenanigan_tiles;v6_terrain_build(&shenanigan_terrain,&collision);
        if(route.index==7)route.room.terrain=&shenanigan_terrain;
#endif
#ifdef V6_TOWER_PRIZE
        collision.tiles=prize_tiles;v6_terrain_build(&prize_terrain,&collision);
#endif
        if(route.index==6)route.room.terrain=&frown_terrain;
#endif
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
#ifdef V6_STATION_COMPANION_CAPTURE
    if(!verify_dma_copy()){FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;}
#endif
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
#ifdef V6_TOWER_PRIZE
       !v6_tower_open(&stream,prize_display,sizeof(prize_display)) ||
       !v6_tower_pairs_validate(&stream,prize_pair_offsets,PRIZE_PAIR_WORDS,PRIZE_TILE_COUNT,2) ||
#endif
#ifdef V6_TOWER_SHENANIGAN
       !v6_tower_open(&stream,shenanigan_display,sizeof(shenanigan_display)) ||
       !v6_tower_pairs_validate(&stream,shenanigan_pair_offsets,SHENANIGAN_PAIR_WORDS,SHENANIGAN_TILE_COUNT,2) ||
#endif
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
#ifdef V6_TOWER_ARRIVAL_SAVE
           building_stage==2?(building_saved.room_x==110?energize_display:building_display):
#else
           building_stage==2?building_display:
#endif
#endif

#ifdef V6_TOWER_STATION
           route.index==7?shenanigan_display:route.index==6?frown_display:route.index==5?energize_display:building_display,
#elif defined(V6_TOWER_ROUNDTRIP)
           building_display,
#elif defined(V6_ENERGIZE_CAPTURE)
           energize_display,
#else
           hallway1_display,
#endif
#ifdef V6_BUILDING_SAVE
#ifdef V6_TOWER_ARRIVAL_SAVE
           building_stage==2?(building_saved.room_x==110?sizeof(energize_display):sizeof(building_display)):
#else
           building_stage==2?sizeof(building_display):
#endif
#endif

#ifdef V6_TOWER_STATION
           route.index==7?sizeof(shenanigan_display):route.index==6?sizeof(frown_display):route.index==5?sizeof(energize_display):sizeof(building_display)) ||
#elif defined(V6_TOWER_ROUNDTRIP)
           sizeof(building_display)) ||
#elif defined(V6_ENERGIZE_CAPTURE)
           sizeof(energize_display)) ||
#else
           sizeof(hallway1_display)) ||
#endif
#endif
#ifdef V6_TOWER_STATION
       !v6_tower_pairs_validate(&stream,FG_OFFSETS,FG_WORDS,FG_COUNT,2) ||
#endif
       !prepare(rings[0],lists[0],0,camera,0)) {
        FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
    }
#ifdef V6_TOWER_AUDIO
    {
        unsigned i;
        cue_chip=chip+CHIP_BYTES-CUE_DMA_BYTES;
        for(i=0;i<CUE_CREW_BYTES;++i)cue_chip[i]=CUE_CREW[i];
        for(i=0;i<CUE_CREW1_BYTES;++i)cue_chip[CUE_CREW_BYTES+i]=cue_crew1[i];
        if(!v6_audio_init(&cue_audio,(ULONG)(cue_chip+CUE_DMA_BYTES-2))) {
            FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
        }
    }
#endif
#ifdef V6_TOWER_UI_SAVE
    {
        unsigned i;ui_captions=rings[0]+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES;
        for(i=0;i<UI_MESSAGE_COUNT;++i)if(!v6_dialogue_draw(ui_captions+i*V6_DIALOGUE_BYTES,dialogue_font,&ui_messages[i])) {
            FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
        }
        ui_fields=250;ui_status=0;
#ifdef V6_TOWER_PICKUP_SCREEN
        pickup_banks=ui_captions+UI_MESSAGE_COUNT*V6_DIALOGUE_BYTES;
        pickup_zero=pickup_banks+2*V6_PICKUP_BANK_BYTES;
        for(i=0;i<V6_PICKUP_PLANE_BYTES;++i)((volatile UBYTE *)pickup_zero)[i]=0;
        v6_pickup_draw_init(&pickup_draw);v6_pickup_draw_count(&pickup_draw,1);
        pickup_bar_room[0]=pickup_bar_room[1]=0xffffffffUL;
        for(i=0;i<V6_PICKUP_HEIGHT;++i) {
            if(!v6_pickup_text_row(&pickup_draw,i,(UBYTE *)pickup_mask+i*40,
                (UBYTE *)pickup_ink+i*40,dialogue_font,pickup_border)) {
                FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
            }
        }
        v6_trinket_screen_init(&pickup_screen);
#endif
    }
#endif
#ifdef V6_TOWER_TRAVEL_AUDIO
    {
        unsigned i;travel_audio_chip=chip+CHIP_BYTES-AUDIO_DMA_BYTES;
        for(i=0;i<TELEPORTER_FLASH_BYTES;++i)travel_audio_chip[i]=teleporter_flash[i];
        for(i=0;i<TELEPORTER_TELEPORT_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+i]=teleporter_teleport[i];
#ifdef V6_TOWER_COEXIST_AUDIO
        coexist_sample=travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES;
        for(i=0;i<64;++i)coexist_sample[i]=(UBYTE)(i<32?(int)i*6-96:288-(int)i*6);
#endif
#ifdef V6_TOWER_PRIZE
        for(i=0;i<PRIZE_VANISH_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+i]=prize_vanish[i];
        for(i=0;i<PRIZE_TRINKET_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_VANISH_BYTES+i]=prize_trinket[i];
#endif
        for(i=0;i<4;++i)if(!v6_paula_init(&travel_voices[i],i,(ULONG)(travel_audio_chip+TRAVEL_AUDIO_BYTES-2))) {
            FreeMem(chip,CHIP_BYTES);CloseLibrary((struct Library *)GfxBase);return 20;
        }
    }
#endif
    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
    OwnBlitter();WaitBlit();Forbid();Disable();
#if defined(V6_TOWER_AUDIO) || defined(V6_TOWER_TRAVEL_AUDIO)
    /* Recheck while scheduling and interrupts are stopped: allocation and
     * display preparation ran with the OS enabled after the early check. */
    if((hw->dmaconr&15) || (hw->intenar&AUDIO_IRQ_MASK)) {
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
    while(
#ifdef V6_TOWER_MENU_TRAVEL
          (((*(volatile UBYTE *)0xbfe001&0x40) && !menu_exit_pending) || menu_save_pending)
#else
          (*(volatile UBYTE *)0xbfe001&0x40)
#endif
          && !diag.error
#if defined(V6_STATION_SAVE) && defined(V6_STATION_CAPTURE)
          && diag.logic_ticks<1000
#endif
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
          && diag.logic_ticks<V6_SAVE_STOP_TICKS
#endif
          ) {
        start=clock_lines();
#ifdef V6_TOWER_UI_SAVE
        {
            int right=(hw->potinp&0x0400)==0,fire=(*(volatile UBYTE *)0xbfe001&0x80)==0;
            unsigned action;
#ifdef V6_TOWER_MENU_TRAVEL
            /* A quit during the audio tail retains the completed-arrival
             * save request. Latch it even when the mouse is released before
             * the voices drain; return to the OS after the write finishes. */
            if(menu_save_pending && !(*(volatile UBYTE *)0xbfe001&0x40))menu_exit_pending=1;
#endif
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
#ifdef V6_PRIZE_ROUTE_CAPTURE
            right=fire=0;
#ifdef V6_PICKUP_CAPTURE_HOLD
            if(!prize_ui_stage && pickup_screen.visible && pickup_pause_ticks>=16) {
                right=1;prize_ui_stage=3;
            }
#else
            #ifdef V6_TOWER_COLLECTION_SAVE
            if(prize_ui_stage==0 && diag.logic_ticks>=154) {right=1;prize_ui_stage=1;}
            else if(prize_ui_stage==1 && diag.logic_ticks>=166) {right=fire=1;prize_ui_stage=2;}
#else
            if(!prize_ui_stage && diag.logic_ticks>=188) {right=1;prize_ui_stage=1;}
#endif
#endif
#endif
#ifdef V6_SHENANIGAN_CAPTURE
            right=fire=0;
            if(shenanigan_ui_stage==0 && diag.logic_ticks>=45) {
                right=1;shenanigan_ui_stage=1;
            } else if(shenanigan_ui_stage==1 && diag.logic_ticks>=60) {
                right=fire=1;shenanigan_ui_stage=2;
            }
#endif
            action=v6_save_controls_tick(&save_controls,right,fire);
#ifdef V6_TOWER_MENU_TRAVEL
            if(menu_save_pending) {
#ifdef V6_TOWER_TRAVEL_AUDIO
                if(travel_audio_busy())++menu_effect_diag.values[3];
                else
#endif
                if(!route_loading && session.death_timer==-1 && !departure.state && !arrival.state && !tele_menu.open) {
                    action=V6_SAVE_ACTION_SAVE;menu_save_pending=0;
                }
            }
#endif
            if(ui_fields
#ifdef V6_MENU_EFFECT_HOLD
               && menu_travel_trace.count<V6_MENU_EFFECT_HOLD
#endif
              )--ui_fields;
            if(action) {
                ULONG before_hash=ui_game_hash(),before_frames=frames,before_ticks=diag.logic_ticks;
                int result=5;
                ++ui_diag.values[0];ui_diag.values[7]=action;
                if(route_loading || session.death_timer!=-1
#ifdef V6_TOWER_PICKUP_SCREEN
                   || pickup_screen.state
#endif
#ifdef V6_TOWER_TELE_MENU
                   || tele_menu.open
#ifdef V6_TOWER_MENU_TRAVEL
                   || departure.state || arrival.state
#endif
#endif
#ifdef V6_TOWER_RESCUE
                   || rescue_vm.active
#endif
#ifdef V6_TOWER_AUDIO
                   || cue_audio.state
#endif
#if defined(V6_TOWER_TRAVEL_AUDIO) && defined(V6_TOWER_MENU_TRAVEL)
                   || travel_audio_busy()
#endif
                  ) {
                    ++ui_diag.values[4];ui_status=4;ui_fields=200;
                } else {
                    V6CheckpointSave c;V6HallwayStory story;
#if defined(V6_TOWER_MENU_TRAVEL) && defined(V6_TOWER_TRAVEL_AUDIO)
                    menu_effect_diag.values[4]=travel_audio_busy();
#endif
#ifdef V6_TOWER_MENU_TRAVEL
                    if(action==V6_SAVE_ACTION_SAVE) {
                        menu_effect_diag.values[2]=diag.logic_ticks;
                        menu_effect_diag.values[5]=menu_exit_pending;
                    }
#endif
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
                    if((hw->dmaconr&15) || (hw->intenar&AUDIO_IRQ_MASK)) {
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
            if(cue_audio.state!=V6_AUDIO_IDLE) {
                v6_audio_tick(&cue_audio,(hw->intreqr&INTF_AUD0)!=0,&plan);
                audio_apply(&plan);
            }
            audio_record();
        }
#endif
#ifdef V6_TOWER_COEXIST_AUDIO
        if(!coexist_tick(frames))diag.error=17;
#endif
#ifdef V6_TOWER_TRAVEL_AUDIO
        {
            unsigned i;V6AudioPlan plan;
            for(i=0;i<4;++i)if((V6_TRAVEL_SFX_MASK&(1U<<i)) && travel_voices[i].audio.state!=V6_AUDIO_IDLE) {
#ifdef V6_TOWER_PICKUP_SCREEN
                unsigned before=travel_voices[i].audio.completed;
#endif
                if(!v6_paula_tick(&travel_voices[i],(hw->intreqr&(INTF_AUD0<<i))!=0,&plan))diag.error=15;
                travel_audio_apply(&plan);
#ifdef V6_TOWER_PICKUP_SCREEN
                if(pickup_screen.stopped)prize_audio_diag.values[3]+=travel_voices[i].audio.completed-before;
#endif
            }
            travel_audio_record();
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
#if defined(V6_TOWER_MENU_TRAVEL) && defined(V6_TELE_MENU_CAPTURE)
            /* Hold after a completed physical-input journey. A live RAM dump
             * can otherwise land between diagnostic counter publications. */
            if(diag.logic_ticks>=600)delta=0;
#endif
#ifdef V6_STATION_CAPTURE
            if(diag.logic_ticks>=1000)delta=0;
#endif
#ifdef V6_MENU_EFFECT_HOLD
            if(menu_travel_trace.count>=V6_MENU_EFFECT_HOLD)delta=0;
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
#ifdef V6_PRIZE_ROUTE_CAPTURE
                input=0;
#ifdef V6_TOWER_PICKUP_SCREEN
                if(pickup_diag.values[3] && diag.logic_ticks>=pickup_diag.values[11] &&
                   diag.logic_ticks<pickup_diag.values[11]+3)input=V6_FLIP;
#endif
                if(diag.logic_ticks==20 || diag.logic_ticks==25 || diag.logic_ticks==40 ||
                   diag.logic_ticks==95 || diag.logic_ticks==150 || diag.logic_ticks==175 ||
                   diag.logic_ticks==185 || diag.logic_ticks==190) {
                    unsigned tick=diag.logic_ticks;
                    int x=tick==40 || tick==95?124:tick==25?236:tick==150?192:tick==185?140:234;
                    int y=tick==20 || tick==190?219:tick==40?70:tick==95?110:
                          tick==25?134:tick==150?128:tick==185?161:-3;
                    v6_player_init(&session.player,x,y,tick==20 || tick==185 || tick==190?0:1);
                    session.death_timer=-1;session.life_timer=0;session.invisible=0;
                    session.motion.ax=0;session.motion.pending_y=y;
                }
#ifdef V6_TOWER_COLLECTION_SAVE
                if(diag.logic_ticks==160) {
                    v6_collect_clear(&station_collected);
                    v6_prize_init(&station_prize,&route.room,&station_collected,world.save.id,134);
                    v6_player_init(&session.player,236,134,1);
                    session.death_timer=-1;session.life_timer=0;session.invisible=0;
                    session.motion.ax=0;session.motion.pending_y=134;
                }
#endif
                if(diag.logic_ticks==60 || diag.logic_ticks==115)v6_tower_session_die(&session);
#endif
#ifdef V6_SHENANIGAN_CAPTURE
                input=0;
                if(diag.logic_ticks==20 || diag.logic_ticks==35 || diag.logic_ticks==50) {
                    unsigned tick=diag.logic_ticks;
                    v6_player_init(&session.player,tick==20?140:tick==35?20:234,
                        tick==20?161:tick==35?110:-3,tick==20?0:1);
                    session.death_timer=-1;session.life_timer=0;session.invisible=0;
                    session.motion.ax=0;session.motion.pending_y=session.player.y;
                }
#endif
#ifdef V6_STATION_CAPTURE
                input=station_story.rescue_triggered?(rescue_vm.waiting && (UWORD)diag.logic_ticks%30==0?V6_FLIP:0):V6_LEFT;
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
#ifdef V6_TOWER_PICKUP_SCREEN
                if(pickup_screen.stopped) {
                    unsigned i,events,changed=0,action=(input&V6_FLIP)!=0;
                    const volatile ULONG *actor=(const volatile ULONG *)&station_prize;
#ifdef V6_PRIZE_ROUTE_CAPTURE
                    /* Hold through the reveal, then release and press. */
                    if(!pickup_pause_ticks)pickup_held=1;
                    /* Hold through the source jingle before attempting DOS
                     * persistence. Release once, then press to dismiss. */
                    action=1;
                    if(pickup_pause_ticks>=18 && !travel_audio_busy()) {
                        if(!prize_pickup_release)prize_pickup_release=pickup_pause_ticks;
                        action=pickup_pause_ticks!=prize_pickup_release;
                    }
#ifdef V6_PICKUP_CAPTURE_HOLD
                    action=1;
#endif
#endif
                    if(!pickup_hash_valid) {
                        pickup_world_hash=ui_game_hash();
                        for(i=0;i<sizeof(station_prize)/sizeof(ULONG);++i)
                            pickup_actor_snapshot[i]=actor[i];
                        pickup_hash_valid=1;
                    }
                    if(v6_trinket_screen_input(&pickup_screen,action,pickup_held))pickup_held=1;
                    if(!action)pickup_held=0;
                    events=v6_trinket_screen_tick(&pickup_screen,0);
                    pickup_draw_tick();
                    ++pickup_pause_ticks;++pickup_diag.values[1];
                    if(events&V6_TRINKET_SHOW) {
                        ++pickup_diag.values[2];pickup_diag.values[4]=pickup_pause_ticks;
                    }
                    if(events&V6_TRINKET_HIDE) {
                        ++pickup_diag.values[3];pickup_diag.values[5]=pickup_pause_ticks;
                        pickup_diag.values[7]=session.player.flips;
                    }
                    for(i=0;i<sizeof(station_prize)/sizeof(ULONG);++i)
                        if(pickup_actor_snapshot[i]!=actor[i])changed=1;
                    if(pickup_world_hash!=ui_game_hash() || changed) {
                        ++pickup_diag.values[8];diag.error=18;
                    }
                    pickup_diag.values[9]=pickup_screen.state;
                    pickup_diag.values[10]=pickup_screen.count;
                    pickup_diag.values[11]=diag.logic_ticks;
                    /* UI consumes a game timestep; world trace ticks count
                     * only active gameplay so replay placements stay stable. */
                    continue;
                }
                if(pickup_held) {
                    if(!(input&V6_FLIP))pickup_held=0;
                    else input&=~V6_FLIP;
                }
#endif
#ifdef V6_TOWER_TELE_MENU
                {
                    UWORD joy=hw->joy1dat;
                    int fire=(*(volatile UBYTE *)0xbfe001&0x80)==0;
                    int down=((joy&0x0100)!=0)!=((joy&1)!=0);
                    unsigned buttons=0,was_open=tele_menu.open,event;
                    ULONG before=0;V6TeleporterDestination target;
                    if(!fire)tele_menu_fire=0;
                    else if(was_open)tele_menu_fire=1;
                    if(tele_menu.open) {
                        if(joy&0x0200)buttons|=V6_TELE_MENU_LEFT;
                        if(joy&0x0002)buttons|=V6_TELE_MENU_RIGHT;
                        if(fire)buttons|=down?V6_TELE_MENU_CANCEL:V6_TELE_MENU_CONFIRM;
                    } else if(fire && !save_controls.suppress_fire && (down || tele_menu_fire)) {
                        buttons=V6_TELE_MENU_CONFIRM;tele_menu_fire=1;
                    }
                    /* State snapshots matter only when opening or pausing
                     * the selector, not on every ordinary gameplay tick. */
                    if(was_open || (buttons&V6_TELE_MENU_CONFIRM))before=ui_game_hash();
                    v6_teleporter_menu_ready(&tele_menu,&route.tele_region,&session.player,
                        route.rooms[route.index].teleporter && session.death_timer==-1 && !route_loading
#ifdef V6_TOWER_MENU_TRAVEL
                        && !departure.state && arrival.control && !menu_save_pending
#endif
                        );
                    event=v6_teleporter_menu_tick(&tele_menu,tele_destinations,tele_destination_count,
                        route.rooms[route.index].x,route.rooms[route.index].y,&session.player,buttons,&target);
                    if(event==V6_TELE_MENU_OPENED){
                        if(!tele_menu_diag.values[0])tele_menu_diag.values[8]=session.player.flips;
                        ++tele_menu_diag.values[0];tele_menu_fire=1;tele_menu_diag.values[6]=before;
                    }
                    tele_menu_diag.values[9]=session.player.flips;
                    if(event==V6_TELE_MENU_CHANGED)++tele_menu_diag.values[1];
                    if(event==V6_TELE_MENU_CLOSED){++tele_menu_diag.values[2];ui_fields=0;}
                    if(event==V6_TELE_MENU_TRAVEL) {
#ifdef V6_TOWER_MENU_TRAVEL
                        if(!v6_teleporter_departure_start(&departure,route.rooms[route.index].teleporter,&route.tele_region))diag.error=13;
                        else {
                            unsigned j;const LONG *body=(const LONG *)&session.player;
#ifdef V6_MENU_EFFECT_HOLD
                            /* Paired pixel captures share deterministic scene
                             * animation/colour RNG irrespective of boot time. */
                            building_random=1;colour_random=7;shake_random=19;
                            building_animation.frame=1;building_animation.delay=building_animation.walking=0;
#endif
                            menu_target=target;ui_fields=0;tele_menu.ready=0;++tele_menu_diag.values[3];
                            menu_travel_active=1;menu_travel_trace.count=0;
#ifdef V6_STATION_MENU
                            station_travel_trace.count=0;
                            for(j=0;j<sizeof(V6Companion)/4;++j)
                                station_travel_trace.snapshot[j]=((const LONG *)&companion)[j];
#endif
                            for(j=0;j<6;++j)menu_effect_diag.values[j]=0;
                            menu_effect_diag.values[0]=diag.logic_ticks;
#ifdef V6_TOWER_SHAKE
                            menu_shake_trace.count=0;menu_shake_trace.seed=shake_random;
#endif
                            for(j=0;j<16;++j)menu_travel_trace.snapshot[j]=body[j];
                            menu_travel_trace.snapshot[16]=session.motion.ax;menu_travel_trace.snapshot[17]=session.motion.pending_y;
                            menu_travel_trace.snapshot[18]=building_animation.frame;menu_travel_trace.snapshot[19]=building_animation.delay;
                            menu_travel_trace.snapshot[20]=building_animation.walking;menu_travel_trace.snapshot[21]=building_random;
                            menu_travel_trace.snapshot[22]=colour_random;
                        }
#else
                        ++tele_menu_diag.values[3];diag.error=13;
#endif
                    }
                    tele_menu_diag.values[4]=tele_menu.selected;
                    if(tele_menu_fire || was_open || tele_menu.open)input&=~V6_FLIP;
                    if((was_open || tele_menu.open) && event!=V6_TELE_MENU_TRAVEL) {
                        ++tele_menu_diag.values[5];tele_menu_diag.values[7]=ui_game_hash();
                        if(tele_menu_diag.values[6]!=tele_menu_diag.values[7])diag.error=13;
                        goto tele_menu_paused;
                    }
                }
#endif
#ifdef V6_TOWER_RESCUE
                V6RescueSignals rescue_signals;
#ifdef V6_TOWER_STATION
                v6_station_companion_step(&companion,&session.player,&route.room,session.death_timer,route.rooms[route.index].x,route.rooms[route.index].y);
#else
                v6_companion_step(&companion,&session.player,&route.room,session.death_timer);
#endif
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
#ifndef V6_TOWER_MENU_TRAVEL
                if(travel_leg==1 && !arrival.state && !departure.state) {
                    if(!v6_teleporter_departure_start(&departure,route.rooms[route.index].teleporter,&route.tele_region))diag.error=14;
                }
#endif
                if(departure.state || !arrival.control)input|=V6_NO_CONTROL;
#ifdef V6_TOWER_MENU_TRAVEL
                if(!departure.state && !arrival.state) {
#ifdef V6_TOWER_SHENANIGAN
                    if(!station_route_step(&route,input,station_conveyor_tick,0))diag.error=6;
#else
                    if(!v6_tower_route_step(&route,input))diag.error=6;
#endif
                } else
#endif
                if(!station_route_step(&route,input,travel_phase,0))diag.error=6;
                if(departure.travel) {
#ifdef V6_TOWER_MENU_TRAVEL
                    int x=menu_target.room_x,y=menu_target.room_y;
#else
                    int x=travel_leg==0?110:111,y=travel_leg==0?105:104;
#endif
                    if(!v6_tower_route_teleport(&route,x,y))diag.error=14;
                    else {
                        departure.travel=0;++travel_leg;
                        v6_teleporter_arrival_init(&arrival);
                        arrival.flash=departure.flash;arrival.shake=departure.shake;
                        if(!v6_teleporter_arrival_start(&arrival))diag.error=14;
                    }
                }
#ifdef V6_TOWER_TRAVEL_AUDIO
                {
                    unsigned events=departure.events|arrival.events,cue,limit=2;
#ifdef V6_TOWER_PRIZE
                    events|=prize_audio_pending;prize_audio_pending=0;limit=4;
#endif
                    for(cue=0;cue<limit;++cue)if(events&(1U<<cue)) {
                        unsigned i,busy=0,age[4];int chosen;V6AudioSample sample;V6AudioPlan plan;
                        for(i=0;i<4;++i) {
                            if(travel_voices[i].audio.state!=V6_AUDIO_IDLE)busy|=1U<<i;
                            age[i]=frames-travel_started[i];
                        }
                        chosen=v6_audio_choose(V6_TRAVEL_SFX_MASK,busy,travel_priority,age,cue+1);
                        if(chosen<0){++travel_audio_dropped;if(chosen==-2)diag.error=15;
#ifdef V6_TOWER_PRIZE
                            if(cue>=2)++prize_audio_diag.values[2];
#endif
                        }
                        else {
                            i=(unsigned)chosen;
                            sample.address=(ULONG)(travel_audio_chip+(cue?TELEPORTER_FLASH_BYTES:0));
                            sample.bytes=cue?TELEPORTER_TELEPORT_BYTES:TELEPORTER_FLASH_BYTES;
                            sample.period=TELEPORTER_PERIOD;sample.volume=64;
#ifdef V6_TOWER_PRIZE
                            if(cue>=2) {
                                sample.address=(ULONG)(travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+(cue==3?PRIZE_VANISH_BYTES:0));
                                sample.bytes=cue==3?PRIZE_TRINKET_BYTES:PRIZE_VANISH_BYTES;
                                sample.period=PRIZE_PERIOD;
                            }
#endif
                            if(!v6_paula_request(&travel_voices[i],&sample,&plan)) {
                                diag.error=15;
#ifdef V6_TOWER_PRIZE
                                if(cue>=2)++prize_audio_diag.values[4];
#endif
                            }
                            else {
                                if(busy&(1U<<i))++travel_stolen;
                                travel_started[i]=frames;travel_priority[i]=cue+1;
                                if(travel_audio_requests<8) {
                                    volatile ULONG *a=travel_audio_diag.records[travel_audio_requests];
                                    a[0]=diag.logic_ticks+1;a[1]=cue;a[2]=i;a[3]=frames;
                                }
#ifdef V6_TOWER_PRIZE
                                if(cue>=2) {
                                    unsigned n=prize_audio_diag.values[0]+prize_audio_diag.values[1];
                                    if(n<32) {
                                        volatile ULONG *a=prize_audio_diag.records[n];
                                        a[0]=diag.logic_ticks+1;a[1]=cue;a[2]=i;a[3]=frames;
                                    }
                                    ++prize_audio_diag.values[cue-2];
                                }
#endif
                                ++travel_audio_requests;travel_audio_apply(&plan);
                            }
                        }
                    }
                    travel_audio_record();
                }
#endif
                arrival_flash=departure.state?departure.flash:arrival.flash;
#ifdef V6_TOWER_SHAKE
                {
                    UWORD samples[2]={0,0};unsigned i;
                    shake_timer=departure.state?departure.shake:arrival.shake;
                    if(shake_timer)for(i=0;i<2;++i) {
                        shake_random^=shake_random<<13;shake_random^=shake_random>>17;shake_random^=shake_random<<5;
                        samples[i]=shake_random>>16;
                    }
                    v6_screen_shake_pre(&shake,shake_timer,samples);
                    v6_screen_shake_plan(&shake,shake_timer,session.noflashing,0,&shake_plan);
#ifdef V6_MENU_SHAKE_REFERENCE
                    v6_screen_shake_plan(&shake,0,session.noflashing,0,&shake_plan);
#endif
                    if(session.noflashing)arrival_flash=0;
                    if(shake_trace.count<128) {
                        LONG *record=shake_trace.records[shake_trace.count++];
                        record[0]=shake_timer;record[1]=shake_plan.x;record[2]=shake_plan.y;
                    }
#ifdef V6_TOWER_MENU_TRAVEL
                    if(menu_travel_active && menu_shake_trace.count<64) {
                        volatile LONG *record=menu_shake_trace.records[menu_shake_trace.count++];
                        record[0]=shake_timer;record[1]=shake_plan.x;record[2]=shake_plan.y;
                    }
#endif
                }
#endif
#ifdef V6_TOWER_MENU_TRAVEL
                if(menu_travel_active && menu_travel_trace.count<128) {
                    volatile LONG *d=menu_travel_trace.records[menu_travel_trace.count];
                    d[0]=departure.state;d[1]=departure.delay;d[2]=departure.control;d[3]=departure.flash;
                    d[4]=departure.shake;d[5]=departure.events;d[6]=departure.travel;d[7]=travel_leg;
                }
#endif
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
                if(!station_route_step(&route,input,arrival_phase,&arrival))diag.error=6;
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
#ifdef V6_TOWER_MENU_TRAVEL
                if(menu_travel_active && menu_travel_trace.count<128) {
                    volatile LONG *a=menu_travel_trace.records[menu_travel_trace.count]+8;
                    a[0]=arrival.state;a[1]=arrival.delay;a[2]=arrival.control;a[3]=arrival.flash;
                    a[4]=arrival.shake;a[5]=arrival.events;a[6]=session.invisible;a[7]=session.player.vx;
                    a[8]=session.player.vy;a[9]=session.player.ay;a[10]=session.player.old_x;
                    a[11]=session.player.old_y;a[12]=session.player.dir;a[13]=session.death_timer;
                }
                if(arrival.events&V6_ARRIVAL_SAVE) {
                    menu_save_pending=1;menu_effect_diag.values[1]=diag.logic_ticks+1;
                }
#endif
                /* Graphics::renderfixedpost effect counters decay once per tick. */
                if(arrival.flash>0)--arrival.flash;
                if(arrival.shake>0)--arrival.shake;
#else
#ifdef V6_TOWER_SHENANIGAN
                if(!station_route_step(&route,input,station_conveyor_tick,0))diag.error=6;
#else
                if(!v6_tower_route_step(&route,input)) diag.error=6;
#endif
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
#ifdef V6_TOWER_ROUNDTRIP
                {
                    int tile=route.rooms[route.index].teleporter?route.rooms[route.index].teleporter->tile:1;
                    teleporter_tint=tile==6?flashing_colour(session.noflashing):tile==1?0x444:0xaaf;
                    player_tint=departure.state>=4000 && departure.state<=4002 && !session.invisible?
                        flashing_colour(session.noflashing):0x6ff;
                    if(colour_trace.count<128) {
                        volatile ULONG *c=colour_trace.records[colour_trace.count++];
                        c[0]=teleporter_tint;c[1]=player_tint;
                    }
                }
#endif
#ifdef V6_TOWER_MENU_TRAVEL
                if(menu_travel_active && menu_travel_trace.count<128) {
                    volatile LONG *r=menu_travel_trace.records[menu_travel_trace.count]+22;
                    V6Teleporter *t=route.rooms[route.index].teleporter;
                    r[0]=route.index;r[1]=session.player.x;r[2]=session.player.y;r[3]=t->tile;r[4]=t->state;
                    r[5]=route.tele_events;r[6]=building_animation.frame;r[7]=world.save.x;r[8]=world.save.y;
                    r[9]=world.save.room_x;r[10]=world.save.room_y;r[11]=route.tele_region.active;
                    r[12]=teleporter_tint;r[13]=player_tint;++menu_travel_trace.count;
                    if(arrival.events&V6_ARRIVAL_SAVE)menu_travel_active=0;
                }
#endif
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
#ifdef V6_TOWER_STATION
                v6_station_trigger_step(&station_trigger,&station_story,&session.player);
                if(station_trigger.pending && !rescue_vm.active) {
                    if(v6_station_trigger_take(&station_trigger)!=V6_STATION_SCRIPT_RESCUE_YELLOW ||
                       !v6_rescue_start(&rescue_vm,&v6_rescuered_program,&v6_skipred_program,
#ifdef V6_TOWER_RESCUE_SKIP
                       1
#else
                       0
#endif
                       ))diag.error=9;
                }
                v6_station_rescue_tick(&rescue_vm,&station_story,&rescue_signals);
                if(rescue_vm.error)diag.error=10;
#ifdef V6_TOWER_AUDIO
                rescue_audio_tick();
#endif
                companion.following=rescue_vm.following;
                if(rescue_vm.tile_serial)companion.mood=0;
                companion_record();rescue_record();record_trigger();
#else
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
                rescue_audio_tick();
#endif
                companion.mood=rescue_vm.mood;companion.following=rescue_vm.following;
                companion_record();
                rescue_record();
#endif
                record_trigger();
#endif
#endif
#else
                v6_tower_session_play_world(&session,&player_room,input,&world);
#endif
#ifdef V6_TOWER_PICKUP_SCREEN
                /* Source updatestate follows entities and physics. The pickup
                 * tick finishes before completestop applies to the next tick. */
                if(pickup_screen.state==1000)v6_trinket_screen_tick(&pickup_screen,0);
                pickup_draw_tick();
                if(pickup_diag.values[3] && diag.logic_ticks<pickup_diag.values[11]+3)
                    pickup_diag.values[7]=session.player.flips;
#endif
#ifdef V6_PRIZE_ROUTE_CAPTURE
                if(prize_route_trace.count<224) {
                    volatile LONG *d=prize_route_trace.records[prize_route_trace.count++];
                    unsigned i;
                    d[0]=route.index;d[1]=session.player.x;d[2]=session.player.y;
                    d[3]=session.player.gravity;d[4]=session.death_timer;d[5]=world.save.id;
                    d[6]=world.save.x;d[7]=world.save.y;d[8]=world.save.gravity;
                    d[9]=world.save.room_x;d[10]=world.save.room_y;d[11]=companion.visible;
                    d[12]=route.room.block_count;d[13]=station_prize.waiting.x;d[14]=station_prize.waiting.state;
                    d[15]=prize_pickups;d[16]=prize_patches;d[17]=v6_collect_has(&station_collected,6);
                    d[18]=station_prize.trinket.visible;d[19]=prize_tiles[9*40+18];
                    for(i=0;i<3;++i)d[20+i]=station_prize.disappearing[i].state;
                    d[23]=session.respawns;
                }
#endif
#ifdef V6_SHENANIGAN_CAPTURE
                if(shenanigan_trace.count<160) {
                    volatile LONG *d=shenanigan_trace.records[shenanigan_trace.count++];
                    d[0]=route.index;d[1]=session.player.x;d[2]=session.player.y;
                    d[3]=session.player.gravity;d[4]=session.death_timer;d[5]=world.save.id;
                    d[6]=world.save.x;d[7]=world.save.y;d[8]=world.save.gravity;
                    d[9]=world.save.room_x;d[10]=world.save.room_y;d[11]=companion.visible;
                    d[12]=route.room.block_count;d[13]=station_conveyor_phase;
                }
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
#ifdef V6_TOWER_MUSIC_TRACE
                if(!music_trace_tick())diag.error=16;
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
            route_budget=(route.rooms[route.index].teleporter || route.index==7 || route.index==8)?1:2;
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
#ifdef V6_PRIZE_ROUTE_CAPTURE
        if(prize_pickups && (pickup_draw.bars || pickup_draw.old_bars || pickup_screen.state) &&
           pickup_frame_trace.count<128) {
            volatile ULONG *r=pickup_frame_trace.records[pickup_frame_trace.count++];
            r[0]=diag.logic_ticks;r[1]=frames;r[2]=logic_work;r[3]=render_work;
            r[4]=pickup_pause_ticks;r[5]=pickup_rows[back];r[6]=pickup_draw.bars;r[7]=frames-previous;
        }
#endif
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
#ifdef V6_TOWER_COEXIST_AUDIO
    {
        V6AudioPlan raw,p;raw.count=1;raw.writes[0].reg=0x96;raw.writes[0].value=15;
        if(v6_music_register_plan(&raw,12,3,&p))coexist_apply(&p);
    }
#endif
#ifdef V6_TOWER_TRAVEL_AUDIO
    {
        unsigned i;V6AudioPlan plan;
        for(i=0;i<4;++i)if(V6_TRAVEL_SFX_MASK&(1U<<i)){v6_paula_stop(&travel_voices[i],&plan);travel_audio_apply(&plan);}
        travel_audio_record();
    }
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
#if defined(V6_TOWER_PERSIST) || defined(V6_TOWER_UI_SAVE) || defined(V6_BUILDING_SAVE) || defined(V6_STATION_SAVE)
static int checkpoint_bank_valid(const V6CheckpointSave *c)
{
    return v6_campaign_route_checkpoint_valid(c,tower_route_rooms,
        sizeof(tower_route_rooms)/sizeof(tower_route_rooms[0]));
}
#endif
int __attribute__((used,section(".text.unlikely"))) _start(void) {
#ifdef V6_STATION_SAVE
    int result,a,t,k;V6CheckpointSave c;V6HallwayStory red;V6StationStory yellow;V6Exploration map;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    a=v6_campaign_dos.exists(save_name);t=v6_campaign_dos.exists(save_temp);k=v6_campaign_dos.exists(save_backup);
    result=(a<0 || t<0 || k<0)?V6_SAVE_IO:V6_SAVE_OK;
    station_stage=(a || t || k)?2:1;station_save_diag.values[0]=station_stage;
    if(!result && station_stage==2) {
        result=v6_campaign_progress_read(&v6_campaign_dos,a?save_name:save_backup,&station_saved,&station_saved_red,&station_saved_yellow,&station_exploration);
        if(!result && (!checkpoint_bank_valid(&station_saved) || station_saved.room_x!=111 || station_saved.room_y!=105 || station_saved_red.companion))result=V6_SAVE_CORRUPT;
        if(!result && a && k) {
            result=v6_campaign_progress_read(&v6_campaign_dos,save_backup,&c,&red,&yellow,&map);
            if(!result && (!checkpoint_bank_valid(&c) || c.room_x!=111 || c.room_y!=105 || red.companion))result=V6_SAVE_CORRUPT;
        }
        if(!result)result=v6_campaign_progress_recover(&v6_campaign_dos,save_name,save_temp,save_backup,&station_saved,&station_saved_red,&station_saved_yellow,&station_exploration);
        if(!result && !v6_campaign_dos_flush("DF1:"))result=V6_SAVE_IO;
    }
    if(result) {station_save_diag.values[1]=result;station_save_diag.values[2]=1;CloseLibrary((struct Library *)DOSBase);return 20;}
    result=run();
    if(!result) {
        /* No mid-script snapshots or unsupported checkpoint banks. */
        if(rescue_vm.active || rescue_vm.error || !checkpoint_bank_valid(&world.save) || world.save.room_x!=111 || world.save.room_y!=105)result=V6_SAVE_INVALID;
        else result=v6_campaign_progress_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&station_story,&station_exploration);
        if(!v6_campaign_dos_flush("DF1:"))result=V6_SAVE_IO;
    }
    station_save_diag.values[1]=result;station_save_diag.values[13]=station_story.rescue_triggered;
    station_save_diag.values[14]=station_story.yellow_rescued;station_save_diag.values[15]=station_story.companion;
    station_save_diag.values[16]=station_trigger.requests;station_save_diag.values[17]=rescue_vm.cues;
    CloseLibrary((struct Library *)DOSBase);return result?20:0;
#elif defined(V6_BUILDING_SAVE)
    int result,a,k;V6HallwayStory story;
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase)return 20;
    a=v6_campaign_dos.exists(save_name);k=v6_campaign_dos.exists(save_backup);
    result=V6_SAVE_OK;building_stage=(a || k)?2:1;building_save_diag.values[0]=building_stage;
    if(a<0 || k<0)result=V6_SAVE_IO;
    if(!result && building_stage==2) {
        result=v6_campaign_read(&v6_campaign_dos,a?save_name:save_backup,&building_saved,&story);
        if(!result && (!checkpoint_bank_valid(&building_saved) || building_saved.room_x!=V6_SAVE_ROOM_X || building_saved.room_y!=V6_SAVE_ROOM_Y || story.companion || story.rescue_triggered || story.red_rescued))result=V6_SAVE_CORRUPT;
        if(!result && a && k) {
            V6CheckpointSave backup;V6HallwayStory bs;
            result=v6_campaign_read(&v6_campaign_dos,save_backup,&backup,&bs);
            if(!result && (!checkpoint_bank_valid(&backup) || backup.room_x!=V6_SAVE_ROOM_X || backup.room_y!=V6_SAVE_ROOM_Y || bs.companion || bs.rescue_triggered || bs.red_rescued))result=V6_SAVE_CORRUPT;
        }
        if(!result)result=v6_campaign_recover(&v6_campaign_dos,save_name,save_temp,save_backup,&building_saved,&story);
        if(!result && !v6_campaign_dos_flush("DF1:"))result=V6_SAVE_IO;
    }
    if(result) {building_save_diag.values[1]=result;building_save_diag.values[2]=1;CloseLibrary((struct Library *)DOSBase);return 20;}
    result=run();
    if(!result && building_stage==1) {
#ifdef V6_TOWER_ARRIVAL_SAVE
        /* A handoff already updates the in-memory centre. Admit disk writes
         * only after the final source arrival SAVE event, with control back. */
        if(arrival.state || !arrival.control || !(arrival.events&V6_ARRIVAL_SAVE) ||
           departure.state || travel_leg!=(V6_SAVE_TICKS==64?1:2))result=V6_SAVE_INVALID;
        else
#endif
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
