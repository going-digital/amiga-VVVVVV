#ifndef V6_KEYBOARD_H
#define V6_KEYBOARD_H
#include <stdint.h>
/* Raw CIA-A SDR decoder. Physical keys remain separate so releasing one
 * of two bound keys cannot release the other. Hardware/OS ownership belongs
 * to the caller; this core never accesses registers. */
typedef struct { uint8_t down[16]; } V6Keyboard;
void v6_keyboard_init(V6Keyboard *);
unsigned v6_keyboard_decode(unsigned serial);
void v6_keyboard_receive(V6Keyboard *,unsigned serial);
unsigned v6_keyboard_map_buttons(const V6Keyboard *);
#endif
