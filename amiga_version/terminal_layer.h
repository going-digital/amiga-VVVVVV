#ifndef V6_TERMINAL_LAYER_H
#define V6_TERMINAL_LAYER_H
#include <stdint.h>
#include "sprite_mux.h"
#define V6_TERMINAL_BITMAP 28800
/* Private row packets expand to forty bytes of one-bitplane caption ink. */
int v6_terminal_layer_decode(uint8_t row[40],const uint8_t *,unsigned);
/* Full-width opaque heading y60..83 and body y86..154. */
unsigned v6_terminal_layer_occlude(uint16_t *dma);
void v6_terminal_layer_bars(uint8_t *,const uint8_t *,unsigned,unsigned);
/* Owned, chronologically merged campaign list. Switch to one bitplane only
 * inside the two full-width captions; resume world/background/NPC fetches at
 * their exact row afterwards. The input and output must be distinct. */
unsigned v6_terminal_layer_copper(uint16_t *,const uint16_t *,unsigned,
    uint32_t bars,uint32_t caption,uint32_t world,uint32_t blank,
    const V6MuxOverlay *npc,int visible,unsigned gray);
/* Camera-zero station fast path: merge caption, sprite and follower events
 * directly into the owned static prefix, without two whole-list passes. */
typedef struct {uint16_t words,c0,c1,blocks[7][24],sizes[7];} V6TerminalPrefix;
void v6_terminal_scene_windows(V6TerminalPrefix *,uint32_t,uint32_t,uint32_t,uint32_t);
int v6_terminal_scene_prefix(V6TerminalPrefix *,const uint16_t *,unsigned);
unsigned v6_terminal_scene_copper(uint16_t *,const V6TerminalPrefix *,
    const V6MuxPlan *,const V6MuxActor *,const V6MuxOverlay *,
    uint32_t,uint32_t,uint32_t,uint32_t,int,unsigned);
#endif
