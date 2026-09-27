#!/usr/bin/env python3
"""Compile original method bodies as an independent float reference for the port."""
import ctypes as C
import hashlib
import json
from pathlib import Path
import random
import re
import struct
import subprocess

from pack_rooms import ROOT, extract

BUILD = ROOT / 'build/amiga'
FIELDS = 'x y old_x old_y vx vy ay ground roof tap_left tap_right held buffer gravity dir flips'.split()


class Player(C.Structure):
    _fields_ = [(name, C.c_int32) for name in FIELDS]


class Terrain(C.Structure):
    _fields_ = [('solid', (C.c_uint8*64)*32), ('directional', C.c_int)]

class DynamicBlock(C.Structure):
    _fields_ = [(name,C.c_int) for name in "x y w h type trigger".split()]

class Room(C.Structure):
    _fields_ = [('tiles', C.POINTER(C.c_uint16)), ('tileset', C.c_int), ('extra_row', C.c_int), ('terrain', C.POINTER(Terrain)), ('blocks',C.POINTER(DynamicBlock)), ('block_count',C.c_uint)]


def block(text, start):
    """Find a balanced source block, ignoring comments and quoted strings."""
    tokens = re.finditer(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\{|\}', text[start:], re.S)
    depth = 0
    for m in tokens:
        if m[0] == '{': depth += 1
        if m[0] == '}':
            depth -= 1
            if depth == 0: return text[start:start + m.end()]
    raise ValueError('Unbalanced source')


def original_reference():
    entity = (ROOT / 'desktop_version/src/Entity.cpp').read_text()
    maps = (ROOT / 'desktop_version/src/Map.cpp').read_text()
    inp = (ROOT / 'desktop_version/src/Input.cpp').read_text()
    methods = ['getgridpoint', 'checkblocks', 'checkwall', 'entitycollidefloor',
               'entitycollideroof', 'testwallsx', 'testwallsy', 'applyfriction',
               'updateentitylogic', 'entitymapcollision', 'checkdamage']
    chunks = ['#include "reference_shim.h"\n']
    for name in methods:
        pattern = r'^(?:static )?(?:int|bool|void) (?:entityclass::)?' + name + r'\([^\n]*\)\s*\n\{'
        matches = list(re.finditer(pattern, entity, re.M))
        assert len(matches) == (2 if name == 'checkwall' else 1), name
        chunks += [block(entity, m.start()) for m in matches]
    m = re.search(r'^bool mapclass::collide\(', maps, re.M)
    chunks.append(block(maps, m.start()))
    start = inp.index('void gameinput(void)')
    movement = inp.index('if(game.press_left)', start)
    # Include both movement branches verbatim.
    move_end = inp.index('\n            }', movement)
    movement_body = inp[movement:move_end]
    controls = inp.index('if (has_control)', move_end)
    chunks.append('''extern "C" void reference_step(unsigned input) {
        game.press_left = input & V6_LEFT;
        game.press_right = input & V6_RIGHT;
        game.press_action = input & V6_FLIP;
        const bool has_control = !(input & V6_NO_CONTROL);
        if (has_control) { const size_t ie = 0;
        ''' + movement_body + '\n}\n' + block(inp, controls) + '''
        entclass& e = obj.entities[0];
        if (obj.entitycollidefloor(0)) e.onground = 2; else --e.onground;
        if (obj.entitycollideroof(0)) e.onroof = 2; else --e.onroof;
        obj.updateentitylogic(0);
        obj.entitymapcollision(0);
    }
    ''')
    # Original spike rectangles from Map.cpp, changing only createblock storage.
    spike_start = maps.index('if(tileset==0)', maps.index('//The room\'s loaded:'))
    spike_end = maps.index('//Breakable blocks', spike_start)
    spike = maps[spike_start:spike_end]
    chunks.append('''extern "C" int reference_hurt(void) {
        obj.blocks.clear();
        const int tileset = map.tileset;
        for (int j=0; j<29+map.extrarow; ++j) for (int i=0; i<40; ++i) {
            int tile = map.contents[j*40+i];
    ''' + spike.replace('obj.createblock(2,', 'add_damage(') + '''
        }
        return obj.checkdamage();
    }
    ''')
    chunks.insert(1, '''static void add_damage(int x,int y,int w,int h) {
        blockclass b = {DAMAGE, 0, {x,y,w,h}}; obj.blocks.push_back(b);
    }
    ''')
    code = '\n'.join(chunks)
    (BUILD / 'player_reference.cpp').write_text(code)
    return hashlib.sha256(code.encode()).hexdigest()


def build_libraries():
    BUILD.mkdir(parents=True, exist_ok=True)
    digest = original_reference()
    subprocess.run(['c++', '-std=c++11', '-O2', '-fno-fast-math', '-shared', '-fPIC',
                    '-I/opt/homebrew/include', '-I' + str(ROOT/'desktop_version/src'),
                    '-I' + str(ROOT/'amiga_version'), '-I' + str(ROOT/'tools/amiga'),
                    str(BUILD/'player_reference.cpp'), '-L/opt/homebrew/lib', '-lSDL3',
                    '-o', str(BUILD/'player_reference.so')], check=True)
    subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                    str(ROOT/'amiga_version/player.c'), str(ROOT/'amiga_version/terrain.c'), '-o', str(BUILD/'player.so')], check=True)
    core, ref = C.CDLL(str(BUILD/'player.so')), C.CDLL(str(BUILD/'player_reference.so'))
    core.v6_terrain_build.argtypes = [C.POINTER(Terrain), C.POINTER(Room)]
    core.v6_player_init.argtypes = [C.POINTER(Player), C.c_int, C.c_int, C.c_int]
    core.v6_player_step.argtypes = [C.POINTER(Player), C.POINTER(Room), C.c_uint]
    core.v6_player_hurt.argtypes = [C.POINTER(Player), C.POINTER(Room)]
    ref.reference_init.argtypes = [C.POINTER(Player), C.POINTER(C.c_uint16), C.c_int, C.c_int]
    ref.reference_read.argtypes = [C.POINTER(Player)]
    ref.reference_step.argtypes = [C.c_uint]
    return core, ref, digest


def main():
    core, ref, digest = build_libraries()
    tick_count = 0
    scenarios = 0
    max_velocity_error = 0
    rng = random.Random(0x666666)

    def compare(values, x, y, gravity, sequence, name, tileset=1, extra=1):
        nonlocal tick_count, scenarios, max_velocity_error
        tiles = (C.c_uint16 * 1200)(*values)
        room = Room(tiles, tileset, extra)
        terrain = Terrain(); core.v6_terrain_build(C.byref(terrain),C.byref(room))
        p, expected = Player(), Player()
        core.v6_player_init(C.byref(p), x, y, gravity)
        ref.reference_init(C.byref(p), tiles, tileset, extra)
        cached = Player.from_buffer_copy(p)
        history = []
        for tick, buttons in enumerate(sequence):
            history.append(buttons)
            ref.reference_step(buttons)
            room.terrain=C.pointer(terrain)
            core.v6_player_step(C.byref(cached), C.byref(room), buttons)
            room.terrain=None
            core.v6_player_step(C.byref(p), C.byref(room), buttons)
            ref.reference_read(C.byref(expected))
            for field in FIELDS:
                a, b = getattr(p, field), getattr(expected, field)
                assert getattr(cached,field)==b, (name,tick,field,"cached",getattr(cached,field),b)
                if field in ('vx', 'vy', 'ay'):
                    max_velocity_error = max(max_velocity_error, abs(a-b))
                    assert a == b, (name, tick, field, a, b, history[-20:])
                else:
                    assert a == b, (name, tick, field, a, b, history[-20:])
            tick_count += 1
        scenarios += 1

    # Enclosed room, platform, and a step exercise floor/roof and axis order.
    tiles = [0]*1200
    for y in range(30):
        for x in range(40):
            if x in (0,39) or y in (0,29) or (y==15 and 10<=x<25): tiles[y*40+x] = 80
    for gravity in (0,1):
        for duration in (1,2,3,4,5,15,60):
            compare(tiles,150,100,gravity,[0]*15+[2]*duration+[0]*12+[1]*duration+[0]*12+[4]*40+[0]*10+[4]*40,
                    f'tap-{duration}-gravity-{gravity}')
    # Input storms cover reversals, held fire, buffering, and opposing directions.
    for trial in range(60):
        compare(tiles,40+rng.randrange(200),40+rng.randrange(100),trial&1,
                [rng.randrange(8) for _ in range(400)], f'random-{trial}')
    for trial in range(10):
        compare(tiles,150,100,trial&1,[rng.randrange(16) for _ in range(300)],
                f'control-lock-{trial}')
    # Border truncation and all directional-block orientations.
    for tile in range(14,18):
        scene=tiles.copy()
        for x in range(2,38): scene[15*40+x]=tile
        compare(scene,100,90,0,[0]*25+[4]*35+[0]*20+[4]*35+[2]*40, f'one-way-{tile}')
    for x in (-20,-14,-8,-1,0,302,308,320):
        compare([0]*1200,x,-10,0,[1,2,0,4]*5, f'negative-and-edge-{x}')
    # Real source room geometry, reinitialized between bounded sequences.
    for index,(meta,raw,_) in enumerate(extract()):
        if index%5: continue
        values=struct.unpack('>1200H',raw)
        compare(values,148,104,0,[0,2,2,2,0,4,4,1,1,0]*8, f'room-{index}')
    # Hazard rectangles are compared to original Map.cpp/Entity.cpp methods.
    damage_cases=0
    for tileset in (0,1,2):
        for tile in range(6,80):
            scene=[0]*1200;scene[10*40+10]=tile
            array=(C.c_uint16*1200)(*scene);room=Room(array,tileset,1)
            for y in range(54,94):
                for x in (61,62,63,70,81,82):
                    p=Player();core.v6_player_init(C.byref(p),x,y,0)
                    ref.reference_init(C.byref(p),array,tileset,1)
                    assert core.v6_player_hurt(C.byref(p),C.byref(room))==ref.reference_hurt(), (tileset,tile,x,y)
                    damage_cases+=1
    report=dict(scenarios=scenarios,compared_ticks=tick_count,cached_compared_ticks=tick_count,hazard_cases=damage_cases,
                max_velocity_error_q24=max_velocity_error,reference_sha256=digest,
                scope='Single-player static tile physics/input and spike rectangles; no complete game-loop equivalence.')
    (BUILD/'player-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__ == '__main__': main()
