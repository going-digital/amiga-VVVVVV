#include "room_codec.h"

static uint16_t word(const uint8_t *p)
{
    return ((uint16_t)p[0] << 8) | p[1];
}

int v6_unpack_room(const uint8_t *src, size_t size, uint16_t *dst, size_t words)
{
    size_t in = 0, out = 0;
    while (in < size) {
        uint16_t control;
        size_t count;
        if (size - in < 2) return 0;
        control = word(src + in);
        in += 2;
        count = control & 0x7fff;
        if (!count || count > words - out) return 0;
        if (control & 0x8000) {
            uint16_t value;
            if (size - in < 2) return 0;
            value = word(src + in);
            in += 2;
            while (count--) dst[out++] = value;
        } else {
            if (count > (size - in) / 2) return 0;
            while (count--) {
                dst[out++] = word(src + in);
                in += 2;
            }
        }
    }
    return out == words;
}
