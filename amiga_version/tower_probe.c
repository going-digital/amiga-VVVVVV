#if defined(V6_MAP_DISPLAY_CAPTURE) && !defined(V6_MAP_INPUT_CAPTURE)
#error Map display requires the physical keyboard/menu fixture
#endif
#if defined(V6_MAP_DIRTY_CAPTURE) && !defined(V6_MAP_DISPLAY_CAPTURE)
#error Map refresh stress fixture requires the map display
#endif
#if defined(V6_MAP_INPUT_CAPTURE) && !defined(V6_VSTITCH_HINT_CAPTURE)
#error Map control capture requires the resident upper V Stitch hint/save fixture
#endif
#if defined(V6_VSTITCH_HINT_LOAD) && !defined(V6_VSTITCH_HINT_CAPTURE)
#error Hint fresh-boot load requires the V Stitch hint capture
#endif
#if defined(V6_VSTITCH_HINT_CAPTURE) && (!defined(V6_VSTITCH_INPUT_CAPTURE) || defined(V6_PRIZE_RETURN_INPUT_CAPTURE))
#error Upper hint capture requires V Stitch and excludes the west return replay
#endif
#if defined(V6_NORTH_ROUTE) && (!defined(V6_MENU_SLIDE) || defined(V6_PRIZE_RETURN_INPUT_CAPTURE))
#error North route requires the complete menu slide build and excludes the west fixture
#endif
#if defined(V6_PRIZE_RETURN_INPUT_CAPTURE) && (!defined(V6_VSTITCH_INPUT_CAPTURE) || !defined(V6_TOWER_PICKUP_SCREEN))
#error West return capture requires the lower V Stitch approach and pickup controller
#endif
#ifdef V6_MAP_DISPLAY_CAPTURE
#define MAP_AUX_TRACE_ROWS(n) 1
#define MAP_AUX_TRACE_ENABLED 0
#else
#define MAP_AUX_TRACE_ROWS(n) (n)
#define MAP_AUX_TRACE_ENABLED 1
#endif
/* The long west replay and upper-hint replay own dedicated traces. Auxiliary fixture
 * traces retain a header/one slot but are disabled to fit the stock 1 MB boot. */
#if defined(V6_PRIZE_RETURN_INPUT_CAPTURE) || defined(V6_VSTITCH_HINT_CAPTURE)
#define AUX_TRACE_ENABLED 0
#define AUX_TRACE_ROWS(n) 1
#else
#define AUX_TRACE_ENABLED 1
#define AUX_TRACE_ROWS(n) (n)
#endif
#if defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE) && (!defined(V6_PRIZE_INPUT_CAPTURE) || !defined(V6_TOWER_PICKUP_SCREEN) || defined(V6_VSTITCH_INPUT_CAPTURE))
#error Collection input capture requires the pickup screen and excludes V Stitch input capture
#endif
#if defined(V6_VSTITCH_INPUT_CAPTURE) && (!defined(V6_PRIZE_INPUT_CAPTURE) || !defined(V6_TOWER_PRIZE))
#error V Stitch lower-passage admission is only for the Prize input capture
#endif
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
#ifdef V6_VSTITCH_HINT_CAPTURE
static V6CampaignHints ui_loaded_hints;
#endif
#endif
#endif
static const V6TeleporterDestination tele_residents[2]={{111,104},{110,105}};
static V6TeleporterDestination menu_target;
static unsigned menu_save_pending,menu_travel_active,menu_exit_pending;
static volatile struct {ULONG magic,version,count;LONG snapshot[23],records[AUX_TRACE_ROWS(128)][36];}
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
#if defined(V6_SAVE_DISPLAY_CAPTURE) && !defined(V6_MAP_DISPLAY_CAPTURE)
#error Save display requires the bounded map display fixture
#endif
#ifdef V6_MAP_INPUT_CAPTURE
#include <proto/cia.h>
#include "keyboard.h"
#include "map_menu.h"
static struct Library *keyboard_resource;
static V6Keyboard keyboard;
static V6MapMenu map_menu;
static unsigned map_action_held,map_previous_buttons;
static ULONG map_pause_hash;
static UBYTE *map_captions;
#ifndef V6_MENU_COMPLETE
static const V6RescueSpeech map_messages[6]={
    {0,1,2,{"Map","Left/right: tabs; ENTER: return"}},
    {1,1,2,{"Crew","Left/right: tabs; ENTER: return"}},
    {2,1,2,{"Stats","Left/right: tabs; ENTER: return"}},
    {3,1,3,{"Save tab","Space or fire: quicksave","ENTER: return to game"}},
    {4,1,2,{"Game saved","ENTER: return to game"}},
    {5,1,2,{"Save failed","ENTER: return to game"}}
};
#endif
#ifdef V6_NORTH_ROUTE
#define MAP_CAPTURE_ROWS(n) 16
#else
#define MAP_CAPTURE_ROWS(n) (n)
#endif
static volatile struct {ULONG magic,version,values[12],count,records[MAP_CAPTURE_ROWS(128)][8];}
    map_diag={0x56364d49,1,{0},0,{{0}}};
#ifdef V6_MAP_DISPLAY_CAPTURE
#include "map_draw.h"
#include "map_transition.h"
#include "map_slide.h"
static unsigned map_slide_offset;
static volatile struct {ULONG magic,version,count,records[MAP_CAPTURE_ROWS(96)][5];}
    map_slide_diag={0x56364d53,1,0,{{0}}};
static V6MapTransition map_transition;
static volatile struct {ULONG magic,version,count,records[MAP_CAPTURE_ROWS(64)][7];}
    map_transition_diag={0x56364d54,1,0,{{0}}};
#include "map_assets.h"
static UBYTE *map_bitmap;
#ifdef V6_MENU_COMPLETE
#include "campaign_menu.h"
#include "ui_menu.h"
#include "ui_assets.h"
static V6CampaignMenu campaign_menu,ui_loaded_menu;
static V6SaveClock menu_action_clock;
static V6SaveSummary menu_candidate;
static unsigned menu_candidate_pending,menu_crew_frame,menu_crew_delay=4;
static int menu_session_deaths;
static UBYTE *ui_bitmaps,*ui_stencil,*ui_footer,*ui_receipt,*ui_note,*ui_tabs,*ui_prompt,*ui_icon_alpha;
static unsigned ui_render_bank,ui_ready,ui_pending,ui_row,ui_present_pending;
static V6UIState ui_pending_state;
static V6UIState ui_rendered;
static unsigned ui_sprite_page[2],ui_sprite_tiles[2][6];
static volatile struct {ULONG magic,version,values[8];} menu_startup_diag={0x56365354,1,{0}};
static volatile struct {ULONG magic,version,values[18];} menu_complete_diag={0x56364d55,2,{0}};
#endif
#ifdef V6_SAVE_DISPLAY_CAPTURE
#include "save_assets.h"
#include <dos/dosextens.h>
static UBYTE *save_bitmap;
static volatile struct {ULONG magic,version,values[4];}
    save_display_diag={0x56365344,1,{0}};
#endif
static void ui_copy(void *,const void *,unsigned);
static V6Exploration map_bitmap_exploration;
static unsigned map_bitmap_rows,map_cursor_state,map_cursor_delay;
#ifdef V6_NORTH_ROUTE
static unsigned map_bitmap_stop=240;
#endif
static volatile struct {ULONG magic,version,values[5],count,records[MAP_CAPTURE_ROWS(128)][6];}
    map_display_diag={0x56364d50,1,{0},0,{{0}}};
#endif
#endif
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
static volatile struct {ULONG magic,version,count,bytes;LONG snapshot[sizeof(V6Companion)/4],records[AUX_TRACE_ROWS(64)][14];}
    station_travel_trace={0x56365943,1,0,sizeof(V6Companion),{0},{{0}}};
#endif

static int rescue_bars,rescue_fade,rescue_fade_mode,rescue_fire;
static UBYTE *rescue_captions;
static unsigned rescue_flips_applied;
static volatile struct { ULONG magic,version,count,capacity,records[AUX_TRACE_ROWS(128)][18]; }
    rescue_trace={0x56365256,1,0,128,{{0}}};
static volatile struct { ULONG magic,version,values[18]; }
    rescue_diag={0x56365241,1,{0}};
static volatile struct { ULONG magic,version,count,capacity,records[AUX_TRACE_ROWS(128)][14]; }
    companion_trace={0x56364354,1,0,128,{{0}}};
static volatile struct { ULONG magic,version,values[14]; }
    companion_diag={0x56364346,1,{0}};
static void companion_record(void)
{
#ifdef V6_NORTH_ROUTE
    companion_diag.values[0]=companion.visible;
    companion_diag.values[1]=companion.following;
    companion_diag.values[2]=companion.mood;
    companion_diag.values[3]=companion.frame;
    companion_diag.values[4]=companion.body.x;
    companion_diag.values[5]=companion.body.y;
    companion_diag.values[6]=companion.body.vx;
    companion_diag.values[7]=companion.body.vy;
    companion_diag.values[8]=companion.body.dir;
    companion_diag.values[9]=companion.animation.delay;
    companion_diag.values[10]=companion.animation.walk;
    companion_diag.values[11]=companion.spawns;
    companion_diag.values[12]=companion.steps;
    companion_diag.values[13]=companion.follow_steps;
#else
    unsigned i;
    ULONG values[14]={companion.visible,companion.following,companion.mood,companion.frame,
        companion.body.x,companion.body.y,companion.body.vx,companion.body.vy,companion.body.dir,
        companion.animation.delay,companion.animation.walk,companion.spawns,companion.steps,companion.follow_steps};
    for(i=0;i<14;++i) companion_diag.values[i]=values[i];
#ifdef V6_STATION_MENU
    if(AUX_TRACE_ENABLED && (station_travel_trace.count<64 && station_travel_trace.count<menu_travel_trace.count)) {
        for(i=0;i<14;++i)station_travel_trace.records[station_travel_trace.count][i]=values[i];
        ++station_travel_trace.count;
    }
#endif
    if(AUX_TRACE_ENABLED && (companion_trace.count<128)) {
        volatile ULONG *record=companion_trace.records[companion_trace.count];
        for(i=0;i<14;++i) record[i]=values[i];
        ++companion_trace.count;
    }
#endif
}
static void rescue_record(void)
{
#ifdef V6_NORTH_ROUTE
    rescue_diag.values[0]=rescue_vm.pc;
    rescue_diag.values[1]=rescue_vm.active;
    rescue_diag.values[2]=rescue_vm.error;
    rescue_diag.values[3]=rescue_vm.delay;
    rescue_diag.values[4]=rescue_vm.waiting;
    rescue_diag.values[5]=rescue_vm.bars;
    rescue_diag.values[6]=rescue_vm.control;
    rescue_diag.values[7]=rescue_vm.mood;
    rescue_diag.values[8]=rescue_vm.following;
    rescue_diag.values[9]=rescue_vm.ui_serial;
    rescue_diag.values[10]=rescue_vm.cues;
    rescue_diag.values[11]=rescue_vm.flips;
    rescue_diag.values[12]=rescue_vm.fade;
    rescue_diag.values[13]=rescue_vm.speech?rescue_vm.speech->index+1:0;
    rescue_diag.values[14]=station_story.yellow_rescued;
    rescue_diag.values[15]=station_story.companion;
    rescue_diag.values[16]=rescue_bars;
    rescue_diag.values[17]=rescue_fade;
#else
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
    if(AUX_TRACE_ENABLED && (rescue_trace.count<128)) {
        volatile ULONG *record=rescue_trace.records[rescue_trace.count];
        for(i=0;i<18;++i) record[i]=values[i];
        ++rescue_trace.count;
    }
#endif
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
static volatile struct { ULONG magic,version,count,capacity,records[AUX_TRACE_ROWS(128)][7]; }
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
    if(AUX_TRACE_ENABLED && (trigger_trace.count<128)) {
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
#include "screen_shake_dma.h"
#include "teleporter_assets.h"
#if defined(V6_TOWER_RESCUE) && !defined(V6_TOWER_STATION)
#error Building route renderer currently reserves six channels plus player; crew sharing is pending
#endif
static UWORD *building_dma;
#ifdef V6_NORTH_ROUTE
#include "teleporter_prepared_assets.h"
static const UWORD *const building_prepared[10]={north_portal_frames[0],north_portal_frames[0],north_portal_frames[1],north_portal_frames[2],north_portal_frames[3],north_portal_frames[4],north_portal_frames[5],north_portal_frames[6],north_portal_frames[7],north_portal_frames[8]};
#else
static UWORD building_prepared[10][6*V6_TELEPORTER_DMA_WORDS];
#endif
static int building_frames[2]={-1,-1};
static V6TeleporterAnimation building_animation;
#ifdef V6_NORTH_ROUTE
static V6Terrain north_shared_terrain;
static unsigned north_terrain_pending,north_terrain_row;
#define building_terrain north_shared_terrain
#else
static V6Terrain building_terrain;
#endif
#ifdef V6_TOWER_ENERGIZE
#include "energize_assets.h"
#ifdef V6_NORTH_ROUTE
#define energize_terrain north_shared_terrain
#else
static V6Terrain energize_terrain;
#endif
#ifdef V6_MENU_COMPLETE
#define energize_prepared building_prepared
#else
static UWORD energize_prepared[10][6*V6_TELEPORTER_DMA_WORDS];
#endif
#ifdef V6_TOWER_STATION
#include "frown_assets.h"
#include "shenanigan_assets.h"
#ifdef V6_TOWER_SHENANIGAN
#include "platform.h"
#ifdef V6_NORTH_ROUTE
#define shenanigan_terrain north_shared_terrain
#else
static V6Terrain shenanigan_terrain;
#endif
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
#ifdef V6_NORTH_ROUTE
#define prize_terrain north_shared_terrain
#else
static V6Terrain prize_terrain;
#endif
static V6Prize station_prize;
static V6Collect station_collected;
#ifdef V6_TOWER_PICKUP_SCREEN
#ifndef V6_TOWER_UI_SAVE
#error Pickup screen requires the caption/menu allocation
#endif
#include "trinket_screen.h"
#include "pickup_draw.h"
#include "pickup_fade.h"
#include "pickup_copper.h"
#include "pickup_assets.h"
static V6TrinketScreen pickup_screen;
typedef char PickupActorWordSize[(sizeof(V6Prize)%sizeof(ULONG))==0?1:-1];
static V6PickupDraw pickup_draw;
static V6PickupFade pickup_fade;
static unsigned pickup_fade_shown;
static ULONG pickup_colours;
static volatile struct {ULONG magic,version,count,records[MAP_AUX_TRACE_ROWS(64)][8];}
    pickup_fade_diag={0x56364646,1,0,{{0}}};
static UBYTE *pickup_banks,*pickup_zero;
static UWORD pickup_mask[V6_PICKUP_PLANE_BYTES/2] __attribute__((aligned(4)));
static UWORD pickup_ink[V6_PICKUP_PLANE_BYTES/2] __attribute__((aligned(4)));
static unsigned pickup_rows[2],pickup_bar_rows[2];
static unsigned pickup_bar_room[2],pickup_bar_camera[2];
static unsigned pickup_bar_position[2],pickup_render_bars;
static volatile struct {ULONG magic,version,count,records[MAP_AUX_TRACE_ROWS(96)][7];}
    pickup_interpolation={0x56365049,1,0,{{0}}};
static UWORD pickup_bar_masks[2][2][20];
typedef ULONG PickupCopperLong __attribute__((__may_alias__));
static UWORD pickup_copper_cache[4][V6_PICKUP_COPPER_WORDS] __attribute__((aligned(4)));
static unsigned pickup_copper_key[4],pickup_copper_words[4];
static unsigned pickup_copper_tints[4][6],pickup_copper_tint_count[4];
static ULONG pickup_copper_colours[4];
static const UWORD pickup_blank[20] __attribute__((aligned(4)))={0};
static ULONG pickup_world_hash,pickup_actor_snapshot[sizeof(V6Prize)/sizeof(ULONG)];
static unsigned pickup_hash_valid;
static volatile struct {ULONG magic,version,count,values[8],records[MAP_AUX_TRACE_ROWS(256)][5];}
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
static volatile struct {ULONG magic,version,count,records[256][8];}
    pickup_frame_trace={0x56365058,1,0,{{0}}};
static unsigned prize_ui_stage,prize_pickup_release;
#endif
#ifdef V6_VSTITCH_HINT_CAPTURE
#define PRIZE_INPUT_TICKS 96
#elif defined(V6_PRIZE_RETURN_INPUT_CAPTURE)
#define PRIZE_INPUT_TICKS 660
#define PRIZE_TRACE_FIELDS 32
#elif defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE)
#define PRIZE_INPUT_TICKS 180
#elif defined(V6_VSTITCH_INPUT_CAPTURE)
#define PRIZE_INPUT_TICKS 302
#else
#define PRIZE_INPUT_TICKS 224
#endif
#if defined(V6_PRIZE_ROUTE_CAPTURE) || defined(V6_PRIZE_INPUT_CAPTURE)
#ifndef PRIZE_TRACE_FIELDS
#define PRIZE_TRACE_FIELDS 24
#endif
static volatile struct {ULONG magic,version,count;LONG records[MAP_AUX_TRACE_ROWS(PRIZE_INPUT_TICKS)][PRIZE_TRACE_FIELDS];}
    prize_route_trace={
#ifdef V6_PRIZE_INPUT_CAPTURE
        0x5636504e,
#else
        0x56365052,
#endif
        1,0,{{0}}};
#endif
#ifdef V6_PRIZE_INPUT_CAPTURE
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
#include "../tools/amiga/prize_checkpoint_replay.h"
#include "../tools/amiga/prize_collection_replay.h"
#include "../tools/amiga/prize_return_replay.h"
#elif defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE)
#include "../tools/amiga/prize_collection_replay.h"
#elif defined(V6_VSTITCH_HINT_CAPTURE)
/* Dedicated upper-checkpoint input schedule below. */
#elif defined(V6_VSTITCH_INPUT_CAPTURE)
#include "../tools/amiga/prize_checkpoint_replay.h"
#else
#include "../tools/amiga/prize_input_replay.h"
#endif
#if defined(V6_PRIZE_ROUTE_CAPTURE) || !defined(V6_TOWER_PRIZE)
#error Input capture requires Prize and excludes placement capture
#endif
#endif
#define PRIZE_FG(value,fallback) (route.index==8?(value):(fallback))
#else
#define PRIZE_FG(value,fallback) (fallback)
#endif
#ifdef V6_VSTITCH_INPUT_CAPTURE
#include "vstitch_assets.h"
#ifdef V6_NORTH_ROUTE
#define vstitch_terrain north_shared_terrain
#else
static V6Terrain vstitch_terrain;
#endif
#ifdef V6_VSTITCH_HINT_CAPTURE
#include "vstitch_trigger.h"
#include "vstitch_hint_draw.h"
static V6VStitchTrigger vstitch_hint;
static int vstitch_seen;
static unsigned vstitch_previous_level,vstitch_bitmap_ready[2];
static UWORD vstitch_mask[V6_HINT_BYTES/2] __attribute__((aligned(4)));
static UWORD vstitch_ink[V6_HINT_BYTES/2] __attribute__((aligned(4)));
#ifdef V6_NORTH_ROUTE
#define VSTITCH_DRAW_ROWS 1
#define VSTITCH_HINT_ROWS 1
#else
#define VSTITCH_DRAW_ROWS 128
#define VSTITCH_HINT_ROWS 96
#endif
static volatile struct {ULONG magic,version,count,compositions;LONG records[VSTITCH_DRAW_ROWS][7];}
    vstitch_draw_trace={0x56365644,1,0,0,{{0}}};
static volatile struct {ULONG magic,version,count;LONG records[VSTITCH_HINT_ROWS][16];}
    vstitch_hint_trace={0x56365648,1,0,{{0}}};
#endif
#define VSTITCH_FG(value,fallback) (route.index==9?(value):(fallback))
#else
#define VSTITCH_FG(value,fallback) (fallback)
#endif
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
#include "prize_return_sprite.h"
#include "prize_return_draw.h"
#include "prize_return_sprite_assets.h"
#include "deception_assets.h"
#include "downunder_assets.h"
static V6Terrain deception_terrain,downunder_terrain;
static V6PrizeReturn west_actors;
static V6Block west_physics_blocks[6];
static V6ReturnEnemyAnimation west_enemy_animation[2];
static V6CollisionAnimation west_player_animation;
static int west_player_frame,west_platform_y[2][4];
static unsigned west_enemy_hits,west_tread_phase,west_tread_delay;
static int west_tread_drawn[2];
static unsigned west_copper_ready[2],west_colour_words[2][8];
#define WEST_FG(a,b,c) (route.index==10?(a):route.index==11?(b):(c))
#else
#define WEST_FG(a,b,c) (c)
#endif
#ifdef V6_NORTH_ROUTE
#include "north_route.h"
#include "sprite_mux.h"
#include "north_actor_assets.h"
#include "prize_return_sprite.h"
#include "prize_return_sprite_assets.h"
#include "pixel_collision.h"
#ifdef V6_REGIONAL_CONTENT
#include "region_cache.h"
static ULONG ui_game_hash(void);
static V6RegionCache north_regions;
static const V6RegionRoom *north_content;
static struct {
    unsigned active;UWORD *dma,*ints,*adk;APTR *old_irq;struct View **view;
    UWORD **lists;unsigned *back;ULONG *start,*previous,*logic_frame;
} region_runtime;
static volatile struct {ULONG magic,version,loads,hits,errors,pauses,drain_fields,room,region,capacity,violations;}
    region_diag={0x56365243,1,0,0,0,0,0,0,0,V6_REGION_BYTES*V6_REGION_SLOTS,0};
#include "region_bindings.h"
#else
#include "reflect_assets.h"
#include "yesmen_assets.h"
#include "gantry_assets.h"
#include "security_assets.h"
#include "linear_assets.h"
#include "filter_assets.h"
#include "traffic_assets.h"
#include "leap_assets.h"
#include "solitude_assets.h"
#include "conundrum_assets.h"
#include "welcome_assets.h"
#endif
#ifdef V6_REGIONAL_CONTENT
#define NORTH_DISPLAY_BYTES(name) (north_content->display_bytes)
#else
#define NORTH_DISPLAY_BYTES(name) sizeof(name##_display)
#endif
#define REFLECT_DISPLAY_BYTES NORTH_DISPLAY_BYTES(reflect)
#define YESMEN_DISPLAY_BYTES NORTH_DISPLAY_BYTES(yesmen)
#define GANTRY_DISPLAY_BYTES NORTH_DISPLAY_BYTES(gantry)
#define SECURITY_DISPLAY_BYTES NORTH_DISPLAY_BYTES(security)
#define LINEAR_DISPLAY_BYTES NORTH_DISPLAY_BYTES(linear)
#define FILTER_DISPLAY_BYTES NORTH_DISPLAY_BYTES(filter)
#define TRAFFIC_DISPLAY_BYTES NORTH_DISPLAY_BYTES(traffic)
#define LEAP_DISPLAY_BYTES NORTH_DISPLAY_BYTES(leap)
#define SOLITUDE_DISPLAY_BYTES NORTH_DISPLAY_BYTES(solitude)
#define CONUNDRUM_DISPLAY_BYTES NORTH_DISPLAY_BYTES(conundrum)
#define WELCOME_DISPLAY_BYTES NORTH_DISPLAY_BYTES(welcome)
#include "firststeps_program.h"
#include "sample_unpack.h"
static V6FirstStepsTrigger firststeps_trigger;
static V6ConundrumTrigger conundrum_trigger;
#if defined(V6_CONUNDRUM_EDGE) || defined(V6_WELCOME_EDGE)
static unsigned conundrum_edge_settled;
#endif
static unsigned conundrum_previous_level;
static const V6RescueSpeech conundrum_speeches[2]={{0,1,2,{"Press SPACE / Z / V", "to flip",0,0}},{1,1,2,{"","",0,0}}};
static volatile struct {ULONG magic,version,flags,active,pending,contacts,removed,visible,timer,level,hints,room,x,y,gravity,deaths;} conundrum_diag={0x5636434e,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0};
static unsigned north_caption_mode,north_caption_pending,north_pcm_pending;
static V6SampleJob north_pcm_job;
static volatile struct {ULONG magic,version,seen,active,pc,waiting,cues,requests,error,caption,room;} firststeps_diag={0x56364653,1,0,0,0,0,0,0,0,0,0};
#include "terminal.h"
#include "terminal_read.h"
#include "terminal_layer.h"
#include "activity.h"
#include "terminal_station_program.h"
#include "terminal_layer_assets.h"
#include "sample_unpack.h"
static V6Terminal north_terminal;
static unsigned north_terminal_cue,north_read_pending,north_read_enter,north_read_fire,north_read_block_action;
static int north_activity_index=-1;
static V6TerminalRead north_reader,north_read_prepared;
static unsigned north_read_bars,north_layer_stage,north_layer_row,north_layer_bars[2],north_read_copied;

static volatile struct {ULONG magic,version,values[20];} north_read_diag={0x56364e52,1,{0}};
static volatile struct {ULONG magic,version,values[6];} north_terminal_diag={0x56364e54,1,{0}};
static V6NorthRoute north_actors;
static V6CompanionRest north_companion_rest[3];
static unsigned north_memo_pending;
static V6MuxPlan north_mux_plan;
static V6MuxActor north_mux_actors[14];
typedef struct {const UWORD *data;UWORD stride,mask;} NorthDMA;
static NorthDMA north_mux_dma[14];
static UWORD *north_extra_dma,*north_bob_source;
static UBYTE *north_bob_bitmaps;
static unsigned north_bob_column[2],north_bob_height[2];
static V6MuxOverlay north_overlay;
#ifdef V6_NORTH_BOB
static unsigned north_bob_actor;
static volatile struct {ULONG magic,version,values[12];} north_bob_diag={0x56364e42,1,{0}};
#endif
static unsigned north_copper_ready[2],north_copper_tick[2],north_copper_room[2];
static UWORD north_base_copper[2][192];
static V6TerminalPrefix north_terminal_prefix[2];
static unsigned north_base_words[2],north_base_room[2],north_base_tail[2];
static V6ReturnEnemyAnimation north_animation[5];
#define NORTH_FG(a,b,c,e,f,g,h,j,k,l,m,d) (route.index==10?(a):route.index==11?(b):route.index==12?(c):route.index==13?(e):route.index==14?(f):route.index==15?(g):route.index==16?(h):route.index==17?(j):route.index==18?(k):route.index==19?(l):route.index==20?(m):(d))
#else
#define NORTH_FG(a,b,c,e,f,g,h,j,k,l,m,d) (d)
#endif
#ifdef V6_NORTH_ROUTE
#define frown_terrain north_shared_terrain
#else
static V6Terrain frown_terrain;
#endif
#define FG_OFFSETS NORTH_FG(reflect_pair_offsets,yesmen_pair_offsets,gantry_pair_offsets,security_pair_offsets,linear_pair_offsets,filter_pair_offsets,traffic_pair_offsets,leap_pair_offsets,solitude_pair_offsets,conundrum_pair_offsets,welcome_pair_offsets,WEST_FG(deception_pair_offsets,downunder_pair_offsets,VSTITCH_FG(vstitch_pair_offsets,PRIZE_FG(prize_pair_offsets, (route.index==7?shenanigan_pair_offsets:route.index==6?frown_pair_offsets:route.index==5?energize_pair_offsets:tower_pair_offsets)))))
#define FG_PAIRS NORTH_FG(reflect_pairs,yesmen_pairs,gantry_pairs,security_pairs,linear_pairs,filter_pairs,traffic_pairs,leap_pairs,solitude_pairs,conundrum_pairs,welcome_pairs,WEST_FG(deception_pairs,downunder_pairs,VSTITCH_FG(vstitch_pairs,PRIZE_FG(prize_pairs, (route.index==7?shenanigan_pairs:route.index==6?frown_pairs:route.index==5?energize_pairs:tower_pairs)))))
#define FG_WORDS NORTH_FG(REFLECT_PAIR_WORDS,YESMEN_PAIR_WORDS,GANTRY_PAIR_WORDS,SECURITY_PAIR_WORDS,LINEAR_PAIR_WORDS,FILTER_PAIR_WORDS,TRAFFIC_PAIR_WORDS,LEAP_PAIR_WORDS,SOLITUDE_PAIR_WORDS,CONUNDRUM_PAIR_WORDS,WELCOME_PAIR_WORDS,WEST_FG(DECEPTION_PAIR_WORDS,DOWNUNDER_PAIR_WORDS,VSTITCH_FG(VSTITCH_PAIR_WORDS,PRIZE_FG(PRIZE_PAIR_WORDS, (route.index==7?SHENANIGAN_PAIR_WORDS:route.index==6?FROWN_PAIR_WORDS:route.index==5?ENERGIZE_PAIR_WORDS:TOWER_PAIR_WORDS)))))
#define FG_COUNT NORTH_FG(REFLECT_TILE_COUNT,YESMEN_TILE_COUNT,GANTRY_TILE_COUNT,SECURITY_TILE_COUNT,LINEAR_TILE_COUNT,FILTER_TILE_COUNT,TRAFFIC_TILE_COUNT,LEAP_TILE_COUNT,SOLITUDE_TILE_COUNT,CONUNDRUM_TILE_COUNT,WELCOME_TILE_COUNT,WEST_FG(DECEPTION_TILE_COUNT,DOWNUNDER_TILE_COUNT,VSTITCH_FG(VSTITCH_TILE_COUNT,PRIZE_FG(PRIZE_TILE_COUNT, (route.index==7?SHENANIGAN_TILE_COUNT:route.index==6?FROWN_TILE_COUNT:route.index==5?ENERGIZE_TILE_COUNT:TOWER_TILE_COUNT)))))
#define FG_PALETTE NORTH_FG(reflect_palette,yesmen_palette,gantry_palette,security_palette,linear_palette,filter_palette,traffic_palette,leap_palette,solitude_palette,conundrum_palette,welcome_palette,WEST_FG(deception_palette,downunder_palette,VSTITCH_FG(vstitch_palette,PRIZE_FG(prize_palette, (route.index==7?shenanigan_palette:route.index==6?frown_palette:route.index==5?energize_palette:tower_palette)))))
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(r->index==10 || r->index==11) {
        v6_prize_return_platforms(&west_actors,&r->room,&r->session->player,
            r->session->life_timer,r->session->motion.pending_y);
        return 1;
    }
#endif
#ifdef V6_NORTH_ROUTE
    if(r->index>=10){unsigned i;V6Player *p=&r->session->player;
        north_actors.push.pending_y=r->session->motion.pending_y;
        for(i=north_actors.platform_count;i>0;--i){V6Platform *e=&north_actors.platforms[i-1];
            if(r->index==10){if(e->vx)continue;
                v6_platform_step_lane(e,north_actors.blocks,north_actors.block_count,north_reflect_walls[i-1],1);
                v6_platform_push_vertical(e,p,&r->room,&north_actors.push);
            }else {if(e->vy)continue;
                v6_platform_step_lane(e,north_actors.blocks,north_actors.block_count,north_gantry_walls,0);}
        }
        if(r->index==12)v6_platform_carry_horizontal(p,&r->room,north_actors.platforms,north_actors.platform_count,r->session->life_timer,north_actors.push.pending_y);
        return 1;}
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
        ++prize_pickups;prize_audio_pending|=V6_PRIZE_PICKUP;
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
    if(events&V6_PRIZE_SOUND) {
        unsigned gate;
        for(gate=0;gate<3;++gate)
            if(events&(1U<<(V6_PRIZE_GATE_SOUND_SHIFT+gate)))++prize_sounds;
        prize_audio_pending|=events&V6_PRIZE_GATE_SOUND_MASK;
    }
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(r->index==10 || r->index==11) {
        v6_prize_return_entities(&west_actors,&r->room);
        r->room.block_count=v6_prize_return_physics_blocks(&west_actors,&r->session->player,west_physics_blocks);
        r->room.blocks=west_physics_blocks;
    }
#endif
#ifdef V6_NORTH_ROUTE
    if(r->index>=10){unsigned events;
        if(r->index==14 && v6_terminal_tick(&north_terminal)){north_terminal_cue|=1;++north_terminal_diag.values[0];}
        if(r->index==11){unsigned i;for(i=5;i>0;--i){unsigned lane=i-1==1?1:i-1<3?0:2;
            v6_enemy_step_vertical_cached(&north_actors.enemies[i-1],north_yesmen_walls[lane]);}events=0;
        }else if(r->index==16){unsigned i;for(i=3;i>0;--i){
            v6_enemy_step_vertical_cached(&north_actors.enemies[i-1],north_traffic_walls[i-1]);}events=0;
        }else if(r->index==14){unsigned i;for(i=2;i>0;--i){
            v6_enemy_step_horizontal_cached(&north_actors.enemies[i-1],north_linear_walls[i-1]);}events=0;
        }else events=v6_north_entities(&north_actors,&r->room,0);
        if(events&V6_DISAPPEAR_SOUND)prize_audio_pending|=1U<<V6_PRIZE_GATE_SOUND_SHIFT;
        return !(events&V6_DISAPPEAR_FULL);}
#endif
    return r->index!=8 || prize_events(r,v6_prize_entities(&station_prize,&r->room,&station_collected));
}
static int prize_contacts(V6TowerRoute *r,void *context)
{
    (void)context;
#ifdef V6_NORTH_ROUTE
    if(r->index>=10){unsigned hits=v6_north_contacts(&north_actors,&r->session->player),i;
        if(r->index==14){v6_terminal_contact(&north_terminal,&r->session->player);
            north_terminal_diag.values[1]=north_terminal.active;north_terminal_diag.values[2]=r->session->player.x;
            north_terminal_diag.values[3]=r->session->player.y;north_terminal_diag.values[4]=north_actors.blocks[0].w;
            north_terminal_diag.values[5]=north_actors.blocks[0].h;
            north_activity_index=north_actors.blocks[0].w?v6_activity_find(north_actors.blocks,north_actors.block_count,&r->session->player):-1;}
        for(i=0;i<north_actors.enemy_count;++i)if((hits&(1U<<i)) &&
            v6_pixel_hit(return_player_collision[player_frame],r->session->player.x,r->session->player.y,
                (r->index==13?north_drone_collision:r->index==14?north_linear_collision:r->index==16?north_traffic_collision:north_enemy_collision)[north_animation[i].frame],north_actors.enemies[i].x,north_actors.enemies[i].y))v6_tower_session_die(r->session);
        return 1;}
#endif
    if(r->index==8)v6_prize_collide(&station_prize,&r->session->player);
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    else if(r->index==10 || r->index==11) {
        const uint32_t *m[2];unsigned i;
        r->room.blocks=west_actors.blocks;r->room.block_count=west_actors.platform_count;
        v6_platform_disable_overlaps(&r->session->player,west_actors.platforms,
            west_actors.platform_count,west_actors.blocks,west_actors.platform_count);
        for(i=0;i<2;++i)m[i]=west_enemy_animation[i].frame<0?
            return_player_collision[0]:return_enemy_collision[west_enemy_animation[i].frame];
        if(v6_prize_return_pixel_hurt(&west_actors,&r->session->player,
            return_player_collision[west_player_frame],m[0],m[1])) {
            ++west_enemy_hits;v6_tower_session_die(r->session);
        }
    }
#endif
    return 1;
}
static int prize_death(V6TowerRoute *r,void *context)
{
    (void)context;
#ifdef V6_NORTH_ROUTE
    if(r->index>=10)return !(v6_north_entities(&north_actors,&r->room,1)&V6_DISAPPEAR_FULL);
#endif
    return r->index!=8 || prize_events(r,v6_prize_death(&station_prize,&r->room));
}
static int station_route_step(V6TowerRoute *r,unsigned input,V6TowerRoutePhase phase,void *context)
{
    V6TowerRouteHooks hooks={phase,prize_entities,prize_contacts,prize_death};
#ifdef V6_CONUNDRUM_TOUR
    input=r->index==19 && r->session->player.x>40 && !(conundrum_trigger.active&1)?V6_LEFT:0;
#endif
#ifdef V6_WELCOME_EDGE
    input=r->index==V6_NORTH_START?(V6_NORTH_START==19?V6_LEFT:V6_RIGHT):0;
#endif
#ifdef V6_CONUNDRUM_EDGE
    input=r->index==V6_NORTH_START?(V6_NORTH_START==18?V6_LEFT:V6_RIGHT):0;
#endif
#ifdef V6_NORTH_CORRIDOR
    input=r->index==V6_NORTH_START?((V6_NORTH_START==13 || V6_NORTH_CORRIDOR==2 || V6_NORTH_CORRIDOR==3)?V6_RIGHT:V6_LEFT):0;
#endif
    int ok=v6_tower_route_step_hooks(r,input,&hooks,context);
#ifdef V6_NORTH_ROUTE
    if(ok && r->index==19)v6_conundrum_contact(&conundrum_trigger,&r->session->player);
    if(ok && r->index==18)v6_firststeps_contact(&firststeps_trigger,&r->session->player);
#endif
#ifdef V6_VSTITCH_HINT_CAPTURE
    if(ok && r->index==9)v6_vstitch_trigger_contact(&vstitch_hint,&r->session->player);
#endif
    return ok;
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
static volatile struct {ULONG magic,version,count,records[AUX_TRACE_ROWS(128)][14];}
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
static struct { ULONG magic,version,count; LONG records[AUX_TRACE_ROWS(128)][3]; } shake_trace={0x56365348,1,0,{{0}}};
#ifdef V6_TOWER_MENU_TRAVEL
static volatile struct {ULONG magic,version,count,seed;LONG records[AUX_TRACE_ROWS(64)][3];}
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
#if defined(V6_NORTH_ROUTE) && FIRSTSTEPS_CRY_BYTES>PRIZE_TRINKET_BYTES
#error Firststeps cry must fit the shared trinket sample bank
#endif
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
static volatile struct {ULONG magic,version,count,records[AUX_TRACE_ROWS(128)][2];}
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
static volatile struct {ULONG magic,version,count,records[AUX_TRACE_ROWS(128)][8];}
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
static volatile struct {ULONG magic,version,count,records[AUX_TRACE_ROWS(128)][12];}
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
#ifdef V6_MENU_SLIDE
#define LIST_WORDS 512
#else
#define LIST_WORDS 384
#endif
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
#ifdef V6_NORTH_ROUTE
#include "terminal_samples.h"
#define TERMINAL_AUDIO_BYTES TERMINAL_TOUCH_BYTES
#else
#define TERMINAL_AUDIO_BYTES 0
#endif
#define TRAVEL_AUDIO_BYTES (TERMINAL_AUDIO_BYTES+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_AUDIO_BYTES+2)
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
#ifdef V6_MAP_INPUT_CAPTURE
#ifdef V6_MAP_DISPLAY_CAPTURE
#ifdef V6_SAVE_DISPLAY_CAPTURE
#define MAP_BITMAP_DMA_BYTES (V6_MAP_BITMAP_BYTES+2*V6_SAVE_BITMAP_BYTES)
#else
#define MAP_BITMAP_DMA_BYTES V6_MAP_BITMAP_BYTES
#endif
#else
#define MAP_BITMAP_DMA_BYTES 0
#endif
#ifdef V6_MENU_COMPLETE
#undef MAP_BITMAP_DMA_BYTES
#ifdef V6_MENU_SLIDE
#ifdef V6_NORTH_ROUTE
#define MAP_BITMAP_DMA_BYTES (V6_MAP_BITMAP_BYTES+2*V6_UI_BYTES+8212+1456+3340)
#else
#define MAP_BITMAP_DMA_BYTES (V6_MAP_BITMAP_BYTES+2*V6_UI_BYTES+8212+1456)
#endif
#else
#define MAP_BITMAP_DMA_BYTES (V6_MAP_BITMAP_BYTES+2*V6_UI_BYTES+8212)
#endif
#define MAP_DMA_BYTES MAP_BITMAP_DMA_BYTES
#else
#define MAP_DMA_BYTES (6*V6_DIALOGUE_BYTES+MAP_BITMAP_DMA_BYTES)
#endif
#else
#define MAP_DMA_BYTES 0
#endif
#define UI_DMA_BYTES (MAP_DMA_BYTES+UI_MESSAGE_COUNT*V6_DIALOGUE_BYTES+PICKUP_DMA_BYTES)
#else
#define UI_DMA_BYTES 0
#endif
#ifdef V6_TOWER_SHAKE
#define SHAKE_DMA_BYTES V6_SHAKE_MASK_BYTES
#else
#define SHAKE_DMA_BYTES 0
#endif
#define CHIP_BYTES (SHAKE_DMA_BYTES+BUILDING_DMA_BYTES+TELE_DMA_BYTES+UI_DMA_BYTES+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES+AUDIO_DMA_BYTES)
#ifdef V6_MENU_SLIDE
#include "menu_slide.h"
static UWORD menu_game_copper[512],menu_game_sprites[8][V6_TELEPORTER_DMA_WORDS];
static unsigned menu_game_words,menu_capture_pending;
static UWORD *menu_map_dma;
static unsigned menu_map_title=9;
#endif

static void free_chip(UBYTE *chip)
{
    FreeMem(chip,CHIP_BYTES);
}
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
#ifdef V6_VSTITCH_INPUT_CAPTURE
    if(route.index==9) {
        data=vstitch_display;bytes=sizeof(vstitch_display);route.room.terrain=&vstitch_terrain;
    }
#endif
    if(route.index==8) {
        data=prize_display;bytes=sizeof(prize_display);
        route.room.terrain=&prize_terrain;
        v6_prize_init(&station_prize,&route.room,&station_collected,world.save.id,route.session->player.y);
        for(i=0;i<3;++i)prize_gate_drawn[0][i]=prize_gate_drawn[1][i]=-2;
        prize_drawn_patch[0]=prize_drawn_patch[1]=~prize_patches;
    }
#endif
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(route.index==10 || route.index==11) {
        unsigned buffer,n;
        data=route.index==10?deception_display:downunder_display;
        bytes=route.index==10?sizeof(deception_display):sizeof(downunder_display);
        route.room.terrain=route.index==10?&deception_terrain:&downunder_terrain;
        if(!v6_prize_return_init(&west_actors,&route.room,110,route.index==10?107:106,
            route.session->player.y))return 0;
        for(n=0;n<2;++n)v6_return_enemy_animation_init(&west_enemy_animation[n]);
        for(buffer=0;buffer<2;++buffer)for(n=0;n<4;++n)west_platform_y[buffer][n]=-1;
        west_tread_phase=west_tread_delay=0;
        west_tread_drawn[0]=west_tread_drawn[1]=-1;
    }
#endif
#ifdef V6_NORTH_ROUTE
    if(route.index>=10 && route.index<=20){unsigned n;
        data=route.index==10?reflect_display:route.index==11?yesmen_display:route.index==12?gantry_display:route.index==13?security_display:route.index==14?linear_display:route.index==15?filter_display:route.index==16?traffic_display:route.index==17?leap_display:route.index==18?solitude_display:route.index==19?conundrum_display:welcome_display;
        bytes=route.index==10?REFLECT_DISPLAY_BYTES:route.index==11?YESMEN_DISPLAY_BYTES:route.index==12?GANTRY_DISPLAY_BYTES:route.index==13?SECURITY_DISPLAY_BYTES:route.index==14?LINEAR_DISPLAY_BYTES:route.index==15?FILTER_DISPLAY_BYTES:route.index==16?TRAFFIC_DISPLAY_BYTES:route.index==17?LEAP_DISPLAY_BYTES:route.index==18?SOLITUDE_DISPLAY_BYTES:route.index==19?CONUNDRUM_DISPLAY_BYTES:WELCOME_DISPLAY_BYTES;
        if(!v6_north_init(&north_actors,&route.room,route.rooms[route.index].x,route.rooms[route.index].y,route.session->player.y))return 0;
        v6_firststeps_enter(&firststeps_trigger,route.rooms[route.index].x,route.rooms[route.index].y,0);
        {unsigned mode=route.index==18?1:route.index==19?2:0;
         if(mode!=north_caption_mode){if((mode==1)!=(north_caption_mode==1))north_pcm_pending=1;
             north_caption_mode=mode;north_caption_pending=4;}}
        v6_conundrum_enter(&conundrum_trigger,route.rooms[route.index].x,route.rooms[route.index].y,0);
        if(route.index!=19)conundrum_trigger.visible=0;
        v6_terminal_init(&north_terminal,252,200,1,0,1);north_terminal_cue=0;
        north_activity_index=-1;north_read_pending=north_read_bars=north_layer_stage=north_layer_row=north_read_copied=0;
        north_reader.active=north_reader.boxes[0].visible=north_reader.boxes[1].visible=0;
        north_reader.bars=north_reader.waiting=north_reader.cues=0;
        north_layer_bars[0]=north_layer_bars[1]=0;
        for(n=0;n<5;++n){v6_return_enemy_animation_init(&north_animation[n]);v6_return_enemy_animation_tick(&north_animation[n],0);}
    }
#endif
#ifdef V6_NORTH_ROUTE
    for(i=0;i<3;++i)north_companion_rest[i].valid=0;
    north_memo_pending=(route.index==11 || route.index==14 || route.index==16)?1:0;
    if(route.rooms[route.index].packed){route.room.terrain=0;north_terrain_pending=1;north_terrain_row=0;}
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
    if(station_story.companion==7){
        v6_station_companion_enter(&companion,7,route.rooms[route.index].x,route.rooms[route.index].y,&route.session->player);
#ifdef V6_NORTH_BOB
    if(companion.visible && route.index>=10)companion.body.x+=20;
#endif
    }else v6_station_companion_idle(&companion,trigger_crew_visible);
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    west_copper_ready[0]=west_copper_ready[1]=0;
#endif
#ifdef V6_VSTITCH_HINT_CAPTURE
    v6_vstitch_trigger_enter(&vstitch_hint,route.rooms[route.index].x,route.rooms[route.index].y,0);
    vstitch_bitmap_ready[0]=vstitch_bitmap_ready[1]=0;
#endif
    route_loading=2;route_budget=1;
#ifdef V6_NORTH_ROUTE
    route_budget=0;
#endif
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(route.index==10 || route.index==11)route_budget=0;
#endif
#ifdef V6_TOWER_TELE_MENU
    if(!tele_note_room(route.rooms[route.index].x,route.rooms[route.index].y))return 0;
#endif
    return 1;
}
static volatile struct { ULONG magic,version,count,records[AUX_TRACE_ROWS(128)][3]; }
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
    ULONG magic,version,max_logic,max_render,peak_logic,peak_render,peak_tick,peak_rows,peak_ui_row,peak_ui_page;
} profile={0x56365046,1,0,0,0,0,0,0,0,0};
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
#ifdef V6_NORTH_ROUTE
        if(rescue_vm.cue_speaker==2){sample.address=(ULONG)(travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_VANISH_BYTES);sample.bytes=FIRSTSTEPS_CRY_BYTES;}
#endif
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
    ULONG records[AUX_TRACE_ROWS(128)][12];
} world_trace={0x56365754,1,0,128,{{0}}};
static void record_world(void)
{
#ifdef V6_TOWER_PRIZE
    { unsigned i;
      collection_diag.room_index=route.index;collection_diag.pickups=prize_pickups;
      collection_diag.visible=route.index==8?station_prize.trinket.visible:0;
      for(i=0;i+3<V6_COLLECT_BYTES;i+=4) {
          collection_diag.bits[i]=station_collected.bits[i];
          collection_diag.bits[i+1]=station_collected.bits[i+1];
          collection_diag.bits[i+2]=station_collected.bits[i+2];
          collection_diag.bits[i+3]=station_collected.bits[i+3];
      }
      for(;i<V6_COLLECT_BYTES;++i)collection_diag.bits[i]=station_collected.bits[i]; }
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
    if(AUX_TRACE_ENABLED && (route_trace.count<128)) {
        route_trace.records[route_trace.count][0]=route.index;
        route_trace.records[route_trace.count][1]=route.transitions;
        route_trace.records[route_trace.count][2]=route.returns;
        ++route_trace.count;
    }
#endif
    if(AUX_TRACE_ENABLED && (world_trace.count<128)) {
        for(i=0;i<12;++i) world_trace.records[world_trace.count][i]=world_diag.values[i];
        ++world_trace.count;
    }
}
#endif
#ifdef V6_TOWER_RECOVERY
#if !defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE) && !defined(V6_PRIZE_RETURN_INPUT_CAPTURE) && !defined(V6_VSTITCH_HINT_CAPTURE)
/* The pickup input capture has its own world trace and a fixed-zero camera. */
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
#endif
static V6TowerSession session;
#endif
static UWORD beam(void) {
    UWORD high,low,after;
    /* A 68000 long read uses two bus cycles. Do not combine the old ninth
     * vertical bit with the new low byte at line 255 or a field wrap. */
    do {high=hw->vposr;low=hw->vhposr;after=hw->vposr;} while((high^after)&1);
    return (UWORD)(((high&1)<<8)|(low>>8));
}
#ifdef V6_MAP_INPUT_CAPTURE
static void keyboard_poll(void)
{
    /* The takeover masks PORTS. cia.resource samples/clears only SP and
     * retains other pending CIA sources for the restored OS handlers. */
    if(SetICR(keyboard_resource,8)&8) {
        UBYTE serial=*(volatile UBYTE *)0xbfec01;
        volatile UBYTE *cra=(volatile UBYTE *)0xbfee01;
        UBYTE before=*cra;unsigned i;UWORD line;
        *cra=before|0x40;
        /* Three line boundaries guarantee at least two complete PAL lines
         * (>127us), above the manual's 85us minimum, including frame wrap. */
        for(i=0;i<3;++i) {line=beam();while(beam()==line){}}
        /* Timer A can finish a one-shot during the handshake. Preserve its
         * current control bits instead of restarting it with the old START. */
        *cra=(*cra&0xbf)|(before&0x40);
        v6_keyboard_receive(&keyboard,serial);
        ++map_diag.values[0];map_diag.values[1]=v6_keyboard_decode(serial);
    }
}
#endif
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
#ifdef V6_REGIONAL_CONTENT
static int region_read(void *context,unsigned region,void *out,unsigned capacity,unsigned *size)
{
    static const char *const names[]={"DF0:north0.v6rg","DF0:north1.v6rg","DF0:north2.v6rg","DF0:north3.v6rg","DF0:north4.v6rg","DF0:north5.v6rg"};
    intptr_t file;unsigned used=0;int n,ok=1;UBYTE extra;
    (void)context;if(region>=6)return 0;
    file=v6_campaign_dos.open(names[region],0);if(!file)return 0;
    while(used<capacity){n=v6_campaign_dos.read(file,(UBYTE *)out+used,capacity-used);
        if(n<0 || (unsigned)n>capacity-used){ok=0;break;}if(!n)break;used+=n;}
    if(used==capacity && v6_campaign_dos.read(file,&extra,1)!=0)ok=0;
    if(!v6_campaign_dos.close(file))ok=0;
    *size=used;return ok;
}
static int region_materialize(V6TowerRoute *r,unsigned index,void *context)
{
    const V6RegionRoom *room;unsigned region,i,hit=0,active=north_regions.active;
    unsigned paused=0;ULONG held=frames,held_ticks=diag.logic_ticks,held_hash=0;int ok;
    (void)context;
    if(index<10)return 1;
    if(index>20)return 0;
    region=(index-10)>>1;
    for(i=0;i<V6_REGION_SLOTS;++i)if(north_regions.slots[i].valid && north_regions.slots[i].region==region)hit=1;
    if(!hit && region_runtime.active){
        held_hash=ui_game_hash();
        /* Keep servicing one-shot voices while the simulation is paused. */
        unsigned fields=0;
        while(cue_audio.state || travel_audio_busy()){
            V6AudioPlan plan;
            if(++fields>500)return 0;
            blank();
            if(cue_audio.state){v6_audio_tick(&cue_audio,(hw->intreqr&INTF_AUD0)!=0,&plan);audio_apply(&plan);}
            for(i=0;i<4;++i)if((V6_TRAVEL_SFX_MASK&(1U<<i)) && travel_voices[i].audio.state){
                v6_paula_tick(&travel_voices[i],(hw->intreqr&(INTF_AUD0<<i))!=0,&plan);travel_audio_apply(&plan);}
        }
        wait_blit();Disable();hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
        __asm volatile("move.l %0,0x6c.w"::"r"(*region_runtime.old_irq):"memory");
        hw->cop1lc=(ULONG)GfxBase->copinit;hw->cop2lc=(ULONG)GfxBase->LOFlist;hw->copjmp1=0;
        hw->adkcon=*region_runtime.adk|0x8000;hw->dmacon=*region_runtime.dma|0x8000;hw->intena=*region_runtime.ints|0x8000;
        SetICR(keyboard_resource,0);Enable();Permit();DisownBlitter();LoadView(*region_runtime.view);WaitTOF();WaitTOF();
        paused=1;++region_diag.pauses;region_diag.drain_fields+=frames-held;
    }
    {struct Process *process=hit?0:(struct Process *)FindTask(0);APTR window=hit?0:process->pr_WindowPtr;
        /* Cache hits do no DOS/Exec work while the machine is taken over. */
        if(!hit)process->pr_WindowPtr=(APTR)-1;
        room=v6_region_get(&north_regions,region,index,region_read,0);
        if(!hit)process->pr_WindowPtr=window;
    }
    ok=room && room->x==(unsigned)r->rooms[index].x && room->y==(unsigned)r->rooms[index].y && room->tileset==r->rooms[index].tileset;
    if(ok){tower_route_rooms[index].decoded=room->tiles;north_content=room;}
    else {north_regions.active=active;++region_diag.errors;
        if(!hit){static const char message[]="VVVVVV: regional content missing or invalid.\n";
            Write(Output(),(APTR)message,sizeof(message)-1);}
    }
    region_diag.loads=north_regions.reads;region_diag.hits=north_regions.hits;
    region_diag.room=index;region_diag.region=region;
    if(paused){
        *region_runtime.view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();OwnBlitter();WaitBlit();Forbid();Disable();
        *region_runtime.dma=hw->dmaconr;*region_runtime.ints=hw->intenar;*region_runtime.adk=hw->adkconr;
        hw->intena=0x7fff;hw->intreq=0x7fff;hw->dmacon=0x7fff;hw->adkcon=0x7fff;
        __asm volatile("move.l 0x6c.w,%0":"=r"(*region_runtime.old_irq));
        __asm volatile("move.l %0,0x6c.w"::"r"((APTR)irq):"memory");
        v6_keyboard_init(&keyboard);blank();frames=held;
        hw->cop1lc=(ULONG)region_runtime.lists[*region_runtime.back^1];hw->copjmp1=0;
        hw->dmacon=DMAF_SETCLR|DMAF_MASTER|DMAF_RASTER|DMAF_COPPER|DMAF_BLITTER|DMAF_SPRITE;
        hw->intena=INTF_SETCLR|INTF_INTEN|INTF_VERTB;Enable();
        *region_runtime.previous=*region_runtime.logic_frame=frames;*region_runtime.start=clock_lines();
        if(diag.logic_ticks!=held_ticks || ui_game_hash()!=held_hash)++region_diag.violations;
    }
    return ok;
}
#endif
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
    if(pickup_fade_shown!=(unsigned)pickup_screen.visible) {
        if(pickup_screen.visible)v6_pickup_fade_show(&pickup_fade);
        else v6_pickup_fade_remove(&pickup_fade);
        pickup_fade_shown=pickup_screen.visible;
    }
    v6_pickup_fade_tick(&pickup_fade);
    v6_pickup_draw_tick(&pickup_draw,pickup_screen.bars);
    if(MAP_AUX_TRACE_ENABLED && (pickup_draw.bars || pickup_draw.old_bars) && pickup_presentation.count<256) {
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
    pickup_colours=v6_pickup_fade_colours(&pickup_fade,diag.logic_remainder);
    pickup_render_bars=v6_pickup_bar_position(&pickup_draw,diag.logic_remainder);
    if(!pickup_banks)return 1;
    if(MAP_AUX_TRACE_ENABLED && pickup_fade_diag.count<64 && (pickup_fade.visible || pickup_fade_diag.count) &&
       (!pickup_fade_diag.count || pickup_fade_diag.records[pickup_fade_diag.count-1][6]!=pickup_colours)) {
        volatile ULONG *r=pickup_fade_diag.records[pickup_fade_diag.count++];
        r[0]=diag.logic_ticks;r[1]=pickup_fade.mode;r[2]=pickup_fade.old_level;
        r[3]=pickup_fade.level;r[4]=diag.logic_remainder;r[5]=pickup_fade.visible;
        r[6]=pickup_colours;r[7]=pickup_screen.stopped;
    }

    bank=pickup_banks+index*V6_PICKUP_BANK_BYTES;
    if(pickup_bar_room[index]!=route.index || pickup_bar_camera[index]!=fo) {
        pickup_bar_room[index]=route.index;pickup_bar_camera[index]=fo;pickup_bar_rows[index]=0;
        pickup_bar_position[index]=0xffffffffUL;
        for(b=0;b<2;++b)for(x=0;x<20;++x)pickup_bar_masks[index][b][x]=0;
    }
    if(route.index!=8 && !pickup_draw.bars && !pickup_fade.visible)return 1;
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
    if(MAP_AUX_TRACE_ENABLED && (pickup_draw.bars || pickup_draw.old_bars) && pickup_interpolation.count<96 &&
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
        if(pickup_fade.visible && pickup_rows[index]!=V6_PICKUP_HEIGHT)return 0;
    }
    pickup_presentation.values[2]=pickup_rows[0];pickup_presentation.values[3]=pickup_rows[1];
    pickup_presentation.values[4]=pickup_bar_rows[0];pickup_presentation.values[5]=pickup_bar_rows[1];
    return 1;
}
#endif
#ifdef V6_VSTITCH_HINT_CAPTURE
static void vstitch_prepare_bitmap(UBYTE *ring,unsigned index,unsigned camera)
{
    unsigned row;UBYTE *bank;
    if(!pickup_banks || route.index!=9 || vstitch_bitmap_ready[index])return;
    bank=pickup_banks+index*V6_PICKUP_BANK_BYTES+V6_PICKUP_TEXT_OFFSET;
    for(row=0;row<V6_HINT_HEIGHT;++row)
        v6_pickup_compose_row((UWORD *)(bank+row*40),V6_PICKUP_PLANE_BYTES/2,
            (const UWORD *)(ring+((camera+V6_HINT_TOP+row)&255)*40),V6_TOWER_PLANE_BYTES/2,
            vstitch_mask+row*20,vstitch_ink+row*20);
    vstitch_bitmap_ready[index]=1;++vstitch_draw_trace.compositions;
}
#endif
#ifdef V6_MENU_COMPLETE
static const char *menu_area(int x,int y)
{
    unsigned a;
    if(x>=102 && x<=104 && y>=110 && y<=111)return "The Ship";
    if(x<100 || x>119 || y<100 || y>119)return "Outside Dimension VVVVVV";
    a=ui_world_areas[(unsigned)(y-100)*20+(unsigned)(x-100)];
    if(a==2)return "Laboratory";
    if(a==3 || a==11)return "The Tower";
    if(a==4)return "Warp Zone";
    if(a==5)return "Space Station";
    return "Dimension VVVVVV";
}
static const char *menu_roomname(void)
{
    static const char *names[23]={"The Tower","The Tower","I'm Sorry...","Seeing Red",
        "Building Apport","Energize","Frown Upside Down","Shenanigan","Prize for the Reckless","V Stitch","A Deception","Down Under","Stop and Reflect","The Yes Men","Gantry and Dolly","Security Sweep","Linear Collider","Atmospheric Filtering Unit","Traffic Jam","Leap of Faith","Solitude","Conundrum","Welcome Aboard"};
#ifdef V6_NORTH_ROUTE
    if(route.index>=10 && route.index<=20)return names[route.index+2];
#endif
    return route.index<12?names[route.index]:"Untitled room";
}
typedef struct {UBYTE *bitmap;unsigned planes,top,bottom;} MenuFill;
static void menu_edge(UBYTE *bitmap,unsigned plane,unsigned row,unsigned word,unsigned mask,unsigned bit)
{
    UWORD *d=(UWORD *)(bitmap+plane*9600+row*40+word*2);
    *d=bit?(UWORD)(*d|mask):(UWORD)(*d&~mask);
}
static int menu_fill(void *opaque,int x,int y,unsigned w,unsigned h,unsigned colour)
{
    MenuFill *f=opaque;int right=x+(int)w,bottom=y+(int)h;unsigned p,row,first,last,leftword,rightword;
    if(x<0)x=0;
    if(y<(int)f->top)y=(int)f->top;
    if(bottom>(int)f->bottom)bottom=(int)f->bottom;
    if(right>320)right=320;
    if(bottom>240)bottom=240;
    if(x>=right || y>=bottom)return 1;
    first=((unsigned)x+15)>>4;last=(unsigned)right>>4;
    leftword=(unsigned)x>>4;rightword=(unsigned)(right-1)>>4;
    wait_blit();
    for(p=0;p<f->planes;++p) {
        unsigned bit=colour&(1U<<p);
        if(leftword==rightword) {
            unsigned mask=(0xffffU>>((unsigned)x&15))&(0xffffU<<(16-((unsigned)(right-1)&15)-1));
            for(row=(unsigned)y;row<(unsigned)bottom;++row)menu_edge(f->bitmap,p,row,leftword,mask,bit);
            continue;
        }
        if((unsigned)x&15)for(row=(unsigned)y;row<(unsigned)bottom;++row)
            menu_edge(f->bitmap,p,row,leftword,0xffffU>>((unsigned)x&15),bit);
        if((unsigned)right&15)for(row=(unsigned)y;row<(unsigned)bottom;++row)
            menu_edge(f->bitmap,p,row,rightword,0xffffU<<(16-((unsigned)right&15)),bit);
        if(last>first) {
            wait_blit();hw->bltcon0=(UWORD)(0x0100|(bit?0xff:0));hw->bltcon1=0;
            hw->bltafwm=hw->bltalwm=0xffff;hw->bltdmod=(UWORD)(40-(last-first)*2);
            hw->bltdpt=f->bitmap+p*9600+(unsigned)y*40+first*2;
            hw->bltsize=(UWORD)(((bottom-y)<<6)|(last-first));
        }
    }
    wait_blit();return 1;
}
static void menu_mask_blit(MenuFill *f,const UBYTE *mask,unsigned stride,unsigned x,unsigned y,unsigned words,unsigned height,unsigned colour)
{
    unsigned p,end=y+height;
    if(y<f->top){{unsigned delta=f->top-y;mask+=stride==4?(delta<<2):(delta<<5)+(delta<<3);}y=f->top;}
    if(end>f->bottom)end=f->bottom;
    if(y>=end)return;
    height=end-y;
    for(p=0;p<f->planes;++p) {
        UBYTE *dest=f->bitmap+p*9600+y*40+x*2;
        wait_blit();hw->bltcon0=0x0bca;hw->bltcon1=0;
        hw->bltafwm=hw->bltalwm=0xffff;hw->bltadat=0;hw->bltbdat=(colour&(1U<<p))?0xffff:0;
        hw->bltamod=(UWORD)(stride-words*2);hw->bltcmod=hw->bltdmod=(UWORD)(40-words*2);
        hw->bltapt=(APTR)mask;hw->bltcpt=(APTR)dest;hw->bltdpt=(APTR)dest;
        hw->bltsize=(UWORD)((height<<6)|words);
    }
    wait_blit();
}
static void menu_text(void *opaque,int x,int y,const char *s,unsigned colour,int align)
{
    MenuFill *f=opaque;unsigned i,row,n=0;ULONG *clear=(ULONG *)ui_stencil;
    if(y+8<=(int)f->top || y>=(int)f->bottom)return;
    if(s[0]=='[' && s[1]=='P'){menu_mask_blit(f,ui_prompt,40,0,(unsigned)y,20,8,colour);return;}
    if(s[0]=='(' && s[1]=='N'){menu_mask_blit(f,ui_note,40,0,(unsigned)y,20,8,colour);return;}
    while(s[n])++n;
    if(x==160 && align==1 && (s[0]=='[' || y==2))for(i=0;i<sizeof(ui_static_texts)/sizeof(ui_static_texts[0]);++i){
        unsigned j=0;while(s[j] && s[j]==ui_static_texts[i][j])++j;
        if(!s[j] && !ui_static_texts[i][j]){unsigned row,word,first=(unsigned)(160-(int)n*4)>>4,last=((unsigned)(160+(int)n*4)+15)>>4;
            wait_blit();
            for(row=0;row<8;++row)if(y+(int)row>=(int)f->top && y+(int)row<(int)f->bottom)
                for(word=first;word<last;++word){unsigned at=row*40+word*2;ui_stencil[at]=ui_static_text_masks[i*320+at];ui_stencil[at+1]=ui_static_text_masks[i*320+at+1];}
            menu_mask_blit(f,ui_stencil+first*2,40,first,(unsigned)y,last-first,8,colour);return;}
    }
    if(x==44 || x==204)for(i=0;i<11;++i)if(ui_crew_text_x[i]==(unsigned)x){
        unsigned j=0;while(s[j] && s[j]==ui_crew_texts[i][j])++j;
        if(!s[j] && !ui_crew_texts[i][j]){unsigned first=(unsigned)x>>4,last=((unsigned)(x+(int)n*8)+15)>>4;
            unsigned row,word;
            wait_blit();
            for(row=0;row<8;++row)if(y+(int)row>=(int)f->top && y+(int)row<(int)f->bottom)
                for(word=first;word<last;++word){unsigned at=row*40+word*2;
                    ui_stencil[at]=ui_crew_text_masks[i*320+at];ui_stencil[at+1]=ui_crew_text_masks[i*320+at+1];}
            menu_mask_blit(f,ui_stencil+first*2,40,first,(unsigned)y,last-first,8,colour);return;}
    }
    if(y==220){unsigned column=x==40?0:x==120?1:x==200?2:3,first,last;
        x-=(int)n*4;first=(unsigned)x>>4;last=((unsigned)(x+(int)n*8)+15)>>4;
        menu_mask_blit(f,ui_tabs+(column*2+(s[0]=='['))*320+first*2,40,first,220,last-first,8,colour);return;}
    wait_blit();for(i=0;i<80;++i)clear[i]=0;
    if(!n)return;
    if(align==1)x-=(int)n*4;else if(align==2)x-=(int)n*8;
    for(i=0;i<n;++i) {
        int xx=x+(int)i*8;unsigned shift=(unsigned)xx&7;
        for(row=0;row<8;++row) {
            unsigned bits;UBYTE *d;
            if(y+(int)row<(int)f->top || y+(int)row>=(int)f->bottom)continue;
            bits=dialogue_font[(unsigned char)s[i]][row];
            d=ui_stencil+row*40+((unsigned)xx>>3);
            if(bits){d[0]|=(UBYTE)(bits>>shift);if(shift)d[1]|=(UBYTE)(bits<<(8-shift));}
        }
    }
        {unsigned first=(unsigned)x>>4,last=((unsigned)(x+(int)n*8)+15)>>4;
     menu_mask_blit(f,ui_stencil+first*2,40,first,(unsigned)y,last-first,8,colour);}
}
static void menu_border(void *opaque,int x,int y,int w,int h)
{
    MenuFill *f=opaque;
    if(y==212){menu_mask_blit(f,ui_footer,40,0,212,20,8,3);menu_mask_blit(f,ui_footer+16*40,40,0,228,20,8,3);}
    else {
        menu_mask_blit(f,ui_receipt,40,0,65,20,8,3);
        menu_mask_blit(f,ui_receipt+82*40,40,0,147,20,8,3);
        menu_mask_blit(f,ui_receipt+8*40+2,40,1,73,2,74,3);
        menu_mask_blit(f,ui_receipt+8*40+36,40,18,73,2,74,3);
    }
    (void)x;(void)w;(void)h;
}
static void menu_icon(void *opaque,const uint32_t *rows,int x,int y,unsigned colour)
{
    MenuFill *f=opaque;unsigned first=(unsigned)x>>4;
    const UBYTE *mask=ui_icon_alpha+(x==34?0:68);
    menu_mask_blit(f,mask,4,first,(unsigned)y,2,x==34?17:16,colour);
    (void)rows;
}
static const V6UIDrawOps menu_ops={menu_text,menu_border,menu_icon};
static void menu_sync(void)
{
    unsigned known=(hallway_story.red_rescued?8:0)|(station_story.yellow_rescued?4:0);
    campaign_menu.crew_mask=(uint16_t)((campaign_menu.crew_mask&~12U)|known|1);
    if(session.deaths>=menu_session_deaths)campaign_menu.deaths+=(unsigned)(session.deaths-menu_session_deaths);
    menu_session_deaths=session.deaths;
}
static int menu_snapshot(const V6SaveClock *clock)
{
    menu_sync();
    return v6_save_summary_capture(&menu_candidate,clock,world.save.room_x,world.save.room_y,&station_collected,campaign_menu.crew_mask);
}
static void menu_record(V6MenuRecord *r)
{
    ui_copy(&r->checkpoint,&world.save,sizeof(world.save));
    ui_copy(&r->red,&hallway_story,sizeof(hallway_story));ui_copy(&r->yellow,&station_story,sizeof(station_story));
    ui_copy(&r->explored,&tele_exploration,sizeof(tele_exploration));ui_copy(&r->collected,&station_collected,sizeof(station_collected));
    r->hints.map_hint_seen=vstitch_seen;ui_copy(&r->menu,&campaign_menu,sizeof(campaign_menu));
    ui_copy(&r->menu.clock,&menu_candidate.clock,sizeof(menu_candidate.clock));
    ui_copy(&r->menu.last,&menu_candidate,sizeof(menu_candidate));
}
static int menu_state_equal(const V6UIState *a,const V6UIState *b)
{
    unsigned i;const UBYTE *x=(const void *)a,*y=(const void *)b;
    for(i=0;i<sizeof(*a);++i)if(x[i]!=y[i])return 0;
    return 1;
}
static int menu_prepare_bitmap(void)
{
    V6UIState s;unsigned i;MenuFill fill;
    if(ui_present_pending){ui_present_pending=0;return 1;}
    /* Zero padding as well as fields so cached state comparisons are stable. */
    {UBYTE *p=(void *)&s;for(i=0;i<sizeof(s);++i)p[i]=0;}
    menu_sync();s.page=(unsigned)map_menu.page;s.saved=map_menu.saved;s.failed=map_menu.failed;
    s.crew_mask=campaign_menu.crew_mask;s.crew_frame=0; /* Portrait frame is a DMA-only change. */
    s.deaths=campaign_menu.deaths;s.trinkets=0;
    for(i=0;i<100;++i)if(station_collected.bits[i>>3]&(1U<<(i&7)))++s.trinkets;
    ui_copy(&s.clock,&campaign_menu.clock,sizeof(s.clock));s.clock.frames=0;
    ui_copy(&s.last,&campaign_menu.last,sizeof(s.last));s.last.clock.frames=0;
    if(s.page!=2){s.clock.hours=s.clock.minutes=s.clock.seconds=s.clock.frames=0;s.deaths=0;}
    s.roomname=menu_roomname();s.area=menu_area(route.rooms[route.index].x,route.rooms[route.index].y);
    s.last_area=menu_area(s.last.room_x,s.last.room_y);s.action="Space";
    if(ui_ready && menu_state_equal(&s,&ui_rendered))return 1;
    if(ui_pending && (s.page!=ui_pending_state.page || s.saved!=ui_pending_state.saved ||
       s.failed!=ui_pending_state.failed))ui_pending=0;
    if(!ui_pending){ui_copy(&ui_pending_state,&s,sizeof(s));ui_pending=1;ui_row=0;}
    fill.bitmap=ui_bitmaps+(ui_render_bank^1)*V6_UI_BYTES;fill.planes=4;
    fill.top=ui_row;fill.bottom=ui_row+12;
#ifdef V6_NORTH_ROUTE
    /* Bound long room titles as well as the Linear Collider sprite snapshot. */
    if(route.index==14 || route.index>=16)fill.bottom=ui_row+4;
    if(route.index==15)fill.bottom=ui_row+2;
#endif
    if(fill.bottom>240)fill.bottom=240;
    /* Last-save area/time is variable-length text. Split its font work over
       fields even when the rest of the page fits a larger blitter batch. */
    if(s.page==3 && ui_row>=96 && ui_row<128)fill.bottom=ui_row+4;
    ui_copy(&s,&ui_pending_state,sizeof(s));
    {
        unsigned old_hog=hw->dmaconr&0x0400;int ok;
        /* The world is paused; let each short mask blit finish without the
           busy-waiting CPU starving its Chip bus slots. */
        hw->dmacon=DMAF_SETCLR|0x0400;
        ok=v6_ui_draw_ops(fill.bitmap,&s,dialogue_font,pickup_border,ui_icons,menu_fill,&menu_ops,&fill);
        wait_blit();if(!old_hog)hw->dmacon=0x0400;
        if(!ok)return 0;
    }
    ui_row=fill.bottom;
    if(ui_row<240)return ui_ready;
    ui_render_bank^=1;ui_pending=0;
    ui_copy(&ui_rendered,&s,sizeof(s));ui_ready=1;ui_present_pending=1;++menu_complete_diag.values[6];return 0;
}
static void menu_copy64(UWORD *out,const UWORD *in)
{
#if defined(__m68k__)
    unsigned blocks=7;
    __asm volatile("1: movem.l (%1)+,%%d0-%%d3\n\t"
        "movem.l %%d0-%%d3,(%0)\n\tlea 16(%0),%0\n\tdbra %2,1b"
        : "+a"(out),"+a"(in),"+d"(blocks) : : "d0","d1","d2","d3","memory","cc");
#else
    unsigned i;for(i=0;i<64;++i)out[i]=in[i];
#endif
}
static unsigned menu_sprite(UWORD *out,const uint32_t rows[32],int x,int y,unsigned crop,unsigned colour,unsigned channel,unsigned offset)
{
    unsigned i,start,stop,first=0,last=32,h,frame=rows==ui_portrait[0]?0:rows==ui_portrait[1]?1:2;int yy=y+(int)offset;
    out[0]=out[1]=0;
    if(yy>=240 || yy+32<=0)return 0;
    if(yy<0)first=(unsigned)-yy;
    if(yy+32>240)last=(unsigned)(240-yy);
    x+=(int)crop;if(x<0 || x+16>320)return 0;
    start=52+yy+first;stop=52+yy+last;h=128+(unsigned)x;
    out[0]=(UWORD)(((start&255)<<8)|(h>>1));out[1]=(UWORD)(((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(h&1));
    if(!first)menu_copy64(out+2,ui_portrait_data[frame][channel&1]);
    else for(i=first;i<last;++i){UWORD bits=ui_portrait_bits[frame][i];out[2+(i-first)*2]=bits;out[3+(i-first)*2]=(channel&1)?bits:0;}
    out[2+(last-first)*2]=out[3+(last-first)*2]=0;
    (void)colour;return 1;
}
#ifdef V6_NORTH_ROUTE
static inline __attribute__((always_inline)) void north_copy_words(UWORD *out,const UWORD *in,unsigned words)
{
    unsigned blocks=words>>4,i;
    if(blocks){unsigned loop=blocks-1;
        __asm volatile("1: movem.l (%1)+,%%d0-%%d5/%%a2-%%a3\n\t"
            "movem.l %%d0-%%d5/%%a2-%%a3,(%0)\n\tlea 32(%0),%0\n\tdbra %2,1b"
            : "+a"(out),"+a"(in),"+d"(loop) : : "d0","d1","d2","d3","d4","d5","a2","a3","memory","cc");}
    if(words&8){
        __asm volatile("movem.l (%1)+,%%d0-%%d3\n\t"
            "movem.l %%d0-%%d3,(%0)\n\tlea 16(%0),%0"
            : "+a"(out),"+a"(in) : : "d0","d1","d2","d3","memory","cc");}
    for(i=0;i<(words&7);++i)out[i]=in[i];
}
static void north_draw_dma(UWORD *const out[8])
{
    UWORD i,k;
    for(i=0;i<8;++i)if(!north_mux_plan.used[i])out[i][0]=out[i][1]=0;
    for(i=0;i<north_mux_plan.count;++i){const V6MuxSpan *s=&north_mux_plan.spans[i];
        const NorthDMA *source=&north_mux_dma[s->actor];const UWORD *body;
        UWORD *d=out[s->channel]+s->words;UWORD words=(s->last-s->first)*2;
        body=source->data+(s->channel&1)*source->stride+s->first*2;
        d[0]=(UWORD)(((s->start&255)<<8)|(s->left>>1));
        d[1]=(UWORD)(((s->stop&255)<<8)|((s->start&256)>>6)|((s->stop&256)>>7)|(s->left&1));
        if(north_reader.boxes[0].visible &&
           ((s->start>=112 && s->stop<=136) || (s->start>=138 && s->stop<=207))){
            north_copy_words(d+2,(const UWORD *)pickup_zero,words);
            north_read_diag.values[5]+=words/2;
        }else {
            if(s->clip==source->mask)north_copy_words(d+2,body,words);
            else for(k=0;k<words;++k)d[2+k]=body[k]&s->clip;
            if(north_reader.boxes[0].visible)north_read_diag.values[5]+=v6_terminal_layer_occlude(d);
        }
        d[2+words]=d[3+words]=0;
    }
}
static int north_draw_bob(unsigned index,unsigned actor)
{
    const V6MuxActor *a=&north_mux_actors[actor];const NorthDMA *source=&north_mux_dma[actor];
    int x=a->x+(int)a->crop,first=a->y<16?16-a->y:0,last=a->y+(int)a->height>216?216-a->y:(int)a->height;
    unsigned row,h,column,shift,old_hog;UBYTE *bitmap=north_bob_bitmaps+index*844;
    if(first>=last || x>=320 || x<=-16)return 1;
    h=last-first;old_hog=hw->dmaconr&0x0400;hw->dmacon=DMAF_SETCLR|0x0400;
    wait_blit();
    if(north_bob_height[index]) {
        hw->bltcon0=0x0100;hw->bltcon1=0;hw->bltdmod=36;
        hw->bltdpt=(APTR)(bitmap+north_bob_column[index]*2);
        hw->bltsize=(UWORD)((north_bob_height[index]<<6)|2);
    }
    north_copy_words(north_bob_source,source->data+first*2,h*2);
    if(x<0){for(row=0;row<h;++row)north_bob_source[row*2]<<=-x;x=0;}
    column=(unsigned)x>>4;shift=(unsigned)x&15;
    wait_blit();
    hw->bltcon0=(UWORD)((shift<<12)|0x09f0);hw->bltcon1=0;
    hw->bltafwm=(UWORD)(column==19?0xffffU<<shift:0xffffU);hw->bltalwm=0xffff;
    hw->bltadat=0;hw->bltamod=0;hw->bltdmod=36;hw->bltapt=(APTR)north_bob_source;
    hw->bltdpt=(APTR)(bitmap+column*2);hw->bltsize=(UWORD)((h<<6)|2);
    wait_blit();if(!old_hog)hw->dmacon=0x0400;
    north_bob_column[index]=column;north_bob_height[index]=h;
#ifdef V6_NORTH_BOB
    north_bob_actor=actor;
#endif
    north_overlay=(V6MuxOverlay){(ULONG)bitmap,(ULONG)pickup_zero,
        52+a->y+first,52+a->y+last,a->colour};
#ifdef V6_NORTH_BOB
    ++north_bob_diag.values[0];north_bob_diag.values[3]=(ULONG)bitmap;
    north_bob_diag.values[4]=(ULONG)(a->x+(int)a->crop);north_bob_diag.values[5]=a->y;
    north_bob_diag.values[6]=first;north_bob_diag.values[7]=last;
    north_bob_diag.values[8]=companion.frame;north_bob_diag.values[9]=companion.mood;
    north_bob_diag.values[10]=a->colour;north_bob_diag.values[11]=index;
#endif
    return 1;
}
static int north_prepare_sprites(unsigned index)
{
    {unsigned n=0,k,crew;int dx=shake_plan.x,dy=shake_plan.y;
        if(!session.invisible){north_mux_dma[n]=(NorthDMA){north_player_dma[player_frame][0],64,0xffff};north_mux_actors[n++]=(V6MuxActor){tower_player_rows[player_frame],session.player.x+dx,session.player.y+dy,6,16,32,DISPLAY_COLOUR(player_tint)};}
        for(k=0;k<world.count;++k){V6Checkpoint *c=&world.checkpoints[k];
            north_mux_dma[n]=(NorthDMA){north_checkpoint_dma[c->tile==21][0],32,0xffff};
            north_mux_actors[n++]=(V6MuxActor){tower_player_rows[c->tile],c->x+dx,c->y+dy,0,16,16,DISPLAY_COLOUR(c->active?0x6f6:0x888)};}
        if(route.index==14){unsigned state=north_terminal.active!=0;
            north_mux_dma[n]=(NorthDMA){north_terminal_dma[1][0],32,0xffff};
            north_mux_actors[n++]=(V6MuxActor){north_terminal_visible[1],252+dx,200+dy,0,16,16,DISPLAY_COLOUR(state?0xfff:0x888)};}
        for(k=0;k<north_actors.enemy_count;++k){unsigned part;V6Enemy *e=&north_actors.enemies[k];
            if(route.index==13){north_mux_dma[n]=(NorthDMA){north_drone_dma[north_animation[k].frame][0],64,0xffff};
                north_mux_actors[n++]=(V6MuxActor){north_drone_visible[north_animation[k].frame],e->x+dx,e->y+dy,0,16,32,DISPLAY_COLOUR(0xf6b)};continue;}
            if(route.index==16){for(part=0;part<2;++part){
                north_mux_dma[n]=(NorthDMA){north_traffic_dma[north_animation[k].frame][part][0],64,part?0xfc00:0xffff};
                north_mux_actors[n++]=(V6MuxActor){north_traffic_visible[north_animation[k].frame],e->x+dx,e->y+dy,part*16,part?6:16,32,DISPLAY_COLOUR(0xf44)};}continue;}
            if(route.index==14){for(part=0;part<2;++part){
                north_mux_dma[n]=(NorthDMA){north_linear_dma[north_animation[k].frame][part][0],64,0xffff};
                north_mux_actors[n++]=(V6MuxActor){north_linear_visible[north_animation[k].frame],e->x+dx,e->y+dy,part*16,16,32,DISPLAY_COLOUR(0x9f9)};}continue;}
            for(part=0;part<2;++part){north_mux_dma[n]=(NorthDMA){north_enemy_dma[north_animation[k].frame][part][0],40,part?0xf000:0xffff};north_mux_actors[n++]=(V6MuxActor){north_enemy_visible[north_animation[k].frame],e->x+dx,e->y+dy,part*16,part?4:16,20,DISPLAY_COLOUR(0xff4)};}}
        for(k=0;k<north_actors.platform_count;++k){unsigned part,frame=route.index==10?4:0;V6Platform *e=&north_actors.platforms[k];
            for(part=0;part<2;++part){north_mux_dma[n]=(NorthDMA){north_platform_dma[frame][part][0],16,0xffff};north_mux_actors[n++]=(V6MuxActor){north_platform_rows[frame],e->x+dx,e->y+dy,part*16,16,8,DISPLAY_COLOUR(north_platform_colours[frame])};}}
        for(k=0;k<north_actors.gate_count;++k)if(!north_actors.gates[k].invisible){unsigned part,frame=(unsigned)north_actors.gates[k].walking_frame;
            if(frame>=4)return 0;
            for(part=0;part<2;++part){north_mux_dma[n]=(NorthDMA){north_platform_dma[frame][part][0],16,0xffff};north_mux_actors[n++]=(V6MuxActor){north_platform_rows[frame],104+(int)k*32+dx,64+dy,part*16,16,8,DISPLAY_COLOUR(north_platform_colours[frame])};}}
        crew=n;north_overlay.start=0;
        if(companion.visible){unsigned frame=companion.frame>=144?companion.frame-144:companion.frame;
            if(frame>=16)return 0;
            north_mux_dma[n]=(NorthDMA){(companion.mood?north_crew_dma[0][0]:north_player_dma[frame][0])+4,64,0xffff};
            north_mux_actors[n++]=(V6MuxActor){(companion.mood?station_crew_rows:tower_player_rows[frame])+2,
                companion.body.x+dx,companion.body.y+dy+2,6,16,21,DISPLAY_COLOUR(0xff4)};
        }
        {uint16_t *ptrs[8];
            if(!v6_sprite_mux_owned_replan(&north_mux_plan,north_mux_actors,crew))return 0;
            if(n>crew){const V6MuxActor *a=&north_mux_actors[crew];
                int hidden=north_reader.boxes[0].visible &&
                    ((a->y>=60 && a->y+a->height<=84) || (a->y>=86 && a->y+a->height<=155));
                if(!hidden && !north_draw_bob(index,crew))return 0;
            }
            for(k=0;k<8;++k)ptrs[k]=k<6?building_dma+(index*6+k)*196:north_extra_dma+(index*2+k-6)*196;
            north_draw_dma(ptrs);
        }
        building_frames[index]=-1;player_sprites[index].count=0;
    }
    return 1;
}
#endif
#if defined(V6_NORTH_ROUTE) && defined(V6_NORTH_BOB)
static int north_validate_sprites(const UWORD *list)
{
    ULONG address[8]={0};UWORD *expected[8];unsigned i,j;
    UWORD *scratch=(UWORD *)(ui_bitmaps+(ui_render_bank^1)*V6_UI_BYTES);
    for(i=0;i+1<512;i+=2){unsigned reg=list[i];if(reg==0xffff)break;
        if(reg>=0x120 && reg<=0x13e && !(reg&1)){unsigned channel=(reg-0x120)>>2;
            if(reg&2)address[channel]=(address[channel]&0xffff0000)|list[i+1];
            else address[channel]=(address[channel]&0xffff)|((ULONG)list[i+1]<<16);}}
    for(i=0;i<8;++i)expected[i]=scratch+i*196;
    v6_sprite_mux_dma(expected,&north_mux_plan,north_mux_actors);
    for(i=0;i<8;++i){if(!address[i])return 0;
        for(j=0;j<north_mux_plan.used[i]+2U;++j)
            if(((const UWORD *)address[i])[j]!=expected[i][j])return 0;}
    return 1;
}
#endif
#if defined(V6_NORTH_ROUTE) && defined(V6_NORTH_BOB)
static int north_validate_bob(const UWORD *list)
{
    ULONG address=0;unsigned i,row,column,first,last;int x;const V6MuxActor *a;
    if(!north_overlay.start)return 1;
    for(i=0;i+1<512;i+=2){if(list[i]==0xffff)break;
        if(list[i]==0xf0)address=(address&0xffff)|((ULONG)list[i+1]<<16);
        if(list[i]==0xf2)address=(address&0xffff0000)|list[i+1];}
    if(!address)return 0;
    a=&north_mux_actors[north_bob_actor];x=a->x+(int)a->crop;
    first=a->y<16?16-a->y:0;last=a->y+(int)a->height>216?216-a->y:(int)a->height;
    for(row=0;row<21;++row){uint16_t expected[20]={0};
        if(row<last-first){unsigned bits=(unsigned)(a->rows[row+first]>>10)&0xffff,shift;
            int px=x;if(px<0){bits=(bits<<-px)&0xffff;px=0;}
            column=(unsigned)px>>4;shift=(unsigned)px&15;
            expected[column]=(uint16_t)(bits>>shift);
            if(column<19 && shift)expected[column+1]=(uint16_t)(bits<<(16-shift));}
        for(column=0;column<20;++column)if(((const UWORD *)address)[row*20+column]!=expected[column]){
            ++north_bob_diag.values[2];return 0;}
    }
    ++north_bob_diag.values[1];return 1;
}
#endif
#ifdef V6_MENU_SLIDE
static int menu_capture_game(const UWORD *list)
{
    ULONG pointers[8]={0};unsigned i,n;
#if defined(V6_NORTH_ROUTE) && defined(V6_NORTH_BOB)
    if(route.index>=10 && !map_transition.active && !north_validate_sprites(list))return 0;
#endif
#if defined(V6_NORTH_ROUTE) && defined(V6_NORTH_BOB)
    if(!north_validate_bob(list))return 0;
#endif
    for(n=0;n+1<512;n+=2){unsigned r=list[n],v=list[n+1];
        menu_game_copper[n]=(UWORD)r;menu_game_copper[n+1]=(UWORD)v;
        if(!(r&1) && r>=0x120 && r<=0x13e){unsigned channel=(r-0x120)>>2;
            if((r&2)==0)pointers[channel]=(pointers[channel]&0xffff)|(v<<16);
            else pointers[channel]=(pointers[channel]&0xffff0000)|v;}
        if(r==0xffff)break;
    }
    if(n+1>=512)return 0;
    menu_game_words=n+2;
    for(i=0;i<8;++i){const UWORD *src=(const UWORD *)pointers[i];UWORD *dest=menu_game_sprites[i];unsigned j,words=0;
        if(!pointers[i])return 0;
        for(;;){unsigned first,last,more;
            if(words+2>196)return 0;
            if(!src[words] && !src[words+1]){words+=2;break;}
            first=(src[words]>>8)|((src[words+1]&4)<<6);last=(src[words+1]>>8)|((src[words+1]&2)<<7);
            if(last<first || last-first>96)return 0;
            more=2+(last-first)*2;if(words+more+2>196)return 0;words+=more;
        }
#ifdef V6_NORTH_ROUTE
        north_copy_words(dest,src,words);(void)j;
#else
        for(j=0;j+64<=words;j+=64)menu_copy64(dest+j,src+j);
        for(;j<words;++j)dest[j]=src[j];
#endif
    }
    menu_capture_pending=1;return 1;
}
static UWORD *menu_map_sprite(unsigned index,unsigned mode,unsigned offset,int *x,int *y)
{
    UWORD *out=menu_map_dma+index*364;unsigned row,height,start,stop,h;
    int rx=route.rooms[route.index].x,ry=route.rooms[route.index].y;
    uint32_t rows[32];
    *x=40+(rx-100)*12;*y=rx==109?21:21+(ry-100)*9;
    out[0]=out[1]=out[2]=out[3]=0;
    if(!mode || *y+(int)offset>=240)return out;
    height=rx==109?180:9;
    if(height>240-(unsigned)*y-offset)height=240-(unsigned)*y-offset;
    if(rx!=109 && !v6_map_cursor_rows(rows,mode,rx,ry,x,y))return 0;
    start=52+(unsigned)*y+offset;stop=start+height;h=128+(unsigned)*x;
    out[0]=(UWORD)(((start&255)<<8)|(h>>1));
    out[1]=(UWORD)(((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(h&1));
    for(row=0;row<height;++row){unsigned bits;
        if(rx==109){bits=mode==1?(row==0 || row==179?0xfff0:0x8010):0;
            if(row>=2 && row<178)bits|=row==2 || row==177?0x3fc0:0x2040;
        } else bits=(unsigned)(rows[row]>>16);
        out[2+row*2]=(UWORD)bits;out[3+row*2]=0;
    }
    out[2+height*2]=out[3+height*2]=0;return out;
}
static unsigned menu_partial_copper(UWORD *list,unsigned index,ULONG bitmap,unsigned planes,const uint16_t palette[32],unsigned offset,unsigned count,const UWORD *cursor)
{
    uint32_t world[8],data[8];uint16_t controls[8][2];unsigned i,n,boundary=52+offset;
    for(i=0;i<8;++i){const UWORD *src=menu_game_sprites[i];UWORD *dest=i<6?
            building_dma+index*(6*V6_TELEPORTER_DMA_WORDS)+i*V6_TELEPORTER_DMA_WORDS:
#ifdef V6_NORTH_ROUTE
            north_extra_dma+(index*2+i-6)*196;
#else
            player_sprites[index].dma+i*68;
#endif
        unsigned at=0,to=0;
        world[i]=(ULONG)dest;
        while(src[at] || src[at+1]){unsigned start=(src[at]>>8)|((src[at+1]&4)<<6),stop=(src[at+1]>>8)|((src[at+1]&2)<<7),end=stop,j,words;
            if(start>=boundary)break;
            if(end>boundary)end=boundary;
            dest[to]=src[at];dest[to+1]=(UWORD)((src[at+1]&0xfd)|((end&255)<<8)|((end&256)>>7));
            words=(end-start)*2;
#ifdef V6_NORTH_ROUTE
            north_copy_words(dest+to+2,src+at+2,words);(void)j;
#else
            for(j=0;j+64<=words;j+=64)menu_copy64(dest+to+2+j,src+at+2+j);
            for(;j<words;++j)dest[to+2+j]=src[at+2+j];
#endif
            to+=2+words;
            if(end!=stop)break;
            at+=2+(stop-start)*2;
        }
        dest[to]=dest[to+1]=0;
        if(i<6 && i<count){const UWORD *actor=cursor?cursor:player_sprites[index].dma+i*68;
            data[i]=(ULONG)(actor+2);controls[i][0]=actor[0];controls[i][1]=actor[1];}
        else {data[i]=(ULONG)pickup_zero;controls[i][0]=controls[i][1]=0;}
    }
    building_frames[index]=-1;
    n=v6_menu_slide_owned_copper(list,menu_game_copper,menu_game_words,bitmap,planes,palette,world,offset);
    return n?v6_menu_slide_owned_rearm(list,n,data,controls,offset):0;
}
#endif
static int menu_full_copper(UWORD *list,unsigned index)
{
    uint16_t palette[32];V6UIIcon icons[8];V6UIState s;unsigned count,i,n;UWORD *p;
    if(!menu_prepare_bitmap())return 1;
    ui_copy(&s,&ui_rendered,sizeof(s));s.crew_frame=menu_crew_frame;
    v6_ui_palette(palette);count=v6_ui_icons(icons,&s);
#ifdef V6_MENU_SLIDE
    unsigned offset=v6_map_transition_offset(&map_transition,(UWORD)diag.logic_remainder/1000);
#endif
    for(i=0;i<count && i<6;++i){unsigned tile=icons[i].tile==12?2:icons[i].tile;
        if(ui_sprite_page[index]!=s.page || ui_sprite_tiles[index][i]!=tile
#ifdef V6_MENU_SLIDE
           || offset
#endif
          )
            menu_sprite(player_sprites[index].dma+i*68,ui_portrait[tile],icons[i].x,icons[i].y,6,icons[i].colour,i,
#ifdef V6_MENU_SLIDE
                offset);
#else
                0);
#endif
        ui_sprite_tiles[index][i]=tile;palette[17+(i>>1)*4+(i&1)*2]=(UWORD)icons[i].colour;
    }
    ui_sprite_page[index]=count?s.page:0;
#ifdef V6_MENU_SLIDE
    /* A translated portrait is not a reusable full-page portrait. */
    if(offset)ui_sprite_page[index]=0;
#endif
#ifdef V6_MENU_SLIDE
    if(offset && offset<240)
        n=menu_partial_copper(list,index,(ULONG)(ui_bitmaps+ui_render_bank*V6_UI_BYTES),4,palette,offset,count,0);
    else
#endif
    {
        n=v6_menu_copper(list,(ULONG)(ui_bitmaps+ui_render_bank*V6_UI_BYTES),palette,(ULONG)pickup_zero,(ULONG)pickup_zero,4);
        if(!n)return 0;
        /* Sprite pointers must precede the line-44 wait. */
        for(i=0;i<8;++i) {
            ULONG address=i<6 && i<count?(ULONG)(player_sprites[index].dma+i*68):(ULONG)pickup_zero;
            list[i*4+1]=(UWORD)(address>>16);list[i*4+3]=(UWORD)address;
        }
    }
    if(!n)return 0;
    p=list+n-2;
    if(s.page==1)for(i=0;i<3;++i) {
        uint16_t colours[4];unsigned j;v6_ui_crew_colours(colours,i);
#ifdef V6_MENU_SLIDE
        unsigned line=83+i*64+offset;
        if(line>=292)continue;
        if(line>=255 && (i==0?52+offset:83+(i-1)*64+offset)<255)p=move(p,0xffdf,0xfffe);
        if(line!=255)p=move(p,(UWORD)(((line&255)<<8)|0xdf),0xfffe);
#else
        p=move(p,(UWORD)(((51+32+i*64)<<8)|0xdf),0xfffe);
#endif
        for(j=0;j<4;++j)p=move(p,0x190+j*2,colours[j]);
    }
    p=move(p,0xffff,0xfffe);
    menu_complete_diag.values[0]=(ULONG)ui_bitmaps;menu_complete_diag.values[1]=ui_render_bank;
    menu_complete_diag.values[2]=campaign_menu.crew_mask;menu_complete_diag.values[3]=campaign_menu.deaths;
    menu_complete_diag.values[4]=campaign_menu.clock.minutes;menu_complete_diag.values[5]=campaign_menu.clock.seconds;
    menu_complete_diag.values[7]=campaign_menu.clock.hours;menu_complete_diag.values[8]=campaign_menu.clock.frames;
    menu_complete_diag.values[9]=campaign_menu.last.exists;menu_complete_diag.values[10]=campaign_menu.last.room_x;
    menu_complete_diag.values[11]=campaign_menu.last.room_y;menu_complete_diag.values[12]=campaign_menu.last.clock.hours;
    menu_complete_diag.values[13]=campaign_menu.last.clock.minutes;menu_complete_diag.values[14]=campaign_menu.last.clock.seconds;
    menu_complete_diag.values[15]=campaign_menu.last.clock.frames;menu_complete_diag.values[16]=campaign_menu.last.trinkets;
    menu_complete_diag.values[17]=campaign_menu.last.crew_mask;
    (void)index;return (unsigned)(p-list)<=LIST_WORDS;
}
#endif
#ifdef V6_MAP_DISPLAY_CAPTURE
static int map_refresh(void)
{
    unsigned i;
        unsigned changed=0;
        for(i=0;i<V6_EXPLORED_BYTES;++i)if(map_bitmap_exploration.rooms[i]!=tele_exploration.rooms[i])changed=1;
        if(changed) {
#ifdef V6_NORTH_ROUTE
            unsigned byte,first=240,last=0,top=21,column=0;
            for(byte=0;byte<50;++byte){unsigned diff=map_bitmap_exploration.rooms[byte]^tele_exploration.rooms[byte];
                if(diff){unsigned bit,local_top=top,local_column=column;
                    for(bit=0;bit<8;++bit){
                        if(diff&(1U<<bit)){
                            if(local_top<first)first=local_top;
                            if(local_top+9>last)last=local_top+9;
                        }
                        if(++local_column==20){local_column=0;local_top+=9;}
                    }
                }
                column+=8;if(column>=20){column-=20;top+=9;}
            }
            if(map_bitmap_rows<240){if(map_bitmap_rows<first)first=map_bitmap_rows;if(map_bitmap_stop>last)last=map_bitmap_stop;}
            map_bitmap_rows=first;map_bitmap_stop=last;
#else
            map_bitmap_rows=0;
#endif
#ifdef V6_MENU_SLIDE
            menu_map_title=~0U;
#endif
            ui_copy(&map_bitmap_exploration,&tele_exploration,sizeof(tele_exploration));
        }
        if(map_bitmap_rows<240) {
            UBYTE row[200];unsigned plane;
            if(!v6_map_draw_template_row(row,map_bitmap_rows,&map_bitmap_exploration,map_template_rle,sizeof(map_template_rle),map_template_offsets,map_fog_bits))return 0;
            for(plane=0;plane<5;++plane)for(i=0;i<40;++i)
                map_bitmap[plane*V6_MAP_PLANE_BYTES+map_bitmap_rows*40+i]=row[plane*40+i];
            ++map_bitmap_rows;++map_display_diag.values[0];
#ifdef V6_NORTH_ROUTE
            if(map_bitmap_rows==map_bitmap_stop)map_bitmap_rows=240;
#endif
        }
    return 1;
}
#endif
static int prepare_world(UBYTE *ring,UWORD *list,unsigned index,unsigned camera,unsigned *drawn) {
#ifdef V6_MENU_COMPLETE
    if(!map_transition.active || !map_menu.page)ui_sprite_page[index]=0;
#endif
    UWORD *p=list;unsigned i,background_rows,copied,bg_camera=background_camera(camera);
#ifdef V6_MENU_SLIDE
    /* Copy a tall frozen sprite bank and compose its first translated field
       as separate bounded jobs. Retain the prepared game list once. */
    if(map_transition.active && menu_capture_pending){menu_capture_pending=0;
#ifdef V6_NORTH_ROUTE
        /* Prepare the hidden title during the existing snapshot field,
         * before translating eight live sprite spans plus the companion. */
        if(route.index>=14 && map_menu.page==0 && map_bitmap_rows==240 && menu_map_title!=route.index){
            MenuFill fill={map_bitmap,5,0,12};
            if(!menu_fill(&fill,0,0,320,12,0))return 0;
            menu_text(&fill,160,2,menu_roomname(),map_ui_colours[4],1);menu_map_title=route.index;}
#endif
        if(drawn){*drawn=0;}return 1;}
#endif
    copied=0;
#ifdef V6_MAP_DISPLAY_CAPTURE
#ifdef V6_MENU_COMPLETE
    if(ui_bitmaps && map_transition.active && map_menu.page>0) {
        if(drawn)*drawn=0;
        return menu_full_copper(list,index);
    }
#endif
#ifdef V6_SAVE_DISPLAY_CAPTURE
    if(save_bitmap && map_transition.active && map_menu.page==3 && !map_menu.saved && route.index==9) {
        unsigned failed=map_menu.failed!=0;
        if(!v6_menu_copper(list,(ULONG)(save_bitmap+failed*V6_SAVE_BITMAP_BYTES),
            save_palette,(ULONG)pickup_zero,(ULONG)pickup_zero,3))return 0;
        ++save_display_diag.values[failed];
        save_display_diag.values[2]=(ULONG)save_bitmap;
        save_display_diag.values[3]=(ULONG)(save_bitmap+V6_SAVE_BITMAP_BYTES);
        if(drawn)*drawn=0;
        return 1;
    }
#endif
    if(map_bitmap) {
#ifdef V6_NORTH_ROUTE
        /* Keep hidden exploration redraw off the live tutorial's full render
         * path. An opened map owns the redraw budget; otherwise defer it. */
        if(!route_loading && (!conundrum_trigger.visible || map_transition.active) && !map_refresh())return 0;
#else
        if(!map_refresh())return 0;
#endif
        map_slide_offset=map_transition.active?v6_map_transition_offset(&map_transition,(UWORD)diag.logic_remainder/1000):240;
#ifdef V6_MENU_SLIDE
        if(map_transition.active && map_menu.page==0 && map_bitmap_rows==240 && menu_map_title!=route.index){
            MenuFill fill={map_bitmap,5,0,12};
            if(!menu_fill(&fill,0,0,320,12,0))return 0;
            menu_text(&fill,160,2,menu_roomname(),map_ui_colours[4],1);menu_map_title=route.index;
        }
        if(map_transition.active && map_menu.page==0 && map_bitmap_rows==240 && map_slide_offset>0 && map_slide_offset<240) {
            uint16_t palette[32];int x,y;unsigned words;UWORD *cursor;
            unsigned mode=v6_map_cursor_mode(map_cursor_state,map_cursor_delay,session.noflashing);
            v6_sprites_begin(&player_sprites[index],player_sprites[index].dma);
            cursor=menu_map_sprite(index,mode,map_slide_offset,&x,&y);if(!cursor)return 0;
            for(i=0;i<32;++i)palette[i]=map_palette[i];
            palette[17]=mode==1?0xfff:0x1ee;
            words=menu_partial_copper(list,index,(ULONG)map_bitmap,5,palette,map_slide_offset,mode?1:0,cursor);
            if(!words)return 0;
            if(map_slide_diag.count<MAP_CAPTURE_ROWS(96)){volatile ULONG *r=map_slide_diag.records[map_slide_diag.count++];
                r[0]=map_slide_offset;r[1]=index;r[2]=(ULONG)list;r[3]=(ULONG)ring;r[4]=(ULONG)cursor;}
            if(drawn)*drawn=0;
            return 1;
        }
#endif
        if(map_transition.active && !map_slide_offset && map_menu.page==0 &&
#ifndef V6_MENU_SLIDE
           route.index==9 &&
#endif
           map_bitmap_rows==240) {
            uint16_t palette[32];int x,y;
            unsigned mode=v6_map_cursor_mode(map_cursor_state,map_cursor_delay,session.noflashing);
            uint32_t sprite=(ULONG)player_sprites[index].dma;
            map_display_diag.values[2]=(ULONG)map_bitmap;
            map_display_diag.values[3]=sprite;
            map_display_diag.values[4]=(ULONG)pickup_zero;
            v6_sprites_begin(&player_sprites[index],player_sprites[index].dma);
#ifdef V6_MENU_SLIDE
            sprite=(ULONG)menu_map_sprite(index,mode,0,&x,&y);if(!sprite)return 0;
#else
            uint32_t rows[32];
            if(!v6_map_cursor_rows(rows,mode,112,107,&x,&y))return 0;
            if(mode && v6_sprites_add_rect(&player_sprites[index],rows,x,y,0,12,9,mode==1?0xfff:0x1ee)<0)return 0;
#endif
            for(i=0;i<32;++i)palette[i]=map_palette[i];
            palette[17]=mode==1?0xfff:0x1ee;
            if(!v6_map_copper(list,(ULONG)map_bitmap,palette,(ULONG)pickup_zero,sprite))return 0;
            if(drawn)*drawn=0;
            ++map_display_diag.values[1];map_display_diag.values[2]=(ULONG)map_bitmap;
            map_display_diag.values[3]=x;map_display_diag.values[4]=y;
            if(map_display_diag.count<MAP_CAPTURE_ROWS(128)) {
                volatile ULONG *r=map_display_diag.records[map_display_diag.count++];
                r[0]=map_cursor_state;r[1]=map_cursor_delay;r[2]=mode;r[3]=index;r[4]=sprite;r[5]=palette[17];
            }
            return 1;
        }
    }
#endif
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if((route.index==10 || route.index==11) && west_copper_ready[index] &&
       !camera && !shake_timer && !ui_fields && !rescue_fade && !rescue_vm.speech && !rescue_bars &&
       !pickup_screen.state && !pickup_draw.bars && !pickup_fade.visible) {
        if(drawn)*drawn=0;
        goto west_actor_draw;
    }
    west_copper_ready[index]=0;
#endif
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
west_actor_draw:
    if(route.index==10 && west_tread_drawn[index]!=(int)west_tread_phase) {
        v6_prize_return_draw_conveyors(ring,deception_treads[west_tread_phase]);
    }
    if(route.index==10)west_tread_drawn[index]=west_tread_phase;
    if(route.index==11) {
        if(!v6_prize_return_draw_platforms(ring,&west_actors,
            &downunder_strips[0][0],downunder_platform,downunder_platform_mask,west_platform_y[index]))return 0;
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(west_copper_ready[index])goto west_sprite_refresh;
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
west_sprite_refresh:
#endif
    v6_sprites_begin(&player_sprites[index],player_sprites[index].dma);
#ifdef V6_TOWER_BUILDING
    if(route.rooms[route.index].teleporter) {
#ifdef V6_TOWER_SHAKE
        /* This bounded fixture restores only teleporter heads. Its six
         * sprite strips must remain away from clipping edges at every offset. */
        if(route.rooms[route.index].teleporter->x<4 || route.rooms[route.index].teleporter->x>222 ||
           route.rooms[route.index].teleporter->y<4 || route.rooms[route.index].teleporter->y>142)return 0;
#endif
        #ifdef V6_NORTH_ROUTE
        const UWORD *const *prepared=building_prepared;
#else
        const UWORD (*prepared)[6*V6_TELEPORTER_DMA_WORDS]=building_prepared;
#endif
#ifdef V6_TOWER_ENERGIZE
        if(route.index==5)prepared=energize_prepared;
#endif
#ifdef V6_MENU_COMPLETE
        int origin_x=route.rooms[route.index].teleporter->x-112;
        int origin_y=route.rooms[route.index].teleporter->y-48;
#endif
        UWORD *bank=building_dma+index*(6*V6_TELEPORTER_DMA_WORDS);
        int frame=building_animation.frame;
        if(frame<1)frame=1;
        if(frame>9)frame=8;
        if(building_frames[index]!=frame) {
            v6_teleporter_copy_dma(bank,prepared[frame]);
#ifdef V6_MENU_COMPLETE
            v6_screen_shake_heads(bank,prepared[frame],V6_TELEPORTER_DMA_WORDS,origin_x,origin_y);
#endif
            building_frames[index]=frame;
#ifdef V6_TOWER_SHAKE
            shake_heads[index]=0;
#endif
        }
#ifdef V6_TOWER_SHAKE
        /* The fixture teleporter is away from viewport edges. Restore heads
         * after each translation; the bounds check excludes pixel clipping. */
        if(shake_heads[index] || shake_plan.x || shake_plan.y)
            v6_screen_shake_heads(bank,prepared[frame],V6_TELEPORTER_DMA_WORDS,
#ifdef V6_MENU_COMPLETE
                origin_x+shake_plan.x,origin_y+shake_plan.y);
#else
                shake_plan.x,shake_plan.y);
#endif
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
        v6_sprites_add(&player_sprites[index],
#ifdef V6_TOWER_PRIZE
                      tower_player_cropped_rows[player_frame],session.player.x+6,
                      session.player.y-(int)camera,0,
#else
                      tower_player_rows[player_frame],session.player.x,
                      session.player.y-(int)camera,6,
#endif
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(route.index==10) {
        unsigned n;
        for(n=0;n<2;++n) {
            int frame=west_enemy_animation[n].frame;
            const uint32_t *rows=frame<0?tower_player_rows[0]:return_enemy_visible[frame];
            if(v6_sprites_add_rect(&player_sprites[index],rows,west_actors.enemies[n].x,
                west_actors.enemies[n].y,0,frame<0?32:16,frame<0?32:16,0xf44)<V6_SPRITE_CLIPPED)return 0;
        }
    }
#endif
#ifdef V6_TOWER_PRIZE
    if(route.index==8) {
        if(v6_sprites_add_rect(&player_sprites[index],prize_waiting_rows,
            station_prize.waiting.x,station_prize.waiting.y,0,32,8,0xfff)<V6_SPRITE_CLIPPED)return 0;
        if(station_prize.trinket.visible &&
           v6_sprites_add_rect(&player_sprites[index],tower_player_rows[22],192,128,0,16,16,0xfff)<V6_SPRITE_CLIPPED)return 0;
    }
#endif
#ifdef V6_NORTH_ROUTE
    if(route.index>=10 && !north_prepare_sprites(index))return 0;
#endif
    if(player_sprites[index].count>world_diag.values[12]) world_diag.values[12]=player_sprites[index].count;
#endif
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(west_copper_ready[index]) {
        for(i=0;i<player_sprites[index].count;++i)
            list[west_colour_words[index][i]]=player_sprites[index].colours[i];
        return 1;
    }
#endif
    for(i=0;i<8;++i) {
        UWORD *sprite=player_sprites[index].dma+i*V6_SPRITE_WORDS;
        unsigned sprite_words=V6_SPRITE_WORDS;
        ULONG address=(ULONG)sprite;
#ifdef V6_NORTH_ROUTE
        if(route.index>=10){sprite=i<6?building_dma+(index*6+i)*196:north_extra_dma+(index*2+i-6)*196;
            sprite_words=196;address=(ULONG)sprite;}
#endif
#ifdef V6_TOWER_BUILDING
        if(route.rooms[route.index].teleporter && i<6) {
            sprite=building_dma+(index*6+i)*V6_TELEPORTER_DMA_WORDS;
            sprite_words=V6_TELEPORTER_DMA_WORDS;address=(ULONG)sprite;
        }
#endif
#ifdef V6_TOWER_SHAKE
        if(
#ifdef V6_NORTH_ROUTE
           route.index<10 &&
#endif
           (shake_plan.x || shake_plan.y) &&
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if(route.index==10 || route.index==11) {
        for(i=0;i<8;++i) {
            west_colour_words[index][i]=(unsigned)(p-list)+1;
            p=move(p,v6_sprite_colour_register(i),DISPLAY_COLOUR(player_sprites[index].colours[i]));
        }
    } else
#endif
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
#ifdef V6_MAP_DISPLAY_CAPTURE
    if(map_transition.active && map_menu.page==0 && route.index==9 && map_bitmap_rows==240 && map_slide_offset>0 && map_slide_offset<240) {
        uint16_t palette[32];uint32_t rows[32];int x,y;
        unsigned mode=v6_map_cursor_mode(map_cursor_state,map_cursor_delay,session.noflashing),words;
        ULONG cursor=(ULONG)(player_sprites[index].dma+7*V6_SPRITE_WORDS);
        if(camera || player_sprites[index].count>=7)return 0;
        for(i=0;i<7;++i) {
            v6_map_slide_clip(player_sprites[index].dma+i*V6_SPRITE_WORDS,map_slide_offset);
            v6_map_slide_channel(player_sprites[index].dma+i*V6_SPRITE_WORDS,i+1);
        }
        /* Only clear the reserved block: v6_sprites_begin clears all eight. */
        for(i=0;i<V6_SPRITE_WORDS;++i)player_sprites[index].dma[7*V6_SPRITE_WORDS+i]=0;
        if(!v6_map_cursor_rows(rows,mode,112,107,&x,&y))return 0;
        y+=(int)map_slide_offset;
        if(mode)v6_map_slide_cursor((UWORD *)cursor,rows,(unsigned)x,(unsigned)y);
        for(i=0;i<32;++i)palette[i]=map_palette[i];
        palette[17]=mode==1?0xfff:0x1ee;
        /* Reserve hardware sprite 0 before its first control DMA fetch.
           Remap the frozen actors to channels 1..7, retaining their colours. */
        for(i=1;i<8;++i) {
            ULONG actor=(ULONG)(player_sprites[index].dma+(i-1)*V6_SPRITE_WORDS);
            p=move(p,0x120+i*4,actor>>16);p=move(p,0x122+i*4,actor);
            if(i<=player_sprites[index].count)p=move(p,v6_sprite_colour_register(i),player_sprites[index].colours[i-1]);
        }
        words=v6_map_slide_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
            bg_camera&255,(ULONG)map_bitmap,palette,(ULONG)pickup_zero,cursor,map_slide_offset);
        if(!words || (unsigned)(p-list)+words>LIST_WORDS)return 0;
        if(map_slide_diag.count<MAP_CAPTURE_ROWS(96)) {
            volatile ULONG *r=map_slide_diag.records[map_slide_diag.count++];
            r[0]=map_slide_offset;r[1]=index;r[2]=(ULONG)list;r[3]=(ULONG)ring;r[4]=cursor;
        }
        return 1;
    }
#endif
#ifdef V6_TOWER_PICKUP_SCREEN
#ifdef V6_MAP_INPUT_CAPTURE
    if((map_menu.open
#ifdef V6_MAP_DISPLAY_CAPTURE
        || map_transition.active
#endif
       )
#ifdef V6_MAP_DISPLAY_CAPTURE
       && !(map_menu.page==0 && map_slide_offset==240)
#endif
      ) {
        unsigned page=map_menu.page;
        if(page==3 && (map_menu.saved || map_menu.failed))page=map_menu.saved?4:5;
        return v6_tower_caption_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
            camera&255,bg_camera&255,(ULONG)(map_captions+page*V6_DIALOGUE_BYTES),
            0x6ff,DISPLAY_COLOUR(FG_PALETTE[1]),DISPLAY_COLOUR(FG_PALETTE[3]))!=0;
    }
#endif
    if(!pickup_prepare(ring,index,camera))return 0;
#ifdef V6_VSTITCH_HINT_CAPTURE
    vstitch_prepare_bitmap(ring,index,camera);
    if(vstitch_hint.visible && route.index==9) {
        ULONG colours=v6_vstitch_hint_colours(vstitch_previous_level,vstitch_hint.level,diag.logic_remainder);
        if(!colours || !vstitch_bitmap_ready[index])return 0;
        if(vstitch_draw_trace.count<VSTITCH_DRAW_ROWS) {
            volatile LONG *h=vstitch_draw_trace.records[vstitch_draw_trace.count++];
            h[0]=diag.logic_ticks;h[1]=vstitch_previous_level;h[2]=vstitch_hint.level;
            h[3]=diag.logic_remainder;h[4]=colours;h[5]=index;h[6]=vstitch_hint.visible;
        }
        return v6_vstitch_hint_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),camera&255,bg_camera&255,
            (ULONG)(pickup_banks+index*V6_PICKUP_BANK_BYTES+V6_PICKUP_TEXT_OFFSET),(ULONG)pickup_zero,
            colours>>16,colours&0xffff)!=0;
    }
#endif
    if(pickup_fade.visible || pickup_draw.bars) {
        unsigned cache=index*2+pickup_fade.visible;
        unsigned key=(camera&255)|((bg_camera&255)<<8)|
            (pickup_fade.visible<<16)|((pickup_render_bars>40)<<17)|
            ((pickup_render_bars>0)<<18);
        /* Bar width changes bitmap words, but its Copper segment changes
         * only when a strip appears/disappears or a ring offset changes. */
        if(!pickup_copper_words[cache] || pickup_copper_key[cache]!=key) {
            pickup_copper_words[cache]=v6_pickup_copper(pickup_copper_cache[cache],
                (ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),camera&255,bg_camera&255,
                (ULONG)(pickup_banks+index*V6_PICKUP_BANK_BYTES),(ULONG)pickup_zero,
                pickup_fade.visible,pickup_render_bars,pickup_colours>>16,pickup_colours&0xffff);
            pickup_copper_key[cache]=key;
            pickup_copper_colours[cache]=pickup_colours;
            pickup_copper_tint_count[cache]=0;
            for(i=0;pickup_fade.visible && i<pickup_copper_words[cache];i+=2) {
                unsigned address=pickup_copper_cache[cache][i];
                if(address==0x18a || (address==0x188 && pickup_copper_cache[cache][i+1]))
                    pickup_copper_tints[cache][pickup_copper_tint_count[cache]++]=i+1;
            }
        }
        if(!pickup_copper_words[cache])return 0;
        /* Palette changes do not rebuild the geometry segment. Only the
         * two textbox fill writes and up to four ink writes need patching. */
        if(pickup_copper_colours[cache]!=pickup_colours) {
            for(i=0;i<pickup_copper_tint_count[cache];++i) {
                unsigned word=pickup_copper_tints[cache][i];
                pickup_copper_cache[cache][word]=(UWORD)(pickup_copper_cache[cache][word-1]==0x188?
                    pickup_colours>>16:pickup_colours&0xffff);
            }
            pickup_copper_colours[cache]=pickup_colours;
        }
        {
            const PickupCopperLong *src=(const void *)pickup_copper_cache[cache];
            PickupCopperLong *dst=(void *)p;
            for(i=0;i<pickup_copper_words[cache]/2;++i)*dst++=*src++;
        }
        return 1;
    }
#endif
#ifdef V6_NORTH_ROUTE
    if(route.index==19 && conundrum_trigger.visible){
        ULONG colours=v6_vstitch_hint_colours(conundrum_previous_level,conundrum_trigger.level,diag.logic_remainder);
        return colours && v6_tower_caption_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
            camera&255,bg_camera&255,(ULONG)rescue_captions,colours&0xffff,
            DISPLAY_COLOUR(FG_PALETTE[1]),DISPLAY_COLOUR(FG_PALETTE[3]))!=0;
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
    if(!v6_tower_dual_copper(p,(ULONG)ring,(ULONG)(ring+V6_TOWER_RING_BYTES),
        camera&255,bg_camera&255))return 0;
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
    if((route.index==10 || route.index==11) && !camera)west_copper_ready[index]=1;
#endif
    return 1;
}
#ifdef V6_NORTH_ROUTE
static void north_layer_warm(const UBYTE *ring,unsigned index)
{
    unsigned row,p,strip;
    if(north_read_copied<TERMINAL_READ_BYTES){unsigned count=TERMINAL_READ_BYTES-north_read_copied;
        if(count>256)count=256;
        north_copy_words((UWORD *)(pickup_banks+north_read_copied),(const UWORD *)(terminal_read_pcm+north_read_copied),count/2);
        north_read_copied+=count;}
    if(north_layer_stage==0){unsigned hog;
        if(index!=north_layer_row || beam()>=70 || !north_base_words[north_layer_row])return;
        hog=hw->dmaconr&0x0400;hw->dmacon=DMAF_SETCLR|0x0400;
        for(strip=0;strip<2;++strip)for(p=0;p<3;++p){unsigned y=strip?224:0;wait_blit();
            hw->bltcon0=p<2?0x09f0:0x0100;hw->bltcon1=0;
            hw->bltafwm=hw->bltalwm=0xffff;hw->bltamod=hw->bltdmod=0;
            hw->bltapt=(APTR)(ring+p*V6_TOWER_PLANE_BYTES+y*40);
            hw->bltdpt=ui_bitmaps+north_layer_row*V6_TERMINAL_BITMAP+p*9600+y*40;
            hw->bltsize=(16<<6)|20;}
        wait_blit();if(!hog)hw->dmacon=0x0400;
        v6_terminal_scene_windows(&north_terminal_prefix[north_layer_row],
            (ULONG)(ui_bitmaps+north_layer_row*V6_TERMINAL_BITMAP),(ULONG)(ui_bitmaps+57600),
            (ULONG)ring,(ULONG)pickup_zero);
        if(++north_layer_row==2){north_layer_stage=1;north_layer_row=0;}
    }else if(north_layer_stage==1){UWORD data[20];
        unsigned end=north_layer_row+2;if(end>120)end=120;
        for(row=north_layer_row;row<end;++row){unsigned at=terminal_row_offsets[row],size=terminal_row_offsets[row+1]-at;
            if(!v6_terminal_layer_decode((UBYTE *)data,terminal_row_packets+at,size)){diag.error=23;return;}
            north_copy_words((UWORD *)(ui_bitmaps+57600+(48+row)*40),data,20);
        }
        north_layer_row=end;if(end==120)north_layer_stage=2;
    }
    north_read_diag.values[6]=north_layer_stage;north_read_diag.values[7]=north_layer_row;
}
static int north_layer_present(UBYTE *ring,UWORD *list,unsigned index)
{
    UBYTE *bitmap=ui_bitmaps+index*V6_TERMINAL_BITMAP,*band=ui_bitmaps+2*V6_TERMINAL_BITMAP;
    unsigned n,visible=north_reader.boxes[0].visible;
    if(north_layer_stage!=2)return 0;
    if(north_layer_bars[index]!=north_read_bars){
        v6_terminal_layer_bars(bitmap,ring,north_read_bars,north_layer_bars[index]);north_layer_bars[index]=north_read_bars;}
    n=v6_terminal_scene_copper(list,&north_terminal_prefix[index],&north_mux_plan,north_mux_actors,
        north_overlay.start?&north_overlay:0,(ULONG)bitmap,(ULONG)band,(ULONG)ring,(ULONG)pickup_zero,
        visible,v6_terminal_box_gray(&north_reader.boxes[0]));
    if(!n)return 0;
    north_read_diag.values[8]=(ULONG)bitmap;north_read_diag.values[9]=(ULONG)band;
    north_read_diag.values[10]=(ULONG)ring;north_read_diag.values[11]=(ULONG)list;
    north_read_diag.values[12]=north_read_bars;north_read_diag.values[13]=visible;
    north_read_diag.values[14]=north_reader.phase;north_read_diag.values[15]=session.player.flips;
    return 1;
}
#endif
static int prepare(UBYTE *ring,UWORD *list,unsigned index,unsigned camera,unsigned *drawn)
{
#ifdef V6_NORTH_ROUTE
    if(diag.status==1 && ui_bitmaps && route.index==14 && !route_loading && !map_transition.active && north_layer_stage<2)north_layer_warm(ring,index);
    if(north_terrain_pending){route.room.terrain=0;
        v6_terrain_build(&north_shared_terrain,&route.room);route.room.terrain=&north_shared_terrain;north_terrain_pending=0;}
    if(north_memo_pending && diag.status!=1){
        if(companion.visible)v6_companion_rest_prime(north_companion_rest,3,&companion,&route.room);
        north_memo_pending=0;
    }
#endif
#ifdef V6_NORTH_ROUTE
    /* Refresh newly explored nine-row map bands on spare cached-world fields.
     * A live tutorial uses prepare_world, which already spends this row budget. */
    if(route.index>=10 && !map_transition.active && !conundrum_trigger.visible && north_base_words[index] &&
       north_base_room[index]==route.index && north_copper_tick[index^1]==diag.logic_ticks)
#ifdef V6_NORTH_ROUTE
        if(!route_loading && !map_refresh())return 0;
#else
        if(!map_refresh())return 0;
#endif
    if(map_transition.active)north_copper_ready[index]=0;
    if(route.index>=10 && north_copper_ready[index] && north_copper_tick[index]==diag.logic_ticks &&
       north_copper_room[index]==route.index && !camera && !shake_timer && !ui_fields && !rescue_fade &&
       !conundrum_trigger.visible && !rescue_vm.speech && !rescue_bars && !pickup_screen.state && !map_transition.active){if(drawn)*drawn=0;return 1;}
#endif
    int ok;
#ifdef V6_NORTH_ROUTE
    if(route.index>=10 && north_base_words[index] && north_base_room[index]==route.index &&
       !camera && !shake_timer && !ui_fields && !rescue_fade && !conundrum_trigger.visible && !rescue_vm.speech && !rescue_bars &&
       !pickup_screen.state && !map_transition.active){
        if(drawn)*drawn=0;
        if(!north_copper_ready[index] && !(route.index==14 &&
           (north_read_bars || north_reader.boxes[0].visible)))
            north_copy_words(list,north_base_copper[index],north_base_words[index]);
        ok=north_prepare_sprites(index);
    } else
#endif
    {
        ok=prepare_world(ring,list,index,camera,drawn);
    }
#ifdef V6_NORTH_ROUTE
    if(ok && route.index>=10 && !map_transition.active){UWORD merged[512];unsigned words,n,i;const UWORD *base;
        if(!camera && !shake_timer && !ui_fields && !rescue_fade && !conundrum_trigger.visible && !rescue_vm.speech && !rescue_bars && !pickup_screen.state){
            if(!north_base_words[index] || north_base_room[index]!=route.index){
                for(words=0;words+1<192;words+=2)if(list[words]==0xffff)break;
                if(words+1>=192)return 0;
                north_base_words[index]=words+2;north_base_room[index]=route.index;
                /* Every sprite/overlay starts at physical line 68 or later.
                 * The stable prefix through line 44 needs no per-tick merge. */
                north_base_tail[index]=words;
                for(i=0;i<words;i+=2)if((list[i]&1) && (list[i]>>8)>=67){north_base_tail[index]=i;break;}
                for(i=0;i<words+2;++i)north_base_copper[index][i]=list[i];
                if(route.index==14 && !v6_terminal_scene_prefix(&north_terminal_prefix[index],north_base_copper[index],words+2))return 0;
            }
            base=north_base_copper[index];words=north_base_words[index];
        } else {base=list;for(words=0;words+1<512;words+=2)if(list[words]==0xffff)break;words+=2;}
        if(route.index==14 && (north_read_bars || north_reader.boxes[0].visible)){
            if(!north_layer_present(ring,list,index))return 0;
            n=1;
        }else if(base==north_base_copper[index] && north_base_tail[index]==words-2) {
            /* All prefix waits precede these actors. Its register prefix
             * is already in this bank; replace only the palette tail. */
            n=north_overlay.start?v6_sprite_mux_append_overlay(list,words,&north_mux_plan,north_mux_actors,&north_overlay):
                v6_sprite_mux_append_palette(list,words,&north_mux_plan,north_mux_actors);
        } else if(base==north_base_copper[index]){
            unsigned head=north_base_tail[index];
            /* Merge only the short ring-wrap tail, preserving the immutable
             * early register prefix already installed in this inactive bank. */
            n=north_overlay.start?v6_sprite_mux_overlay_copper(list+head,base+head,words-head,&north_mux_plan,north_mux_actors,&north_overlay):
                v6_sprite_mux_rendered_copper(list+head,base+head,words-head,&north_mux_plan,north_mux_actors);
        } else {
            n=north_overlay.start?v6_sprite_mux_overlay_copper(merged,base,words,&north_mux_plan,north_mux_actors,&north_overlay):
                v6_sprite_mux_rendered_copper(merged,base,words,&north_mux_plan,north_mux_actors);
            if(n)north_copy_words(list,merged,n);
        }
        if(!n)return 0;
        north_copper_ready[index]=!ui_fields && !conundrum_trigger.visible && !rescue_vm.speech && !rescue_bars && !pickup_screen.state &&
            !north_read_bars && !north_reader.boxes[0].visible;
        north_copper_tick[index]=diag.logic_ticks;north_copper_room[index]=route.index;
    }
#endif
    return ok;
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
#ifdef V6_VSTITCH_HINT_CAPTURE
    HASH(vstitch_seen);
#ifdef V6_MENU_COMPLETE
    HASH(campaign_menu.story_flags);
#ifdef V6_NORTH_ROUTE
    HASH(conundrum_trigger.active);HASH(conundrum_trigger.pending);HASH(conundrum_trigger.visible);
    HASH(conundrum_trigger.timer);HASH(conundrum_trigger.level);HASH(conundrum_trigger.hints);
#endif
#endif
#ifdef V6_MAP_INPUT_CAPTURE
    HASH(vstitch_hint.active);HASH(vstitch_hint.pending);HASH(vstitch_hint.visible);
    HASH(vstitch_hint.timer);HASH(vstitch_hint.level);HASH(vstitch_hint.mode);
#endif
#endif
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
#if defined(V6_STATION_MENU) && !defined(V6_MENU_COMPLETE)
static int ui_station_checkpoint_valid(const V6CheckpointSave *c,const V6HallwayStory *s)
{
    /* Only resident station rooms run the yellow slice; red progress is retained,
     * but its active companion requires the separate red runtime. */
#ifdef V6_MENU_COMPLETE
    (void)s;return checkpoint_bank_valid(c);
#else
    return checkpoint_bank_valid(c) && !s->companion &&
        ((c->room_x==111 && (c->room_y==104 || c->room_y==105 || c->room_y==106
#ifdef V6_TOWER_COLLECTION_SAVE
            || c->room_y==107
#endif
        )) ||
         (c->room_x==110 && c->room_y==105)
#ifdef V6_VSTITCH_HINT_CAPTURE
         || (c->room_x==112 && c->room_y==107)
#endif
         );
#endif
}
#endif
static int ui_load_checked(V6CheckpointSave *out,V6HallwayStory *story)
{
#ifdef V6_MENU_COMPLETE
    V6MenuRecord r,b;int a=v6_campaign_dos.exists(save_name),k=v6_campaign_dos.exists(save_backup),result;
    if(a<0 || k<0)return V6_SAVE_IO;
    result=v6_campaign_menu_read(&v6_campaign_dos,a?save_name:save_backup,&r);if(result)return result;
    if(!checkpoint_bank_valid(&r.checkpoint))return V6_SAVE_CORRUPT;
    if(a && k){result=v6_campaign_menu_read(&v6_campaign_dos,save_backup,&b);if(result)return result;if(!checkpoint_bank_valid(&b.checkpoint))return V6_SAVE_CORRUPT;}
    result=v6_campaign_menu_recover(&v6_campaign_dos,save_name,save_temp,save_backup,&r);if(result)return result;
    ui_copy(out,&r.checkpoint,sizeof(*out));ui_copy(story,&r.red,sizeof(*story));
    ui_copy(&ui_loaded_yellow,&r.yellow,sizeof(r.yellow));ui_copy(&ui_loaded_exploration,&r.explored,sizeof(r.explored));
    ui_copy(&ui_loaded_collection,&r.collected,sizeof(r.collected));ui_copy(&ui_loaded_hints,&r.hints,sizeof(r.hints));
    ui_copy(&ui_loaded_menu,&r.menu,sizeof(r.menu));return 0;
#else
    int a=v6_campaign_dos.exists(save_name),k=v6_campaign_dos.exists(save_backup),result;
    V6CheckpointSave c,b;V6HallwayStory s,bs;
#ifdef V6_TOWER_MENU_TRAVEL
    V6Exploration map,bmap;
#ifdef V6_STATION_MENU
    V6StationStory yellow,byellow;
#ifdef V6_TOWER_COLLECTION_SAVE
    V6Collect collected,bcollected;
#ifdef V6_VSTITCH_HINT_CAPTURE
    V6CampaignHints hints,bhints;
#endif
#endif
#endif
#endif
    if(a<0 || k<0)return V6_SAVE_IO;
#ifdef V6_VSTITCH_HINT_CAPTURE
    result=v6_campaign_hint_read(&v6_campaign_dos,a?save_name:save_backup,&c,&s,&yellow,&map,&collected,&hints);
#elif defined(V6_TOWER_COLLECTION_SAVE)
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
#ifdef V6_VSTITCH_HINT_CAPTURE
        result=v6_campaign_hint_read(&v6_campaign_dos,save_backup,&b,&bs,&byellow,&bmap,&bcollected,&bhints);
#elif defined(V6_TOWER_COLLECTION_SAVE)
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
#ifdef V6_VSTITCH_HINT_CAPTURE
    return v6_campaign_hint_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_yellow,&ui_loaded_exploration,&ui_loaded_collection,&ui_loaded_hints);
#elif defined(V6_TOWER_COLLECTION_SAVE)
    return v6_campaign_collection_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_yellow,&ui_loaded_exploration,&ui_loaded_collection);
#elif defined(V6_STATION_MENU)
    return v6_campaign_progress_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_yellow,&ui_loaded_exploration);
#elif defined(V6_TOWER_MENU_TRAVEL)
    return v6_campaign_state_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story,&ui_loaded_exploration);
#else
    return v6_campaign_recover(&v6_campaign_dos,save_name,save_temp,save_backup,out,story);
#endif
#endif
}
static int ui_save_checked(void)
{
#ifdef V6_MENU_COMPLETE
    V6MenuRecord record;V6CheckpointSave c;V6HallwayStory story;int a,k,result;
    if(!checkpoint_bank_valid(&world.save))return V6_SAVE_INVALID;
    menu_record(&record);
    a=v6_campaign_dos.exists(save_name);k=v6_campaign_dos.exists(save_backup);
    if(a<0 || k<0)return V6_SAVE_IO;
    if(a || k){result=ui_load_checked(&c,&story);if(result)return result;}
    return v6_campaign_menu_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&record);
#else
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
#ifdef V6_VSTITCH_HINT_CAPTURE
    { uint8_t bytes[V6_CAMPAIGN_HINT_BYTES];V6CampaignHints hints={vstitch_seen};
      if(!v6_campaign_hint_encode(bytes,sizeof(bytes),&world.save,&hallway_story,&station_story,&tele_exploration,&station_collected,&hints))return V6_SAVE_INVALID; }
#elif defined(V6_TOWER_COLLECTION_SAVE)
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
#ifdef V6_VSTITCH_HINT_CAPTURE
    { V6CampaignHints hints={vstitch_seen};
      return v6_campaign_hint_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&station_story,&tele_exploration,&station_collected,&hints); }
#elif defined(V6_TOWER_COLLECTION_SAVE)
    return v6_campaign_collection_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&station_story,&tele_exploration,&station_collected);
#elif defined(V6_STATION_MENU)
    return v6_campaign_progress_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&station_story,&tele_exploration);
#elif defined(V6_TOWER_MENU_TRAVEL)
    return v6_campaign_state_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story,&tele_exploration);
#else
    return v6_campaign_replace(&v6_campaign_dos,save_name,save_temp,save_backup,&world.save,&hallway_story);
#endif
#endif
}
static int ui_apply_load(const V6CheckpointSave *c,const V6HallwayStory *story)
{
#ifdef V6_MENU_COMPLETE
    ui_copy(&campaign_menu,&ui_loaded_menu,sizeof(campaign_menu));menu_session_deaths=session.deaths;ui_ready=0;
#endif
#ifdef V6_TOWER_PICKUP_SCREEN
    v6_trinket_screen_init(&pickup_screen);pickup_held=0;pickup_pause_ticks=0;
    v6_pickup_draw_init(&pickup_draw);v6_pickup_fade_init(&pickup_fade);pickup_fade_shown=0;pickup_rows[0]=pickup_rows[1]=0;
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
#ifdef V6_VSTITCH_HINT_CAPTURE
    v6_vstitch_trigger_init(&vstitch_hint);vstitch_seen=ui_loaded_hints.map_hint_seen;
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
#ifdef V6_REGION_REPLAY
static unsigned region_replay_stage;
static V6CheckpointSave region_replay_origin;
static int region_replay(void)
{
    if(route_loading)return 1;
    if(region_replay_stage<3 && diag.logic_ticks>=20+region_replay_stage*30){
        unsigned index=12+region_replay_stage;const V6TowerRouteRoom *r=&tower_route_rooms[index];V6Checkpoint *c=r->checkpoints;
        world.save=(V6CheckpointSave){c->x-4,c->y-(c->tile==20?2:7),c->tile==20,1,r->x,r->y,c->id};
        if(region_replay_stage==2){V6AudioPlan plan;
            V6AudioSample sample={(ULONG)travel_audio_chip,TELEPORTER_FLASH_BYTES,TELEPORTER_PERIOD,64};
            if(!v6_paula_request(&travel_voices[2],&sample,&plan))return 0;
            travel_audio_apply(&plan);++travel_audio_requests;}
        if(!v6_tower_route_load(&route,r->x,r->y,1) || !route_source())return 0;
        ++region_replay_stage;
    }else if(region_replay_stage==3 && diag.logic_ticks>=110){
        ui_copy(&world.save,&region_replay_origin,sizeof(world.save));v6_tower_session_die(&session);++region_replay_stage;
    }else if(region_replay_stage==4 && route.index==11 && session.death_timer==-1)++region_replay_stage;
    return 1;
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
#ifdef V6_REGIONAL_CONTENT
    v6_region_init(&north_regions);route.materialize=region_materialize;
#endif
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
#ifdef V6_PRIZE_INPUT_CAPTURE
    station_story.rescue_triggered=station_story.yellow_rescued=1;station_story.companion=7;
    rescue_vm.following=1;rescue_vm.mood=0;
#ifdef V6_PRIZE_COLLECTION_INPUT_CAPTURE
    world.save=(V6CheckpointSave){236,134,1,1,111,107,443490};
#elif defined(V6_VSTITCH_HINT_CAPTURE)
    v6_vstitch_trigger_init(&vstitch_hint);vstitch_seen=0;
    world.save=(V6CheckpointSave){60,73,0,1,112,107,443501};
#elif defined(V6_VSTITCH_INPUT_CAPTURE)
    world.save=(V6CheckpointSave){276,185,0,1,112,107,443500};
#else
    world.save=(V6CheckpointSave){140,161,0,1,111,106,442490};
#endif
#ifdef V6_PRIZE_COLLECTION_INPUT_CAPTURE
    /* Bounded shaft entry; the earlier checkpoint approach is tested separately. */
    v6_tower_session_init(&session,10,6,0,1);
    session.save_x=world.save.x;session.save_y=world.save.y;
    session.save_gravity=world.save.gravity;session.save_dir=world.save.dir;
    if(!v6_tower_route_load(&route,world.save.room_x,world.save.room_y,0))return 20;
#else
    v6_tower_session_init(&session,world.save.x,world.save.y,world.save.gravity,1);
    if(!v6_tower_route_load(&route,world.save.room_x,world.save.room_y,1))return 20;
#endif
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
#ifdef V6_MENU_SCENE_CAPTURE
    /* Menu DMA fixture: retain an actual resident world/camera while physical
       keyboard input exercises menus. Physics remains covered by live routes. */
    if(V6_MENU_SCENE_CAPTURE>=TOWER_ROUTE_COUNT)return 20;
    if(!v6_tower_route_load(&route,tower_route_rooms[V6_MENU_SCENE_CAPTURE].x,
        tower_route_rooms[V6_MENU_SCENE_CAPTURE].y,0))return 20;
    v6_player_init(&session.player,140,V6_MENU_CAMERA_CAPTURE+120,0);
    session.camera.y=session.camera.old_y=V6_MENU_CAMERA_CAPTURE;
#endif
#ifdef V6_NORTH_START
    {
        const V6TowerRouteRoom *r,*saved;V6Checkpoint *c;
        if(V6_NORTH_START<10 || V6_NORTH_START>=TOWER_ROUTE_COUNT)return 20;
        r=&tower_route_rooms[V6_NORTH_START];saved=r;
#ifdef V6_SOLITUDE_SEEN
        campaign_menu.story_flags=1;
#endif
        /* A checkpoint-free room retains its actual predecessor's save. */
        if(V6_NORTH_START==17)saved=&tower_route_rooms[16];
        if(V6_NORTH_START==19 || V6_NORTH_START==20)saved=&tower_route_rooms[18];
        if(!saved->count)return 20;
        c=saved->checkpoints;
        world.save=(V6CheckpointSave){c->x-4,c->y-(c->tile==20?2:7),c->tile==20,1,saved->x,saved->y,c->id};
        /* Live room/DF1 fixture starts after the rescued crew has returned. */
#ifdef V6_NORTH_FOLLOWER
        station_story.companion=7;rescue_vm.following=1;
#else
        station_story.companion=0;rescue_vm.following=0;
#endif
        v6_tower_session_init(&session,world.save.x,world.save.y,world.save.gravity,1);
        if(!v6_tower_route_load(&route,r->x,r->y,V6_NORTH_START!=17 && V6_NORTH_START!=19 && V6_NORTH_START!=20))return 20;
        if(V6_NORTH_START==20){v6_player_init(&session.player,290,110,0);session.motion.pending_y=110;}
        if(V6_NORTH_START==19){v6_player_init(&session.player,290,110,1);session.motion.pending_y=110;}
        if(V6_NORTH_START==17){v6_player_init(&session.player,120,80,0);session.motion.pending_y=80;}
#ifdef V6_NORTH_TERMINAL_CONTACT
        v6_player_init(&session.player,248,193,0);session.motion.pending_y=193;
#endif
#ifdef V6_NORTH_CORRIDOR
        v6_player_init(&session.player,(V6_NORTH_START==13 || V6_NORTH_CORRIDOR==2 || V6_NORTH_CORRIDOR==3)?290:8,
            (V6_NORTH_START>=15 || V6_NORTH_CORRIDOR>=2)?97:161,0);
        session.motion.pending_y=session.player.y;
#endif
#ifdef V6_WELCOME_EDGE
        v6_player_init(&session.player,V6_NORTH_START==19?8:290,110,0);session.motion.pending_y=110;
#endif
#ifdef V6_CONUNDRUM_EDGE
        v6_player_init(&session.player,V6_NORTH_START==18?8:290,110,0);session.motion.pending_y=110;
#endif
#ifdef V6_LEAP_SHAFT
        v6_player_init(&session.player,120,
            V6_LEAP_SHAFT==2?(V6_NORTH_START==17?200:32):(V6_NORTH_START==16?200:32),
            V6_LEAP_SHAFT==2?V6_NORTH_START==18:V6_NORTH_START==17);
        session.motion.pending_y=session.player.y;
#endif
#ifdef V6_NORTH_SHAFT
        /* One actual open-shaft crossing, then hold the destination for
         * menu/checkpoint inspection. This is a capture fixture only. */
#ifdef V6_NORTH_SHAFT_REVERSE
        v6_player_init(&session.player,60,190,0);session.motion.pending_y=190;
#else
        v6_player_init(&session.player,60,32,1);session.motion.pending_y=32;
#endif
#endif
    }
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
#if defined(V6_NORTH_START) && V6_NORTH_START==17
    /* Direct Leap fixture represents entry from the saved Traffic checkpoint. */
    if(!tele_note_room(115,103))return 20;
#endif
#if defined(V6_NORTH_START) && (V6_NORTH_START==19 || V6_NORTH_START==20)
    if(!tele_note_room(115,105))return 20;
#endif
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
#ifdef V6_MENU_COMPLETE
    campaign_menu.crew_mask=(uint16_t)(1|(station_story.yellow_rescued?4:0)|(hallway_story.red_rescued?8:0));
#endif
#ifdef V6_VSTITCH_HINT_LOAD
    { V6CheckpointSave loaded;V6HallwayStory story;
      if(ui_load_checked(&loaded,&story)!=V6_SAVE_OK || !ui_apply_load(&loaded,&story))return 20;
      camera=session.camera.y;controller=session.camera;
#ifdef V6_CONUNDRUM_REVISIT
      if(!v6_tower_route_load(&route,114,105,0))return 20;
      v6_player_init(&session.player,290,110,1);session.motion.pending_y=110;
#endif
#ifdef V6_WELCOME_REVISIT
      if(!v6_tower_route_load(&route,113,105,0))return 20;
      v6_player_init(&session.player,290,110,0);session.motion.pending_y=110;
#endif
    }
#endif
    diag.step=0;diag.route_min=0;diag.route_max=5368;
    (void)direction;
#endif
#ifdef V6_NORTH_ROUTE
    if(!v6_terminal_read_start(&north_read_prepared,&v6_station_terminal_program))return 20;
#endif
    __asm volatile("move.l 4.w,%0":"=r"(SysBase));
    if(SysBase->AttnFlags&AFF_68010) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=11;
#endif
        return 20;
    }
#ifdef V6_MAP_INPUT_CAPTURE
    keyboard_resource=(struct Library *)OpenResource((CONST_STRPTR)"ciaa.resource");
    if(!keyboard_resource) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=12;
#endif
        return 20;
    }
    v6_keyboard_init(&keyboard);v6_map_menu_init(&map_menu);
#ifdef V6_MAP_DISPLAY_CAPTURE
    v6_map_transition_init(&map_transition);
#endif
#endif
    GfxBase=(struct GfxBase *)OpenLibrary((CONST_STRPTR)"graphics.library",0);
    if(!GfxBase) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=13;
#endif
        return 20;
    }
    if(!(GfxBase->DisplayFlags&PAL)) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=14;menu_startup_diag.values[5]=GfxBase->DisplayFlags;
#endif
        CloseLibrary((struct Library *)GfxBase);return 20;
    }
#if defined(V6_TOWER_AUDIO) || defined(V6_TOWER_TRAVEL_AUDIO)
    /* This takeover fixture cannot resume another client's write-only audio
     * pointers. Start only with all audio DMA and our audio IRQs idle. */
    if((hw->dmaconr&15) || (hw->intenar&AUDIO_IRQ_MASK)) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=15;menu_startup_diag.values[5]=hw->dmaconr;menu_startup_diag.values[6]=hw->intenar;
#endif
        CloseLibrary((struct Library *)GfxBase);return 20;
    }
#endif
#ifdef V6_MENU_COMPLETE
    menu_startup_diag.values[0]=1;menu_startup_diag.values[1]=AvailMem(MEMF_CHIP|MEMF_LARGEST);
    menu_startup_diag.values[2]=AvailMem(MEMF_FAST|MEMF_LARGEST);menu_startup_diag.values[3]=CHIP_BYTES;
#endif
    chip=AllocMem(CHIP_BYTES,MEMF_CHIP|MEMF_CLEAR);
#ifdef V6_MENU_COMPLETE
    menu_startup_diag.values[0]=chip?2:10;menu_startup_diag.values[4]=(ULONG)chip;
#endif
    if(!chip) {
#ifdef V6_TOWER_UI_SAVE
        static const char message[]="Not enough contiguous Chip RAM for graphics.\n"
            "Use Kickstart 1.3 with 512K Chip + 512K Slow.\n"
            "AROS needs additional memory for this build.\n";
        Write(Output(),(APTR)message,sizeof(message)-1);
#endif
        CloseLibrary((struct Library *)GfxBase);return 20;
    }
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
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
            }
    }
#endif
#ifdef V6_TOWER_BUILDING
    {
        unsigned frame;
#ifndef V6_NORTH_ROUTE
        V6Room collision;
#endif
#ifdef V6_NORTH_ROUTE
        (void)frame;
#endif
        building_dma=(UWORD *)(chip+CHIP_BYTES-BUILDING_DMA_BYTES-AUDIO_DMA_BYTES);

#ifdef V6_NORTH_ROUTE
        north_extra_dma=(UWORD *)(rings[0]+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES+UI_MESSAGE_COUNT*V6_DIALOGUE_BYTES+PICKUP_DMA_BYTES+MAP_BITMAP_DMA_BYTES-3340);
        north_bob_bitmaps=(UBYTE *)(north_extra_dma+784);
        north_bob_source=(UWORD *)(north_bob_bitmaps+1688);
#endif
#ifndef V6_NORTH_ROUTE
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
#ifdef V6_VSTITCH_INPUT_CAPTURE
        collision.tiles=vstitch_tiles;v6_terrain_build(&vstitch_terrain,&collision);
        if(route.index==9)route.room.terrain=&vstitch_terrain;
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
        collision.tiles=deception_tiles;v6_terrain_build(&deception_terrain,&collision);
        collision.tiles=downunder_tiles;v6_terrain_build(&downunder_terrain,&collision);
#endif
#endif
#endif
        if(route.index==6)route.room.terrain=&frown_terrain;
#endif
#ifndef V6_MENU_COMPLETE
        for(frame=1;frame<10;++frame)
            if(!v6_teleporter_draw(energize_prepared[frame],teleporter_masks[0],teleporter_masks[frame],36,68)) {
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
            }
#endif
#endif
#endif /* non-north startup collision caches */
#ifndef V6_NORTH_ROUTE
        for(frame=1;frame<10;++frame)
            if(!v6_teleporter_draw(building_prepared[frame],teleporter_masks[0],teleporter_masks[frame],112,48)) {
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
            }
#endif
    }
#ifdef V6_STATION_COMPANION_CAPTURE
    if(!verify_dma_copy()){free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;}
#endif
#endif
#ifdef V6_TOWER_TELEPORTER_HOLD
    tele_dma=(UWORD *)(chip+CHIP_BYTES-TELE_DMA_BYTES);
#ifdef V6_TELEPORTER_LIVE
    {
        unsigned frame;
        for(frame=1;frame<10;++frame)
            if(!v6_teleporter_draw(tele_prepared[frame],teleporter_masks[0],teleporter_masks[frame],112,48)) {
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
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
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
        tele_dma[6*V6_TELEPORTER_DMA_WORDS]=tele_dma[6*V6_TELEPORTER_DMA_WORDS+1]=0;
    }
#endif
#endif
    if(
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
       !v6_tower_open(&stream,deception_display,sizeof(deception_display)) ||
       !v6_tower_pairs_validate(&stream,deception_pair_offsets,DECEPTION_PAIR_WORDS,DECEPTION_TILE_COUNT,2) ||
       !v6_tower_open(&stream,downunder_display,sizeof(downunder_display)) ||
       !v6_tower_pairs_validate(&stream,downunder_pair_offsets,DOWNUNDER_PAIR_WORDS,DOWNUNDER_TILE_COUNT,2) ||
#endif
#ifdef V6_VSTITCH_INPUT_CAPTURE
       !v6_tower_open(&stream,vstitch_display,sizeof(vstitch_display)) ||
       !v6_tower_pairs_validate(&stream,vstitch_pair_offsets,VSTITCH_PAIR_WORDS,VSTITCH_TILE_COUNT,2) ||
#endif
#ifdef V6_NORTH_ROUTE
#ifndef V6_REGIONAL_CONTENT
       !v6_tower_open(&stream,reflect_display,REFLECT_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,reflect_pair_offsets,REFLECT_PAIR_WORDS,REFLECT_TILE_COUNT,2) ||
       !v6_tower_open(&stream,yesmen_display,YESMEN_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,yesmen_pair_offsets,YESMEN_PAIR_WORDS,YESMEN_TILE_COUNT,2) ||
       !v6_tower_open(&stream,welcome_display,WELCOME_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,welcome_pair_offsets,WELCOME_PAIR_WORDS,WELCOME_TILE_COUNT,2) ||
       !v6_tower_open(&stream,conundrum_display,CONUNDRUM_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,conundrum_pair_offsets,CONUNDRUM_PAIR_WORDS,CONUNDRUM_TILE_COUNT,2) ||
       !v6_tower_open(&stream,solitude_display,SOLITUDE_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,solitude_pair_offsets,SOLITUDE_PAIR_WORDS,SOLITUDE_TILE_COUNT,2) ||
       !v6_tower_open(&stream,leap_display,LEAP_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,leap_pair_offsets,LEAP_PAIR_WORDS,LEAP_TILE_COUNT,2) ||
       !v6_tower_open(&stream,traffic_display,TRAFFIC_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,traffic_pair_offsets,TRAFFIC_PAIR_WORDS,TRAFFIC_TILE_COUNT,2) ||
       !v6_tower_open(&stream,filter_display,FILTER_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,filter_pair_offsets,FILTER_PAIR_WORDS,FILTER_TILE_COUNT,2) ||
       !v6_tower_open(&stream,linear_display,LINEAR_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,linear_pair_offsets,LINEAR_PAIR_WORDS,LINEAR_TILE_COUNT,2) ||
       !v6_tower_open(&stream,security_display,SECURITY_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,security_pair_offsets,SECURITY_PAIR_WORDS,SECURITY_TILE_COUNT,2) ||
       !v6_tower_open(&stream,gantry_display,GANTRY_DISPLAY_BYTES) || !v6_tower_pairs_validate(&stream,gantry_pair_offsets,GANTRY_PAIR_WORDS,GANTRY_TILE_COUNT,2) ||
#endif
#endif
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
#ifdef V6_VSTITCH_INPUT_CAPTURE
           route.index==9?vstitch_display:
#endif
#ifdef V6_TOWER_PRIZE
           route.index==8?prize_display:
#endif
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
#ifdef V6_VSTITCH_INPUT_CAPTURE
           route.index==9?sizeof(vstitch_display):
#endif
#ifdef V6_TOWER_PRIZE
           route.index==8?sizeof(prize_display):
#endif
           route.index==7?sizeof(shenanigan_display):route.index==6?sizeof(frown_display):route.index==5?sizeof(energize_display):sizeof(building_display)) ||
#elif defined(V6_TOWER_ROUNDTRIP)
           sizeof(building_display)) ||
#elif defined(V6_ENERGIZE_CAPTURE)
           sizeof(energize_display)) ||
#else
           sizeof(hallway1_display)) ||
#endif
#endif
#ifdef V6_NORTH_ROUTE
       (route.index>=10 && !v6_tower_open(&stream,route.index==10?reflect_display:route.index==11?yesmen_display:route.index==12?gantry_display:route.index==13?security_display:route.index==14?linear_display:route.index==15?filter_display:route.index==16?traffic_display:route.index==17?leap_display:route.index==18?solitude_display:route.index==19?conundrum_display:welcome_display,
           route.index==10?REFLECT_DISPLAY_BYTES:route.index==11?YESMEN_DISPLAY_BYTES:route.index==12?GANTRY_DISPLAY_BYTES:route.index==13?SECURITY_DISPLAY_BYTES:route.index==14?LINEAR_DISPLAY_BYTES:route.index==15?FILTER_DISPLAY_BYTES:route.index==16?TRAFFIC_DISPLAY_BYTES:route.index==17?LEAP_DISPLAY_BYTES:route.index==18?SOLITUDE_DISPLAY_BYTES:route.index==19?CONUNDRUM_DISPLAY_BYTES:WELCOME_DISPLAY_BYTES)) ||
#endif
#ifdef V6_TOWER_STATION
       !v6_tower_pairs_validate(&stream,FG_OFFSETS,FG_WORDS,FG_COUNT,2) ||
#endif
#ifdef V6_PRIZE_INPUT_CAPTURE
       !route_source() ||
#endif
       !prepare(rings[0],lists[0],0,camera,0)) {
        free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
    }
#ifdef V6_TOWER_AUDIO
    {
        unsigned i;
        cue_chip=chip+CHIP_BYTES-CUE_DMA_BYTES;
#ifdef V6_NORTH_ROUTE
        (void)i;
        if(!v6_sample_unpack_delta(cue_chip,CUE_CREW_BYTES,CUE_CREW_PACKED,sizeof(CUE_CREW_PACKED)) ||
           !v6_sample_unpack_delta(cue_chip+CUE_CREW_BYTES,CUE_CREW1_BYTES,cue_crew1_packed,sizeof(cue_crew1_packed))){
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;}
#else
        for(i=0;i<CUE_CREW_BYTES;++i)cue_chip[i]=CUE_CREW[i];
        for(i=0;i<CUE_CREW1_BYTES;++i)cue_chip[CUE_CREW_BYTES+i]=cue_crew1[i];
#endif
        if(!v6_audio_init(&cue_audio,(ULONG)(cue_chip+CUE_DMA_BYTES-2))) {
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
    }
#endif
#ifdef V6_TOWER_UI_SAVE
    {
        unsigned i;ui_captions=rings[0]+2*LAYER_BYTES+2*LIST_WORDS*2+PLAYER_DMA_BYTES+CAPTION_DMA_BYTES;
        for(i=0;i<UI_MESSAGE_COUNT;++i)if(!v6_dialogue_draw(ui_captions+i*V6_DIALOGUE_BYTES,dialogue_font,&ui_messages[i])) {
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
        ui_fields=250;ui_status=0;
#ifdef V6_NORTH_ROUTE
        /* The complete menu supplies the controls/save guidance. Keep the
           initial world list plain so both actor banks can warm before DMA. */
        ui_fields=0;
#endif
#ifdef V6_TOWER_PICKUP_SCREEN
        pickup_banks=ui_captions+UI_MESSAGE_COUNT*V6_DIALOGUE_BYTES;
#ifdef V6_MAP_INPUT_CAPTURE
        map_captions=pickup_banks+PICKUP_DMA_BYTES;
#ifndef V6_MENU_COMPLETE
        for(i=0;i<6;++i)if(!v6_dialogue_draw(map_captions+i*V6_DIALOGUE_BYTES,dialogue_font,&map_messages[i])) {
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
#endif
#ifdef V6_MAP_DISPLAY_CAPTURE
#ifdef V6_MENU_COMPLETE
        map_bitmap=map_captions;ui_bitmaps=map_bitmap+V6_MAP_BITMAP_BYTES;
        ui_stencil=ui_bitmaps+2*V6_UI_BYTES;ui_footer=ui_stencil+320;ui_receipt=ui_footer+960;ui_note=ui_receipt+3600;
        ui_copy(ui_note,ui_note_mask,320);ui_tabs=ui_note+320;ui_copy(ui_tabs,ui_tab_masks,2560);ui_prompt=ui_tabs+2560;ui_copy(ui_prompt,ui_prompt_mask,320);ui_icon_alpha=ui_prompt+320;ui_copy(ui_icon_alpha,ui_icon_masks,132);
        ui_copy(ui_footer,ui_footer_mask,sizeof(ui_footer_mask));ui_copy(ui_receipt,ui_receipt_mask,sizeof(ui_receipt_mask));
#ifdef V6_MENU_SLIDE
        menu_map_dma=(UWORD *)(ui_icon_alpha+132);
#endif
#else
        map_bitmap=map_captions+6*V6_DIALOGUE_BYTES;
#endif
        ui_copy(&map_bitmap_exploration,&tele_exploration,sizeof(tele_exploration));
        for(i=0;i<240;++i) {
            UBYTE row[200];unsigned p,x;
            if(!v6_map_draw_template_row(row,i,&map_bitmap_exploration,map_template_rle,sizeof(map_template_rle),map_template_offsets,map_fog_bits)) {
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
            }
            for(p=0;p<5;++p)for(x=0;x<40;++x)map_bitmap[p*V6_MAP_PLANE_BYTES+i*40+x]=row[p*40+x];
        }
        map_bitmap_rows=240;map_display_diag.values[0]=240;
#if defined(V6_SAVE_DISPLAY_CAPTURE) && !defined(V6_MENU_COMPLETE)
        save_bitmap=map_bitmap+V6_MAP_BITMAP_BYTES;
        if(!v6_save_page_unpack(save_bitmap,save_prompt_rle,sizeof(save_prompt_rle)) ||
           !v6_save_page_unpack(save_bitmap+V6_SAVE_BITMAP_BYTES,save_failure_rle,sizeof(save_failure_rle))) {
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
#endif
#endif
#endif
        pickup_zero=pickup_banks+2*V6_PICKUP_BANK_BYTES;
        for(i=0;i<V6_PICKUP_PLANE_BYTES;++i)((volatile UBYTE *)pickup_zero)[i]=0;
        v6_pickup_draw_init(&pickup_draw);v6_pickup_fade_init(&pickup_fade);pickup_fade_shown=0;v6_pickup_draw_count(&pickup_draw,1);
        pickup_bar_room[0]=pickup_bar_room[1]=0xffffffffUL;
        for(i=0;i<V6_PICKUP_HEIGHT;++i) {
            if(!v6_pickup_text_row(&pickup_draw,i,(UBYTE *)pickup_mask+i*40,
                (UBYTE *)pickup_ink+i*40,dialogue_font,pickup_border)) {
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
            }
        }
        v6_trinket_screen_init(&pickup_screen);
#ifdef V6_VSTITCH_HINT_CAPTURE
        for(i=0;i<V6_HINT_HEIGHT;++i)if(!v6_vstitch_hint_row(i,(UBYTE *)vstitch_mask+i*40,
            (UBYTE *)vstitch_ink+i*40,dialogue_font,pickup_border)) {
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
        /* Fixed room art: compose the first bank before takeover and the
         * second during normal boot warming, before gameplay measurements. */
        vstitch_prepare_bitmap(rings[0],0,camera);ui_fields=0;
#endif
#endif
    }
#endif
#ifdef V6_TOWER_TRAVEL_AUDIO
    {
        unsigned i;travel_audio_chip=chip+CHIP_BYTES-AUDIO_DMA_BYTES;
#ifdef V6_NORTH_ROUTE
        if(!v6_sample_unpack_delta(travel_audio_chip,TELEPORTER_FLASH_BYTES,teleporter_flash_packed,sizeof(teleporter_flash_packed)) ||
           !v6_sample_unpack_delta(travel_audio_chip+TELEPORTER_FLASH_BYTES,TELEPORTER_TELEPORT_BYTES,teleporter_teleport_packed,sizeof(teleporter_teleport_packed))){
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;}
#else
        for(i=0;i<TELEPORTER_FLASH_BYTES;++i)travel_audio_chip[i]=teleporter_flash[i];
        for(i=0;i<TELEPORTER_TELEPORT_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+i]=teleporter_teleport[i];
#endif
#ifdef V6_TOWER_COEXIST_AUDIO
        coexist_sample=travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES;
        for(i=0;i<64;++i)coexist_sample[i]=(UBYTE)(i<32?(int)i*6-96:288-(int)i*6);
#endif
#ifdef V6_TOWER_PRIZE
#ifdef V6_NORTH_ROUTE
        {UBYTE *dest=travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES;
            if(!v6_sample_unpack_delta(dest,PRIZE_VANISH_BYTES,prize_vanish_packed,sizeof(prize_vanish_packed)) ||
               !v6_sample_unpack_delta(dest+PRIZE_VANISH_BYTES,PRIZE_TRINKET_BYTES,prize_trinket_packed,sizeof(prize_trinket_packed))){
                free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;}}
#else
        for(i=0;i<PRIZE_VANISH_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+i]=prize_vanish[i];
        for(i=0;i<PRIZE_TRINKET_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_VANISH_BYTES+i]=prize_trinket[i];
#endif
#endif
#ifdef V6_NORTH_ROUTE
        for(i=0;i<TERMINAL_TOUCH_BYTES;++i)travel_audio_chip[TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_AUDIO_BYTES+i]=terminal_touch[i];
#endif
        for(i=0;i<4;++i)if(!v6_paula_init(&travel_voices[i],i,(ULONG)(travel_audio_chip+TRAVEL_AUDIO_BYTES-2))) {
            free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
        }
    }
#endif
#ifdef V6_MENU_COMPLETE
    menu_startup_diag.values[0]=3;
#endif
    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
    OwnBlitter();WaitBlit();Forbid();Disable();
#if defined(V6_TOWER_AUDIO) || defined(V6_TOWER_TRAVEL_AUDIO)
    /* Recheck while scheduling and interrupts are stopped: allocation and
     * display preparation ran with the OS enabled after the early check. */
    if((hw->dmaconr&15) || (hw->intenar&AUDIO_IRQ_MASK)) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=15;menu_startup_diag.values[5]=hw->dmaconr;menu_startup_diag.values[6]=hw->intenar;
#endif
        Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();
        free_chip(chip);CloseLibrary((struct Library *)GfxBase);return 20;
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
#ifdef V6_REGIONAL_CONTENT
    region_runtime.active=1;region_runtime.dma=&dma;region_runtime.ints=&ints;region_runtime.adk=&adk;
    region_runtime.old_irq=&old_irq;region_runtime.view=&view;region_runtime.lists=lists;region_runtime.back=&back;
    region_runtime.start=&start;region_runtime.previous=&previous;region_runtime.logic_frame=&logic_frame;
#ifdef V6_REGION_REPLAY
    ui_copy(&region_replay_origin,&world.save,sizeof(world.save));
#endif
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
#ifdef V6_REGION_REPLAY
        if(!region_replay()){diag.error=24;break;}
#endif
#ifdef V6_MAP_INPUT_CAPTURE
        keyboard_poll();
#endif
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
#ifdef V6_MAP_INPUT_CAPTURE
            if(map_menu.open && map_menu.save_pending)action=V6_SAVE_ACTION_SAVE;
            else if(map_menu.open
#ifdef V6_MAP_DISPLAY_CAPTURE
                    || map_transition.active
#endif
                   )action=V6_SAVE_ACTION_NONE;
#endif
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
#ifdef V6_MENU_COMPLETE
                    if(action==V6_SAVE_ACTION_SAVE && !menu_candidate_pending && !menu_snapshot(&campaign_menu.clock)){diag.error=21;break;}
#endif
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
#ifdef V6_MAP_INPUT_CAPTURE
                    SetICR(keyboard_resource,0);
#endif
                    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=3;ui_os_paused=1;
#ifdef V6_REGIONAL_CONTENT
                    region_runtime.active=0;
#endif
                    ++ui_diag.values[5];
#ifdef V6_SAVE_DISPLAY_CAPTURE
                    struct Process *save_process=(struct Process *)FindTask(0);
                    APTR save_window=save_process->pr_WindowPtr;
                    save_process->pr_WindowPtr=(APTR)-1;
#endif
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
                    int save_flushed=v6_campaign_dos_flush("DF1:");
#ifdef V6_SAVE_DISPLAY_CAPTURE
                    save_process->pr_WindowPtr=save_window;
#endif
                    if(!save_flushed) {
                        ui_diag.values[8]=V6_SAVE_IO;diag.error=12;diag.status=2;break;
                    }
                    if(result){++ui_diag.values[3];ui_status=3;}else{++ui_diag.values[action];ui_status=action;}
#ifdef V6_NORTH_ROUTE
                    /* The full Save page already presents this receipt.
                     * Avoid a second gameplay caption after it closes. */
                    ui_fields=map_menu.open?0:200;
#else
                    ui_fields=200;
#endif
                    camera=session.camera.y;ui_copy(&controller,&session.camera,sizeof(controller));
#ifdef V6_MAP_INPUT_CAPTURE
                    v6_keyboard_init(&keyboard);
#endif
                    /* Refill both banks while the OS owns the display. No DOS
                     * time is added to the private VBlank clock or accumulator. */
                    { unsigned i;
#ifdef V6_SAVE_DISPLAY_CAPTURE
                        unsigned resume_menu=map_menu.open,resume_transition=map_transition.active;
                        /* Menu early returns cannot refill invalidated game rings. */
                        map_menu.open=map_transition.active=0;
#endif
                        for(i=0;i<2;++i) {
                            v6_tower_draw_reset(&draw[i]);v6_tower_draw_reset(&background_draw[i]);
                            prepared_camera[i]=camera;
                            if(!prepare(rings[i],lists[i],i,camera,0))diag.error=12;
                        }
#ifdef V6_SAVE_DISPLAY_CAPTURE
#ifdef V6_MENU_SLIDE
                        if(!menu_capture_game(lists[0]))diag.error=22;
#endif
                        map_menu.open=resume_menu;map_transition.active=resume_transition;
                        if(resume_menu || resume_transition)for(i=0;i<2;++i)
                            if(!prepare(rings[i],lists[i],i,camera,0))diag.error=12;
#endif
                    }
                    route_loading=0;back=1;
                    view=GfxBase->ActiView;LoadView(0);WaitTOF();WaitTOF();
                    OwnBlitter();WaitBlit();Forbid();Disable();
                    if((hw->dmaconr&15) || (hw->intenar&AUDIO_IRQ_MASK)) {
#ifdef V6_MENU_COMPLETE
        menu_startup_diag.values[0]=15;menu_startup_diag.values[5]=hw->dmaconr;menu_startup_diag.values[6]=hw->intenar;
#endif
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
#ifdef V6_REGIONAL_CONTENT
                    region_runtime.active=1;
#endif
                }
#ifdef V6_MENU_COMPLETE
                if(action==V6_SAVE_ACTION_SAVE) {
                    if(!result)v6_save_summary_publish(&campaign_menu.last,&menu_candidate,1);
                    menu_candidate_pending=0;ui_ready=ui_pending=ui_present_pending=0;
                }
#endif
                ui_diag.values[8]=result;ui_diag.values[9]=before_hash;ui_diag.values[10]=ui_game_hash();
#ifdef V6_MAP_INPUT_CAPTURE
                if(map_menu.save_pending) {
                    v6_map_menu_save_result(&map_menu,result==0);
                    ++map_diag.values[5];map_diag.values[6]=result;
                }
#endif
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
#ifdef V6_MENU_COMPLETE
                menu_action_clock=campaign_menu.clock;
                if(!v6_save_clock_tick(&campaign_menu.clock,0))diag.error=21;
#endif
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
#ifdef V6_MAP_INPUT_CAPTURE
                {
                    unsigned buttons=v6_keyboard_map_buttons(&keyboard),was_open=map_menu.open,event;
#ifdef V6_WELCOME_EARLY_MENU
                    /* Fixture: open at the first live hint, independent of DF0 seek time. */
                    if(conundrum_trigger.visible && conundrum_trigger.timer==60 &&
                       !map_menu.open && !map_transition.active)buttons|=V6_MAP_ENTER;
#endif
#ifdef V6_MAP_DISPLAY_CAPTURE
                    unsigned was_active=map_transition.active;
#endif
                    UWORD joy=hw->joy1dat;
                    int fire=(*(volatile UBYTE *)0xbfe001&0x80)==0;
                    if(joy&0x0200)buttons|=V6_MAP_LEFT;
                    if(joy&2)buttons|=V6_MAP_RIGHT;
                    if(fire)buttons|=V6_MAP_ACTION;
                    if(!(buttons&V6_MAP_ACTION))map_action_held=0;
#ifdef V6_NORTH_ROUTE
                    {unsigned pressed=(buttons&V6_MAP_ENTER) && !north_read_enter;
                        unsigned action=(buttons&V6_MAP_ACTION)!=0,old_active=north_reader.active,old_cues=north_reader.cues;
                        north_read_enter=(buttons&V6_MAP_ENTER)!=0;north_read_block_action=north_reader.waiting;
                        if(route.index==14 && !map_transition.active && !map_menu.open){
                            if(pressed){V6ActivitySignals signals={1,1,session.death_timer!=-1,session.life_timer,
                                north_reader.active || north_read_pending,0};
                            V6ActivityResult result=v6_activity_input(north_actors.blocks,north_actors.block_count,
                                north_activity_index,&session.player,&signals);
                            if(result.consumed)map_menu.mapheld=1;
                            if(result.action==V6_INTERACT_ACTIVITY){north_read_pending=1;map_menu.mapheld=1;}}
                            if(north_read_pending && north_layer_stage==2){north_read_pending=0;
                                north_copy_words((UWORD *)&north_reader,(const UWORD *)&north_read_prepared,sizeof(north_reader)/2);++north_read_diag.values[0];}
                            v6_terminal_read_tick(&north_reader,&(V6TerminalReadSignals){(int)north_read_bars,(int)(action && !north_read_fire)});
                            if(north_reader.cues!=old_cues){north_terminal_cue|=2;++north_read_diag.values[2];}
                            if(old_active && !north_reader.active){++north_read_diag.values[1];north_read_diag.values[12]=north_read_diag.values[13]=0;}
                            if(north_reader.bars){north_read_bars+=25;if(north_read_bars>361)north_read_bars=361;}
                            else north_read_bars=north_read_bars<25?0:north_read_bars-25;
                            v6_terminal_read_animate(&north_reader);
                            if(north_reader.active || north_read_pending){if(buttons&V6_MAP_ENTER)map_menu.mapheld=1;}
                        }
                        north_read_fire=action;
                        if(route.index==14){north_read_diag.values[3]=north_actors.blocks[0].w;north_read_diag.values[4]=north_actors.blocks[0].h;
                            north_read_diag.values[16]=north_reader.control;north_read_diag.values[17]=north_actors.enemies[0].x;
                            north_read_diag.values[18]=north_actors.enemies[1].x;north_read_diag.values[19]=north_read_copied;}

                    }
#endif
                    event=v6_map_menu_tick(&map_menu,buttons,
                        !route_loading && session.death_timer==-1 && !pickup_screen.state &&
                        !tele_menu.open && !departure.state && !arrival.state && !rescue_vm.active &&
                        !cue_audio.state && !travel_audio_busy()
#ifdef V6_NORTH_ROUTE
                        && !north_reader.active && !north_read_pending
#endif
                        ,
#ifdef V6_MAP_DISPLAY_CAPTURE
                        v6_map_transition_input_locked(&map_transition),
#else
                        0,
#endif
                        0,0);
                    if(event==V6_MAP_OPENED) {
#ifdef V6_NORTH_ROUTE
                        north_layer_stage=north_layer_row=north_read_copied=0;north_layer_bars[0]=north_layer_bars[1]=0;

#endif
#ifdef V6_MENU_SLIDE
                        if(!menu_capture_game(lists[back^1])){diag.error=22;break;}
#endif
#ifdef V6_MENU_COMPLETE
                        ui_ready=ui_pending=ui_present_pending=0;
#endif
                        ++map_diag.values[2];map_pause_hash=ui_game_hash();ui_fields=0;
                        map_diag.values[9]=diag.logic_ticks;
#ifdef V6_MAP_DISPLAY_CAPTURE
                        map_cursor_state=map_cursor_delay=0;
                        v6_map_transition_open(&map_transition);
#endif
                    }
#ifdef V6_MENU_COMPLETE
                    if(event==V6_MAP_SAVE) {
                        if(!menu_snapshot(&menu_action_clock))diag.error=21;
                        else menu_candidate_pending=1;
                    }
#endif
                    if(event==V6_MAP_CHANGED)++map_diag.values[3];
                    if(event==V6_MAP_CLOSED) {
                        ++map_diag.values[4];map_diag.values[10]=diag.logic_ticks;
                        map_menu.mapheld=1; /* Closing transition's input latch. */
#ifdef V6_MAP_DISPLAY_CAPTURE
                        v6_map_transition_close(&map_transition);
#endif
                    }
                    if(was_open || map_menu.open
#ifdef V6_MAP_DISPLAY_CAPTURE
                       || was_active || map_transition.active
#endif
                      ) {
#ifdef V6_MAP_DISPLAY_CAPTURE
#ifdef V6_MENU_COMPLETE
                        if(!--menu_crew_delay){menu_crew_delay=8;menu_crew_frame^=1;}
#endif
                        v6_map_cursor_tick(&map_cursor_state,&map_cursor_delay);
                        {
                            unsigned moving=v6_map_transition_input_locked(&map_transition);
                            unsigned closing=map_transition.closing;
                            unsigned done=v6_map_transition_tick(&map_transition);
                            if(done)map_menu.mapheld=1;
                            if((moving || event) && map_transition_diag.count<MAP_CAPTURE_ROWS(64)) {
                                volatile ULONG *r=map_transition_diag.records[map_transition_diag.count++];
                                r[0]=diag.logic_ticks;r[1]=map_transition.previous;r[2]=map_transition.offset;
                                r[3]=closing;r[4]=map_transition.active;r[5]=buttons;r[6]=done;
                            }
                        }
#endif
                        if(buttons&V6_MAP_ACTION)map_action_held=1;
                        ++map_diag.values[7];
                        if(ui_game_hash()!=map_pause_hash) {++map_diag.values[8];diag.error=21;}
                        if(map_diag.count<MAP_CAPTURE_ROWS(128) && (event || buttons!=map_previous_buttons || !(map_diag.values[7]&15))) {
                            volatile ULONG *r=map_diag.records[map_diag.count++];
                            r[0]=diag.logic_ticks;r[1]=buttons;r[2]=event;r[3]=map_menu.open;
                            r[4]=map_menu.page;r[5]=map_menu.saved;r[6]=map_menu.failed;r[7]=session.player.flips;
                        }
                        map_diag.values[11]=session.player.flips;
                        map_previous_buttons=buttons;
                        continue; /* Consume UI timestep without advancing the game. */
                    }
                }
#endif
#ifdef V6_MAP_DIRTY_CAPTURE
                /* Fixture-only exploration of the adjacent resident Prize
                 * room: stress hidden-bank refresh without teleporting the
                 * player or changing the source physics/hint replay. */
                if(diag.logic_ticks==100 && !v6_exploration_visit(&tele_exploration,111,107))diag.error=21;
#endif
#ifdef V6_NORTH_ROUTE
                if(route.index==19){
                    conundrum_previous_level=conundrum_trigger.level;
                    v6_conundrum_tick(&conundrum_trigger);
                    if(v6_conundrum_dispatch(&conundrum_trigger,&campaign_menu.story_flags)&2)conundrum_previous_level=5;
                }
#endif
#ifdef V6_MENU_SCENE_CAPTURE
                continue;
#endif
#ifdef V6_WELCOME_EDGE
                if(route.index==19)conundrum_diag.visible=conundrum_trigger.visible;
                if(route.index!=(unsigned)V6_NORTH_START && conundrum_edge_settled>=4)continue;
#elif defined(V6_CONUNDRUM_EDGE)
                if(route.index!=(unsigned)V6_NORTH_START && conundrum_edge_settled)continue;
#endif
#ifdef V6_WELCOME_DEATH
                if(diag.logic_ticks==8 && route.index==20)v6_tower_session_die(&session);
                if(route.index==18)continue;
#endif
#ifdef V6_CONUNDRUM_DEATH
                if(diag.logic_ticks==8 && route.index==19)v6_tower_session_die(&session);
                if(route.index==18)continue;
#endif
#ifdef V6_LEAP_HOLD
                if(route.index==17 && diag.logic_ticks)continue;
#endif
#ifdef V6_LEAP_DEATH
                if(diag.logic_ticks==8 && route.index==17)v6_tower_session_die(&session);
                if(route.index==16)continue;
#endif
#ifdef V6_LEAP_SHAFT
                if(route.index!=(unsigned)V6_NORTH_START)continue;
#endif
#ifdef V6_NORTH_CORRIDOR
                if(route.index!=(unsigned)V6_NORTH_START)continue;
#endif
#ifdef V6_NORTH_SHAFT
#ifdef V6_NORTH_SHAFT_REVERSE
                if(route.index==V6_NORTH_START-1)continue;
#else
                if(route.index==V6_NORTH_START+1)continue;
#endif
#endif
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
#ifdef V6_NORTH_ROUTE
                if(route.index>=10){unsigned n;for(n=0;n<north_actors.enemy_count;++n)v6_return_enemy_animation_tick(&north_animation[n],0);}
#endif
#ifdef V6_PRIZE_INPUT_CAPTURE
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
                unsigned n;
                input=v6_prize_return_replay(diag.logic_ticks);
                if(!pickup_screen.state) {
                    west_player_frame=v6_collision_frame(&west_player_animation,&session.player,
                        session.player.ground,session.player.roof,session.death_timer);
                    if(route.index==10 || route.index==11) {
                        for(n=0;n<west_actors.enemy_count;++n)
                            v6_return_enemy_animation_tick(&west_enemy_animation[n],0);
                        if(route.index==10) {
                            if(!west_tread_delay){west_tread_phase=(west_tread_phase+3)&3;west_tread_delay=3;}
                            --west_tread_delay;
                        }
                    }
                }
#elif defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE)
                input=v6_prize_collection_replay(diag.logic_ticks);
#elif defined(V6_VSTITCH_HINT_CAPTURE)
                vstitch_previous_level=vstitch_hint.level;
                v6_vstitch_hint_tick(&vstitch_hint);
                if(v6_vstitch_trigger_dispatch(&vstitch_hint,&vstitch_seen))vstitch_previous_level=5;
                input=diag.logic_ticks<4?V6_LEFT:diag.logic_ticks<8?V6_RIGHT:0;
#ifdef V6_MAP_INPUT_CAPTURE
                /* Retain the eight-tick source fixture approach, then expose
                 * ordinary physical controls for gameplay/dismissal checks. */
                if(diag.logic_ticks>=8) {
                    unsigned keys=v6_keyboard_map_buttons(&keyboard);UWORD joy=hw->joy1dat;
                    if((keys&V6_MAP_LEFT)||(joy&0x0200))input|=V6_LEFT;
                    if((keys&V6_MAP_RIGHT)||(joy&2))input|=V6_RIGHT;
                    if((keys&V6_MAP_ACTION)||!(*(volatile UBYTE *)0xbfe001&0x80))input|=V6_FLIP;
                }
#endif
#elif defined(V6_VSTITCH_INPUT_CAPTURE)
                input=v6_prize_checkpoint_replay(diag.logic_ticks);
#else
                input=v6_prize_input_replay(diag.logic_ticks);
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
#ifdef V6_MAP_INPUT_CAPTURE
                if(map_action_held)input&=~V6_FLIP;
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
#if defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE) || defined(V6_PRIZE_RETURN_INPUT_CAPTURE)
                    /* Ordinary released fire, then one fresh press after the jingle. */
                    action=pickup_pause_ticks==94;
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
#ifdef V6_NORTH_ROUTE
                if(route.index==11 || route.index==14 || route.index==16)v6_station_companion_step_memo(&companion,&session.player,&route.room,session.death_timer,
                    route.rooms[route.index].x,route.rooms[route.index].y,north_companion_rest,3);
                else
#endif
                v6_station_companion_step(&companion,&session.player,&route.room,session.death_timer,route.rooms[route.index].x,route.rooms[route.index].y);
#else
                v6_companion_step(&companion,&session.player,&route.room,session.death_timer);
#endif
                rescue_animate();
#ifdef V6_NORTH_ROUTE
                if(route.index==14 && north_reader.active){
                    if(!north_reader.control)input|=V6_NO_CONTROL;
                    if(north_read_block_action){session.player.held=(input&V6_FLIP)!=0;session.player.buffer=0;}
                }
#endif
#ifdef V6_NORTH_ROUTE
                if(!rescue_vm.active && v6_firststeps_dispatch(&firststeps_trigger,campaign_menu.story_flags&1)){
                    unsigned following=rescue_vm.following;
                    campaign_menu.story_flags|=1;
                    if(!v6_rescue_start(&rescue_vm,&v6_firststeps_program,&v6_firststeps_program,0))diag.error=9;
                    rescue_vm.following=following;cue_consumed=0;rescue_flips_applied=0;
                }
#endif
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
                    unsigned events=departure.events|arrival.events,cue,slot,limit=2;
#ifdef V6_TOWER_PRIZE
                    unsigned pending=prize_audio_pending;prize_audio_pending=0;
                    limit=pending?6:2;
#endif
                    if(!events
#ifdef V6_TOWER_PRIZE
                       && !pending
#endif
                    )limit=0;
#ifdef V6_NORTH_ROUTE
                    unsigned terminal_pending=north_terminal_cue;north_terminal_cue=0;
                    if(terminal_pending)limit=8;
#endif
                    for(slot=0;slot<limit;++slot) {
                        cue=slot;
#ifdef V6_TOWER_PRIZE
                        if(slot>=2)cue=v6_prize_audio_cue(pending,slot-2);
#endif
#ifdef V6_NORTH_ROUTE
                        if(slot==6)cue=(terminal_pending&1)?5:4;
                        if(slot==7)cue=(terminal_pending&2)?6:4;
#endif
                        if(slot<2 ? !(events&(1U<<slot)) : cue==4)continue;
                        unsigned i,busy=0,age[4];int chosen;V6AudioSample sample;V6AudioPlan plan;
                        for(i=0;i<4;++i) {
                            if(travel_voices[i].audio.state!=V6_AUDIO_IDLE)busy|=1U<<i;
                            age[i]=frames-travel_started[i];
                        }
                        chosen=v6_audio_choose(V6_TRAVEL_SFX_MASK,busy,travel_priority,age,cue+1);
                        if(chosen<0){++travel_audio_dropped;if(chosen==-2)diag.error=15;
#ifdef V6_TOWER_PRIZE
                            if(cue>=2 && cue<=3)++prize_audio_diag.values[2];
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
#ifdef V6_NORTH_ROUTE
                            if(cue>=5){sample.address=(ULONG)(travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_AUDIO_BYTES);
                                if(cue==6)sample.address=(ULONG)pickup_banks;
                                sample.bytes=cue==6?TERMINAL_READ_BYTES:TERMINAL_TOUCH_BYTES;sample.period=TERMINAL_PERIOD;}
#endif
                            if(!v6_paula_request(&travel_voices[i],&sample,&plan)) {
                                diag.error=15;
#ifdef V6_TOWER_PRIZE
                                if(cue>=2 && cue<=3)++prize_audio_diag.values[4];
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
                                if(cue>=2 && cue<=3) {
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
#ifdef V6_NORTH_ROUTE
                    if(shake_timer || shake_plan.x || shake_plan.y) {
#endif
                    v6_screen_shake_pre(&shake,shake_timer,samples);
                    v6_screen_shake_plan(&shake,shake_timer,session.noflashing,0,&shake_plan);
#ifdef V6_NORTH_ROUTE
                    }
#endif
#ifdef V6_MENU_SHAKE_REFERENCE
                    v6_screen_shake_plan(&shake,0,session.noflashing,0,&shake_plan);
#endif
                    if(session.noflashing)arrival_flash=0;
                    if(AUX_TRACE_ENABLED && (shake_trace.count<128)) {
                        LONG *record=shake_trace.records[shake_trace.count++];
                        record[0]=shake_timer;record[1]=shake_plan.x;record[2]=shake_plan.y;
                    }
#ifdef V6_TOWER_MENU_TRAVEL
                    if(AUX_TRACE_ENABLED && (menu_travel_active && menu_shake_trace.count<64)) {
                        volatile LONG *record=menu_shake_trace.records[menu_shake_trace.count++];
                        record[0]=shake_timer;record[1]=shake_plan.x;record[2]=shake_plan.y;
                    }
#endif
                }
#endif
#ifdef V6_TOWER_MENU_TRAVEL
                if(AUX_TRACE_ENABLED && (menu_travel_active && menu_travel_trace.count<128)) {
                    volatile LONG *d=menu_travel_trace.records[menu_travel_trace.count];
                    d[0]=departure.state;d[1]=departure.delay;d[2]=departure.control;d[3]=departure.flash;
                    d[4]=departure.shake;d[5]=departure.events;d[6]=departure.travel;d[7]=travel_leg;
                }
#endif
                if(AUX_TRACE_ENABLED && (departure_trace.count<128)) {
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
                if(AUX_TRACE_ENABLED && (arrival_trace.count<128)) {
                    volatile ULONG *a=arrival_trace.records[arrival_trace.count++];
                    a[0]=arrival.state;a[1]=arrival.delay;a[2]=arrival.control;
                    a[3]=arrival.flash;a[4]=arrival.shake;a[5]=arrival.events;
                    a[6]=session.invisible;a[7]=session.player.vx;a[8]=session.player.vy;
                    a[9]=session.player.ay;a[10]=session.player.old_x;a[11]=session.player.old_y;
                    a[12]=session.player.dir;a[13]=session.death_timer;
                }
#ifdef V6_TOWER_MENU_TRAVEL
                if(AUX_TRACE_ENABLED && (menu_travel_active && menu_travel_trace.count<128)) {
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
#if defined(V6_CONUNDRUM_EDGE) || defined(V6_WELCOME_EDGE)
                if(route.index!=(unsigned)V6_NORTH_START && route.index==index)++conundrum_edge_settled;
#endif
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
                    if(AUX_TRACE_ENABLED && (colour_trace.count<128)) {
                        volatile ULONG *c=colour_trace.records[colour_trace.count++];
                        c[0]=teleporter_tint;c[1]=player_tint;
                    }
                }
#endif
#ifdef V6_TOWER_MENU_TRAVEL
                if(AUX_TRACE_ENABLED && (menu_travel_active && menu_travel_trace.count<128)) {
                    volatile LONG *r=menu_travel_trace.records[menu_travel_trace.count]+22;
                    V6Teleporter *t=route.rooms[route.index].teleporter;
                    r[0]=route.index;r[1]=session.player.x;r[2]=session.player.y;r[3]=t->tile;r[4]=t->state;
                    r[5]=route.tele_events;r[6]=building_animation.frame;r[7]=world.save.x;r[8]=world.save.y;
                    r[9]=world.save.room_x;r[10]=world.save.room_y;r[11]=route.tele_region.active;
                    r[12]=teleporter_tint;r[13]=player_tint;++menu_travel_trace.count;
                    if(arrival.events&V6_ARRIVAL_SAVE)menu_travel_active=0;
                }
#endif
                if(AUX_TRACE_ENABLED && (building_trace.count<128)) {
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
#ifdef V6_NORTH_ROUTE
                if(route.index==19){conundrum_diag.flags=campaign_menu.story_flags;conundrum_diag.active=conundrum_trigger.active;
                conundrum_diag.pending=conundrum_trigger.pending;conundrum_diag.contacts=conundrum_trigger.contacts;
                conundrum_diag.removed=conundrum_trigger.removed;conundrum_diag.visible=conundrum_trigger.visible;
                conundrum_diag.timer=conundrum_trigger.timer;conundrum_diag.level=conundrum_trigger.level;
                conundrum_diag.hints=conundrum_trigger.hints;conundrum_diag.room=route.index;
                conundrum_diag.x=session.player.x;conundrum_diag.y=session.player.y;
                conundrum_diag.gravity=session.player.gravity;conundrum_diag.deaths=session.deaths;}
                firststeps_diag.seen=campaign_menu.story_flags&1;firststeps_diag.active=rescue_vm.active;
                firststeps_diag.pc=rescue_vm.pc;firststeps_diag.waiting=rescue_vm.waiting;firststeps_diag.cues=rescue_vm.cues;
                firststeps_diag.requests=firststeps_trigger.requests;firststeps_diag.error=rescue_vm.error;
                firststeps_diag.caption=north_caption_pending;firststeps_diag.room=route.index;
#endif
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
#if defined(V6_PRIZE_ROUTE_CAPTURE) || defined(V6_PRIZE_INPUT_CAPTURE)
                if(MAP_AUX_TRACE_ENABLED && prize_route_trace.count<PRIZE_INPUT_TICKS) {
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
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
                    d[24]=west_enemy_hits;d[25]=session.player.vx;d[26]=session.player.vy;
                    d[27]=session.motion.pending_y;d[28]=west_actors.platforms[0].y;
                    d[29]=west_actors.enemies[0].x;d[30]=west_actors.enemies[1].x;d[31]=route.error;
#endif
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
#ifdef V6_VSTITCH_HINT_CAPTURE
                if(vstitch_hint_trace.count<VSTITCH_HINT_ROWS) {
                    volatile LONG *h=vstitch_hint_trace.records[vstitch_hint_trace.count++];
                    h[0]=session.player.x;h[1]=session.player.y;h[2]=session.player.gravity;
                    h[3]=session.death_timer;h[4]=world.save.id;h[5]=vstitch_seen;
                    h[6]=vstitch_hint.active;h[7]=vstitch_hint.pending;h[8]=vstitch_hint.visible;
                    h[9]=vstitch_hint.timer;h[10]=vstitch_hint.level;h[11]=vstitch_hint.mode;
                    h[12]=vstitch_hint.contacts;h[13]=vstitch_hint.hints;
                    h[14]=session.player.flips;h[15]=input;
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
#if !defined(V6_PRIZE_COLLECTION_INPUT_CAPTURE) && !defined(V6_PRIZE_RETURN_INPUT_CAPTURE) && !defined(V6_VSTITCH_HINT_CAPTURE)
                if(camera_trace.count<CAMERA_TRACE_TICKS) {
                    volatile int32_t *r=camera_trace.players[camera_trace.count];
                    r[0]=session.player.x;r[1]=session.player.y;r[2]=session.player.vx;r[3]=session.player.vy;
                    r[4]=session.player.gravity;r[5]=session.player.dir;r[6]=session.death_timer;
                    r[7]=session.invisible;r[8]=session.deaths;r[9]=session.respawns;
                    r[10]=session.player.old_x;r[11]=session.player.old_y;
                }
                trace_camera(&session.camera,session.life_timer,session.resume_delay);
#endif
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
#ifdef V6_NORTH_ROUTE
            if(north_terrain_pending){unsigned last=north_terrain_row+2;
                route.room.terrain=0;v6_terrain_build_rows(&north_shared_terrain,&route.room,north_terrain_row,last);
                north_terrain_row=last;
                if(last==32){route.room.terrain=&north_shared_terrain;north_terrain_pending=0;}}
#endif
            drawn=fg_rows+bg_rows;++route_diag.loading_frames;
#ifdef V6_TOWER_BUILDING
            /* Leave room for the six-channel DMA copy on final cold fields. */
            route_budget=(route.rooms[route.index].teleporter || route.index==7 || route.index==8
#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE
                || route.index==10 || route.index==11
#endif
                )?1:2;
#else
            route_budget=2;
#endif
            if(!fg || !bg) { diag.error=8;break; }
#ifdef V6_NORTH_ROUTE
            route_budget=1;
#endif
            /* A cold field finishes tile work; compose its sprite/Copper
             * bank on the following field instead of stacking both jobs. */
            publish=fg==1 && bg==1
#ifdef V6_NORTH_ROUTE
                && !drawn
#endif
                ;
#ifdef V6_NORTH_ROUTE
            if(north_terrain_pending)publish=0;
            if(publish && north_pcm_pending){int state;
                if(north_pcm_pending==1){UBYTE *dest=travel_audio_chip+TELEPORTER_FLASH_BYTES+TELEPORTER_TELEPORT_BYTES+COEXIST_BYTES+PRIZE_VANISH_BYTES;
                    if(travel_audio_busy() || cue_audio.state){publish=0;}
                    else {
                        if(!v6_sample_job_init(&north_pcm_job,dest,north_caption_mode==1?FIRSTSTEPS_CRY_BYTES:PRIZE_TRINKET_BYTES,
                            north_caption_mode==1?firststeps_cry_packed:prize_trinket_packed,
                            north_caption_mode==1?sizeof(firststeps_cry_packed):sizeof(prize_trinket_packed))){diag.error=11;break;}
                        north_pcm_pending=2;
                    }
                }
                if(north_pcm_pending==2){state=v6_sample_job_step(&north_pcm_job,192);if(state<0){diag.error=11;break;}if(state==1)north_pcm_pending=0;}
                publish=0;
            }
            if(publish && north_caption_pending){unsigned job=4-north_caption_pending;
                const V6RescueSpeech *speech=north_caption_mode==1?&v6_firststeps_speeches[job/2]:north_caption_mode==2?&conundrum_speeches[job/2]:&v6_rescue_speeches[job/2];
                if(!v6_dialogue_replace_line(rescue_captions+(job/2)*V6_DIALOGUE_BYTES,dialogue_font,2,job&1,speech->lines[job&1])){diag.error=10;break;}
                --north_caption_pending;publish=0;
            }
            if(publish && north_memo_pending){
                if(companion.visible)v6_companion_rest_prime(north_companion_rest,3,&companion,&route.room);
                north_memo_pending=0;publish=0;
            }
            if(publish){unsigned rows=map_display_diag.values[0];
                /* Finish exploration bands as separate loading jobs, before
                 * a live tutorial or an immediately opened map needs them. */
                if(!map_refresh()){diag.error=21;break;}
                if(map_display_diag.values[0]!=rows)publish=0;
            }
#endif
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
           pickup_frame_trace.count<256) {
            volatile ULONG *r=pickup_frame_trace.records[pickup_frame_trace.count++];
            r[0]=diag.logic_ticks;r[1]=frames;r[2]=logic_work;r[3]=render_work;
            r[4]=pickup_pause_ticks;r[5]=pickup_rows[back];r[6]=pickup_draw.bars;r[7]=frames-previous;
        }
#endif
#ifdef V6_NORTH_ROUTE

#endif
        if(logic_work>profile.max_logic)profile.max_logic=logic_work;
        if(render_work>profile.max_render) profile.max_render=render_work;
        if(work>diag.max_work_lines) {
            profile.peak_logic=logic_work;profile.peak_render=render_work;
            profile.peak_tick=diag.logic_ticks;profile.peak_rows=drawn;
#ifdef V6_MENU_COMPLETE
            profile.peak_ui_row=ui_row;profile.peak_ui_page=map_menu.page;
#endif
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
#ifdef V6_MAP_INPUT_CAPTURE
    SetICR(keyboard_resource,0);
#endif
    Enable();Permit();DisownBlitter();LoadView(view);WaitTOF();WaitTOF();diag.status=2;
#ifdef V6_TOWER_UI_SAVE
    }
#endif
    free_chip(chip);CloseLibrary((struct Library *)GfxBase);return diag.error?20:0;
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
