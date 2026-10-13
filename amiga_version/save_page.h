#ifndef V6_SAVE_PAGE_H
#define V6_SAVE_PAGE_H
#include <stdint.h>
#define V6_SAVE_BITMAP_BYTES 28800U
enum {
    V6_SAVE_PAGE_PROMPT,V6_SAVE_PAGE_RECEIPT,V6_SAVE_PAGE_REPLAY,
    V6_SAVE_PAGE_NODEATH,V6_SAVE_PAGE_TIMETRIAL,V6_SAVE_PAGE_SECRETLAB,
    V6_SAVE_PAGE_FAILED
};
enum {
    V6_SAVE_PAGE_IN_REPLAY=1,V6_SAVE_PAGE_EXPLORING=2,
    V6_SAVE_PAGE_NO_DEATH=4,V6_SAVE_PAGE_TIME_TRIAL=8,
    V6_SAVE_PAGE_SECRET_LAB=16,V6_SAVE_PAGE_ERROR=32,
    V6_SAVE_PAGE_SAVED=64,V6_SAVE_PAGE_CUSTOM=128,
    V6_SAVE_PAGE_LAST_EXISTS=256
};
typedef struct {unsigned state,autosave_note,last_summary;} V6SavePage;
/* Render policy only: source Render.cpp page 3, independent of save I/O.
 * Custom/special rendering and summary contents remain caller-owned. */
V6SavePage v6_save_page(unsigned flags);
const char *v6_save_page_message(unsigned state);
/* Packed count/byte stream; validate full length before writing Chip RAM. */
int v6_save_page_unpack(uint8_t *,const uint8_t *,unsigned);
#endif
