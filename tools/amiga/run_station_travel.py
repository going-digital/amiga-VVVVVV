#!/usr/bin/env python3
"""Yellow companion menu travel and V3 arrival save, including cold return."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import struct
import subprocess
from run_interactive_save import config, EMU, KEYS
from run_tower_probe import diagnostics
from run_menu_travel import verify_travel
from save_disk import create_save_disk, read_record
from test_companion import Companion, bind, state
from test_player import Player, Room, FIELDS
from test_tower_player import libraries
from tower_gameplay_data import building_room, energize_room


def verify_crew(data, returning):
    at = data.index(b'V6YC\0\0\0\1')
    count, size = struct.unpack_from('>2I', data, at+8)
    assert count == 64 and size == C.sizeof(Companion), (count, size)
    # The native struct contains only 32-bit scalars; convert BE to host order.
    words = struct.unpack_from('>'+str(size//4)+'I', data, at+16)
    crew = Companion.from_buffer_copy(struct.pack('='+str(size//4)+'I', *words))
    records = [struct.unpack_from('>14I', data, at+16+size+56*i) for i in range(count)]
    mt = data.index(b'V6MT\0\0\0\1')
    snapshot = struct.unpack_from('>23i', data, mt+12)
    travel = [struct.unpack_from('>36i', data, mt+104+144*i) for i in range(count)]
    core, _ = libraries()
    bind(core)
    core.v6_station_companion_step.argtypes = [C.POINTER(Companion), C.POINTER(Player), C.POINTER(Room), C.c_int, C.c_int, C.c_int]
    core.v6_station_companion_enter.argtypes = [C.POINTER(Companion), C.c_int, C.c_int, C.c_int, C.POINTER(Player)]
    tiles_b = (C.c_uint16*1200)(*building_room())
    tiles_e = (C.c_uint16*1200)(*energize_room()['tiles'])
    rooms = {4: Room(tiles_b, 2, 0), 5: Room(tiles_e, 0, 0)}
    coords = {4: (111, 104), 5: (110, 105)}
    index = 5 if returning else 4
    hero = Player()
    for name, value in zip(FIELDS, snapshot):
        setattr(hero, name, value)
    transitions = []
    for tick, (row, expected) in enumerate(zip(travel, records)):
        core.v6_station_companion_step(C.byref(crew), C.byref(hero), C.byref(rooms[index]), -1, *coords[index])
        hero.x, hero.y, hero.vx, hero.vy, hero.dir = row[23], row[24], row[15], row[16], row[20]
        if row[22] != index:
            index = row[22]
            core.v6_station_companion_enter(C.byref(crew), 7, *coords[index], C.byref(hero))
            transitions.append((tick+1, index, crew.body.x, crew.body.y))
        assert state(crew) == expected, (tick+1, state(crew), expected)
    assert len(transitions) == 1 and transitions[0][0] == 22, transitions
    assert transitions[0][2:] == ((150, 86) if returning else (320, 86)), transitions
    return count*14, transitions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--live', type=Path, required=True)
    args = parser.parse_args()
    build, live = args.build.resolve(), args.live.resolve()
    disk = build/'capture-travel-disk.adf'
    disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf', disk)

    def capture(directory, label, returning=False):
        cfg = config(directory, disk)
        dump = directory/(label+'.bin')
        dump.unlink(missing_ok=True)
        boot = (directory/'tower.adf').read_bytes()
        env = dict(os.environ, COPPERLINE_DBG_AFTER='80', COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
        start = 52 if returning else 45
        inputs = ['--joy-after', str(start), 'down', '200', '--joy-after', str(start), 'fire', '200',
                  '--joy-after', str(start+1), 'left', '200', '--joy-after', str(start+2), 'fire', '200']
        if returning:
            inputs = ['--joy-after', '45', 'fire', '200', '--click-after', '45', 'right', '200', *inputs]
        inputs += ['--click-after', str(start+2.4), 'right', '200',
                   '--click-after', str(start+4.6), 'right', '200',
                   '--click-after', '74', 'left', '200']
        with (directory/(label+'.log')).open('w') as log:
            subprocess.run([EMU, '--config', str(cfg), '--floppy-drives', '2', '--noaudio', *inputs,
                            '--screenshot-after', '81', str(directory/(label+'.png'))],
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
        data = dump.read_bytes()
        display = diagnostics(dump)
        assert display['status'] == 2 and display['error'] == display['missed'] == 0 and display['max_work_lines'] <= 250, display
        at = data.index(b'V6TM\0\0\0\1')
        menu = struct.unpack_from('>10I', data, at+8)
        assert menu[:4] == (1, 1, 0, 1) and menu[5] > 30 and menu[6] == menu[7], menu
        assert menu[8] == menu[9] == 0, menu
        at = data.index(b'V6UI\0\0\0\1')
        ui = dict(zip(KEYS, struct.unpack_from('>18I', data, at+8)))
        assert ui['saves'] == 1 and ui['loads'] == int(returning) and ui['busy'] == 2 and ui['errors'] == ui['last_result'] == 0, ui
        at = data.index(b'V6IT\0\0\0\1')
        n = struct.unpack_from('>I', data, at+8)[0]
        events = [struct.unpack_from('>10I', data, at+16+40*i) for i in range(n)]
        assert [e[:2] for e in events] == ([(2, 0)] if returning else [])+[(1, 5), (1, 5), (1, 0)], events
        for action, result, bh, ah, fb, fa, tb, ta, x, y in events:
            assert tb == ta and fa-fb <= 4 and (action == 2 or bh == ah), events
        at = data.index(b'V6ME\0\0\0\1')
        start_tick, arrival_tick, save_tick = struct.unpack_from('>3I', data, at+8)
        assert arrival_tick == save_tick == start_tick+64, (start_tick, arrival_tick, save_tick)
        mt = data.index(b'V6MT\0\0\0\1')
        for i, event in enumerate(events[int(returning):int(returning)+2]):
            tick = event[6]-start_tick
            assert 1 <= tick <= 64, tick
            row = struct.unpack_from('>36i', data, mt+104+144*(tick-1))
            assert (row[0] != 0 if i == 0 else row[0] == 0 and row[8] != 0), row
        fields, checkpoint = verify_travel(data, returning)
        crew_fields, transitions = verify_crew(data, returning)
        record = read_record(disk)
        assert record[5] == 3 and struct.unpack_from('>7iI', record, 8) == checkpoint[:-1]+(56,), record.hex()
        for rx, ry in ((111, 104), (110, 105), (111, 105)):
            bit = (ry-100)*20+rx-100
            assert record[40+(bit>>3)] & (1 << (bit & 7)), (rx, ry)
        at = data.index(b'V6RA\0\0\0\1')
        rescue = struct.unpack_from('>18I', data, at+8)
        assert rescue[1:3] == (0, 0) and rescue[10] == 0 and rescue[14:16] == (1, 7), rescue
        assert (directory/'tower.adf').read_bytes() == boot
        return dict(display=display, menu=menu, ui=ui, events=events,
                    source_travel_fields=fields, companion_fields=crew_fields, transitions=transitions)

    outbound = capture(build, 'yellow-outbound')
    arrival = read_record(disk)
    returning = capture(live, 'yellow-return', True)
    assert arrival != read_record(disk)
    report = dict(outbound=outbound, returning=returning,
                  scope='Physical teleporter selector, 64-tick travel and companion traces both ways, V3 arrival autosaves, cold return, departure/arrival busy rejection')
    (build/'station-travel-capture.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS yellow travel:', json.dumps(report))


if __name__ == '__main__':
    main()
