#ifndef V6_CAMPAIGN_MENU_H
#define V6_CAMPAIGN_MENU_H
#include "campaign_file.h"
#include "save_summary.h"
#define V6_CAMPAIGN_MENU_BYTES 144
/* V6 retains the V5 checkpoint/story/exploration/collection prefix through107.
 * Clock108, deaths116, crew120, last-exists121, last-clock122, room130/132,
 * trinkets134, crew136, zero138/139, CRC140. All integers big endian.
 * V7 uses the same size, with story flags at138 (bit0=original flag4).
 * V8 additionally admits bits1/2 for original Conundrum flags2/3.
 * Writers retain V6 while these flags are zero. V1..V6 migrate with flags=0.
 * V1..V5 migrate without inventing elapsed time or a previous receipt. */
typedef struct {
    V6SaveClock clock;
    uint32_t deaths;
    uint16_t crew_mask;
    V6SaveSummary last;
    uint16_t story_flags; /* V7 bit0: firststeps flag4; V8 bits1/2: Conundrum flags2/3. */
} V6CampaignMenu;
typedef struct {
    V6CheckpointSave checkpoint;
    V6HallwayStory red;
    V6StationStory yellow;
    V6Exploration explored;
    V6Collect collected;
    V6CampaignHints hints;
    V6CampaignMenu menu;
} V6MenuRecord;
int v6_campaign_menu_encode(uint8_t *,size_t,const V6MenuRecord *);
int v6_campaign_menu_decode(V6MenuRecord *,const uint8_t *,size_t);
int v6_campaign_menu_read(const V6CampaignIO *,const char *,V6MenuRecord *);
int v6_campaign_menu_recover(const V6CampaignIO *,const char *,const char *,const char *,V6MenuRecord *);
int v6_campaign_menu_replace(const V6CampaignIO *,const char *,const char *,const char *,const V6MenuRecord *);
#endif
