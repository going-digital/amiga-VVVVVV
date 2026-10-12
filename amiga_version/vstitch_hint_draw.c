#include "vstitch_hint_draw.h"
static void glyph(uint8_t *out,unsigned x,uint8_t bits)
{
    out[x/8]|=bits>>(x&7);
    if(x&7)out[x/8+1]|=(uint8_t)(bits<<(8-(x&7)));
}
int v6_vstitch_hint_row(unsigned row,uint8_t mask[40],uint8_t ink[40],
    const uint8_t font[128][8],const uint8_t border[8][8])
{
    static const char *const lines[2]={"Press ENTER to view","map and quicksave"};
    unsigned x,i,y,base=0;
    if(row>=V6_HINT_HEIGHT || !mask || !ink || !font || !border)return 0;
    for(i=0;i<40;++i){mask[i]=0;ink[i]=0;}
    mask[7]=15;for(i=8;i<32;++i)mask[i]=255;mask[32]=240;
    if(row<8 || row>=25) {
        y=row;if(row>=25){y-=25;base=5;}
        glyph(ink,60,border[base][y]);
        for(x=68;x<252;x+=8)glyph(ink,x,border[base+1][y]);
        glyph(ink,252,border[base+2][y]);
    } else {
        uint8_t left=0,right=0;
        if(row<24){left=border[3][row&7];right=border[4][row&7];}
        if(row>=17){left|=border[3][row-17];right|=border[4][row-17];}
        glyph(ink,60,left);glyph(ink,252,right);
    }
    if(row>=8 && row<16) {i=0;y=row-8;x=84;}
    else if(row>=17 && row<25) {i=1;y=row-17;x=92;}
    else return 1;
    for(base=0;lines[i][base];++base)glyph(ink,x+base*8,font[(unsigned char)lines[i][base]][y]);
    return 1;
}
uint32_t v6_vstitch_hint_colours(unsigned previous,unsigned level,unsigned elapsed)
{
    static const uint32_t scaled[11]={0,34000,68000,102000,136000,170000,204000,238000,272000,306000,340000};
    static const uint32_t threshold[11]={3060000,8840000,14620000,20400000,26180000,31960000,37740000,43520000,49300000,55080000,60860000};
    uint32_t value,fill,ink;unsigned shade=0;
    if(previous<5 || previous>10 || level<5 || level>10 ||
       (previous>level?previous-level:level-previous)>1)return 0;
    if(elapsed>34000)elapsed=34000;
    value=scaled[previous];
    if(level>previous)value+=elapsed;
    else if(level<previous)value-=elapsed;
    value=value*174;
    while(shade<11 && value>=threshold[shade])++shade;
    ink=(shade<<8)|(shade<<4)|shade;
    fill=value>=53040000?0x222:0x111;
    return (fill<<16)|ink;
}
