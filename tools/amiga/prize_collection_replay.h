/* Bounded north-entry fixture with the Prize checkpoint already saved.
 * The return journey from that checkpoint to the shaft is not simulated. */
static unsigned v6_prize_collection_replay(unsigned tick)
{
    if(tick<24)return 2;
    if(tick<98)return 0;
    if(tick<107)return 2;
    if(tick<115)return 1;
    return tick==125?4:0;
}
