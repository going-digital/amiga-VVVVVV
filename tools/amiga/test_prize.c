#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "prize.h"
#include "audio_policy.h"
int main(void)
{
    uint16_t tiles[1200]={0};
    V6Room room={tiles,0,0,0,0,0};
    V6Prize s;
    V6Collect bank;
    V6Player p;
    unsigned e,input,i;
    /* Same request ordering and reservation policy as the native dispatcher.
     * Equal-priority collapses cannot steal each other or the pickup jingle. */
    for(unsigned pickup=0;pickup<2;++pickup)for(unsigned mask=0;mask<8;++mask)
    for(unsigned occupied=0;occupied<4;++occupied) {
        unsigned priority[4]={9,9,2,2},age[4]={0,0,1,2};
        unsigned busy=3|(occupied<<2),accepted=0,dropped=0;
        unsigned events=(mask<<V6_PRIZE_GATE_SOUND_SHIFT)|(pickup?V6_PRIZE_PICKUP:0);
        for(unsigned slot=0;slot<4;++slot) {
            unsigned cue=v6_prize_audio_cue(events,slot);
            if(cue==4)continue;
            int chosen=v6_audio_choose(12,busy,priority,age,cue+1);
            if(chosen<0) {assert(chosen==-1);++dropped;continue;}
            assert(chosen==2 || chosen==3);
            busy|=1U<<chosen;priority[chosen]=cue+1;age[chosen]=0;++accepted;
        }
        unsigned requests=pickup+!!(mask&1)+!!(mask&2)+!!(mask&4);
        assert(accepted==(requests<2?requests:2));
        assert(dropped==requests-accepted && priority[0]==9 && priority[1]==9);
        if(pickup)assert(priority[2]==4 || priority[3]==4);
    }
    v6_collect_clear(&bank);
    v6_player_init(&p,200,200,0);
    v6_prize_init(&s,&room,&bank,-1,p.y);
    assert(s.waiting.x==88 && s.waiting.y==72 && s.waiting.behavior==15 && s.waiting.speed==4);
    assert(s.waiting.x1==0 && s.waiting.x2==320 && s.waiting.y1==0 && s.waiting.y2==240);
    assert(room.blocks==s.blocks && room.block_count==4);
    assert(s.checkpoint.id==443490 && !s.checkpoint.active && s.trinket.id==6);
    /* Any of the three gates can release the platform: source tests X only.
     * A collapse this tick must not release it until the next platform pass. */
    for(i=0;i<3;++i) {
        v6_prize_init(&s,&room,&bank,-1,p.y);
        s.disappearing[i].state=2;s.disappearing[i].life=1;s.disappearing[i].on_entity=0;
        e=v6_prize_live(&s,&room,&p,0,0,&bank,&input);
        assert(!(e&V6_PRIZE_FULL) && s.disappearing[i].state==3);
        assert(s.waiting.state==0 && s.waiting.x==88 && s.blocks[i].w==0 && s.blocks[i].h==0);
        v6_prize_live(&s,&room,&p,0,0,&bank,&input);
        assert(s.waiting.state==1 && s.waiting.vx==4 && s.waiting.x==92);
    }
    /* Every simultaneous subset preserves identities and pickup-first order. */
    for(unsigned mask=0;mask<8;++mask) {
        v6_collect_clear(&bank);v6_prize_init(&s,&room,&bank,-1,p.y);
        s.trinket.pending=1;
        for(i=0;i<3;++i)if(mask&(1U<<i))s.disappearing[i].state=1;
        e=v6_prize_entities(&s,&room,&bank);
        assert((e&V6_PRIZE_GATE_SOUND_MASK)==(mask<<V6_PRIZE_GATE_SOUND_SHIFT));
        assert(!!(e&V6_PRIZE_SOUND)==!!mask);
        assert(v6_prize_audio_cue(e,0)==3);
        for(i=1;i<=3;++i)assert(v6_prize_audio_cue(e,i)==((mask&(1U<<(3-i)))?2:4));
        assert(v6_prize_audio_cue(e,4)==4);
        assert(!(v6_prize_entities(&s,&room,&bank)&(V6_PRIZE_SOUND|V6_PRIZE_GATE_SOUND_MASK)));
    }
    v6_collect_clear(&bank);
    v6_prize_init(&s,&room,&bank,-1,p.y);
    for(i=0;i<3;++i) {
        s.disappearing[i].state=2;s.disappearing[i].life=1;
        s.disappearing[i].on_entity=0;
    }
    assert(!(v6_prize_death(&s,&room)&V6_PRIZE_TILE)); /* completing state 2 isn't state 3 entry */
    for(i=0;i<3;++i)assert(s.disappearing[i].state==4 && s.disappearing[i].invisible);
    /* Death relocates the waiting platform once, then freezes movement,
     * recharge and pending pickup. */
    s.trinket.pending=1;
    for(i=0;i<30;++i)assert(v6_prize_death(&s,&room)==0);
    assert(s.waiting.x==152 && s.waiting.old_x==88 && !v6_collect_has(&bank,6));
    assert(s.blocks[3].x==152 && s.blocks[3].y==72 && s.blocks[3].w==32 && s.blocks[3].h==8);
    e=v6_prize_live(&s,&room,&p,0,9,&bank,&input);
    assert(e&V6_PRIZE_PICKUP);
    assert(v6_collect_has(&bank,6) && !s.trinket.visible && room.block_count==4);
    for(i=0;i<4;++i)assert(s.blocks[i].type==V6_BLOCK);
    assert(s.blocks[0].y==128 && s.blocks[1].y==112 && s.blocks[2].y==72); /* first disabled reuse, reverse update */
    v6_prize_respawn(&s,134);
    assert(v6_collect_has(&bank,6) && !s.trinket.visible);
    v6_prize_init(&s,&room,&bank,443490,134);
    assert(!s.trinket.visible && s.checkpoint.active);
    /* State 3 entry adds the special solid tile exactly once, then recharge waits. */
    s.disappearing[0].state=3;s.disappearing[0].invisible=1;
    assert(v6_prize_death(&s,&room)&V6_PRIZE_TILE);
    assert(!(v6_prize_death(&s,&room)&V6_PRIZE_TILE));
    /* Checkpoint update occurs after input, retaining the current direction. */
    s.checkpoint.pending=1;p.dir=1;
    e=v6_prize_live(&s,&room,&p,V6_LEFT,0,&bank,&input);
    assert(e&V6_PRIZE_SAVE);
    assert(s.save.x==236 && s.save.y==134 && s.save.gravity==1 && s.save.dir==0);
    puts("PASS Prize composition: eight simultaneous gate subsets, 64 reserved-channel allocations, source order, death/recharge, pickup/reentry and checkpoint direction");
    return 0;
}
