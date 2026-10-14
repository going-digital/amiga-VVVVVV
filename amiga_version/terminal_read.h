#ifndef V6_TERMINAL_READ_H
#define V6_TERMINAL_READ_H
#include <stdint.h>
#define V6_TERMINAL_LINES 6
typedef struct {int x,y;unsigned flip,count;const char *lines[V6_TERMINAL_LINES];} V6TerminalPage;
typedef struct {const V6TerminalPage *pages;unsigned count;} V6TerminalReadProgram;
typedef struct {
    const V6TerminalPage *page;
    int x,y,w,h;
    unsigned visible,mode,step;
    uint32_t opacity,previous_opacity; /* Source binary32 samples in Q8.24. */
} V6TerminalBox;
typedef struct {
    const V6TerminalReadProgram *program;
    V6TerminalBox boxes[2];
    unsigned active,phase,bars,control,waiting,cues,serial;
} V6TerminalRead;
typedef struct {int bars_position,advance;} V6TerminalReadSignals;
/* Bounded station-log flow: opening bars, background heading + blocking log,
 * released/pressed advance, removal, closing bars. Immutable descriptors must
 * outlive the runner. Zero-initialize the runner before its first start.
 * An invalid program or active restart changes nothing. */
int v6_terminal_read_start(V6TerminalRead *,const V6TerminalReadProgram *);
void v6_terminal_read_tick(V6TerminalRead *,const V6TerminalReadSignals *);
/* Call once per original fixed update after script processing. Textboxes
 * retain their removal fade even after the read script finishes. */
void v6_terminal_read_animate(V6TerminalRead *);
/* Per-row transparent mask and ink planes, 40 bytes each. Index 0 is outside,
 * 1 is gray/6 fill, 3 is gray border/text. Palette fade is reported separately.
 * Original border tiles 40..47 and original ASCII font are caller-owned.
 * Flip mode reverses line order and mirrors only boxes marked flipme. */
int v6_terminal_read_row(uint8_t out[80],unsigned row,const V6TerminalRead *,
    const uint8_t font[128][8],const uint8_t border[8][8],int flipmode);
unsigned v6_terminal_box_gray(const V6TerminalBox *);
#endif
