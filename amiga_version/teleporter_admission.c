/* Adapted from Map.cpp's normal-world teleporters and Input.cpp exploration
 * filtering. Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "teleporter_admission.h"
static const V6TeleporterDestination source[V6_SOURCE_TELEPORTERS]={
    {100,100},{100,116},{102,104},{102,111},{107,109},{107,115},
    {108,111},{110,105},{111,104},{113,102},{113,108},{114,119},
    {115,100},{117,112},{117,117},{118,101},{118,107}
};
static int index(int x,int y)
{ return x>=100 && x<120 && y>=100 && y<120?(x-100)+(y-100)*20:-1; }
void v6_exploration_init(V6Exploration *e)
{unsigned i;if(e)for(i=0;i<V6_EXPLORED_BYTES;++i)e->rooms[i]=0;}
int v6_exploration_visit(V6Exploration *e,int x,int y)
{int n=index(x,y);if(!e || n<0)return 0;e->rooms[n>>3]|=1u<<(n&7);return 1;}
int v6_exploration_seen(const V6Exploration *e,int x,int y)
{int n=index(x,y);return e && n>=0 && (e->rooms[n>>3]&(1u<<(n&7)))!=0;}
int v6_teleporter_admit(const V6Exploration *e,const V6TeleporterDestination *r,
    unsigned residents,V6TeleporterDestination *out,unsigned capacity,unsigned *count)
{
    unsigned i,j,k,n=0;V6TeleporterDestination selected[V6_SOURCE_TELEPORTERS];
    if(!e || !count || residents>V6_SOURCE_TELEPORTERS || (residents && !r) || (capacity && !out))return 0;
    for(i=0;i<residents;++i) {
        for(j=0;j<i;++j)if(r[i].room_x==r[j].room_x && r[i].room_y==r[j].room_y)return 0;
        for(j=0;j<V6_SOURCE_TELEPORTERS;++j)if(r[i].room_x==source[j].room_x && r[i].room_y==source[j].room_y)break;
        if(j==V6_SOURCE_TELEPORTERS)return 0;
    }
    for(i=0;i<V6_SOURCE_TELEPORTERS;++i)if(v6_exploration_seen(e,source[i].room_x,source[i].room_y))
        for(k=0;k<residents;++k)if(r[k].room_x==source[i].room_x && r[k].room_y==source[i].room_y){selected[n++]=source[i];break;}
    if(n>capacity)return 0;
    for(i=0;i<n;++i)out[i]=selected[i];
    *count=n;return 1;
}
