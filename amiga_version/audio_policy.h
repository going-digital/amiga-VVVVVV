#ifndef V6_AUDIO_POLICY_H
#define V6_AUDIO_POLICY_H
/* Pure allocation decision; bit N permits SFX on Paula channel N.
 * Busy includes cooldown and draining. Age is elapsed time since acceptance,
 * supplied by the caller (unsigned clock subtraction handles wraparound).
 * Lowest idle channel wins. If full, steal only a strictly lower priority:
 * lowest priority first, then oldest age, then lowest channel.
 * Returns channel 0..3, -1 for rejection, -2 for invalid input.
 * The caller validates the sample and applies its channel-local register plan
 * before recording a successful allocation. Reserved channels are untouched.
 * No shipping music channel count or cue priority is fixed by this policy. */
int v6_audio_choose(unsigned allowed,unsigned busy,const unsigned priority[4],
    const unsigned age[4],unsigned incoming_priority);
#endif
