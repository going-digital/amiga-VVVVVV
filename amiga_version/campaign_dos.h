#ifndef V6_CAMPAIGN_DOS_H
#define V6_CAMPAIGN_DOS_H
#include "campaign_file.h"
/* Caller opens DOSBase and keeps the OS running for every operation. */
extern const V6CampaignIO v6_campaign_dos;
/* Wait for ACTION_FLUSH on a named filesystem device (for example DF1:).
 * Required before suspending the OS again after file/metadata changes. */
int v6_campaign_dos_flush(const char *device);
#endif
