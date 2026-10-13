#ifndef V6_MAP_TRANSITION_H
#define V6_MAP_TRANSITION_H
/* Normal gameplay menu only; script/teleporter return paths are separate. */
typedef struct {
    unsigned active,closing,previous,offset;
} V6MapTransition;
void v6_map_transition_init(V6MapTransition *t);
void v6_map_transition_open(V6MapTransition *t);
void v6_map_transition_close(V6MapTransition *t);
/* Returns one on the fixed tick that returns to gameplay. */
unsigned v6_map_transition_tick(V6MapTransition *t);
/* Render remainder in milliseconds within the 34ms fixed timestep. */
unsigned v6_map_transition_offset(const V6MapTransition *t,unsigned remainder);
unsigned v6_map_transition_input_locked(const V6MapTransition *t);
#endif
