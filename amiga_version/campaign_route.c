#include "campaign_route.h"
int v6_campaign_route_checkpoint_valid(const V6CheckpointSave *c,
    const V6TowerRouteRoom *rooms,unsigned count)
{
    unsigned i;
    if(!c || !rooms)return 0;
    for(i=0;i<count;++i)if(rooms[i].x==c->room_x && rooms[i].y==c->room_y) {
        if(rooms[i].teleporter && v6_teleporter_checkpoint_valid(rooms[i].teleporter,c))return 1;
        return v6_campaign_checkpoint_valid(c,rooms[i].checkpoints,rooms[i].count);
    }
    return 0;
}
