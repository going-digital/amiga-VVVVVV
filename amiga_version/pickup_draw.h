#ifndef V6_PICKUP_DRAW_H
#define V6_PICKUP_DRAW_H
#include <stdint.h>
/* English normal-game pickup: 8-pixel font, one-pixel line gap.
 * Three foreground planes retain source colours 0..3; 4 is box/bar fill,
 * 5 is gray text. An opaque mask hides sprites only inside the rectangles. */
enum { V6_PICKUP_TOP=85, V6_PICKUP_HEIGHT=76,
       V6_PICKUP_PLANE_BYTES=40*V6_PICKUP_HEIGHT,
       V6_PICKUP_BAR_PLANE_BYTES=40*16,
       V6_PICKUP_TEXT_OFFSET=3*V6_PICKUP_BAR_PLANE_BYTES,
       V6_PICKUP_BOTTOM_OFFSET=V6_PICKUP_TEXT_OFFSET+3*V6_PICKUP_PLANE_BYTES,
       V6_PICKUP_BANK_BYTES=V6_PICKUP_BOTTOM_OFFSET+3*V6_PICKUP_BAR_PLANE_BYTES,
       V6_PICKUP_DMA_BYTES=2*V6_PICKUP_BANK_BYTES+V6_PICKUP_PLANE_BYTES };
typedef struct {
    int bars,old_bars;
    unsigned count,length,x,width;
    char text[37];
} V6PickupDraw;
void v6_pickup_draw_init(V6PickupDraw *);
/* Count is the complete source collection bank, 0..100. Invalid count
 * leaves state unchanged. Uses the source English wordy number format. */
int v6_pickup_draw_count(V6PickupDraw *,unsigned count);
void v6_pickup_draw_tick(V6PickupDraw *,int show_bars);
/* Source render interpolation within the 34 ms fixed timestep. Elapsed is
 * clamped to 34000 us. The final zero-position tick hides retreating bars. */
unsigned v6_pickup_bar_position(const V6PickupDraw *,unsigned elapsed_us);
/* Generate one row of the two source-positioned textboxes. Mask/ink are
 * 40 bytes each; border tiles are source alpha masks 40..47. */
int v6_pickup_text_row(const V6PickupDraw *,unsigned row,uint8_t mask[40],
    uint8_t ink[40],const uint8_t font[128][8],const uint8_t border[8][8]);
/* Source bars: (0,0,pos,16) and (360-pos,224,pos,16), clipped to 320. */
int v6_pickup_bar_row(uint8_t mask[40],unsigned position,int bottom);
/* All row pointers are aligned to four bytes; strides are even 16-bit word
 * counts. Preserve the
 * original two-plane foreground wherever the new third-plane mask is zero. */
void v6_pickup_compose_row(uint16_t *out,unsigned stride,const uint16_t *fg,
    unsigned fg_stride,const uint16_t mask[20],const uint16_t ink[20]);
/* One moving bar word across up to 16 contiguous source rows. The caller
 * splits at a 256-row ring wrap. Bar planes have a 320-word stride. */
void v6_pickup_bar_column(uint16_t *out,const uint16_t *fg,uint16_t mask,unsigned rows);
#endif
