#ifndef V6_MUSIC_AREA_H
#define V6_MUSIC_AREA_H
/* Music.cpp changemusicarea policy on normalized main-map coordinates 0..19
 * (caller subtracts 100 from source room coordinates). Flags must be 0/1.
 * Returns 1 with track -1 for no change, or a base ID for niceplay; returns 0
 * on invalid arguments, preserving *track. Script ownership suppresses changes.
 * This is not the policy for custom/final-level rooms outside the main map. */
int v6_music_area_track(int x,int y,int script_running,int flip_mode,
    int time_trial,int *track);
#endif
