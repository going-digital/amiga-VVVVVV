#!/usr/bin/env python3
"""Bounded normal map controls versus the desktop Input.cpp statements."""
import ctypes as C
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
class Menu(C.Structure):
    _fields_=[(n,C.c_uint) for n in 'open mapheld jumpheld saved failed save_pending'.split()]+[('page',C.c_int)]
def main():
    out=ROOT/'build/amiga-map-menu';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'desktop_version/src/Input.cpp').read_text()
    opening=source[source.index('//Normal map screen, do transition later',source.index('bool enter_pressed')):source.index('    if (!game.mapheld\n',source.index('bool enter_pressed'))]
    assert 'game.gamesaved = false;' in opening and 'game.gamesavefailed = false;' in opening
    assert 'game.menupage = 3;' in opening and 'game.menupage = 0;' in opening
    assert 'savequick' not in opening
    # Use the final menu input block, including action-before-tab-wrap ordering.
    start=source.index('    if (!game.mapheld)\n    {\n        if(game.press_map')
    end=source.index('\n}\n\nstatic void mapmenuactionpress',start)
    navigation=source[start:end]
    action_start=source.index('    if (!game.gamesaved && !game.gamesavefailed && !game.inspecial())',end)
    action_end=source.index('\n        break;',action_start)
    action=source[action_start:action_end]
    shim='''#include "map_menu.h"
struct Game {bool mapheld,jumpheld,press_map,press_action,press_left,press_right;
 int menupage,flashlight,screenshake,savetime,savetrinkets;
 bool gamesaved,gamesavefailed,special,success;int attempts;
 bool inspecial(){return special;}int timestring(){return 0;}int trinkets(){return 0;}
 bool savequick(){++attempts;return success;}bool customsavequick(int){return savequick();}
} game;
struct Script {bool running;} script;
struct Graphics {bool resumegamemode;} graphics;
struct Map {bool custommodeforreal;} map;
struct Meta {int filename;};struct CL {Meta ListOfMetaData[1];} cl;
struct Music {void playef(int){}} music;
const int Sound_GAMESAVED=1;
void mapmenuactionpress(bool){if(game.menupage==3){'''+action+'''}}
extern "C" void reference(V6MapMenu *m,unsigned b,int running,int special,int success){
 game.mapheld=m->mapheld;game.jumpheld=m->jumpheld;game.menupage=m->page;
 game.gamesaved=m->saved;game.gamesavefailed=m->failed;game.special=special;
 game.success=success;game.attempts=0;script.running=running;
 game.press_map=b&1;game.press_left=b&2;game.press_right=b&4;game.press_action=b&8;
 graphics.resumegamemode=false;bool version2_2=true;
 if(!game.press_action&&!game.press_left&&!game.press_right)game.jumpheld=false;
 if(!game.press_map)game.mapheld=false;
'''+navigation+'''
 m->open=!graphics.resumegamemode;m->mapheld=game.mapheld;m->jumpheld=game.jumpheld;
 m->page=game.menupage;m->saved=game.gamesaved;m->failed=game.gamesavefailed;
 m->save_pending=game.attempts;
}
'''
    # Stub fields used by the extracted Save tab action.
    shim=shim.replace('int menupage,flashlight','int playcustomlevel=0;int menupage,flashlight')
    (out/'reference.cpp').write_text(shim)
    common=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version')]
    subprocess.run(['cc','-std=c99',*common,str(ROOT/'amiga_version/map_menu.c'),'-o',str(out/'menu.so')],check=True)
    subprocess.run(['c++','-std=c++11',*common,str(out/'reference.cpp'),'-o',str(out/'reference.so')],check=True)
    lib=C.CDLL(str(out/'menu.so'));ref=C.CDLL(str(out/'reference.so'))
    lib.v6_map_menu_tick.argtypes=[C.POINTER(Menu),C.c_uint,C.c_int,C.c_int,C.c_int,C.c_int]
    ref.reference.argtypes=[C.POINTER(Menu),C.c_uint,C.c_int,C.c_int,C.c_int]
    lib.v6_map_menu_save_result.argtypes=[C.POINTER(Menu),C.c_int]
    count=0
    for page in range(4):
      for latches in range(4):
       for status in range(3):
        for buttons in range(16):
         for running in range(2):
          for special in range(2):
           for success in range(2):
            a=Menu(1,latches&1,latches>>1,status==1,status==2,0,page)
            r=Menu.from_buffer_copy(a)
            event=lib.v6_map_menu_tick(C.byref(a),buttons,1,0,running,special)
            ref.reference(C.byref(r),buttons,running,special,success)
            assert (event==4)==bool(r.save_pending)
            if event==4:lib.v6_map_menu_save_result(C.byref(a),success)
            r.save_pending=0
            assert bytes(a)==bytes(r),(page,latches,status,buttons,running,special,success,list(bytes(a)),list(bytes(r)))
            count+=1
    # Opening, transition holds, disabled interaction, and asynchronous saves.
    for running in range(2):
      m=Menu()
      assert lib.v6_map_menu_tick(C.byref(m),1,0,0,running,0)==0
      assert lib.v6_map_menu_tick(C.byref(m),1,1,0,running,0)==1
      assert m.page==(3 if running else 0) and not m.save_pending
      for _ in range(120):assert lib.v6_map_menu_tick(C.byref(m),15,1,1,running,0)==0
      assert m.open and not m.saved
      lib.v6_map_menu_tick(C.byref(m),0,1,0,running,0)
      assert lib.v6_map_menu_tick(C.byref(m),1,1,0,running,0)==3
      assert lib.v6_map_menu_tick(C.byref(m),1,1,1,running,0)==0
      assert lib.v6_map_menu_tick(C.byref(m),1,1,0,running,0)==0
    m=Menu(1,0,0,0,0,0,3)
    assert lib.v6_map_menu_tick(C.byref(m),8,1,0,0,0)==4
    for _ in range(100):
      lib.v6_map_menu_tick(C.byref(m),0,1,0,0,0)
      assert lib.v6_map_menu_tick(C.byref(m),8,1,0,0,0)!=4
    lib.v6_map_menu_save_result(C.byref(m),0)
    assert m.failed and not m.save_pending
    lib.v6_map_menu_save_result(C.byref(m),1)
    assert m.failed and not m.saved  # unsolicited completion is ignored
    print(f'PASS map menu: {count} desktop comparisons; opening, transition/release gates and asynchronous save protection')
if __name__=='__main__':main()
