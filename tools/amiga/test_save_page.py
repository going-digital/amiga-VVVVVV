#!/usr/bin/env python3
"""Save-page display precedence against the original Render.cpp branches."""
import ctypes as C
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
class Page(C.Structure):
 _fields_=[(n,C.c_uint) for n in ('state','autosave_note','last_summary')]
def main():
 out=ROOT/'build/amiga-save-page';out.mkdir(parents=True,exist_ok=True)
 source=(ROOT/'desktop_version/src/Render.cpp').read_text()
 start=source.index('        if (game.inintermission || game.translator_exploring)')
 body=source[start:source.index('        graphics.drawpixeltextbox(17, 65, 286, 90',start)]
 shim='''#include <string>
#include <cstring>
#include "save_page.h"
#define FLIP(y,h) (y)
const int PR_CEN=1,SCREEN_WIDTH_CHARS=40,ActionSet_InGame=0,Action_InGame_ACTION=0;
struct Game {bool inintermission,translator_exploring,nodeathmode,intimetrial,insecretlab,gamesavefailed,gamesaved;
 struct Summary {bool exists;int saverx=112,savery=107,hours=0,minutes=0,seconds=0;} last_quicksave;
 std::string giventimestring(int,int,int){return "0:00";}
} game;
struct Map {bool custommode;const char *currentarea(int,int){return "Space Station";}} map;
struct {int glow=0;} help;
namespace loc {const char *gettext(const char *s){return s;}const char *gettext_roomname_special(const char *s){return s;}}
const char *vformat_button(int,int){return "Space";}
void vformat_buf(char *b,unsigned n,const char*,...){std::strncpy(b,"prompt",n);}
static V6SavePage result;static const char *message;
namespace font {
void print(int,int,int y,const char *s,int,int,int){if(y==100)result.last_summary=1;(void)s;}
void print_wrap(int,int,int y,const char *s,int,int,int,int=0){
 if(y==174){result.autosave_note=1;return;}
 message=s;
 if(y==36)result.state=V6_SAVE_PAGE_RECEIPT;
 else if(std::strcmp(s,"Cannot Save in Level Replay")==0)result.state=V6_SAVE_PAGE_REPLAY;
 else if(std::strcmp(s,"Cannot Save in No Death Mode")==0)result.state=V6_SAVE_PAGE_NODEATH;
 else if(std::strcmp(s,"How'd you get here?")==0)result.state=V6_SAVE_PAGE_TIMETRIAL;
 else if(std::strcmp(s,"Cannot Save in Secret Lab")==0)result.state=V6_SAVE_PAGE_SECRETLAB;
 else if(std::strcmp(s,"ERROR: Could not save game!")==0)result.state=V6_SAVE_PAGE_FAILED;
}}
extern "C" V6SavePage reference(unsigned f){
 game.inintermission=f&1;game.translator_exploring=f&2;game.nodeathmode=f&4;
 game.intimetrial=f&8;game.insecretlab=f&16;game.gamesavefailed=f&32;
 game.gamesaved=f&64;map.custommode=f&128;game.last_quicksave.exists=f&256;
 result={0,0,0};message=nullptr;
 do {
'''+body+'''
 } while(false);
 return result;
}
extern "C" const char *reference_message(){return message;}
'''
 (out/'reference.cpp').write_text(shim)
 flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
 subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/save_page.c'),'-o',str(out/'page.so')],check=True)
 subprocess.run(['c++','-std=c++11',*flags,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
 lib=C.CDLL(str(out/'page.so'));ref=C.CDLL(str(out/'reference.so'))
 lib.v6_save_page.argtypes=[C.c_uint];lib.v6_save_page.restype=Page
 ref.reference.argtypes=[C.c_uint];ref.reference.restype=Page
 lib.v6_save_page_message.argtypes=[C.c_uint];lib.v6_save_page_message.restype=C.c_char_p
 ref.reference_message.restype=C.c_char_p
 for flags in range(512):
  a=lib.v6_save_page(flags);b=ref.reference(flags)
  assert bytes(a)==bytes(b),(flags,list(bytes(a)),list(bytes(b)))
  assert lib.v6_save_page_message(a.state)==ref.reference_message(),flags
 print('PASS Save page: all 512 original renderer flag combinations and message strings (UBSan)')
if __name__=='__main__':main()
