#!/usr/bin/env python3
"""Streamed tower player physics/spikes versus extracted desktop methods."""
import ctypes as C
import json
import re
import subprocess
from test_player import ROOT, BUILD, Player, Room, FIELDS, original_reference, block
from test_tower_stream import Stream
from probe_feasibility import tower_probe

OUT=ROOT/'build/amiga-tower-player'
READ=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_int,C.c_int)
class Tiles(C.Structure):
    _fields_=[('read',READ),('context',C.c_void_p),('invincible',C.c_int),('walls',C.c_void_p)]

def libraries():
    OUT.mkdir(parents=True,exist_ok=True);BUILD.mkdir(parents=True,exist_ok=True)
    original_reference()
    shim=(ROOT/'tools/amiga/reference_shim.h').read_text()
    tower=(ROOT/'desktop_version/src/Tower.cpp').read_text()
    methods='\n'.join(block(tower,tower.index('int towerclass::'+name+'(')) for name in ('at','miniat'))
    definition='''#define POS_MOD(x,n) ((((x)%(n))+(n))%(n))
struct towerclass { bool minitowermode; int contents[28000],minitower[4000];
int at(int,int,int); int miniat(int,int,int); };\n'''+methods+'\n'
    shim=shim.replace('struct mapclass {',definition+'struct mapclass {')
    shim=shim.replace('struct Tower { int at(int, int, int) { std::abort(); } } tower;','towerclass tower;\n    bool towerspikecollide(int,int);')
    shim=shim.replace('bool checkdamage(bool scm = false);','bool checkdamage(bool scm = false);\n    bool checktowerspikes(int);')
    (OUT/'tower_shim.h').write_text(shim)
    code=(BUILD/'player_reference.cpp').read_text().replace('#include "reference_shim.h"','#include "tower_shim.h"')
    entity=(ROOT/'desktop_version/src/Entity.cpp').read_text();maps=(ROOT/'desktop_version/src/Map.cpp').read_text()
    code+='\n'+block(entity,entity.index('bool entityclass::checktowerspikes('))
    code+='\n'+block(maps,maps.index('bool mapclass::towerspikecollide('))
    code+='''
extern "C" void tower_init(const V6Player *p,const uint16_t *tiles,int height,int invincible) {
uint16_t empty[1200]={}; reference_init(p,empty,2,0);
map.towermode=true; map.invincibility=invincible;map.tower.minitowermode=height==100;
for(int i=0;i<height*40;++i) {
if(height==100) map.tower.minitower[i]=tiles[i];else map.tower.contents[i]=tiles[i];
}
}
extern "C" int tower_hurt() { return obj.checktowerspikes(0); }
extern "C" void ordinary_init(const V6Player *p,const uint16_t *tiles) {
map.towermode=false;map.invincibility=false;reference_init(p,tiles,2,0);
}
'''
    (OUT/'reference.cpp').write_text(code)
    flags=['-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['c++','-std=c++11',*flags,'-I/opt/homebrew/include','-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),str(OUT/'reference.cpp'),'-L/opt/homebrew/lib','-lSDL3','-o',str(OUT/'reference.so')],check=True)
    subprocess.run(['cc','-std=c99',*flags,'-Wall','-Wextra','-Werror',*[str(ROOT/'amiga_version'/f) for f in ('player.c','blocks.c','tower_stream.c','room_codec.c','tower_session.c','tower_camera.c','checkpoints.c','tower_gameplay.c','tower_route.c','teleporter.c','hallway_crew.c','hallway_trigger.c','rescue_script.c','companion.c','animation.c','terrain.c')],'-o',str(OUT/'core.so')],check=True)
    core=C.CDLL(str(OUT/'core.so'));ref=C.CDLL(str(OUT/'reference.so'))
    core.v6_tower_open.argtypes=[C.POINTER(Stream),C.c_char_p,C.c_size_t]
    core.v6_player_tower_room.argtypes=[C.POINTER(Room),C.POINTER(Tiles)]
    core.v6_player_init.argtypes=[C.POINTER(Player),C.c_int,C.c_int,C.c_int]
    core.v6_player_step.argtypes=[C.POINTER(Player),C.POINTER(Room),C.c_uint]
    core.v6_player_hurt.argtypes=[C.POINTER(Player),C.POINTER(Room)]
    ref.tower_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16),C.c_int,C.c_int]
    ref.reference_read.argtypes=[C.POINTER(Player)]
    return core,ref

def main():
    core,ref=libraries();tower_probe(OUT)
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text();ticks=0;hazards=0
    reader=READ(('v6_tower_tile',core))
    for name in ('loadmap','loadminitower1','loadminitower2'):
        raw=source[source.index('void towerclass::'+name+'('):]
        raw=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',raw,re.S)[1]
        raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
        values=[int(v) for v in raw.split(',') if v.strip()];height=len(values)//40
        data=(C.c_uint16*len(values))(*values);blob=(OUT/(name+'.v6tr')).read_bytes()
        stream=Stream();assert core.v6_tower_open(C.byref(stream),blob,len(blob))
        for mode in range(4):
            invincible=mode&1
            tiles=Tiles(reader,C.addressof(stream),invincible);room=Room()
            if mode&2: tiles.walls=C.cast(core.v6_tower_walls,C.c_void_p).value
            core.v6_player_tower_room(C.byref(room),C.byref(tiles))
            for row in range(-4,height+4,7):
                for gravity in (0,1):
                    p=Player();expected=Player();core.v6_player_init(C.byref(p),144,row*8,gravity)
                    ref.tower_init(C.byref(p),data,height,invincible)
                    for tick in range(48):
                        buttons=(1 if tick<16 else 2 if tick<32 else 0)|(4 if tick%11<3 else 0)
                        ref.reference_step(buttons);core.v6_player_step(C.byref(p),C.byref(room),buttons)
                        ref.reference_read(C.byref(expected))
                        assert bytes(p)==bytes(expected),(name,row,gravity,tick,[(f,getattr(p,f),getattr(expected,f)) for f in FIELDS if getattr(p,f)!=getattr(expected,f)])
                        assert core.v6_player_hurt(C.byref(p),C.byref(room))==ref.tower_hurt()
                        ticks+=1
            # Probe every source tile, including duplicated horizontal edges.
            for row in range(height):
                for x in (-8,0,144,304,312,320):
                    p=Player();core.v6_player_init(C.byref(p),x,row*8-3,0)
                    ref.tower_init(C.byref(p),data,height,invincible)
                    assert core.v6_player_hurt(C.byref(p),C.byref(room))==ref.tower_hurt(),(name,row,x)
                    hazards+=1
    report=dict(ticks=ticks,hazard_cases=hazards,scope='Source-extracted tower movement and spike probes; main and both mini maps, signed positions, invincibility; no full entity loop')
    (OUT/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
