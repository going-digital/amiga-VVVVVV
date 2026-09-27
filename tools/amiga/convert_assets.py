#!/usr/bin/env python3
"""Convert user-supplied assets for the first room prototype (never committed)."""
import argparse
from collections import Counter
import io
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import wave
import zipfile

from pack_rooms import ROOT, prototype_record, SLICE_ROOMS, enemy_record

DEFAULT_DATA = Path.home() / 'Library/Application Support/Steam/steamapps/common/vvvvvv/VVVVVV.app/Contents/Resources/data.zip'


def build(data, out, scene="world"):
    out.mkdir(parents=True, exist_ok=True)
    fingerprint = dict(scene=scene, path=str(data.resolve()), size=data.stat().st_size,
                       mtime_ns=data.stat().st_mtime_ns,
                       tools=hashlib.sha256(Path(__file__).read_bytes() +
                           (ROOT / 'tools/amiga/png_rgba.cpp').read_bytes() +
                           (ROOT / 'tools/amiga/pack_rooms.py').read_bytes() +
                           (ROOT / 'desktop_version/src/Otherlevel.cpp').read_bytes() +
                           (ROOT / 'desktop_version/src/Spacestation2.cpp').read_bytes()).hexdigest())
    report_path = out / 'assets.json'
    if report_path.exists() and (out / 'prototype_assets.h').exists():
        if json.loads(report_path.read_text()).get('input_fingerprint') == fingerprint:
            return
    decoder = out / 'png_rgba'
    subprocess.run(['c++', '-O2', '-I' + str(ROOT / 'third_party/lodepng'),
                    str(ROOT / 'tools/amiga/png_rgba.cpp'),
                    str(ROOT / 'third_party/lodepng/lodepng.cpp'), '-o', str(decoder)], check=True)
    with zipfile.ZipFile(data) as archive:
        def png(name):
            path = out / Path(name).name
            path.write_bytes(archive.read(name))
            header, rgba = subprocess.check_output([str(decoder), str(path)]).split(b'\n', 1)
            w, h = map(int, header.split())
            assert len(rgba) == w * h * 4
            return w, h, rgba

        records = [enemy_record(scene=scene)] if scene != 'world' else [prototype_record(coords=c) for c in SLICE_ROOMS]
        w, h, rgba = png('graphics/tiles.png' if scene != 'world' else 'graphics/tiles2.png')
        ids = sorted({tile for record in records for tile in struct.unpack('>1200H', record[1])})
        tiles = []
        colors = Counter()
        for tile in ids:
            x, y = (tile % (w // 8)) * 8, (tile // (w // 8)) * 8
            assert y + 8 <= h
            pixels = []
            for dy in range(8):
                for dx in range(8):
                    r, g, b, a = rgba[((y + dy) * w + x + dx) * 4:((y + dy) * w + x + dx) * 4 + 4]
                    c = tuple(round(v * a / 255 / 17) for v in (r, g, b))
                    pixels.append(c)
                    if c != (0, 0, 0): colors[c] += 1
            tiles.append(pixels)
        palette = [(0, 0, 0)] + [c for c, _ in colors.most_common(12)]
        palette += [(0, 0, 0)] * (13 - len(palette))
        palette += [(6, 15, 6), (6, 15, 15), (15, 15, 15)]
        planar = []
        for pixels in tiles:
            indices = [min(range(13), key=lambda i: sum((palette[i][j] - c[j]) ** 2 for j in range(3))) for c in pixels]
            planar.append([sum(((indices[y * 8 + x] >> plane) & 1) << (7-x) for x in range(8))
                           for plane in range(4) for y in range(8)])
        mapping = [0] * (max(ids) + 1)
        for i, tile in enumerate(ids): mapping[tile] = i
        assert len(ids) <= 256
        # Source size-2 platforms repeat the selected 8x8 tile four times.
        platform_rows=[0]*32
        if scene in ('platform','pick'):
            platform_tile=159 if scene=='pick' else 616
            ox,oy=(platform_tile%(w//8))*8,(platform_tile//(w//8))*8
            for y in range(8):
                row=sum((rgba[((oy+y)*w+ox+x)*4+3]>127 and
                         max(rgba[((oy+y)*w+ox+x)*4:((oy+y)*w+ox+x)*4+3])>0) << (7-x) for x in range(8))
                platform_rows[y]=row*0x01010101
        fw, fh, font = png('graphics/font.png')
        glyphs = []
        for ch in range(128):
            x, y = (ch % (fw // 8)) * 8, (ch // (fw // 8)) * 8
            assert y + 8 <= fh
            glyphs.append([sum((font[((y+dy)*fw+x+dx)*4+3] > 127 and
                                max(font[((y+dy)*fw+x+dx)*4:((y+dy)*fw+x+dx)*4+3]) > 0) << (7-dx)
                               for dx in range(8)) for dy in range(8)])
        sw, sh, sprites = png('graphics/sprites.png')
        assert sw >= 32 and sh >= 32
        sprite_frames = []
        collision_frames = []
        for tile in range(40):
            ox, oy = tile % (sw//32)*32, tile // (sw//32)*32
            assert oy+32 <= sh
            sprite_frames.append([sum((sprites[((oy+y)*sw+ox+x)*4+3] > 127 and
                                      max(sprites[((oy+y)*sw+ox+x)*4:((oy+y)*sw+ox+x)*4+3]) > 0) << (31-x)
                                     for x in range(32)) for y in range(32)])
            collision_frames.append([sum((sprites[((oy+y)*sw+ox+x)*4] != 0) << (31-x)
                                           for x in range(32)) for y in range(32)])
        assert all((bits & ~0x03fffc00) == 0 for frame in sprite_frames[:16] for bits in frame), 'Player exceeds 16-pixel crop'
        assert all((bits & 0xffff) == 0 for frame in sprite_frames[36:40] for bits in frame), 'Drone exceeds one sprite channel'
        assert all((bits & 0xffff) == 0 and (y < 16 or bits == 0)
                   for frame in sprite_frames[20:22] for y,bits in enumerate(frame)), 'Checkpoint exceeds 16x16'
        with wave.open(io.BytesIO(archive.read('sounds/jump.wav'))) as wav:
            channels, width, rate, count = wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()
            pcm = wav.readframes(count)
        assert width in (1, 2)
        mono = []
        for i in range(count):
            samples = [pcm[(i*channels+c)] - 128 if width == 1 else
                       struct.unpack_from('<h', pcm, (i*channels+c)*2)[0] / 256 for c in range(channels)]
            mono.append(sum(samples) / channels)
        # Offline linear resampling; only this short SFX, not music, is included.
        target_rate = 11025
        sound = []
        for i in range(round(count * target_rate / rate)):
            p = i * rate / target_rate
            k = int(p)
            value = mono[k] * (1-(p-k)) + mono[min(k+1, count-1)] * (p-k)
            sound.append(round(max(-128, min(127, value))) & 255)
        if len(sound) & 1: sound.append(0)

    def matrix(name, rows):
        return f'static const unsigned char {name}[{len(rows)}][{len(rows[0])}] = {{\n' + ',\n'.join('{' + ','.join(map(str,r)) + '}' for r in rows) + '\n};\n'
    header = '/* Generated from user-supplied assets; do not redistribute without permission. */\n'
    room_colors = []
    for record in records:
        used = set(struct.unpack('>1200H', record[1]))
        candidates = [c for tile, pixels in zip(ids, tiles) if tile in used for c in pixels]
        room_colors.append(max(candidates, key=lambda c: sum(c)))
    two_planes = [[sum((max(pixels[y*8+x]) >= 3) << (7-x) for x in range(8))
                   for y in range(8)] + [0]*8 for pixels in tiles]
    header += '#if V6_PLANES == 2\n'
    header += 'static const unsigned short palette[4] = {0,' + hex(sum(v << shift for v, shift in zip(room_colors[0], (8,4,0)))) + ',0x6f6,0xfff};\n'
    header += 'static const unsigned short room_colors[] = {' + ','.join(hex(r<<8|g<<4|b) for r,g,b in room_colors) + '};\n'
    header += matrix('tile_planes', two_planes)
    header += '#define CHECKPOINT_COLOR 2\n#define TEXT_COLOR 3\n#else\n'
    header += 'static const unsigned short palette[16] = {' + ','.join(hex(r<<8|g<<4|b) for r,g,b in palette) + '};\n'
    header += matrix('tile_planes', planar)
    header += '#define CHECKPOINT_COLOR 13\n#define TEXT_COLOR 15\n#endif\n'
    header += 'static const unsigned char tile_mapping[] = {' + ','.join(map(str,mapping)) + '};\n'
    header += matrix('font_rows', glyphs)
    header += 'static const unsigned long sprite_rows[40][32] = {\n' + ',\n'.join(
        '{' + ','.join(hex(v)+'UL' for v in sprite) + '}' for sprite in sprite_frames) + '\n};\n'
    if scene in ('platform','pick'):
        header += 'static const uint32_t platform_rows[32] = {' + ','.join(hex(v)+'UL' for v in platform_rows) + '};\n'
    header += 'static const uint32_t collision_rows[40][32] = {\n' + ',\n'.join(
        '{' + ','.join(hex(v)+'UL' for v in sprite) + '}' for sprite in collision_frames) + '\n};\n'
    header += 'static const unsigned char flip_sound[] = {' + ','.join(map(str,sound)) + '};\n'
    (out / 'prototype_assets.h').write_text(header)
    report = dict(input_fingerprint=fingerprint, tiles=len(ids), tile_bytes=len(ids)*32, source_room_ocs_colors=len(colors)+1,
                  two_plane_tile_bytes=len(ids)*16, two_plane_room_colors=room_colors,
                  scene_palette_slots=13, checkpoint_palette_index=13, sprite_palette_index=14, text_palette_index=15,
                  font_bytes=1024, sound_bytes=len(sound), sound_rate=target_rate,
                  note=('Just Pick Yourself Down (117,109): both checkpoints and horizontal platform, tile 159.' if scene=='pick' else 'Stop and Reflect (112,106): three platforms using repeated tile 616.' if scene == 'platform' else 'Traffic Jam (115,103): original tiles, three enemies, frames 28-31 and red-channel collision masks.' if scene == 'traffic' else 'Security Sweep (112,103): original tiles, player, drone frames 36-39 and red-channel collision masks.' if scene == 'enemy' else
                        'Rooms (100,110) and (119,110), static tiles, player animation and checkpoints. No other room entities or scripts.'))
    (out / 'assets.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=DEFAULT_DATA)
    parser.add_argument('--out', type=Path, default=ROOT / 'build/amiga')
    parser.add_argument('--scene', choices=('world','enemy','traffic','platform','pick'), default='world')
    args = parser.parse_args()
    build(args.data, args.out, args.scene)
