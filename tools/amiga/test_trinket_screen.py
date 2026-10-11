#!/usr/bin/env python3
"""Pickup controller compared with the original Game.cpp state cases."""
import ctypes as C
import random
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIELDS = 'state delay control stopped bars advance visible count'.split()

class Screen(C.Structure):
    _fields_ = [(name, C.c_int) for name in FIELDS]

class Bank(C.Structure):
    _fields_ = [('bits', C.c_ubyte * 13)]

def main():
    out = ROOT / 'build/amiga-trinket-screen'
    out.mkdir(parents=True, exist_ok=True)
    game = (ROOT / 'desktop_version/src/Game.cpp').read_text()
    cases = game[game.index('        case 1000:'):game.index('        case 1010:')]
    inp = (ROOT / 'desktop_version/src/Input.cpp').read_text()
    start = inp.index('                if (GlitchrunnerMode_less_than_or_equal(Glitchrunner2_0)')
    end = inp.index('            }', inp.index('                    game.glitchrunkludge=true;', start))
    advance = inp[start:end]
    reference = r'''
#include "trinket_screen.h"
#define TEXT_COLOUR(x) 0
#define TEXTTRANSLATE_FUNCTION 0
#define PR_FONT_INTERFACE 0
#define Glitchrunner2_0 0
bool GlitchrunnerMode_less_than_or_equal(int) {return false;}
int foundtrinket_textbox1,foundtrinket_textbox2;
struct Graphics {
 bool showcutscenebars=false,visible=false;
 struct Textboxes {int size(){return 2;}} textboxes;
 void createtextboxflipme(const char*,int,int,int){visible=true;}
 void textboxprintflags(int){} void textboxcenterx(){}
 void textboxtranslate(int,int){} void textboxapplyposition(){}
 void textboxindex(int){} void textboxremove(){visible=false;}
} graphics;
struct Music {int currentsong=-1,fade=0;
 void fadeMusicVolumeIn(int ms){fade=ms;}
} music;
struct Game {
 int state=0,statedelay=0;bool hascontrol=true,completestop=false;
 bool advancetext=false,jumpheld=false,glitchrunkludge=false;
 void incstate(){++state;}void setstate(int s){state=s;}
 void setstatedelay(int n){statedelay=n;}void unlockstate(){}
 void tick(){
   --statedelay;
   if(statedelay<=0){statedelay=0;glitchrunkludge=false;
     switch(state){CASES}
   }
 }
} game;
extern "C" {
 void reset(){game=Game();graphics=Graphics();music=Music();}
 void begin(int present){game.state=1000;music.currentsong=present?0:-1;}
 void clear_advance(){game.advancetext=false;}
 int input(int action,int held){
   game.jumpheld=held;
   if(game.advancetext && action && !game.jumpheld){ADVANCE return 1;}
   return 0;
 }
 unsigned tick(int present){
   music.currentsong=present?0:-1;music.fade=0;
   bool before=graphics.visible;game.tick();
   return (!before&&graphics.visible?1:0)|(before&&!graphics.visible?2:0)
     |(music.fade==3000?16:0);
 }
 void read(V6TrinketScreen *s){
   s->state=game.state;s->delay=game.statedelay;s->control=game.hascontrol;
   s->stopped=game.completestop;s->bars=graphics.showcutscenebars;
   s->advance=game.advancetext;s->visible=graphics.visible;
 }
}
'''.replace('CASES', cases).replace('ADVANCE', advance)
    path = out / 'reference.cpp'
    path.write_text(reference)
    subprocess.run(['c++', '-std=c++11', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                    '-I'+str(ROOT/'amiga_version'), str(path), '-o', str(out/'reference.so')], check=True)
    subprocess.run(['cc', '-std=c99', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                    '-I'+str(ROOT/'amiga_version'), str(ROOT/'amiga_version/trinket_screen.c'),
                    *(str(ROOT/'amiga_version'/name) for name in ('trinkets.c', 'player.c', 'terrain.c', 'blocks.c')),
                    '-o', str(out/'core.so')], check=True)
    core, ref = C.CDLL(str(out/'core.so')), C.CDLL(str(out/'reference.so'))
    core.v6_trinket_screen_init.argtypes = [C.POINTER(Screen)]
    core.v6_trinket_screen_begin.argtypes = [C.POINTER(Screen), C.POINTER(Bank), C.c_int]
    core.v6_trinket_screen_input.argtypes = [C.POINTER(Screen), C.c_int, C.c_int]
    core.v6_trinket_screen_tick.argtypes = [C.POINTER(Screen), C.c_int]
    ref.read.argtypes = [C.POINTER(Screen)]
    rng = random.Random(1003)
    ticks = 0
    for trial in range(256):
        state, expected, bank = Screen(), Screen(), Bank()
        ids = rng.sample(range(100), trial % 101)
        for ident in ids:
            bank.bits[ident//8] |= 1 << (ident%8)
        core.v6_trinket_screen_init(C.byref(state)); ref.reset()
        music = trial % 2
        assert core.v6_trinket_screen_begin(C.byref(state), C.byref(bank), music) == 8 | (4 if music else 0)
        assert state.count == len(ids)
        ref.begin(music)
        held = trial % 2
        for tick in range(128):
            # Held pickup action, early presses, release/repress and music
            # disappearing during the screen; then a second pickup cycle.
            action = 1 if tick < 20 else rng.randrange(2)
            consumed = core.v6_trinket_screen_input(C.byref(state), action, held)
            assert consumed == ref.input(action, held)
            if consumed: held = 1
            if not action: held = 0
            present = music if tick < 25 else rng.randrange(2)
            assert core.v6_trinket_screen_tick(C.byref(state), present) == ref.tick(present)
            ref.read(C.byref(expected))
            assert all(getattr(state, f) == getattr(expected, f) for f in FIELDS[:-1]), (trial, tick)
            if tick == 0: assert state.stopped and state.delay == 15 and not state.visible
            if tick == 14: assert not state.visible
            if tick == 15: assert state.visible and state.state == 1002
            if tick == 80:
                assert state.state == 0
                core.v6_trinket_screen_begin(C.byref(state), C.byref(bank), music); ref.begin(music)
            ticks += 1
    # Source state 1002 recovers on the following update if advancement was
    # unexpectedly cleared; it must not leave the player permanently frozen.
    core.v6_trinket_screen_init(C.byref(state)); ref.reset()
    core.v6_trinket_screen_begin(C.byref(state), C.byref(bank), 1); ref.begin(1)
    for _ in range(16):
        assert core.v6_trinket_screen_tick(C.byref(state), 1) == ref.tick(1)
    state.advance = 0; ref.clear_advance()
    for _ in range(2):
        assert core.v6_trinket_screen_tick(C.byref(state), 1) == ref.tick(1)
        ref.read(C.byref(expected))
        assert all(getattr(state, f) == getattr(expected, f) for f in FIELDS[:-1])
    assert state.control and not state.stopped and not state.visible
    print(f'PASS pickup screen: {ticks} source differential ticks, held action, 15-tick delay, repeated pickups, complete bank count and music fade')

if __name__ == '__main__':
    main()
