#include "blocks.h"
void v6_blocks_disable_at(V6Block *blocks, unsigned count, int x, int y)
{
    unsigned i;
    for(i=0;i<count;++i) if(blocks[i].x==x && blocks[i].y==y)
        blocks[i].w=blocks[i].h=0;
}
int v6_blocks_move(V6Block *blocks, unsigned count, int old_x, int old_y,
                   int x, int y, int w, int h)
{
    unsigned i;
    for(i=0;i<count;++i) if(blocks[i].x==old_x && blocks[i].y==old_y) {
        blocks[i].x=x; blocks[i].y=y; blocks[i].w=w; blocks[i].h=h;
        return 1;
    }
    return 0;
}
int v6_blocks_create_solid(V6Block *blocks,unsigned *count,unsigned capacity,
                           int x,int y,int w,int h)
{
    unsigned i;
    for(i=0;i<*count;++i) if(blocks[i].w==0 && blocks[i].h==0) break;
    if(i==*count) {
        if(i>=capacity) return -1;
        ++*count;
    }
    blocks[i]=(V6Block){x,y,w,h,V6_BLOCK,0};
    return (int)i;
}
