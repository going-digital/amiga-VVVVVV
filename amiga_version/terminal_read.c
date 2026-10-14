/* TerminalScripts.cpp station log; Script.cpp and Textbox.cpp presentation.
 * Copyright Terry Cavanagh; see ../LICENSE.md. */
#include "terminal_read.h"
static int dimensions(const V6TerminalPage *p,int *width,int *height)
{
    unsigned i,n,max=0;
    if(!p || !p->count || p->count>V6_TERMINAL_LINES || p->flip>1 ||
       (p->x!=-500 && (p->x<0 || p->x>320)) ||
       (p->y!=-500 && (p->y<0 || p->y>240)))return 0;
    for(i=0;i<p->count;++i){const unsigned char *s=(const void *)p->lines[i];
        if(!s)return 0;
        for(n=0;s[n];++n)if(n>=36 || s[n]>=128)return 0;
        if(n>max)max=n;
    }
    *width=(int)max*8+16;*height=(int)p->count*9+15;return 1;
}
int v6_terminal_read_start(V6TerminalRead *v,const V6TerminalReadProgram *p)
{
    unsigned i;int widths[2],heights[2];
    if(!v || v->active || !p || !p->pages || p->count!=2)return 0;
    for(i=0;i<2;++i)if(!dimensions(&p->pages[i],&widths[i],&heights[i]))return 0;
    v->program=p;
    for(i=0;i<2;++i){V6TerminalBox *b=&v->boxes[i];const V6TerminalPage *page=&p->pages[i];
        b->page=page;b->w=widths[i];b->h=heights[i];
        b->x=page->x==-500?160-b->w/2:page->x;
        b->y=page->y==-500?120-b->h/2:page->y;
        /* Textbox.cpp adjust ordering is significant for very wide boxes. */
        if(b->x<10)b->x=10;
        if(b->y<10)b->y=10;
        if(b->x+b->w>310)b->x=310-b->w;
        if(b->y+b->h>230)b->y=230-b->h;
        b->visible=b->mode=b->step=0;b->opacity=8388608;b->previous_opacity=0;
    }
    v->active=v->bars=v->control=1;v->phase=v->waiting=v->cues=v->serial=0;return 1;
}
void v6_terminal_read_tick(V6TerminalRead *v,const V6TerminalReadSignals *s)
{
    unsigned i;
    if(!v || !s || !v->active)return;
    if(v->phase==0){
        if(s->bars_position<360)return;
        for(i=0;i<2;++i)v->boxes[i].visible=1;
        ++v->cues;++v->serial;v->control=0;v->waiting=1;v->phase=1;return;
    }
    if(v->phase==1){
        if(!s->advance)return;
        for(i=0;i<2;++i){v->boxes[i].mode=2;v->boxes[i].step=0;v->boxes[i].opacity=16777216;}
        ++v->serial;v->waiting=v->bars=0;v->control=1;v->phase=2;
    }
    if(s->bars_position<=0)v->active=0;
}
void v6_terminal_read_animate(V6TerminalRead *v)
{
    static const uint32_t appear[6]={8388608,10066330,11744052,13421774,15099496,16777216};
    static const uint32_t disappear[6]={16777216,15099494,13421772,11744050,10066328,8388608};
    unsigned i,removed=0;
    if(!v)return;
    for(i=0;i<2;++i){V6TerminalBox *b=&v->boxes[i];
        if(!b->visible)continue;
        b->previous_opacity=b->opacity;
        if(b->mode==1)continue;
        if(b->step<5)++b->step;
        b->opacity=b->mode==2?disappear[b->step]:appear[b->step];
        if(b->step==5){if(b->mode==2){b->visible=0;removed=1;}else b->mode=1;}
    }
    if(removed)++v->serial;
}
unsigned v6_terminal_box_gray(const V6TerminalBox *b)
{
    /* 174 * opacity truncated like the source's float-to-int conversion. */
    static const unsigned appear[6]={87,104,121,139,156,174};
    static const unsigned disappear[6]={174,156,139,121,104,87};
    if(!b || b->step>5)return 0;
    return b->mode==2?disappear[b->step]:appear[b->step];
}
static void stamp(uint8_t *mask,uint8_t *ink,int x,unsigned bits)
{
    /* Prepared geometry keeps each eight-pixel stamp inside the screen. */
    unsigned column=(unsigned)x>>3,shift=(unsigned)x&7,value=bits>>shift;
    mask[column]|=(uint8_t)value;ink[column]|=(uint8_t)value;
    if(shift){value=bits<<(8-shift);mask[column+1]|=(uint8_t)value;ink[column+1]|=(uint8_t)value;}
}
static void fill(uint8_t *mask,uint8_t *ink,unsigned x,unsigned width)
{
    unsigned first=x>>3,last=(x+width-1)>>3,i;
    uint8_t left=(uint8_t)(255U>>(x&7));
    uint8_t right=(uint8_t)(255U<<(7-((x+width-1)&7)));
    if(first==last){left&=right;mask[first]|=left;ink[first]&=(uint8_t)~left;return;}
    mask[first]|=left;ink[first]&=(uint8_t)~left;
    for(i=first+1;i<last;++i){mask[i]=255;ink[i]=0;}
    mask[last]|=right;ink[last]&=(uint8_t)~right;
}
int v6_terminal_read_row(uint8_t out[80],unsigned row,const V6TerminalRead *v,
    const uint8_t font[128][8],const uint8_t border[8][8],int flip)
{
    unsigned i,j,k;uint8_t *ink;
    if(!out || !v || !font || !border || row>=240)return 0;
    /* Validate all descriptors before touching the destination. */
    for(i=0;i<2;++i)if(v->boxes[i].visible){int w,h;
        if(!dimensions(v->boxes[i].page,&w,&h) || w!=v->boxes[i].w || h!=v->boxes[i].h ||
           v->boxes[i].x<0 || v->boxes[i].x+w>320 || v->boxes[i].y<0 || v->boxes[i].y+h>240)return 0;
    }
    ink=out+40;for(i=0;i<80;++i)out[i]=0;
    for(i=0;i<2;++i){const V6TerminalBox *b=&v->boxes[i];int y,local;
        if(!b->visible)continue;
        y=b->y;
        if(flip && b->page->flip)y=240-y-16-(int)b->page->count*9;
        local=(int)row-y;if(local<0 || local>=b->h)continue;
        fill(out,ink,(unsigned)b->x,(unsigned)b->w);
        if(local<8 || local>=b->h-8){unsigned tile=local<8?1:6,by=(unsigned)(local<8?local:local-(b->h-8));
            for(j=0;j<(unsigned)b->w/8-2;++j)stamp(out,ink,b->x+8+(int)j*8,border[tile][by]);
            if(b->w&7)stamp(out,ink,b->x+b->w-16,border[tile][by]);
            stamp(out,ink,b->x,border[tile==1?0:5][by]);
            stamp(out,ink,b->x+b->w-8,border[tile==1?2:7][by]);
        }else{
            unsigned by=(unsigned)(local-8)&7;
            if(local<(b->h/8-1)*8){
                stamp(out,ink,b->x,border[3][by]);stamp(out,ink,b->x+b->w-8,border[4][by]);}
            /* A nonmultiple height repeats the final vertical tile at h-16. */
            if((b->h&7) && local>=b->h-16){by=(unsigned)(local-(b->h-16));
                stamp(out,ink,b->x,border[3][by]);stamp(out,ink,b->x+b->w-8,border[4][by]);}
        }
        for(j=0;j<b->page->count;++j){int top=8+(int)(flip?b->page->count-1-j:j)*9;
            const unsigned char *text=(const void *)b->page->lines[j];
            if(local<top || local>=top+8)continue;
            for(k=0;text[k];++k)stamp(out,ink,b->x+8+(int)k*8,font[text[k]][local-top]);
        }
    }
    return 1;
}
