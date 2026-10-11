#include "prize_return_draw.h"
#include "tower_draw.h"
int v6_prize_return_draw_platforms(uint8_t *ring,const V6PrizeReturn *s,
    const uint8_t *strips,const uint8_t tile[16],const uint8_t mask[8],int last_y[4])
{
    unsigned i,p,row;
    if(s->platform_count!=4 || s->flags!=V6_PLATFORMS_VERTICAL)return 0;
    for(i=0;i<4;++i) {
        const V6Platform *a=&s->platforms[i];
        if(a->x!=88+(int)i*48 || a->w!=32 || a->h!=8 || a->y<0 || a->y>232 ||
           last_y[i]<-1 || last_y[i]>232)return 0;
    }
    for(i=0;i<4;++i) {
        const V6Platform *a=&s->platforms[i];
        if(last_y[i]==a->y)continue;
        if(last_y[i]>=0)for(p=0;p<2;++p) {
            uint8_t *d=ring+p*V6_TOWER_PLANE_BYTES+last_y[i]*40+a->x/8;
            const uint8_t *b=strips+i*1920+last_y[i]*8+p*4;
            for(row=0;row<8;++row,d+=40,b+=8) {
                d[0]=b[0];d[1]=b[1];d[2]=b[2];d[3]=b[3];
            }
        }
        for(p=0;p<2;++p) {
            uint8_t *d=ring+p*V6_TOWER_PLANE_BYTES+a->y*40+a->x/8;
            for(row=0;row<8;++row,d+=40) {
                uint8_t bits=tile[p*8+row];
                if(mask[row]==255) {
                    d[0]=d[1]=d[2]=d[3]=bits;
                } else {
                    uint8_t keep=(uint8_t)~mask[row];
                    d[0]=(d[0]&keep)|bits;d[1]=(d[1]&keep)|bits;
                    d[2]=(d[2]&keep)|bits;d[3]=(d[3]&keep)|bits;
                }
            }
        }
        last_y[i]=a->y;
    }
    return 1;
}

/* Source conveyor origins are odd byte columns; the interior halfwords are
 * aligned. Stamp their repeated source bits with fewer bus writes. */
static inline __attribute__((always_inline)) void west_stamp32(uint8_t *d,uint8_t bits,uint16_t pair)
{ d[0]=bits;*(uint16_t *)(d+1)=pair;d[3]=bits; }
static inline __attribute__((always_inline)) void west_stamp64(uint8_t *d,uint8_t bits,uint16_t pair)
{ d[0]=bits;*(uint16_t *)(d+1)=pair;*(uint16_t *)(d+3)=pair;*(uint16_t *)(d+5)=pair;d[7]=bits; }
#ifdef __m68k__
/* Fixed eight-row tiles: avoid loop/address overhead in the cold phase stamp. */
__attribute__((optimize("unroll-loops")))
#endif
void v6_prize_return_draw_conveyors(uint8_t *ring,const uint8_t treads[16])
{
    unsigned row,plane;
        for(plane=0;plane<2;++plane) {
            uint8_t *top=ring+plane*V6_TOWER_PLANE_BYTES+80*40;
            uint8_t *bottom=ring+plane*V6_TOWER_PLANE_BYTES+144*40;
            const uint8_t *source=treads+plane*8;
            for(row=0;row<8;++row,top+=40,bottom+=40) {
                uint8_t bits=source[row];uint16_t pair=((uint16_t)bits<<8)|bits;
                west_stamp64(top+13,bits,pair);west_stamp64(top+21,bits,pair);
                west_stamp32(top+29,bits,pair);
                west_stamp64(bottom+7,bits,pair);west_stamp64(bottom+15,bits,pair);
                west_stamp32(bottom+23,bits,pair);
            }
        }
}
