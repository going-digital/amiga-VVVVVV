#include "ui_menu.h"
static const uint16_t palette[16]={0,0x112,0x122,0x4bc,0xccf,0x444,0xfff,0x99b,0,0,0,0,0x888,0x666,0xaaa,0x1ff};
static const uint16_t names[6]={0x1ee,0xe1e,0xee1,0xe11,0x1e1,0x11e};
static const uint16_t status[6]={0x188,0x818,0x881,0x811,0x181,0x118};
static const uint16_t portraits[6]={0x9cd,0xc7c,0xcc7,0xf44,0x6d7,0x44e};
static const char *crew[6]={"Viridian","Violet","Vitellary","Vermilion","Verdigris","Victoria"};
void v6_ui_palette(uint16_t out[32]){unsigned i;for(i=0;i<32;++i)out[i]=i<16?palette[i]:0;}
void v6_ui_crew_colours(uint16_t out[4],unsigned band)
{if(band<3){out[0]=names[band];out[1]=status[band];out[2]=names[band+3];out[3]=status[band+3];}}
unsigned v6_ui_colour(unsigned colour,unsigned row,const V6UIState *s)
{
    if(colour>=16)return 0;
    if(s->page==1 && colour>=8 && colour<=11) {
        unsigned band=row>=160?2:row>=96?1:0,c=band+(colour>=10?3:0);
        return (colour&1)?status[c]:names[c];
    }
    return palette[colour];
}
static int string(const char *s,unsigned limit)
{unsigned n=0;if(!s)return 0;while(s[n]){if(n>=limit || (unsigned char)s[n]<32 || (unsigned char)s[n]>126)return 0;++n;}return 1;}
static void span(uint8_t *out,unsigned bits,int x,int y,unsigned colour,unsigned planes)
{
    unsigned p,shift,mask,offset;int left=x;
    if(y<0 || y>=240 || x>=320 || x<=-8 || !bits)return;
    if(left<0){bits=(bits<<-left)&255;left=0;}
    if(left>312)bits&=255U<<(left-312);
    shift=(unsigned)left&7;mask=bits<<(8-shift);offset=(unsigned)y*40+((unsigned)left>>3);
    for(p=0;p<planes;++p) {
        uint8_t *d=out+p*9600+offset;unsigned value=(unsigned)d[0]<<8;
        if((left>>3)<39)value|=d[1];
        value=(colour&(1U<<p))?value|mask:value&~mask;
        d[0]=(uint8_t)(value>>8);if((left>>3)<39)d[1]=(uint8_t)value;
    }
}
static void glyph(uint8_t *out,const uint8_t fontrow[8],int x,int y,unsigned colour)
{unsigned row;for(row=0;row<8;++row)span(out,fontrow[row],x,y+(int)row,colour,4);}
static void text(uint8_t *out,const uint8_t font[128][8],int x,int y,const char *s,unsigned colour,int align,const V6UIDrawOps *ops,void *context)
{
    unsigned n=0,i;
    if(ops && ops->text){ops->text(context,x,y,s,colour,align);return;}
    while(s[n])++n;
    if(align==1)x-=n*4;else if(align==2)x-=n*8;
    for(i=0;i<n;++i)glyph(out,font[(unsigned char)s[i]],x+(int)i*8,y,colour);
}
void v6_ui_text(uint8_t *out,unsigned planes,const uint8_t font[128][8],int x,int y,const char *s,unsigned colour,int align)
{
    unsigned n=0,i,row;while(s[n])++n;
    if(align==1)x-=n*4;else if(align==2)x-=n*8;
    for(i=0;i<n;++i)for(row=0;row<8;++row)span(out,font[(unsigned char)s[i]][row],x+(int)i*8,y+(int)row,colour,planes);
}
static char *number(char *out,uint32_t value)
{
    static const uint32_t powers[10]={1000000000U,100000000U,10000000U,1000000U,100000U,10000U,1000U,100U,10U,1U};
    unsigned i,started=0;
    for(i=0;i<10;++i) {
        unsigned digit=0;while(value>=powers[i]){value-=powers[i];++digit;}
        if(digit || started || i==9){*out++=(char)('0'+digit);started=1;}
    }
    *out=0;return out;
}
static char *append(char *out,const char *s){while(*s)*out++=*s++;*out=0;return out;}
static void box(uint8_t *out,const uint8_t border[8][8],int x,int y,int w,int h,const V6UIDrawOps *ops,void *context)
{
    int k;
    if(ops && ops->border){ops->border(context,x,y,w,h);return;}
    for(k=0;k<w/8-2;++k){glyph(out,border[1],x+8+k*8,y,3);glyph(out,border[6],x+8+k*8,y+h-8,3);}
    if(w%8){glyph(out,border[1],x+w-16,y,3);glyph(out,border[6],x+w-16,y+h-8,3);}
    for(k=0;k<h/8-2;++k){glyph(out,border[3],x,y+8+k*8,3);glyph(out,border[4],x+w-8,y+8+k*8,3);}
    if(h%8){glyph(out,border[3],x,y+h-16,3);glyph(out,border[4],x+w-8,y+h-16,3);}
    glyph(out,border[0],x,y,3);glyph(out,border[2],x+w-8,y,3);glyph(out,border[5],x,y+h-8,3);glyph(out,border[7],x+w-8,y+h-8,3);
}
int v6_ui_draw_ops(uint8_t *out,const V6UIState *s,const uint8_t font[128][8],const uint8_t border[8][8],const uint32_t icons[2][32],V6UIFill fill,const V6UIDrawOps *ops,void *context)
{
    static const char *tabs[4]={"MAP","CREW","STATS","SAVE"};char buffer[41],time[12];unsigned i;
    if(!out || !s || !font || !border || !icons || !fill || s->page<1 || s->page>3 || s->saved>1 || s->failed>1 ||
       s->last.exists>1 || s->crew_mask>63 || s->crew_frame>1 || s->trinkets>100 || s->deaths>0x7fffffffU ||
       !string(s->roomname,36) || !string(s->area,26) || !string(s->last_area,26) ||
       !string(s->action,8) || !*s->action || !v6_save_clock_text(time,&s->clock))return 0;
    if(s->last.exists && (!v6_save_clock_text(time,&s->last.clock) || s->last.trinkets>100 || s->last.crew_mask>63))return 0;
    if(s->saved && !s->last.exists)return 0;
    if(!fill(context,0,0,320,240,1) || !fill(context,0,0,320,12,0) || !fill(context,-10,212,344,24,2))return 0;
    text(out,font,160,2,s->roomname,4,1,ops,context);box(out,border,-10,212,344,24,ops,context);
    for(i=0;i<4;++i) {
        const char *label=tabs[i];if(i==s->page){char *p=append(buffer,"[");p=append(p,label);append(p,"]");label=buffer;}
        text(out,font,40+(int)i*80,220,label,i==s->page?4:5,1,ops,context);
    }
    if(s->page==1) {
        for(i=0;i<6;++i) {
            unsigned active=s->crew_mask&(1U<<i),slot=i<3?i:i-3;int x=i<3?44:204,y=36+(int)slot*64;
            text(out,font,x,y,crew[i],active?(i<3?8:10):12,0,ops,context);
            text(out,font,x,y+10,active?(i==0?"(that's you!)":"Rescued!"):"Missing...",active?(i<3?9:11):5,0,ops,context);
        }
    } else if(s->page==2) {
        text(out,font,160,52,"[Trinkets found]",4,1,ops,context);
        append(number(buffer,s->trinkets)," out of 20");text(out,font,160,64,buffer,13,1,ops,context);
        text(out,font,160,102,"[Number of Deaths]",4,1,ops,context);number(buffer,s->deaths);text(out,font,160,114,buffer,13,1,ops,context);
        text(out,font,160,152,"[Time Taken]",4,1,ops,context);v6_save_clock_text(time,&s->clock);text(out,font,160,164,time,13,1,ops,context);
    } else if(s->failed)text(out,font,160,115,"ERROR: Could not save game!",7,1,ops,context);
    else {
        text(out,font,160,174,"(Note: The game is autosaved at every",7,1,ops,context);text(out,font,160,186,"teleporter.)",7,1,ops,context);
        if(!s->saved) {
            char *p=append(buffer,"[Press ");p=append(p,s->action);append(p," to save your game]");text(out,font,160,80,buffer,6,1,ops,context);
            if(s->last.exists) {
                text(out,font,160,100,"Last Save:",14,1,ops,context);v6_save_clock_text(time,&s->last.clock);
                p=append(buffer,s->last_area);p=append(p,", ");append(p,time);text(out,font,160,112,buffer,14,1,ops,context);
            }
        } else {
            text(out,font,160,36,"Game saved ok!",6,1,ops,context);
            if(!fill(context,17,65,286,90,2))return 0;
            box(out,border,17,65,286,90,ops,context);text(out,font,160,80,s->last_area,15,1,ops,context);
            v6_save_clock_text(time,&s->last.clock);text(out,font,59,132,time,6,0,ops,context);
            number(buffer,s->last.trinkets);text(out,font,262,132,buffer,6,2,ops,context);
            {unsigned icon,row,byte;for(icon=0;icon<2;++icon) {
                if(ops && ops->icon){ops->icon(context,icons[icon],icon?270:34,126,12);continue;}
                for(row=0;row<32;++row)for(byte=0;byte<4;++byte)
                span(out,(icons[icon][row]>>(24-byte*8))&255,icon?270+(int)byte*8:34+(int)byte*8,126+(int)row,12,4);}}

        }
    }
    return 1;
}
unsigned v6_ui_icons(V6UIIcon out[8],const V6UIState *s)
{
    unsigned i;
    if(s->page!=1 && !(s->page==3 && s->saved && !s->failed))return 0;
    for(i=0;i<6;++i) {
        unsigned active=s->crew_mask&(1U<<i);
        out[i].x=s->page==1?(i<3?16:176):(43+(int)i*42);
        out[i].y=s->page==1?32+(int)(i<3?i:i-3)*64:95;
        if(!active && s->page==1)out[i].x-=8;
        out[i].tile=active?s->crew_frame:12;out[i].colour=active?portraits[i]:0x444;
    }
    if(s->page==1)return 6;
    out[6].x=34;out[6].y=126;out[6].tile=50;out[6].colour=0x888;
    out[7].x=270;out[7].y=126;out[7].tile=22;out[7].colour=0x888;return 8;
}

int v6_ui_draw(uint8_t *out,const V6UIState *s,const uint8_t font[128][8],const uint8_t border[8][8],const uint32_t icons[2][32],V6UIFill fill,void *context)
{return v6_ui_draw_ops(out,s,font,border,icons,fill,0,context);}
