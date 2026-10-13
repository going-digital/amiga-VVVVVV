#ifndef V6_UI_MENU_H
#define V6_UI_MENU_H
#include "campaign_menu.h"
#define V6_UI_PLANES 4
#define V6_UI_BYTES 38400
/* RGB12 palette slots 8..11 are crew-band text colours; 17..31 are sprites.
 * Driver fills rectangles in an inactive bitmap (native uses the blitter). */
typedef int (*V6UIFill)(void *,int,int,unsigned,unsigned,unsigned);
typedef struct {
    unsigned page,saved,failed,crew_mask,crew_frame;
    uint32_t deaths;
    unsigned trinkets;
    V6SaveClock clock;
    V6SaveSummary last;
    const char *roomname,*area,*last_area,*action;
} V6UIState;
typedef struct {int x,y;unsigned tile,colour;} V6UIIcon;
typedef struct {
    void (*text)(void *,int,int,const char *,unsigned,int);
    void (*border)(void *,int,int,int,int);
    void (*icon)(void *,const uint32_t *,int,int,unsigned);
} V6UIDrawOps;
int v6_ui_draw_ops(uint8_t *,const V6UIState *,const uint8_t font[128][8],
    const uint8_t border[8][8],const uint32_t icons[2][32],V6UIFill,
    const V6UIDrawOps *,void *);
/* Source menu without flip/custom/secret/ship modes, glow=0. */
int v6_ui_draw(uint8_t *,const V6UIState *,const uint8_t font[128][8],
    const uint8_t border[8][8],const uint32_t icons[2][32],V6UIFill,void *);
void v6_ui_text(uint8_t *,unsigned planes,const uint8_t font[128][8],int,int,const char *,unsigned colour,int align);
unsigned v6_ui_icons(V6UIIcon out[8],const V6UIState *);
void v6_ui_palette(uint16_t out[32]);
void v6_ui_crew_colours(uint16_t out[4],unsigned band);
unsigned v6_ui_colour(unsigned colour,unsigned row,const V6UIState *);
#endif
