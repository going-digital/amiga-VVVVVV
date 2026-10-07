#ifndef V6_CAMPAIGN_ROUTE_H
#define V6_CAMPAIGN_ROUTE_H
#include "campaign_save.h"
#include "tower_route.h"
/* Select by room identity before checking a source checkpoint or teleporter.
 * Unknown rooms and checksum-valid noncanonical positions are rejected. */
int v6_campaign_route_checkpoint_valid(const V6CheckpointSave *,
    const V6TowerRouteRoom *,unsigned count);
#endif
