#!/usr/bin/env python3
"""Pack literal campaign tile initializers; deliberately does NOT export room logic.

V6RP v1: >4sHHI header (magic, version, records, directory offset=12),
then >III per record (absolute offset, packed bytes, CRC32 of big-endian raw tiles).
Each record decodes to exactly 1200 unsigned 16-bit tile IDs. Duplicate payloads
share an offset. The JSON manifest identifies source locations and variants;
record indices are build artifacts, not stable campaign room coordinates.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ('Otherlevel', 'Spacestation2', 'Labclass', 'Finalclass', 'WarpClass')
ARRAY = re.compile(r'static\s+const\s+short\s+contents\s*\[(\d*)\]\s*=\s*\{([^}]+)\}\s*;')


SLICE_ROOMS = ((0, 10), (19, 10))


def prototype_record(records=None, coords=(0, 10)):
    """Select a unique literal room within the explicitly supported slice."""
    records = extract() if records is None else records
    chosen = [r for r in records if r[0]['source'].endswith('/Otherlevel.cpp') and
              r[0]['enclosing_label'] == f'case rn({coords[0]},{coords[1]})']
    if len(chosen) != 1: raise ValueError('Playable slice room is ambiguous')
    return chosen[0]


def prototype_checkpoint(coords=(0, 10)):
    source = (ROOT/'desktop_version/src/Otherlevel.cpp').read_text()
    start = source.index(f'case rn({coords[0]},{coords[1]}):')
    end = source.index('case rn(', start+5)
    calls = re.findall(r'obj\.createentity\(([^;]+)\);', source[start:end])
    if len(calls) != 1: raise ValueError('Slice requires unsupported room entities')
    values = [int(v.strip()) for v in calls[0].split(',')]
    if len(values) != 5 or values[2] != 10: raise ValueError('Expected one checkpoint')
    x, y, _, orientation, identity = values
    if x % 8 or not (0 <= x <= 288 and 0 <= y <= 208) or orientation not in (0, 1):
        raise ValueError('Checkpoint outside supported drawing geometry')
    body = re.sub(r'//[^\n]*|/\*.*?\*/', '', source[start:end], flags=re.S)
    body = ARRAY.sub('', body)
    body = re.sub(r'obj\.createentity\([^;]+\);', '', body)
    body = re.sub(r'case rn\(\d+,\d+\):|result\s*=\s*contents;|break;|[{}\s]', '', body)
    if body: raise ValueError(f'Unsupported slice setup: {body}')
    return x, y, orientation, identity


def encode(values):
    result = bytearray()
    i = 0
    while i < len(values):
        end = i + 1
        while end < len(values) and values[end] == values[i] and end - i < 32767:
            end += 1
        if end - i >= 3:
            result += struct.pack('>HH', 0x8000 | (end - i), values[i])
            i = end
        else:
            start = i
            i = end
            while i < len(values) and i - start < 32767:
                if i + 2 < len(values) and values[i] == values[i + 1] == values[i + 2]:
                    break
                i += 1
            result += struct.pack('>H', i - start)
            result += struct.pack('>' + 'H' * (i - start), *values[start:i])
    return bytes(result)


def extract():
    records = []
    for name in SOURCES:
        path = ROOT / 'desktop_version/src' / (name + '.cpp')
        original = path.read_text()
        # Retain offsets/line numbers while blanking comments.
        text = re.sub(r'//[^\n]*|/\*.*?\*/',
                      lambda m: re.sub(r'[^\n]', ' ', m[0]), original, flags=re.S)
        matches = list(ARRAY.finditer(text))
        declarations = len(re.findall(r'static\s+const\s+short\s+contents\s*\[', text))
        if len(matches) != declarations:
            raise ValueError(f'{name}: unrecognized tile initializer')
        for m in matches:
            tokens = [t.strip() for t in m[2].split(',') if t.strip()]
            if any(not re.fullmatch(r'\d+', t) for t in tokens):
                raise ValueError(f'{name}: nonliteral initializer')
            values = [int(t) for t in tokens]
            declared = int(m[1]) if m[1] else len(values)
            if declared != 1200 or len(values) > declared:
                raise ValueError(f'{name}: expected 40x30 tiles')
            values += [0] * (declared - len(values))
            if any(v > 65535 for v in values):
                raise ValueError(f'{name}: tile outside uint16')
            raw = struct.pack('>1200H', *values)
            labels = list(re.finditer(r'\b(case\s+[^:]+|default)\s*:', text[:m.start()]))
            records.append((dict(source=str(path.relative_to(ROOT)),
                                 line=original.count('\n', 0, m.start()) + 1,
                                 enclosing_label=labels[-1][1] if labels else None,
                                 sha256=hashlib.sha256(raw).hexdigest()), raw, encode(values)))
    return records


def enemy_record(records=None, scene="enemy"):
    records = extract() if records is None else records
    label = {"pick":"55,45","platform":"50,42","traffic":"53,39","enemy":"50,39"}[scene]
    name = {"pick":"Just Pick Yourself Down","platform":"Stop and Reflect","traffic":"Traffic Jam","enemy":"Security Sweep"}[scene]
    matches = [r for r in records if r[0]['source'].endswith('/Spacestation2.cpp')
               and r[0]['enclosing_label'] == f'case rn({label})']
    if len(matches) != 1: raise ValueError(f'{name} source ambiguous')
    source = (ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    start=source.index(f'case rn({label}):'); end=source.index('case rn(',start+5)
    body=re.sub(r'//[^\n]*|/\*.*?\*/','',source[start:end],flags=re.S)
    body=ARRAY.sub('',body)
    if scene=='pick':body=body.replace('216 - 4','212')
    calls=re.findall(r'obj\.createentity\(([^;]+)\);',body)
    values=[[int(v.strip()) for v in c.split(',')] for c in calls]
    expected = ([[45,118,1,1,4],[205,118,1,1,4],[125,18,1,0,4],[232,184,10,0,1]]
                if scene == "traffic" else [[200,32,1,0,8],[168,104,10,1,439500]])
    if scene == "platform":
        expected=[[288,160,10,1,442500],[135,75,2,0,3,100,70,320,160],
                  [185,110,2,0,3,100,70,320,160],[235,145,2,0,3,100,70,320,160]]
    if scene=='pick':expected=[[24,80,2,3,6],[64,176,10,0,445550],[212,192,10,1,445551]]
    if values != expected:
        raise ValueError(f'{name} setup changed; review native actor metadata')
    body=re.sub(rf'obj\.createentity\([^;]+\);|roomname = "{name}";','',body)
    body=re.sub(r'case rn\(\d+,\d+\):|result\s*=\s*contents;|break;|[{}\s]','',body)
    if scene=='pick':
        if body.count('obj.platformtile=159;')!=1:
            raise ValueError('Just Pick Yourself Down platform tile changed')
        body=body.replace('obj.platformtile=159;','')
    if body: raise ValueError(f'Unsupported enemy room setup: {body}')
    return matches[0]


def build(out, scene="world"):
    records = extract()
    offset = 12 + len(records) * 12
    payloads, directory, manifest, seen = bytearray(), bytearray(), [], {}
    for index, (meta, raw, packed) in enumerate(records):
        if packed not in seen:
            seen[packed] = offset + len(payloads)
            payloads += packed
        position = seen[packed]
        crc = zlib.crc32(raw)
        directory += struct.pack('>III', position, len(packed), crc)
        manifest.append(dict(index=index, **meta, offset=position, packed_bytes=len(packed), crc32=crc))
    pack = struct.pack('>4sHHI', b'V6RP', 1, len(records), 12) + directory + payloads
    out.mkdir(parents=True, exist_ok=True)
    (out / 'rooms.v6rp').write_bytes(pack)
    report = dict(format='V6RP', version=1, records=len(records), unique_payloads=len(seen),
                  raw_bytes=len(records) * 2400, pack_bytes=len(pack),
                  scope='Literal tile arrays only; no entities, room setup, scripts, or tower.',
                  rooms=manifest)
    (out / 'rooms.json').write_text(json.dumps(report, indent=2) + '\n')
    if scene in ('enemy','traffic','platform','pick'):
        selected=enemy_record(records,scene)[2]
        header = '/* Generated bounded enemy room: literal actors and checkpoint. */\n'
        header += 'static const unsigned char packed_room_0[] = {' + ','.join(map(str,selected)) + '};\n'
        header += '#define SLICE_ROOM_COUNT 1\n#define SLICE_TILESET 0\n#define SLICE_EXTRA_ROW 0\n'
        header += ('static const V6RoomSetup room_setups[] = {{115,103,232,184,20,1}};\n' if scene=='traffic' else
                   'static const V6RoomSetup room_setups[] = {{112,103,168,104,21,439500}};\n')
        header += ('#define ENEMY_COUNT 3\n#define ENEMY_TILE 28\n#define ENEMY_WIDTH 22\n#define ENEMY_HEIGHT 32\n#define ENEMY_DRAW_WIDTH 32\n#define ENEMY_COLOUR 0xf66\n#define SLICE_CAPTION "115,103 - TRAFFIC JAM             "\nstatic const int enemy_setup[3][4]={{45,118,1,4},{205,118,1,4},{125,18,0,4}};\n' if scene=='traffic' else
                   '#define ENEMY_COUNT 1\n#define ENEMY_TILE 36\n#define ENEMY_WIDTH 16\n#define ENEMY_HEIGHT 16\n#define ENEMY_DRAW_WIDTH 16\n#define ENEMY_COLOUR 0xf6b\n#define SLICE_CAPTION "112,103 - SECURITY SWEEP          "\nstatic const int enemy_setup[1][4]={{200,32,0,8}};\n')
        if scene == 'platform':
            header = '/* Generated bounded Stop and Reflect setup. */\n'
            header += 'static const unsigned char packed_room_0[] = {' + ','.join(map(str,selected)) + '};\n'
            header += '#define SLICE_ROOM_COUNT 1\n#define SLICE_TILESET 0\n#define SLICE_EXTRA_ROW 0\n'
            header += '#if !defined(V6_HORIZONTAL_REPLAY) && !defined(V6_CRUSH_REPLAY) && !defined(V6_DISAPPEAR_REPLAY)\n'
            header += 'static const V6RoomSetup room_setups[] = {{112,106,288,160,21,442500}};\n'
            header += '#define PLATFORM_COUNT 3\n#define SLICE_CAPTION "112,106 - STOP AND REFLECT        "\n'
            header += 'static const int platform_setup[3][2]={{135,75},{185,110},{235,145}};\n#endif\n'
        if scene=='pick':
            header='/* Generated Just Pick Yourself Down: all original room entities. */\n'
            header+='static const unsigned char packed_room_0[] = {'+','.join(map(str,selected))+'};\n'
            header+='#define SLICE_ROOM_COUNT 1\n#define SLICE_TILESET 0\n#define SLICE_EXTRA_ROW 0\n'
            header+='static const V6RoomSetup room_setups[]={{117,109,64,176,20,445550}};\n'
            header+='#define PLATFORM_COUNT 1\n#define CHECKPOINT_COUNT 2\n#define SLICE_CAPTION "117,109 - JUST PICK YOURSELF DOWN"\n'
            header+='static const int platform_setup[1][2]={{24,80}};\n'
            header+='static const int checkpoint_setup[2][4]={{64,176,20,445550},{212,192,21,445551}};\n'
        header += 'static const unsigned char * const packed_rooms[] = {packed_room_0};\n'
        header += 'static const unsigned short packed_sizes[] = {sizeof(packed_room_0)};\n'
    else:
        header = '/* Generated bounded room setup; only literal checkpoints supported. */\n'
        setups = []
        for index, coords in enumerate(SLICE_ROOMS):
            selected = prototype_record(records, coords)[2]
            cx, cy, orientation, checkpoint_id = prototype_checkpoint(coords)
            header += f'static const unsigned char packed_room_{index}[] = {{\n' + ','.join(map(str, selected)) + '\n};\n'
            setups.append(f'{{{coords[0]+100},{coords[1]+100},{cx},{cy},{20+orientation},{checkpoint_id}}}')
        header += f'#define SLICE_ROOM_COUNT {len(SLICE_ROOMS)}\n'
        header += 'static const V6RoomSetup room_setups[] = {' + ','.join(setups) + '};\n'
        header += 'static const unsigned char * const packed_rooms[] = {' + ','.join(f'packed_room_{i}' for i in range(len(SLICE_ROOMS))) + '};\n'
        header += 'static const unsigned short packed_sizes[] = {' + ','.join(f'sizeof(packed_room_{i})' for i in range(len(SLICE_ROOMS))) + '};\n'
        header += '#define SLICE_TILESET 1\n#define SLICE_EXTRA_ROW 1\n'
    (out / 'prototype_room.h').write_text(header)
    print(f'{len(records)} arrays: {report["raw_bytes"]:,} raw bytes -> {len(pack):,} packed bytes '
          f'(including directory); {len(seen)} unique payloads')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'build/amiga')
    parser.add_argument('--scene', choices=('world','enemy','traffic','platform','pick'), default='world')
    args=parser.parse_args()
    build(args.out, args.scene)
