/* Adapted from Entity.cpp trinket creation, update and rule-3 collision.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "trinkets.h"
void v6_collect_clear(V6Collect *c)
{
    unsigned i;
    for(i=0;i<V6_COLLECT_BYTES;++i) c->bits[i]=0;
}
int v6_collect_has(const V6Collect *c,int id)
{
    return id>=0 && id<V6_COLLECT_COUNT &&
        (c->bits[(unsigned)id>>3] & (1u<<((unsigned)id&7)))!=0;
}
int v6_collect_import(V6Collect *c,const unsigned char *bytes)
{
    unsigned i;
    if(bytes[V6_COLLECT_BYTES-1]&0xf0) return 0;
    for(i=0;i<V6_COLLECT_BYTES;++i) c->bits[i]=bytes[i];
    return 1;
}
int v6_trinket_init(V6Trinket *t,int x,int y,int id,const V6Collect *c)
{
    if(id<0 || id>=V6_COLLECT_COUNT) return 0;
    t->x=x;t->y=y;t->id=id;t->visible=!v6_collect_has(c,id);t->pending=0;
    return 1;
}
void v6_trinket_collide(V6Trinket *t,const V6Player *p)
{
    if(t->visible && t->y>p->y-14 && t->y<p->y+23 &&
       v6_player_overlaps(p,t->x,t->y,16,16)) t->pending=1;
}
int v6_trinket_update(V6Trinket *t,V6Collect *c)
{
    if(!t->visible || !t->pending) return 0;
    if(t->id<0 || t->id>=V6_COLLECT_COUNT) return 0;
    c->bits[(unsigned)t->id>>3]|=(unsigned char)(1u<<((unsigned)t->id&7));
    t->visible=0;t->pending=0;
    return 1;
}
