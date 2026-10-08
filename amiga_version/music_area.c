#include "music_area.h"
#include "music_area_map.h"
int v6_music_area_track(int x,int y,int script_running,int flip_mode,
    int time_trial,int *track)
{
    int value;
    if(!track || x<0 || x>=20 || y<0 || y>=20 ||
       (unsigned)script_running>1 || (unsigned)flip_mode>1 || (unsigned)time_trial>1)return 0;
    value=script_running?-1:v6_music_area_map[x+y*20];
    if(value==-2)value=flip_mode?9:2;
    else if(value==-3)value=time_trial?1:4;
    *track=value;return 1;
}
