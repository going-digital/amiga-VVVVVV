#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "trinkets.h"
int main(void)
{
    V6Collect bank,restored,before;
    V6Trinket t,unchanged;
    V6Player p={0};
    int id,x,y,j;
    unsigned cases=0;
    v6_collect_clear(&bank);
    for(id=0;id<V6_COLLECT_COUNT;++id) {
        assert(!v6_collect_has(&bank,id));
        assert(v6_trinket_init(&t,192,128,id,&bank));
        assert(t.visible && !t.pending);
        assert(!v6_trinket_update(&t,&bank));
        /* Independent source rectangle intersection, including touching edges. */
        for(y=100;y<=150;++y) for(x=170;x<=212;++x) {
            int hit=x+6<208 && x+18>192 && y+2<144 && y+23>128;
            t.pending=0;p.x=x;p.y=y;
            v6_trinket_collide(&t,&p);
            assert(t.pending==hit);
            assert(!v6_collect_has(&bank,id));
            ++cases;
        }
        t.pending=0;p.x=190;p.y=126;
        v6_trinket_collide(&t,&p);
        /* Pending pickup remains caller-owned while death updates are paused. */
        assert(t.visible && t.pending && !v6_collect_has(&bank,id));
        assert(v6_trinket_update(&t,&bank)==1);
        assert(!t.visible && !t.pending && v6_collect_has(&bank,id));
        for(j=0;j<V6_COLLECT_COUNT;++j)
            assert(v6_collect_has(&bank,j)==(j<=id));
        assert(!v6_trinket_update(&t,&bank));
        v6_trinket_collide(&t,&p);assert(!t.pending);
        assert(v6_trinket_init(&t,192,128,id,&bank));
        assert(!t.visible && !t.pending);
        assert(v6_collect_import(&restored,bank.bits));
        assert(!memcmp(&restored,&bank,sizeof bank));
    }
    assert(bank.bits[12]==15);
    assert(!v6_collect_has(&bank,-1) && !v6_collect_has(&bank,100));
    unchanged=t;
    assert(!v6_trinket_init(&t,0,0,-1,&bank));
    assert(!memcmp(&t,&unchanged,sizeof t));
    assert(!v6_trinket_init(&t,0,0,100,&bank));
    assert(!memcmp(&t,&unchanged,sizeof t));
    before=restored;
    for(id=16;id<256;++id) {
        bank.bits[12]=(unsigned char)id;
        assert(!v6_collect_import(&restored,bank.bits));
        assert(!memcmp(&restored,&before,sizeof restored));
    }
    v6_collect_clear(&bank);
    assert(v6_collect_import(&restored,bank.bits));
    for(id=0;id<V6_COLLECT_COUNT;++id) assert(!v6_collect_has(&restored,id));
    printf("trinkets: %u collision positions, 100 pickups/reentries, 240 malformed banks pass\n",cases);
    return 0;
}
