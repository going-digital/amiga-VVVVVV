#ifndef V6_SPRITE_MUX_H
#define V6_SPRITE_MUX_H
#include <stdint.h>
enum { V6_MUX_ACTORS=14,V6_MUX_WORDS=196 };
typedef struct { const uint32_t *rows;int16_t x,y;uint16_t crop,width,height,colour; } V6MuxActor;
typedef struct {uint8_t actor,channel;uint16_t first,last,left,start,stop,words,clip;} V6MuxSpan;
typedef struct {V6MuxSpan spans[14];uint16_t count,used[8];} V6MuxPlan;
/* Eight real channels; vertical reuse needs two rows between DMA chains.
 * The source gameplay viewport is y16..215. Invalid/unplaceable input leaves
 * the output unchanged: a caller must never silently drop a source actor. */
int v6_sprite_mux_plan(V6MuxPlan *,const V6MuxActor *,unsigned count);
/* Eight contiguous V6_MUX_WORDS blocks, terminated chains and sprite palette
 * events. Colours must be installed before each span's physical start line. */
void v6_sprite_mux_dma(uint16_t *const out[8],const V6MuxPlan *,const V6MuxActor *);
unsigned v6_sprite_mux_copper(uint16_t *,const uint16_t *,unsigned words,
    const V6MuxPlan *,const V6MuxActor *);
/* Same compositor for a list already produced/validated by our renderer. */
unsigned v6_sprite_mux_rendered_copper(uint16_t *,const uint16_t *,unsigned words,
    const V6MuxPlan *,const V6MuxActor *);

/* Append palettes after an owned static Copper prefix whose final wait precedes all actors. */
unsigned v6_sprite_mux_append_palette(uint16_t *out,unsigned words,const V6MuxPlan *p,const V6MuxActor *a);

/* Asset/room-owned descriptors with validated dimensions. Failure is fatal
 * to the caller; this fast path may modify the output before returning 0. */
int v6_sprite_mux_owned_plan(V6MuxPlan *,const V6MuxActor *,unsigned);
/* Same canonical output, seeded by a previous valid (or zeroed) owned plan. */
int v6_sprite_mux_owned_replan(V6MuxPlan *,const V6MuxActor *,unsigned);
typedef struct {uint32_t bitmap,blank;uint16_t start,stop,colour;} V6MuxOverlay;
/* Optional third foreground plane for a software actor. The blank plane
 * supplies the unused second background plane during this bounded band. */
unsigned v6_sprite_mux_overlay_copper(uint16_t *,const uint16_t *,unsigned,
    const V6MuxPlan *,const V6MuxActor *,const V6MuxOverlay *);
unsigned v6_sprite_mux_append_overlay(uint16_t *,unsigned,const V6MuxPlan *,
    const V6MuxActor *,const V6MuxOverlay *);
/* Rectangle-only preflight: intrinsic spans already fit eight channels. */
int v6_sprite_mux_pressure(const V6MuxActor *,unsigned,const V6MuxActor *optional);
/* Owned descriptors; preserve output if the previous assignment no longer fits. */
int v6_sprite_mux_update(V6MuxPlan *,const V6MuxActor *,unsigned);
#endif
