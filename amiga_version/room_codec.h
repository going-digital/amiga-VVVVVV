#ifndef V6_ROOM_CODEC_H
#define V6_ROOM_CODEC_H
#include <stddef.h>
#include <stdint.h>
/* Big-endian packet: bit 15 = repeated word, bits 0..14 = word count.
 * Otherwise count literal words follow. Exact input/output lengths required. */
int v6_unpack_room(const uint8_t *src, size_t size, uint16_t *dst, size_t words);
#endif
