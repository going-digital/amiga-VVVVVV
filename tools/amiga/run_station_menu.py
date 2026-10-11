#!/usr/bin/env python3
"""Exercise V3 yellow progress through interactive save/load and a fresh boot."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
from run_interactive_save import config, EMU, KEYS
from run_tower_probe import diagnostics
from save_disk import create_save_disk, read_record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--live', type=Path, required=True)
    args = parser.parse_args()
    build, live = args.build.resolve(), args.live.resolve()
    disk = build/'capture-menu-disk.adf'
    disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf', disk)

    def capture(directory, name, inputs):
        cfg = config(directory, disk)
        dump = directory/(name+'.bin')
        dump.unlink(missing_ok=True)
        boot = (directory/'tower.adf').read_bytes()
        env = dict(os.environ, COPPERLINE_DBG_AFTER='85',
                   COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
        with (directory/(name+'.log')).open('w') as log:
            subprocess.run([EMU, '--config', str(cfg), '--floppy-drives', '2',
                            '--noaudio', *inputs, '--screenshot-after', '86',
                            str(directory/(name+'.png'))], env=env, stdout=log,
                           stderr=subprocess.STDOUT, check=True)
        data = dump.read_bytes()
        at = data.index(b'V6UI\0\0\0\1')
        ui = dict(zip(KEYS, struct.unpack_from('>18I', data, at+8)))
        at = data.index(b'V6IT\0\0\0\1')
        count = struct.unpack_from('>I', data, at+8)[0]
        events = list(struct.iter_unpack('>10I', data[at+16:at+16+count*40]))
        display = diagnostics(dump)
        assert display['status'] == 2 and display['error'] == display['missed'] == 0, display
        assert display['max_work_lines'] <= 250, display
        assert ui['last_result'] == 0 and (ui['loaded_x'], ui['loaded_y']) == (188, 86), ui
        for action, result, before, after, fb, fa, tb, ta, x, y in events:
            assert tb == ta and fa-fb <= 4, (action, result, fb, fa, tb, ta)
            if action == 1 or result:
                assert before == after, (action, result, before, after)
        assert (directory/'tower.adf').read_bytes() == boot
        return ui, events, display, data

    ui, events, display, _ = capture(build, 'station-menu', [])
    assert [(e[0], e[1]) for e in events] == [(2, 3), (1, 5), (1, 0), (2, 0)], events
    assert ui['saves'] == ui['loads'] == 1 and ui['busy'] == ui['errors'] == 1, ui
    record = read_record(disk)
    assert struct.unpack_from('>4sHH7iI', record) == (b'V6CS', 3, 96, 188, 86, 1, 0, 111, 105, 441490, 56)
    assert record[40+(111>>3)] & (1 << (111 & 7))
    cold_ui, cold_events, cold_display, data = capture(live, 'station-menu-cold', [
        '--joy-after', '45', 'fire', '600', '--click-after', '45', 'right', '600',
        '--click-after', '70', 'left', '200'])
    assert cold_ui['actions'] == cold_ui['loads'] == 1 and cold_ui['saves'] == cold_ui['errors'] == cold_ui['busy'] == 0, cold_ui
    at = data.index(b'V6CF\0\0\0\1')
    crew = struct.unpack_from('>14I', data, at+8)
    assert crew[:3] == (1, 1, 0), crew  # visible, following, happy
    at = data.index(b'V6RA\0\0\0\1')
    rescue = struct.unpack_from('>18I', data, at+8)
    assert rescue[1:3] == (0, 0) and rescue[10] == 0 and rescue[14:16] == (1, 7), rescue
    assert read_record(disk) == record
    report = dict(ui=ui, events=events, display=display, cold_ui=cold_ui,
                  cold_events=cold_events, cold_display=cold_display,
                  scope='V3 interactive save/load, busy rejection, frozen game state across DOS, fresh-boot yellow companion restoration')
    (build/'station-menu-capture.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS station menu:', json.dumps(report))


if __name__ == '__main__':
    main()
