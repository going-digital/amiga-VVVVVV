#ifndef V6_CAMPAIGN_FILE_H
#define V6_CAMPAIGN_FILE_H
#include "campaign_save.h"
/* OS-safe callers with exclusive ownership of their paths only.
 * Handles are nonzero. exists: 0 absent, 1 present,
 * -1 error. Read/write return byte count or -1; close/rename/remove bool.
 * write_new requires distinct, absent final/temp paths and never replaces an
 * existing save. Temporary cleanup failures retain the file for inspection. */
typedef struct {
    int (*exists)(const char *);
    intptr_t (*open)(const char *,int write);
    int (*read)(intptr_t,void *,unsigned);
    int (*write)(intptr_t,const void *,unsigned);
    int (*close)(intptr_t);
    int (*rename)(const char *,const char *);
    int (*remove)(const char *);
} V6CampaignIO;
enum { V6_SAVE_OK=0,V6_SAVE_INVALID,V6_SAVE_EXISTS,V6_SAVE_IO,V6_SAVE_CORRUPT };
int v6_campaign_read(const V6CampaignIO *,const char *,V6CheckpointSave *,V6HallwayStory *);
int v6_campaign_write_new(const V6CampaignIO *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *);
/* Reserved, pairwise distinct paths with exclusive ownership. recover rolls
 * back a missing final from a valid backup, or accepts a valid final. It then
 * removes owned stale temp/backup files. Corrupt final/backup files are retained
 * and reported, never replaced by an uncommitted temp. Failure leaves outputs
 * unchanged. A replacement I/O error may occur after promotion: call recover
 * before retrying; success does not promise physical power-loss durability. */
int v6_campaign_recover(const V6CampaignIO *,const char *,const char *,const char *,V6CheckpointSave *,V6HallwayStory *);
int v6_campaign_replace(const V6CampaignIO *,const char *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *);
/* Full-state operations share the same transactional path rules. Read/recover
 * accept versions 1 and 2; writes always publish version 2 atomically. Legacy
 * operations reject version 2 and cannot overwrite its exploration map. */
int v6_campaign_state_read(const V6CampaignIO *,const char *,V6CheckpointSave *,V6HallwayStory *,V6Exploration *);
int v6_campaign_state_write_new(const V6CampaignIO *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *,const V6Exploration *);
int v6_campaign_state_recover(const V6CampaignIO *,const char *,const char *,const char *,V6CheckpointSave *,V6HallwayStory *,V6Exploration *);
int v6_campaign_state_replace(const V6CampaignIO *,const char *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *,const V6Exploration *);
/* Progress operations accept V1/V2/V3 and write V3; identical path/fault rules. */
int v6_campaign_progress_read(const V6CampaignIO *,const char *,V6CheckpointSave *,V6HallwayStory *,V6StationStory *,V6Exploration *);
int v6_campaign_progress_write_new(const V6CampaignIO *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *,const V6StationStory *,const V6Exploration *);
int v6_campaign_progress_recover(const V6CampaignIO *,const char *,const char *,const char *,V6CheckpointSave *,V6HallwayStory *,V6StationStory *,V6Exploration *);
int v6_campaign_progress_replace(const V6CampaignIO *,const char *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *,const V6StationStory *,const V6Exploration *);
/* Collection operations read V1..V4 and write V4; identical path/fault rules. */
int v6_campaign_collection_read(const V6CampaignIO *,const char *,V6CheckpointSave *,V6HallwayStory *,V6StationStory *,V6Exploration *,V6Collect *);
int v6_campaign_collection_write_new(const V6CampaignIO *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *,const V6StationStory *,const V6Exploration *,const V6Collect *);
int v6_campaign_collection_recover(const V6CampaignIO *,const char *,const char *,const char *,V6CheckpointSave *,V6HallwayStory *,V6StationStory *,V6Exploration *,V6Collect *);
int v6_campaign_collection_replace(const V6CampaignIO *,const char *,const char *,const char *,const V6CheckpointSave *,const V6HallwayStory *,const V6StationStory *,const V6Exploration *,const V6Collect *);
#endif
