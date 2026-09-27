#include "pixel_collision.h"
int v6_pixel_hit(const uint32_t *a, int ax, int ay,
                 const uint32_t *b, int bx, int by)
{
    int dx=bx-ax, dy=by-ay, first=dy>0?dy:0, end=dy+32<32?dy+32:32, y;
    if (dx<=-32 || dx>=32 || first>=end) return 0;
    for (y=first;y<end;++y) {
        uint32_t bits=b[y-dy];
        bits=dx>=0?bits>>dx:bits<<-dx;
        if (a[y]&bits) return 1;
    }
    return 0;
}
