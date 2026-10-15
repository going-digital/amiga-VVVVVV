#ifndef V6_SAMPLE_UNPACK_H
#define V6_SAMPLE_UNPACK_H
#include <stdint.h>
/* Boot-only lossless PCM expansion into Chip RAM. Output may be partially
 * written on rejection; callers must discard it and abort startup. */
int v6_sample_unpack(uint8_t *,unsigned,const uint8_t *,unsigned);
#endif
