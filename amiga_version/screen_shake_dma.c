#include "screen_shake_dma.h"
int v6_screen_shake_sprite(uint16_t *d,unsigned words,int x,int y)
{
    int start,stop,left,first,last,row;unsigned horizontal;uint16_t mask=0xffff;
    if(!d || words<4 || x< -4 || x>2 || y< -4 || y>4)return 0;
    if(!d[0] && !d[1])return 1;
    start=(d[0]>>8)|((d[1]&4)<<6);stop=(d[1]>>8)|((d[1]&2)<<7);
    if(stop<=start || (unsigned)(stop-start)*2+4>words || (d[1]&0x80))return 0;
    left=((d[0]&255)*2+(d[1]&1))-128+x;
    if(left>=0 && left<=304 && start+y>=52 && stop+y<=292) {
        start+=y;stop+=y;horizontal=128+left;
        d[0]=((start&255)<<8)|(horizontal>>1);
        d[1]=((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(horizontal&1);
        return 1;
    }
    first=start+y<52?52-start-y:0;
    last=stop+y>292?292-start-y:stop-start;
    if(first>=last || left>=320 || left<=-16){d[0]=d[1]=0;return 1;}
    if(left<0)mask&=0xffffu>>-left;
    if(left>304)mask&=(uint16_t)(0xffffu<<(left-304));
    if(first || last!=stop-start || mask!=0xffff)for(row=first;row<last;++row) {
        d[2+2*(row-first)]=d[2+2*row]&mask;
        d[3+2*(row-first)]=d[3+2*row]&mask;
    }
    d[2+2*(last-first)]=d[3+2*(last-first)]=0;
    start+=y+first;stop=start+last-first;horizontal=128+left;
    d[0]=((start&255)<<8)|(horizontal>>1);
    d[1]=((stop&255)<<8)|((start&256)>>6)|((stop&256)>>7)|(horizontal&1);
    return 1;
}
