#ifndef V6_SAMPLE_UNPACK_H
#define V6_SAMPLE_UNPACK_H
#include <stdint.h>
/* Boot-only lossless PCM expansion into Chip RAM. Output may be partially
 * written on rejection; callers must discard it and abort startup. */
int v6_sample_unpack(uint8_t *,unsigned,const uint8_t *,unsigned);
/* Packed first differences, modulo 256; reconstruct the identical PCM. */
int v6_sample_unpack_delta(uint8_t *,unsigned,const uint8_t *,unsigned);
/* Resumable exact delta expansion. Back references recover first differences
 * from already reconstructed PCM, requiring no separate history buffer. */
typedef struct {
    uint8_t *out;const uint8_t *in;
    unsigned capacity,size,at,used,flags,bit,remaining,distance,previous,error;
} V6SampleJob;
int v6_sample_job_init(V6SampleJob *,uint8_t *,unsigned,const uint8_t *,unsigned);
/* At most budget output bytes; -1 malformed, 0 pending, 1 complete. */
int v6_sample_job_step(V6SampleJob *,unsigned budget);
#endif
