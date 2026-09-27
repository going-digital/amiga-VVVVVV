#!/usr/bin/env python3
"""Decode V6_PROFILE peak-update phase costs from a Copperline slow-RAM dump."""
import argparse
import json
import struct
from pathlib import Path


def read_profile(path):
    ram = path.read_bytes()
    names = ('enemies', 'player_and_hits', 'checkpoint_and_room_events',
             'checkpoint_restore', 'sprites', 'hud')
    for offset in range(0, len(ram)-27, 2):
        if ram[offset:offset+4] != b'V6PF':
            continue
        values = struct.unpack_from('>6I', ram, offset+4)
        if sum(values) and all(v < 10000 for v in values):
            return dict(zip(names, values))
    raise ValueError('No populated V6_PROFILE record in RAM dump')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dump', type=Path)
    print(json.dumps(read_profile(parser.parse_args().dump), indent=2))
