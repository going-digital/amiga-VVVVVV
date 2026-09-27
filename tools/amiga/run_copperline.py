#!/usr/bin/env python3
"""Launch the minimum A500 profile, or capture deterministic diagnostic runs."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def read_diagnostics(path):
    ram = path.read_bytes()
    # Require a running/stopped record, not a coincidental executable byte string.
    for offset in range(0, len(ram) - 136, 2):
        if ram[offset:offset+8] == b'V6DG\0\0\0\5':
            values = struct.unpack_from('>14I6i8I2i4I', ram, offset)
            if values[13] not in (1, 2):
                continue
            names = ('magic', 'version', 'frames', 'ticks', 'renders', 'max_work_lines',
                     'missed_frames', 'flips', 'peak_tick', 'chip_free', 'other_free',
                     'chip_allocated', 'error', 'status', 'player_x', 'player_y',
                     'player_vx', 'player_vy', 'gravity', 'death_timer',
                     'deaths', 'respawns', 'checkpoint', 'exits',
                     'room_index', 'transitions', 'max_load_lines', 'load_frames',
                     'enemy_x','enemy_y','enemy_ticks','enemy_hits','sprite_channels','max_sprite_channels')
            return dict(zip(names, values))
    raise RuntimeError(f'No live prototype diagnostics in {path}')


def audio_peak(path):
    blob = path.read_bytes()
    assert blob[:4] == b'RIFF' and blob[8:12] == b'WAVE'
    pos, fmt, audio = 12, None, None
    while pos + 8 <= len(blob):
        tag, length = struct.unpack_from('<4sI', blob, pos)
        value = blob[pos+8:pos+8+length]
        if tag == b'fmt ':
            fmt = struct.unpack_from('<HHIIHH', value)
            if fmt[0] == 0xfffe:  # WAVE_FORMAT_EXTENSIBLE subtype GUID
                assert len(value) >= 40
                fmt = (struct.unpack_from('<I', value, 24)[0],) + fmt[1:]
        if tag == b'data': audio = value
        pos += 8 + length + (length & 1)
    assert fmt and audio and fmt[0] == 3 and fmt[5] == 32, 'Expected float32 PCM capture'
    # Check the flip cue at 13s, rather than counting floppy/boot audio as success.
    start = int(12.9 * fmt[2]) * fmt[4]
    end = int(13.5 * fmt[2]) * fmt[4]
    return max(abs(v[0]) for v in struct.iter_unpack('<f', audio[start:end]))


def visible_player(build, path):
    # In the default two-plane build only hardware sprite colour 17 is cyan.
    # This catches a disabled/mistimed sprite DMA list despite healthy logic.
    header, rgba = subprocess.check_output([str(build / 'png_rgba'), str(path)]).split(b'\n', 1)
    w, h = map(int, header.split())
    assert len(rgba) == w*h*4
    pixels = sum(rgba[i] < 180 and rgba[i+1] > 180 and rgba[i+2] > 180
                 for i in range(0, len(rgba), 4))
    assert pixels > 40, f'Hardware player missing from {path}'
    return pixels


def visible_enemy(build, path):
    _, rgba = subprocess.check_output([str(build / 'png_rgba'), str(path)]).split(b'\n', 1)
    pixels=sum(rgba[i]>230 and 70<rgba[i+1]<160 and 150<rgba[i+2]<225
               for i in range(0,len(rgba),4))
    assert pixels>20, f'Hardware drone missing from {path}'
    return pixels


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=Path.home() / 'amiga/KICK13.ROM')
    parser.add_argument('--emulator', default='/Applications/Copperline.app/Contents/MacOS/copperline')
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--build', type=Path, default=ROOT / 'build/amiga')
    parser.add_argument('--transitions', action='store_true', help='Validate the test-only transition replay build')
    parser.add_argument('--enemy', action='store_true')
    parser.add_argument('--traffic', action='store_true')
    parser.add_argument('--platform', action='store_true')
    parser.add_argument('--horizontal', action='store_true')
    parser.add_argument('--pick', action='store_true')
    parser.add_argument('--pick-checkpoints', action='store_true')
    args = parser.parse_args()
    build = args.build.resolve()
    config = build / 'copperline.toml'
    config.write_text(f'''rom = {json.dumps(str(args.rom.resolve()))}
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
path = {json.dumps(str(build / 'prototype.adf'))}
write_protected = true
''')
    command = [args.emulator, '--config', str(config)]
    if args.capture:
        env = dict(os.environ, RUST_LOG='info', COPPERLINE_DBG_AFTER='16.5',
                   COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{build / "slow.bin"}')
        command += ([] if args.platform or args.horizontal or args.pick or args.pick_checkpoints else
                    ['--joy-after','12','left','200'] if args.traffic else
                    ['--joy-after','12','right','300'] if args.enemy else
                    ['--joy-after','13','fire','100','--joy-after','15.5','right','300',
                     '--joy-after','16','left','300'])
        command += ['--noaudio',
                    '--save-state-after', '16', str(build / 'prototype.clstate'),
                    '--audio-wav', str(build / 'prototype.wav'),
                    '--screenshot-after', '17', str(build / 'prototype.png')]
        with (build / 'copperline.log').open('w') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env, check=True)
        report = read_diagnostics(build / 'slow.bin')
        report['visible_player_pixels'] = visible_player(build, build / 'prototype.png')
        assert report['error'] == 0 and report['status'] == 1, report
        if args.transitions:
            assert report['transitions'] >= 1 and report['room_index'] == 0, report
            assert 0 < report['max_load_lines'] < 250 and report['exits'] == 0, report
            assert report['load_frames'] == 0, report
        elif args.pick_checkpoints:
            assert report['checkpoint']==2 and report['deaths']==1 and report['respawns']==1, report
            assert report['player_x']==208 and report['player_y']==185 and report['gravity']==0, report
            assert report['max_sprite_channels']==3, report
            header,rgba=subprocess.check_output([str(build/'png_rgba'),str(build/'prototype.png')]).split(b'\n',1)
            w,h=map(int,header.split())
            green=[(i//4)%w for i in range(0,len(rgba),4)
                   if 80<rgba[i]<125 and rgba[i+1]>245 and 80<rgba[i+2]<125]
            assert len(green)>20 and min(green)>w//2, 'Expected only the right checkpoint to be green'
            report['checkpoint_fixture']='Test-only placement at second checkpoint; not room traversal'
            report['second_checkpoint_pixels']=len(green)
        elif args.pick:
            assert report['enemy_ticks']>100 and report['max_sprite_channels']==3, report
            assert report['checkpoint']==1, report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
        elif args.horizontal:
            assert report['enemy_ticks']>100 and report['max_sprite_channels']==3, report
            assert report['enemy_hits']>100 and report['checkpoint']==1, report
            assert report['player_vx']==0 and report['player_y']==93, report
            assert report['deaths']==0 and report['respawns']==0 and report['exits']==0, report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
            report['horizontal_transport_ticks']=report['enemy_hits']
            report['fixture']='Synthetic horizontal ride; not a campaign room'
            trace=json.loads((ROOT/'build/amiga/horizontal-reference-trace.json').read_text())
            assert report['ticks']==report['enemy_ticks'], 'Snapshot fell within an unfinished tick'
            assert 0<report['ticks']<=len(trace), report
            expected=trace[report['ticks']-1]
            for field,value in expected.items():
                assert report[field]==value, (field,report[field],value)
            report['reference_tick_verified']=report['ticks']
        elif args.platform:
            assert report['enemy_ticks']>100 and report['max_sprite_channels']==7, report
            assert report['enemy_y']!=75 and report['checkpoint']==1, report
            assert report['enemy_hits']>=8 and report['deaths']>=1 and report['respawns']>=1, report
            header,rgba=subprocess.check_output([str(build/'png_rgba'),str(build/'prototype.png')]).split(b'\n',1)
            w,h=map(int,header.split())
            columns=sorted({(i//4)%w for i in range(0,len(rgba),4)
                            if rgba[i]>245 and 80<rgba[i+1]<125 and 170<rgba[i+2]<200})
            bands=sum(i==0 or x-columns[i-1]>8 for i,x in enumerate(columns))
            assert bands==3, f'Expected three pink platforms, got {bands} bands'
            report['visible_platform_bands']=bands
            report['platform_ticks']=report['enemy_ticks']
            report['platform_pushes']=report['enemy_hits']
        elif args.traffic:
            assert report['enemy_ticks'] > 100 and report['max_sprite_channels'] == 7, report
            assert report['enemy_y'] != 118 and report['checkpoint'] == 1, report
            header, rgba = subprocess.check_output([str(build/'png_rgba'),str(build/'prototype.png')]).split(b'\n',1)
            w,h=map(int,header.split())
            columns=sorted({(i//4)%w for i in range(0,len(rgba),4)
                            if rgba[i]>245 and 80<rgba[i+1]<125 and 80<rgba[i+2]<125})
            bands=sum(i==0 or x-columns[i-1]>8 for i,x in enumerate(columns))
            assert bands==3, f'Expected three red enemies, got {bands} horizontal bands'
            report['visible_enemy_bands']=bands
        elif args.enemy:
            assert report['enemy_ticks'] > 100 and report['enemy_hits'] >= 1, report
            report['visible_enemy_pixels']=visible_enemy(build,build/'prototype.png')
        else:
            assert report['flips'] == 1 and report['checkpoint'] == 1, report
        if not args.traffic and not args.platform and not args.horizontal and not args.pick and not args.pick_checkpoints:
            assert report['deaths'] >= 1 and report['respawns'] >= 1, report
        # Snapshot can land between a tick and completion of its render.
        assert report['ticks'] > 100 and 0 <= report['ticks'] - report['renders'] <= 1, report
        report['video_headroom_passed'] = report['missed_frames'] == 0 and report['max_work_lines'] < 250
        report['max_work_ms'] = round(report['max_work_lines'] * 227 / 3546895 * 1000, 3)
        if not args.transitions and not args.enemy and not args.traffic and not args.platform and not args.horizontal and not args.pick and not args.pick_checkpoints:
            report['flip_audio_peak'] = audio_peak(build / 'prototype.wav')
            assert report['flip_audio_peak'] > 0.001, report
        report['max_load_ms'] = round(report['max_load_lines'] * 227 / 3546895 * 1000, 3)
        # Resume the same binary/state to verify the OS restoration path.
        env['COPPERLINE_DBG_AFTER'] = '18.5'
        env['COPPERLINE_DBG_RAMDUMP'] = f'C00000:80000:{build / "exit-slow.bin"}'
        with (build / 'exit.log').open('w') as log:
            subprocess.run([args.emulator, '--config', str(config), '--noaudio',
                            '--load-state', str(build / 'prototype.clstate'),
                            '--click-after', '17', 'left', '100',
                            '--screenshot-after', '19', str(build / 'exit.png')],
                           stdout=log, stderr=subprocess.STDOUT, env=env, check=True)
        exited = read_diagnostics(build / 'exit-slow.bin')
        assert exited['status'] == 2, exited
        report['exit_restored'] = True
        if args.transitions:
            env['COPPERLINE_DBG_AFTER'] = '13.4'
            env['COPPERLINE_DBG_RAMDUMP'] = f'C00000:80000:{build / "neighbor-slow.bin"}'
            with (build / 'neighbor.log').open('w') as log:
                subprocess.run([args.emulator, '--config', str(config), '--noaudio',
                                '--screenshot-after', '13.5', str(build / 'neighbor.png')],
                               stdout=log, stderr=subprocess.STDOUT, env=env, check=True)
            neighbor = read_diagnostics(build / 'neighbor-slow.bin')
            assert neighbor['room_index'] == 1 and neighbor['transitions'] == 1, neighbor
            assert neighbor['deaths'] == 0 and neighbor['respawns'] == 0, neighbor
            report['neighbor_player_pixels'] = visible_player(build, build / 'neighbor.png')
            report['neighbor_verified'] = True
        (build / 'smoke-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        assert report['video_headroom_passed'], report
        print(f'PASS: emulator smoke assertions; capture: {build / "prototype.png"}')
    else:
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
