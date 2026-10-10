#ifndef V6_MUSIC_REGISTERS_H
#define V6_MUSIC_REGISTERS_H
#include "audio.h"
/* Filter decoded WORD writes to music-owned channels, preserving order.
 * Masks must be disjoint subsets of 15. Recognizes AUDn location/length/period/
 * volume, audio-only DMACON and INTREQ. Removes SFX/unassigned channel writes
 * and strips their DMA/IRQ bits. Drops empty masked operations.
 * Rejects unsupported registers, global DMA/interrupt bits, oversized values,
 * invalid volumes and oversized plans before changing output. Exact in-place
 * filtering is supported. This checks ownership, not Chip address accessibility
 * or sample lifetime. Volume inputs must already use music_gain scaling.
 * Raw LSP code must first be adapted to emit decoded plans; it cannot run
 * directly against hardware while this boundary is expected to protect SFX. */
int v6_music_register_plan(const V6AudioPlan *,unsigned music_mask,
    unsigned sfx_mask,V6AudioPlan *);
#endif
