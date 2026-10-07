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
#endif
