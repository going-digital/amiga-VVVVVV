#!/usr/bin/env python3
"""Compare each logical display pixel in fixed-camera native captures.

The installed Copperline presentation is 716x540, with a 686x480 inner
playfield at (15,30). Sampling pixel centres avoids its border/filter blends.
This checks all 320x240 logical pixels, not every resampled PNG pixel.
"""
import json
import argparse
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'build/amiga-feasibility'
BUILD = ROOT / 'build/amiga-tower-pixels'
EMU = '/Applications/Copperline.app/Contents/MacOS/copperline'
CAMERAS = (0, 16, 17, 52, 53, 255, 5599, 5600)


def reference_rows():
    # Read the desktop map directly; do not reuse the native RLE/cache renderer.
    source = (ROOT / 'desktop_version/src/Tower.cpp').read_text()
    body = source[source.index('void towerclass::loadmap('):]
    body = re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};', body, re.S)[1]
    body = re.sub(r'//[^\n]*|/\*.*?\*/', '', body, flags=re.S)
    assert re.fullmatch(r'[\s\d,]+', body)
    tiles = [int(x) for x in body.split(',') if x.strip()]
    assert len(tiles) == 40*700
    atlas = (ASSETS / 'tower_tiles.bin').read_bytes()
    palette = json.loads((ASSETS / 'tower-assets.json').read_text())['palette']
    palette = [bytes(((c >> shift) & 15)*17 for shift in (8, 4, 0)) for c in palette]
    rows = []
    for y in range(5600):
        row = bytearray()
        for tile in tiles[(y//8)*40:(y//8+1)*40]:
            for x in range(8):
                index = ((atlas[tile*16+y%8] >> (7-x)) & 1)
                index |= ((atlas[tile*16+8+y%8] >> (7-x)) & 1) << 1
                row.extend(palette[index])
        rows.append(bytes(row))
    body = source[source.index('void towerclass::loadbackground('):]
    body = re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};', body, re.S)[1]
    body = re.sub(r'//[^\n]*|/\*.*?\*/', '', body, flags=re.S)
    backtiles = [int(x) for x in body.split(',') if x.strip()]
    assert len(backtiles) == 40*120
    backdrop = (ASSETS / 'tower_backdrop.bin').read_bytes()
    background = []
    for y in range(960):
        background.append(b''.join(bytes((34,34,51)) if (backdrop[t*8+y%8]>>(7-x))&1
            else bytes(3) for t in backtiles[y//8*40:(y//8+1)*40] for x in range(8)))
    return rows, background


def compare(path, camera, rows, parallax=True):
    header, rgba = subprocess.check_output([str(ASSETS / 'png_rgba'), str(path)]).split(b'\n', 1)
    width, height = map(int, header.split())
    assert (width, height) == (716, 540), 'Copperline presentation changed; review sampling geometry'
    assert len(rgba) == width*height*4
    background_pixels = 0
    for y in range(240):
        foreground = rows[0][(camera+y) % 5600]
        background = rows[1][(camera//2+y) % 960]
        expected = b''.join(foreground[x:x+3] if foreground[x:x+3]!=bytes(3)
            else background[x:x+3] for x in range(0,960,3))
        for x in range(320):
            if expected[x*3:x*3+3] == bytes((34,34,51)):
                background_pixels += 1
            px = 15 + ((2*x+1)*686)//640
            at = ((30+2*y)*width+px)*4
            assert rgba[at:at+3] == expected[x*3:x*3+3], (camera, x, y, rgba[at:at+3], expected[x*3:x*3+3])
    if parallax: assert background_pixels > 0, (camera, "No visible parallax pixels")
    return 320*240


def main():
    global BUILD,CAMERAS
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paired',action='store_true')
    parser.add_argument('--hallways',action='store_true')
    args=parser.parse_args()
    if args.paired: BUILD=ROOT/'build/amiga-tower-paired-pixels'
    if args.hallways: BUILD=ROOT/'build/amiga-hallway-pixels';CAMERAS=(0,1)
    BUILD.mkdir(parents=True, exist_ok=True)
    config = f'''rom = {json.dumps(str(Path.home() / 'amiga/KICK13.ROM'))}
[machine]
model = "A500"
[cpu]
model = "68000"
[memory]
chip = "512K"
slow = "512K"
fast = "0"
[chipset]
revision = "OCS"
video = "PAL"
[emulation]
pacing_budget = "cycles"
[floppy.df0]
path = {json.dumps(str(BUILD / 'tower.adf'))}
write_protected = true
'''
    (BUILD / 'tower.toml').write_text(config)
    rows = reference_rows()
    checks = 0
    for camera in CAMERAS:
        flags=f'-DV6_TOWER_HOLD={camera}'+(' -DV6_TOWER_PAIRS' if args.paired else '')
        if args.hallways:
            flags=f'-DV6_TOWER_HALLWAY_HOLD={camera} -DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE'
        with (BUILD / f'build-{camera}.log').open('w') as log:
            subprocess.run(['make', '-C', str(ROOT / 'amiga_version'), f'BUILD={BUILD}',
                            f'CPPFLAGS={flags}', str(BUILD / 'tower.adf')],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        path = BUILD / f'camera-{camera}.png'
        path.unlink(missing_ok=True)
        with (BUILD / f'capture-{camera}.log').open('w') as log:
            subprocess.run([EMU, '--config', str(BUILD / 'tower.toml'), '--noaudio',
                            '--screenshot-after', '22', str(path)],
                           stdout=log, stderr=subprocess.STDOUT, check=True)
        if args.hallways:
            from tower_gameplay_data import hallway_rooms
            atlas=(ASSETS/'tower_tiles.bin').read_bytes()
            palette=json.loads((ASSETS/'tower-assets.json').read_text())['palette']
            colours=[bytes(((c>>shift)&15)*17 for shift in (8,4,0)) for c in palette]
            tiles=hallway_rooms()[camera]['tiles'];foreground=[]
            for y in range(240):
                foreground.append(b''.join(colours[((atlas[t*16+y%8]>>(7-x))&1)|
                    (((atlas[t*16+8+y%8]>>(7-x))&1)<<1)]
                    for t in tiles[y//8*40:(y//8+1)*40] for x in range(8)))
            # compare() indexes modulo the tower height; these views are at 0.
            checks+=compare(path,0,(foreground,[bytes(960)]*960),parallax=False)
        else: checks += compare(path, camera, rows)
        print(f'PASS: native camera {camera}, 76800 logical pixels', flush=True)
    report = dict(cameras=CAMERAS, logical_pixel_checks=checks,
                  scope='Three-plane dual-playfield fixed-camera native Copper/DMA captures vs desktop map and converted atlas; exact RGB at logical pixel centres; not moving-frame tearing or physical hardware validation')
    if args.hallways:
        report.update(hallways=((108,109),(110,104)),scope='Fixed native hallway terrain captures vs literal Finalclass maps and converted tower atlas; black backgrounds and hidden entities; no moving-frame or story-script validation')
    (BUILD / 'pixels.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
