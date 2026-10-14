#include "map_draw.h"
#include "sprites.h"
static void tile(uint8_t *pixels,unsigned row,int x,int y,unsigned t,
    const uint8_t border[8][8],unsigned ink)
{
    unsigned i,b;if((int)row<y || (int)row>=y+8)return;
    b=border[t][row-y];
    for(i=0;i<8;++i)if(x+(int)i>=0 && x+(int)i<320 && (b&(128>>i)))pixels[x+i]=(uint8_t)ink;
}
static void box(uint8_t *pixels,unsigned row,int x,int y,int w,int h,
    const uint8_t border[8][8],unsigned fill,unsigned ink)
{
    int i,k;if((int)row>=y && (int)row<y+h)
        for(i=x;i<x+w;++i)if(i>=0 && i<320)pixels[i]=(uint8_t)fill;
    for(k=0;k<w/8-2;++k) {tile(pixels,row,x+8+k*8,y,1,border,ink);tile(pixels,row,x+8+k*8,y+h-8,6,border,ink);}
    if(w%8) {tile(pixels,row,x+w-16,y,1,border,ink);tile(pixels,row,x+w-16,y+h-8,6,border,ink);}
    for(k=0;k<h/8-2;++k) {tile(pixels,row,x,y+8+k*8,3,border,ink);tile(pixels,row,x+w-8,y+8+k*8,4,border,ink);}
    if(h%8) {tile(pixels,row,x,y+h-16,3,border,ink);tile(pixels,row,x+w-8,y+h-16,4,border,ink);}
    tile(pixels,row,x,y,0,border,ink);tile(pixels,row,x+w-8,y,2,border,ink);
    tile(pixels,row,x,y+h-8,5,border,ink);tile(pixels,row,x+w-8,y+h-8,7,border,ink);
}
static void text(uint8_t *pixels,unsigned row,int center,int y,const char *s,
    const uint8_t font[128][8],unsigned ink)
{
    unsigned n=0,i,b;int x;if((int)row<y || (int)row>=y+8)return;
    while(s[n])++n;
    x=center-(int)n*4;
    for(i=0;i<n;++i) {
        for(b=0;b<8;++b)if(x+(int)b>=0 && x+(int)b<320 && (font[(unsigned char)s[i]][row-y]&(128>>b)))pixels[x+b]=(uint8_t)ink;
        x+=8;
    }
}
static int draw_row(uint8_t out[200],unsigned row,const V6Exploration *explored,
    const uint8_t *minimap,const uint8_t fog[108],const uint8_t font[128][8],
    const uint8_t border[8][8],const uint8_t colours[6],const char *name)
{
    uint8_t pixels[320];unsigned x,p,n=0,i;
    if(!out || row>=240 || !explored || !minimap || !fog || !font || !border || !colours || !name)return 0;
    while(name[n]) {if(n>=36 || (unsigned char)name[n]>=128)return 0;++n;}
    for(i=0;i<6;++i)if(colours[i]>31)return 0;
    for(x=0;x<320;++x)pixels[x]=colours[row>=12?1:0];
    text(pixels,row,160,2,name,font,colours[4]);
    box(pixels,row,-10,212,344,24,border,colours[2],colours[3]);
    box(pixels,row,35,16,250,190,border,colours[2],colours[3]);
    if(row>=21 && row<201) {
        unsigned yy=row-21,room=0,cell,within,fy=yy;
        while(fy>=9){fy-=9;room+=20;}
        for(cell=0;cell<20;++cell) {
            unsigned bit=room+cell,seen=explored->rooms[bit>>3]&(1U<<(bit&7));
            x=cell*12;
            for(within=0;within<12;++within)
                pixels[40+x+within]=seen?minimap[x+within]:fog[fy*12+within];
        }
    }
    text(pixels,row,40,220,"[MAP]",font,colours[4]);
    text(pixels,row,120,220,"CREW",font,colours[5]);
    text(pixels,row,200,220,"STATS",font,colours[5]);
    text(pixels,row,280,220,"SAVE",font,colours[5]);
    for(p=0;p<5;++p)for(x=0;x<40;++x) {
        unsigned byte=0;
        for(i=0;i<8;++i)byte|=((pixels[x*8+i]>>p)&1)<<(7-i);
        out[p*40+x]=(uint8_t)byte;
    }
    return 1;
}
int v6_map_draw_row(uint8_t out[200],unsigned row,const V6Exploration *e,
    const uint8_t minimap[43200],const uint8_t fog[108],const uint8_t font[128][8],
    const uint8_t border[8][8],const uint8_t colours[6],const char *name)
{
    if(!minimap)return 0;
    return draw_row(out,row,e,minimap+((row>=21 && row<201)?(row-21)*240:0),fog,font,border,colours,name);
}
int v6_map_draw_row_rle(uint8_t out[200],unsigned row,const V6Exploration *e,
    const uint8_t *runs,unsigned bytes,const uint16_t offsets[181],const uint8_t fog[108],
    const uint8_t font[128][8],const uint8_t border[8][8],const uint8_t colours[6],const char *name)
{
    uint8_t line[240];unsigned n=0,at,end,i;
    if(!runs || !offsets || row>=240)return 0;
    if(row>=21 && row<201) {
        at=offsets[row-21];end=offsets[row-20];
        if(at>end || end>bytes || ((end-at)&1))return 0;
        while(at<end) {
            unsigned count=runs[at++],value=runs[at++];
            if(!count || value>31 || n+count>240)return 0;
            for(i=0;i<count;++i)line[n++]=(uint8_t)value;
        }
        if(n!=240)return 0;
    }
    return draw_row(out,row,e,line,fog,font,border,colours,name);
}
int v6_map_draw_template_row(uint8_t out[200],unsigned row,const V6Exploration *e,
    const uint8_t *runs,unsigned bytes,const uint16_t offsets[241],const uint16_t fog[9][5])
{
    uint8_t packed[200];unsigned n=0,at,end,i;
    if(!out || row>=240 || !e || !runs || !offsets || !fog)return 0;
    at=offsets[row];end=offsets[row+1];
    if(at>end || end>bytes || ((end-at)&1))return 0;
    while(at<end) {
        unsigned count=runs[at++],value=runs[at++];
        if(!count || n+count>200)return 0;
        for(i=0;i<count;++i)packed[n++]=(uint8_t)value;
    }
    if(n!=200)return 0;
    if(row>=21 && row<201) {
        unsigned fy=row-21,room=0,cell,plane,byte=5;
        while(fy>=9){fy-=9;room+=20;}
        for(plane=0;plane<5;++plane)if(fog[fy][plane]&15)return 0;
        for(cell=0;cell<20;++cell) {
            unsigned bit=room+cell;
            if(!(e->rooms[bit>>3]&(1U<<(bit&7)))) {
                for(plane=0;plane<5;++plane) {
                    unsigned bits=fog[fy][plane];uint8_t *d=packed+plane*40+byte;
                    if(cell&1) {d[0]=(uint8_t)((d[0]&0xf0)|(bits>>12));d[1]=(uint8_t)(bits>>4);}
                    else {d[0]=(uint8_t)(bits>>8);d[1]=(uint8_t)((d[1]&15)|(bits&0xf0));}
                }
            }
            byte+=(cell&1)?2:1;
        }
    }
    for(i=0;i<200;++i)((volatile uint8_t *)out)[i]=packed[i];
    return 1;
}
void v6_map_cursor_tick(unsigned *state,unsigned *delay)
{
    if(*state==0) {++*delay;if(*delay>10){*state=1;*delay=0;}}
    else if(*state==1) {++*delay;if(*delay>30)*state=2;}
    else if(*state==2) {
        /* Preserve the source's /15 blink indefinitely without overflow. */
        if(*delay==59)*delay=30;else ++*delay;
    }
}
unsigned v6_map_cursor_mode(unsigned state,unsigned delay,int noflashing)
{
    if(noflashing || (state==2 && (delay<15 || (delay>=30 && delay<45))))return 2;
    if(state==1 && (delay/4)%2==0)return 1;
    return 0;
}
int v6_map_cursor_rows(uint32_t rows[32],unsigned mode,int room_x,int room_y,int *x,int *y)
{
    unsigned i,j;
    if(!rows || !x || !y || mode>2 || room_x<100 || room_x>119 || room_x==109 || room_y<100 || room_y>119)return 0;
    for(i=0;i<32;++i) {
        uint32_t r=0;
        for(j=0;j<12;++j) {
            int outer=mode==1 && i<9 && (i==0 || i==8 || j==0 || j==11);
            int inner=mode && i>=2 && i<7 && j>=2 && j<10 && (i==2 || i==6 || j==2 || j==9);
            if(outer || inner)r|=1UL<<(31-j);
        }
        rows[i]=r;
    }
    *x=40+(room_x-100)*12;*y=21+(room_y-100)*9;return 1;
}
int v6_map_tower_cursor_rows(uint32_t rows[180],unsigned mode,int *x,int *y)
{
    unsigned i,j;
    if(!rows || !x || !y || mode>2)return 0;
    for(i=0;i<180;++i){uint32_t row=0;
        for(j=0;j<12;++j){
            int outer=mode==1 && (i==0 || i==179 || j==0 || j==11);
            int inner=mode && i>=2 && i<178 && j>=2 && j<10 && (i==2 || i==177 || j==2 || j==9);
            if(outer || inner)row|=1UL<<(31-j);
        }
        rows[i]=row;
    }
    *x=148;*y=21;return 1;
}
static uint16_t *reg(uint16_t *p,unsigned r,unsigned v)
{*p++=(uint16_t)r;*p++=(uint16_t)v;return p;}
static uint16_t *pointer(uint16_t *p,unsigned r,uint32_t a)
{p=reg(p,r,a>>16);return reg(p,r+2,a);}
unsigned v6_menu_copper(uint16_t *out,uint32_t bitmap,const uint16_t palette[32],uint32_t blank,uint32_t cursor,unsigned planes)
{
    uint16_t *p=out;unsigned i;
    if(!out || !palette || (planes!=3 && planes!=4 && planes!=5) || ((bitmap|blank|cursor)&1) || bitmap>0x1000000UL-planes*V6_MAP_PLANE_BYTES || blank>0xfffffc || cursor>0x1000000UL-V6_SPRITE_WORDS*2)return 0;
    /* Force word reads: the m68k GCC 14 byte-loop transformation otherwise
     * compares low colour bytes against 15 as well as the high nibbles. */
    for(i=0;i<32;++i)if(((const volatile uint16_t *)palette)[i]>0xfff)return 0;
    /* Sprite control DMA starts before line 44: publish pointers first. */
    for(i=0;i<8;++i)p=pointer(p,0x120+i*4,i?blank:cursor);
    p=reg(p,0x2c01,0xfffe);
    /* Single-playfield sprite priority uses PF2P (bits 5..3). */
    p=reg(p,0x100,(planes<<12)|0x200);p=reg(p,0x102,0);p=reg(p,0x104,0x20);
    p=reg(p,0x108,0);p=reg(p,0x10a,0);
    p=reg(p,0x08e,0x3481);p=reg(p,0x090,0x24c1);
    p=reg(p,0x092,0x38);p=reg(p,0x094,0xd0);
    for(i=0;i<planes;++i)p=pointer(p,0xe0+i*4,bitmap+i*V6_MAP_PLANE_BYTES);
    for(i=0;i<32;++i)p=reg(p,0x180+i*2,palette[i]);
    p=reg(p,0xffff,0xfffe);return (unsigned)(p-out);
}

unsigned v6_map_copper(uint16_t *out,uint32_t bitmap,const uint16_t palette[32],uint32_t blank,uint32_t cursor)
{return v6_menu_copper(out,bitmap,palette,blank,cursor,5);}

int v6_save_draw_row(uint8_t out[200],unsigned row,const V6SavePage *page,
    const uint8_t font[128][8],const uint8_t border[8][8],
    const uint8_t colours[8],const char *name,const char *action)
{
    uint8_t pixels[320];char prompt[39];unsigned i,n=0,a=0,x,p;
    const char *message=0;
    if(!out || row>=240 || !page || !font || !border || !colours || !name || !action ||
       (page->state!=V6_SAVE_PAGE_PROMPT && page->state!=V6_SAVE_PAGE_FAILED) || page->last_summary ||
       page->autosave_note>1 || (page->state!=V6_SAVE_PAGE_PROMPT && page->autosave_note))return 0;
    while(name[n]) {if(n>=36 || (unsigned char)name[n]>=128)return 0;++n;}
    while(action[a]) {if(a>=8 || (unsigned char)action[a]<32 || (unsigned char)action[a]>=127)return 0;++a;}
    if(!a)return 0;
    for(i=0;i<8;++i)if(colours[i]>31)return 0;
    if(page->state==V6_SAVE_PAGE_FAILED)message="ERROR: Could not save game!";
    for(x=0;x<320;++x)pixels[x]=colours[row>=12?1:0];
    text(pixels,row,160,2,name,font,colours[4]);
    box(pixels,row,-10,212,344,24,border,colours[2],colours[3]);
    text(pixels,row,40,220,"MAP",font,colours[5]);
    text(pixels,row,120,220,"CREW",font,colours[5]);
    text(pixels,row,200,220,"STATS",font,colours[5]);
    text(pixels,row,280,220,"[SAVE]",font,colours[4]);
    if(message)text(pixels,row,160,115,message,font,colours[7]);
    else {
        const char *head="[Press ",*tail=" to save your game]";
        n=0;for(i=0;head[i];++i)prompt[n++]=head[i];
        for(i=0;i<a;++i)prompt[n++]=action[i];
        for(i=0;tail[i];++i)prompt[n++]=tail[i];
        prompt[n]=0;
        text(pixels,row,160,80,prompt,font,colours[6]);
        if(page->autosave_note) {
            text(pixels,row,160,174,"(Note: The game is autosaved at every",font,colours[7]);
            text(pixels,row,160,186,"teleporter.)",font,colours[7]);
        }
    }
    for(p=0;p<5;++p)for(x=0;x<40;++x) {
        unsigned byte=0;
        for(i=0;i<8;++i)byte|=((pixels[x*8+i]>>p)&1)<<(7-i);
        out[p*40+x]=(uint8_t)byte;
    }
    return 1;
}
