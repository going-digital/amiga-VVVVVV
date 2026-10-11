/* Adapted from Game.cpp foundtrinket text, UtilityClass.cpp number_words,
 * Textbox.cpp geometry and Graphics.cpp textbox/bar drawing.
 * Original code copyright Terry Cavanagh; see ../LICENSE.md. */
#include "pickup_draw.h"
static unsigned append(char *out,unsigned at,const char *text)
{
    while(*text)out[at++]=*text++;
    out[at]=0;return at;
}
int v6_pickup_draw_count(V6PickupDraw *s,unsigned count)
{
    static const char *const ones[]={"One","Two","Three","Four","Five","Six","Seven","Eight","Nine"};
    static const char *const tens[]={"Ten","Twenty","Thirty","Forty","Fifty","Sixty","Seventy","Eighty","Ninety"};
    static const char *const teens[]={"Eleven","Twelve","Thirteen","Fourteen","Fifteen","Sixteen","Seventeen","Eighteen","Nineteen"};
    unsigned n=count,t=0,length=0;
    if(count>100)return 0;
    if(n==0)length=append(s->text,0,"Zero");
    else if(n==100)length=append(s->text,0,"One Hundred");
    else if(n<10)length=append(s->text,0,ones[n-1]);
    else if(n>10 && n<20)length=append(s->text,0,teens[n-11]);
    else {
        while(n>=10){n-=10;++t;}
        length=append(s->text,0,tens[t-1]);
        if(n){s->text[length++]=' ';length=append(s->text,length,ones[n-1]);}
    }
    s->length=append(s->text,length," out of Twenty");s->count=count;
    s->width=(s->length+4)*8;s->x=160-s->width/2;
    return 1;
}
void v6_pickup_draw_init(V6PickupDraw *s)
{
    s->bars=s->old_bars=0;v6_pickup_draw_count(s,0);
}
void v6_pickup_draw_tick(V6PickupDraw *s,int show)
{
    s->old_bars=s->bars;
    if(show){s->bars+=25;if(s->bars>361)s->bars=361;}
    else if(s->bars>0){s->bars-=25;if(s->bars<0)s->bars=0;}
}
static void span(uint8_t *out,unsigned x,unsigned end)
{
    unsigned a=x>>3,b=(end-1)>>3,i;
    if(x>=end)return;
    if(a==b){out[a]|=(uint8_t)((255U>>(x&7)) & (255U<<(7-((end-1)&7))));return;}
    out[a]|=(uint8_t)(255U>>(x&7));
    for(i=a+1;i<b;++i)out[i]=255;
    out[b]|=(uint8_t)(255U<<(7-((end-1)&7)));
}
static void glyph(uint8_t *out,unsigned x,uint8_t bits)
{
    out[x>>3]|=bits>>(x&7);
    if(x&7)out[(x>>3)+1]|=(uint8_t)(bits<<(8-(x&7)));
}
static void box(uint8_t *mask,uint8_t *ink,unsigned x,unsigned width,
    unsigned row,unsigned height,const uint8_t border[8][8])
{
    unsigned i,base=0;uint8_t left=0,right=0;
    span(mask,x,x+width);
    if(row<8 || row>=height-8) {
        if(row>=height-8){base=5;row-=height-8;}
        glyph(ink,x,border[base][row]);
        for(i=8;i<width-8;i+=8)glyph(ink,x+i,border[base+1][row]);
        glyph(ink,x+width-8,border[base+2][row]);
    } else {
        /* Source h=42 has an overlapping final side tile at h-16. */
        if(row<(height/8-1)*8){left=border[3][row&7];right=border[4][row&7];}
        if(height%8 && row>=height-16) {
            left|=border[3][row-(height-16)];right|=border[4][row-(height-16)];
        }
        glyph(ink,x,left);glyph(ink,x+width-8,right);
    }
}
int v6_pickup_text_row(const V6PickupDraw *s,unsigned row,uint8_t mask[40],
    uint8_t ink[40],const uint8_t font[128][8],const uint8_t border[8][8])
{
    unsigned i,y,x;const char *text=0;
    if(row>=V6_PICKUP_HEIGHT || !s || !mask || !ink || !font || !border)return 0;
    for(i=0;i<40;++i){mask[i]=0;ink[i]=0;}
    if(row<42) {
        box(mask,ink,20,280,row,42,border);
        if(row>=8 && row<16){text="Congratulations!";x=92;y=row-8;}
        else if(row>=26 && row<34){text="You have found a shiny trinket!";x=36;y=row-26;}
        else return 1;
    } else if(row>=52) {
        box(mask,ink,s->x,s->width,row-52,24,border);
        if(row>=60 && row<68){text=s->text;x=s->x+16;y=row-60;}
        else return 1;
    } else return 1;
    for(i=0;text[i];++i)glyph(ink,x+i*8,font[(unsigned char)text[i]][y]);
    return 1;
}
int v6_pickup_bar_row(uint8_t mask[40],unsigned position,int bottom)
{
    unsigned i,x=0,end=position;
    if(!mask || position>361 || (bottom!=0 && bottom!=1))return 0;
    for(i=0;i<40;++i)mask[i]=0;
    if(bottom){x=position<360?360-position:0;end=320;}
    else if(end>320)end=320;
    if(x<end)span(mask,x,end);
    return 1;
}
void v6_pickup_compose_row(uint16_t *out,unsigned stride,const uint16_t *fg,
    unsigned fg_stride,const uint16_t mask[20],const uint16_t ink[20])
{
    unsigned i;
    uint32_t *a=(void *)out,*b=(void *)(out+stride),*c=(void *)(out+2*stride);
    const uint32_t *f=(const void *)fg,*g=(const void *)(fg+fg_stride);
    const uint32_t *m=(const void *)mask,*k=(const void *)ink;
    for(i=0;i<10;++i) {
        uint32_t bits=*m++;
        *a++=(*f++&~bits)|*k++;
        *b++=*g++&~bits;
        *c++=bits;
    }
}
void v6_pickup_bar_column(uint16_t *out,const uint16_t *fg,uint16_t mask,unsigned rows)
{
    uint16_t *b=out+320,*c=out+640;const uint16_t *g=fg+5120;
    if(mask==0) {
        while(rows>=4) {
            *out=*fg;*b=*g;*c=0;
            out[20]=fg[20];b[20]=g[20];c[20]=0;
            out[40]=fg[40];b[40]=g[40];c[40]=0;
            out[60]=fg[60];b[60]=g[60];c[60]=0;
            out+=80;b+=80;c+=80;fg+=80;g+=80;rows-=4;
        }
        while(rows--) {
            *out=*fg;*b=*g;*c=0;
            out+=20;b+=20;c+=20;fg+=20;g+=20;
        }
        return;
    }
    if(mask==65535) {
        while(rows--) {
            *out=0;*b=0;*c=65535;
            out+=20;b+=20;c+=20;
        }
        return;
    }
    while(rows--) {
        *out=*fg&~mask;*b=*g&~mask;*c=mask;
        out+=20;b+=20;c+=20;fg+=20;g+=20;
    }
}
