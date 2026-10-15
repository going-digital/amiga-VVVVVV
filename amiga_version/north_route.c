/* Original entities: Spacestation2.cpp rn(50,39..42), rn(51,39); Ent.cpp rn(12,3/5), rn(13,3).
 * Copyright Terry Cavanagh; see ../LICENSE.md. */
#include "north_route.h"
int v6_north_init(V6NorthRoute *s,V6Room *r,int x,int y,int player_y)
{
    unsigned i;
    if(!s || !r || !((x==112 && y>=103 && y<=106) || (x==113 && y==103)))return 0;
    s->room_y=(unsigned)y;s->enemy_count=s->gate_count=s->platform_count=s->block_count=s->flags=0;
    s->push.pending_y=player_y;s->push.visual_ground=s->push.visual_roof=0;
    if(x==113){s->enemy_count=2;s->block_count=1;
        v6_enemy_init(&s->enemies[0],80,88,3,3,0,0,320,240,0,0,32,16);
        v6_enemy_init(&s->enemies[1],208,128,2,3,0,0,320,240,0,0,32,16);
        s->blocks[0]=(V6Block){248,200,20,16,V6_ACTIVITY,6};
    } else if(y==106){s->platform_count=s->block_count=3;s->flags=V6_PLATFORMS_VERTICAL;
        for(i=0;i<3;++i){int px=135+(int)i*50,py=75+(int)i*35;
            v6_platform_init(&s->platforms[i],px,py,0,3,100,70,320,160);
            s->blocks[i]=(V6Block){px,py,32,8,V6_BLOCK,0};}
    } else if(y==105){static const int xy[5][3]={{122,8,0},{266,8,0},{122,204,1},{194,172,1},{194,40,0}};
        s->enemy_count=5;
        for(i=0;i<5;++i)v6_enemy_init(&s->enemies[i],xy[i][0],xy[i][1],xy[i][2],3,
            0,0,320,240,0,0,20,20);
    } else if(y==103){s->enemy_count=1;
        v6_enemy_init(&s->enemies[0],200,32,0,8,0,0,320,240,0,0,16,16);
    } else {s->gate_count=3;s->platform_count=1;s->block_count=4;s->flags=V6_PLATFORMS_HORIZONTAL;
        for(i=0;i<3;++i){v6_disappearing_init(&s->gates[i]);s->blocks[i]=(V6Block){104+(int)i*32,64,32,8,V6_BLOCK,0};}
        v6_platform_init(&s->platforms[0],56,152,3,3,0,0,320,240);
        s->blocks[3]=(V6Block){56,152,32,8,V6_BLOCK,0};
    }
    r->blocks=s->blocks;r->block_count=s->block_count;return 1;
}
void v6_north_platforms(V6NorthRoute *s,V6Room *r,V6Player *p,int life,int pending_y)
{
    s->push.pending_y=pending_y;
    v6_platform_transport(p,r,s->platforms,s->platform_count,s->blocks,s->block_count,s->flags,life,&s->push);
}
unsigned v6_north_entities(V6NorthRoute *s,V6Room *r,int dying)
{
    unsigned i,events=0;
    for(i=s->enemy_count;i>0;--i)if(!dying)v6_enemy_step(&s->enemies[i-1],r,r->blocks,r->block_count);
    for(i=s->gate_count;i>0;--i)events|=v6_disappearing_update_room(&s->gates[i-1],104+(int)(i-1)*32,64,
        s->blocks,&s->block_count,4,dying,112,104,0);
    r->block_count=s->block_count;return events;
}
unsigned v6_north_contacts(V6NorthRoute *s,V6Player *p)
{
    unsigned i,hits=0;
    for(i=0;i<s->gate_count;++i)v6_disappearing_contact(&s->gates[i],v6_player_overlaps(p,104+(int)i*32,63,32,10));
    v6_platform_disable_overlaps(p,s->platforms,s->platform_count,s->blocks,s->block_count);
    for(i=0;i<s->enemy_count;++i){const V6Enemy *e=&s->enemies[i];
        if(v6_player_overlaps(p,e->x+e->cx,e->y+e->cy,e->w,e->h))hits|=1U<<i;}
    return hits;
}
