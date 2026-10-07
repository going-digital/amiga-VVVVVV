#ifndef V6_HALLWAY_CREW_H
#define V6_HALLWAY_CREW_H
/* Campaign conditions used by Finalclass.cpp's Seeing Red room setup. */
typedef struct {
    int time_trial, translator_exploring, companion, rescue_triggered, red_rescued;
} V6HallwayStory;
/* Bounded stand-still (AI 17) appearance only. Dialogue and follow-player AI
 * belong to the script integration, which must update the campaign flags. */
int v6_hallway_crew_visible(int room_x,int room_y,const V6HallwayStory *);
#endif
