#ifndef V6_MUSIC_GAIN_H
#define V6_MUSIC_GAIN_H
#include "audio.h"
/* Word-register adapter boundary, not a tracker driver. Music/SFX masks must
 * be disjoint subsets of 0xf; remaining channels are unassigned. */
int v6_music_gain_plan(unsigned music_mask,unsigned sfx_mask,
    const unsigned instrument_volume[4],unsigned control_volume,unsigned user_volume,
    int muted,int music_muted,V6AudioPlan *);
/* Source control*user/256 truncates first (0..128). Each tracker instrument's
 * 0..64 volume then scales by this gain/128, truncating to Paula resolution.
 * Muting never destroys the caller's original instrument volumes. Only music
 * AUDnVOL words are emitted; DMA, IRQ, SFX and unassigned registers are untouched.
 * Invalid input preserves output. Tracker writes must pass through an ownership
 * boundary too; this function alone cannot safely coexist with raw LSP writes. */
#endif
