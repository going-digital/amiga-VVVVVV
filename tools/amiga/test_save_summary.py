#!/usr/bin/env python3
"""Receipt data: original game clock, time formatter and collection count."""
import ctypes as C,random,subprocess
from pathlib import Path
from test_music_control import method
ROOT=Path(__file__).resolve().parents[2]
class Clock(C.Structure):_fields_=[(n,C.c_uint16) for n in ('hours','minutes','seconds','frames')]
class Summary(C.Structure):
 _fields_=[('clock',Clock),('room_x',C.c_int16),('room_y',C.c_int16)]+[(n,C.c_uint16) for n in ('trinkets','crew_mask','exists')]
def main():
 out=ROOT/'build/amiga-save-summary';out.mkdir(parents=True,exist_ok=True)
 source=(ROOT/'desktop_version/src/Game.cpp').read_text()
 clock=method(source,'void Game::gameclock(');count=method(source,'int Game::trinkets(')
 formatter=method((ROOT/'desktop_version/src/UtilityClass.cpp').read_text(),'void UtilityClass::format_time(')
 shim='''#include <cstdio>
#include <cstddef>
#include <cstring>
#include "save_summary.h"
#define SDL_arraysize(a) (sizeof(a)/sizeof(a[0]))
struct {bool collect[100];} obj;
struct Game {int hours,minutes,seconds,frames,timetrialcountdown;void gameclock();int trinkets();} game;
struct UtilityClass {void format_time(char*,size_t,int,int,bool);} help;
namespace loc {const char *gettext(const char *s){return s;}}
void vformat_buf(char *b,size_t n,const char *format,const char*,int a,int c,int d=0,int e=0){
 (void)e;
 if(std::strstr(format,"hrs"))std::snprintf(b,n,"%d:%02d:%02d",a,c,d);
 else std::snprintf(b,n,"%d:%02d",a,c);
}
'''+clock+count+formatter+'''
extern "C" void reference_tick(V6SaveClock *c,int countdown){
 game.hours=c->hours;game.minutes=c->minutes;game.seconds=c->seconds;game.frames=c->frames;
 game.timetrialcountdown=countdown;game.gameclock();
 c->hours=game.hours;c->minutes=game.minutes;c->seconds=game.seconds;c->frames=game.frames;}
extern "C" void reference_text(char *out,const V6SaveClock *c){help.format_time(out,12,c->hours*3600+c->minutes*60+c->seconds,-1,true);}
extern "C" unsigned reference_count(const unsigned char *bits){for(unsigned i=0;i<100;++i)obj.collect[i]=bits[i/8]&(1<<(i%8));return game.trinkets();}
'''
 (out/'reference.cpp').write_text(shim)
 flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
 subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/save_summary.c'),'-o',str(out/'summary.so')],check=True)
 subprocess.run(['c++','-std=c++11',*flags,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
 lib=C.CDLL(str(out/'summary.so'));ref=C.CDLL(str(out/'reference.so'))
 for fn in (lib.v6_save_clock_tick,ref.reference_tick):fn.argtypes=[C.POINTER(Clock),C.c_int]
 for fn in (lib.v6_save_clock_text,ref.reference_text):fn.argtypes=[C.c_char_p,C.POINTER(Clock)]
 lib.v6_save_summary_capture.argtypes=[C.POINTER(Summary),C.POINTER(Clock),C.c_int,C.c_int,C.POINTER(C.c_uint8),C.c_uint]
 lib.v6_save_summary_publish.argtypes=[C.POINTER(Summary),C.POINTER(Summary),C.c_int]
 ref.reference_count.argtypes=[C.POINTER(C.c_uint8)]
 rng=random.Random(443501);clocks=[]
 for h in (0,1,65534):
  for m in (0,1,58,59):
   for s in (0,1,58,59):
    for f in (0,1,28,29):clocks.append(Clock(h,m,s,f))
 clocks += [Clock(rng.randrange(65535),rng.randrange(60),rng.randrange(60),rng.randrange(30)) for _ in range(2048)]
 for original in clocks:
  for countdown in (-1,0,1):
   a=Clock.from_buffer_copy(original);b=Clock.from_buffer_copy(original)
   assert lib.v6_save_clock_tick(C.byref(a),countdown);ref.reference_tick(C.byref(b),countdown)
   assert bytes(a)==bytes(b)
  a=C.create_string_buffer(12);b=C.create_string_buffer(12)
  assert lib.v6_save_clock_text(a,C.byref(original));ref.reference_text(b,C.byref(original));assert a.value==b.value
 for bad in [Clock(0,60,0,0),Clock(0,0,60,0),Clock(0,0,0,30),Clock(65535,59,59,29)]:
  before=bytes(bad);assert not lib.v6_save_clock_tick(C.byref(bad),0) and bytes(bad)==before
 collections=[bytes(13),bytes([255]*12+[15])]+[bytes((1<<(i%8)) if b==i//8 else 0 for b in range(13)) for i in range(100)]
 collections += [rng.randbytes(12)+bytes([rng.randrange(16)]) for _ in range(128)]
 c=Clock(1,2,3,4);last=Summary();candidate=Summary()
 for raw in collections:
  bits=(C.c_uint8*13).from_buffer_copy(raw)
  for crew in range(64):
   assert lib.v6_save_summary_capture(C.byref(candidate),C.byref(c),112,107,bits,crew)
   assert candidate.trinkets==ref.reference_count(bits) and candidate.crew_mask==crew and candidate.exists==1
   assert bytes(candidate.clock)==bytes(c)
   before=bytes(last);assert not lib.v6_save_summary_publish(C.byref(last),C.byref(candidate),0) and bytes(last)==before
   assert lib.v6_save_summary_publish(C.byref(last),C.byref(candidate),1) and bytes(last)==bytes(candidate)
 bits=(C.c_uint8*13)();before=bytes(candidate)
 for x,y,crew in ((99,107,1),(120,107,1),(112,99,1),(112,120,1),(112,107,64)):
  assert not lib.v6_save_summary_capture(C.byref(candidate),C.byref(c),x,y,bits,crew) and bytes(candidate)==before
 bits[12]=16;assert not lib.v6_save_summary_capture(C.byref(candidate),C.byref(c),112,107,bits,1) and bytes(candidate)==before
 print(f'PASS Save summary: {len(clocks)*3} original clock updates, {len(clocks)} original formatted times, {len(collections)*64} source counts/snapshots and failure-preserving publishes (UBSan)')
if __name__=='__main__':main()
