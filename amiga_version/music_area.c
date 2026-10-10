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

int v6_music_entry_track(int x,int y,int final_mode,int custom_mode,
    int script_running,int flip_mode,int time_trial,int *track)
{
    if(!track || (unsigned)final_mode>1 || (unsigned)custom_mode>1 ||
       (unsigned)script_running>1 || (unsigned)flip_mode>1 || (unsigned)time_trial>1)return 0;
    if(final_mode){*track=(time_trial && x==46 && y==54)?15:-1;return 1;}
    if(custom_mode){*track=-1;return 1;}
    x=x<100?119:x>119?100:x;y=y<100?119:y>119?100:y;
    return v6_music_area_track(x-100,y-100,script_running,flip_mode,time_trial,track);
}
