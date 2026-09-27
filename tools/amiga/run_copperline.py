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


def audio_peak(path, start_seconds=12.9, end_seconds=13.5):
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
    start = int(start_seconds * fmt[2]) * fmt[4]
    end = int(end_seconds * fmt[2]) * fmt[4]
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
    pixels=sum(rgba[i]>245 and 80<rgba[i+1]<125 and 170<rgba[i+2]<200
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
    parser.add_argument('--waiting', action='store_true')
    parser.add_argument('--horizontal', action='store_true')
    parser.add_argument('--crush', action='store_true')
    parser.add_argument('--retrigger', action='store_true')
    parser.add_argument('--disappearing', action='store_true')
    parser.add_argument('--beneath-route', action='store_true')
    parser.add_argument('--beneath', action='store_true')
    parser.add_argument('--pick', action='store_true')
    parser.add_argument('--pick-checkpoints', action='store_true')
    parser.add_argument('--pick-route', action='store_true')
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
        command += ([] if args.waiting or args.retrigger or args.beneath_route or args.beneath or args.platform or args.horizontal or args.crush or args.disappearing or args.pick or args.pick_checkpoints or args.pick_route else
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
        elif args.pick_route:
            trace=json.loads((ROOT/'build/amiga/pick-route-trace.json').read_text())
            assert 0<report['ticks']<=len(trace), report
            for field,value in trace[report['ticks']-1].items():
                assert report[field]==value, (field,report[field],value)
            assert report['checkpoint']==2 and report['deaths']==1 and report['respawns']==1, report
            assert report['enemy_hits']>=15 and report['exits']==0, report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
            report['native_host_trace_tick_verified']=report['ticks']
            report['route_scope']='Normal-input traversal and ride, then requested restart; host integration trace, not independent desktop-loop equivalence'
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
        elif args.beneath_route:
            trace=json.loads((ROOT/'build/amiga/beneath-replay-trace.json').read_text())
            assert report['ticks']==report['renders'] and 0<report['ticks']<=len(trace),report
            for field,value in trace[report['ticks']-1].items():
                assert report[field]==value,(field,report[field],value)
            assert report['deaths']==1 and report['respawns']==1 and report['enemy_hits']==3,report
            assert report['max_sprite_channels']==7 and report['exits']==0 and report['flips']==3,report
            report['native_host_trace_tick_verified']=report['ticks']
            report['scope']='Normal-input route: all three platform collapses, ceiling-spike death and checkpoint respawn; native host trace, not full desktop-loop equivalence'
        elif args.beneath:
            assert report['enemy_ticks']>100 and report['max_sprite_channels']==7,report
            assert report['checkpoint']==1 and report['exits']==0,report
            assert report['player_x']==60 and report['player_y']==145,report
            assert report['enemy_hits']==0 and report['deaths']==0,report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
            header,rgba=subprocess.check_output([str(build/'png_rgba'),str(build/'prototype.png')]).split(b'\n',1)
            width,height=map(int,header.split())
            columns=sorted({(i//4)%width for i in range(0,len(rgba),4)
                            if rgba[i]>245 and 80<rgba[i+1]<125 and 170<rgba[i+2]<210})
            bands=sum(i==0 or x-columns[i-1]>8 for i,x in enumerate(columns))
            assert bands==3, ('Expected three visible platforms',bands)
            report['visible_platform_bands']=bands
            report['scope']='Original room idle smoke: checkpoint and three platforms; no traversal or collapse asserted'
        elif args.pick:
            assert report['enemy_ticks']>100 and report['max_sprite_channels']==3, report
            assert report['checkpoint']==1, report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
        elif args.retrigger:
            trace=json.loads((ROOT/'build/amiga/retrigger-replay-trace.json').read_text())
            assert report['ticks']==report['renders'] and 0<report['ticks']<=len(trace),report
            for field,value in trace[report['ticks']-1].items():
                assert report[field]==value,(field,report[field],value)
            assert report['deaths']>=2 and report['respawns']>=2 and report['enemy_hits']>=3,report
            assert report['enemy_y']>4 and report['exits']==0 and report['max_sprite_channels']==3,report
            report['native_host_trace_tick_verified']=report['ticks']
            report['scope']='Synthetic checkpoint on disappearing platform; automatic recharge contact and extended frames'
        elif args.disappearing:
            trace=json.loads((ROOT/'build/amiga/disappearing-replay-trace.json').read_text())
            assert report['ticks']==report['renders'] and 0<report['ticks']<=len(trace),report
            for field,value in trace[report['ticks']-1].items():
                assert report[field]==value,(field,report[field],value)
            assert report['deaths']==1 and report['respawns']==1 and report['enemy_x']==0,report
            assert report['enemy_hits']==1 and report['exits']==0 and report['max_sprite_channels']==3,report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
            report['native_host_trace_tick_verified']=report['ticks']
            report['disappear_audio_peak']=audio_peak(build/'prototype.wav',10,11.5)
            report['background_audio_peak']=audio_peak(build/'prototype.wav')
            assert report['disappear_audio_peak']>max(0.01,2*report['background_audio_peak']),report
            report['fixture']='Synthetic disappearing platform: initialized on platform, respawn at safe ledge; native host trace'
        elif args.crush:
            trace=json.loads((ROOT/'build/amiga/crush-replay-trace.json').read_text())
            assert 0<report['ticks']<=len(trace),report
            for field,value in trace[report['ticks']-1].items():
                assert report[field]==value,(field,report[field],value)
            assert report['deaths']>=1 and report['respawns']>=1 and report['enemy_hits']>0,report
            assert report['exits']==0 and report['max_sprite_channels']==3,report
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
            report['native_host_trace_tick_verified']=report['ticks']
            report['fixture']='Synthetic upward spike push; host slice trace, not a complete desktop-loop replay'
        elif args.waiting:
            trace=json.loads((ROOT/'build/amiga/waiting-reference-trace.json').read_text())
            assert 0<report['ticks']<=len(trace),report
            for field,value in trace[report['ticks']-1].items():
                assert report[field]==value,(field,report[field],value)
            assert report['enemy_hits']>100 and report['max_sprite_channels']==3,report
            assert report['deaths']==0 and report['exits']==0,report
            report['desktop_transport_tick_verified']=report['ticks']
            report['visible_platform_pixels']=visible_enemy(build,build/'prototype.png')
            report['scope']='Synthetic waiting platform: externally staged hidden trigger after 20 ticks, then no-input ride; source movement/transport trace'
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
        if not args.waiting and not args.retrigger and not args.beneath_route and not args.beneath and not args.traffic and not args.platform and not args.horizontal and not args.crush and not args.disappearing and not args.pick and not args.pick_checkpoints and not args.pick_route:
            assert report['deaths'] >= 1 and report['respawns'] >= 1, report
        # Snapshot can land between a tick and completion of its render.
        assert report['ticks'] > 100 and 0 <= report['ticks'] - report['renders'] <= 1, report
        report['video_headroom_passed'] = report['missed_frames'] == 0 and report['max_work_lines'] < 250
        report['max_work_ms'] = round(report['max_work_lines'] * 227 / 3546895 * 1000, 3)
        if not args.waiting and not args.retrigger and not args.beneath_route and not args.beneath and not args.transitions and not args.enemy and not args.traffic and not args.platform and not args.horizontal and not args.crush and not args.disappearing and not args.pick and not args.pick_checkpoints and not args.pick_route:
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
        if args.disappearing or args.beneath_route or args.retrigger:
            start_time=16.5-report['ticks']*0.034
            phases=[]
            targets=(('collapse',16,2),('hidden',60,0x444),('recharge',84,0x555)) if args.beneath_route else (('collapse',8,2),('hidden',28,4),('recharge',53,5))
            if args.retrigger: targets=(('extended',60,2),)
            for name,target_tick,state in targets:
                for attempt in range(3):
                    stamp=start_time+target_tick*0.034+0.012+attempt*0.006
                    env['COPPERLINE_DBG_AFTER']=str(round(stamp,6))
                    env['COPPERLINE_DBG_RAMDUMP']=f'C00000:80000:{build / (name+"-slow.bin")}'
                    with (build/(name+'.log')).open('w') as log:
                        subprocess.run([args.emulator,'--config',str(config),'--noaudio',
                            '--screenshot-after',str(round(stamp+0.004,6)),str(build/(name+'.png'))],
                            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
                    phase=read_diagnostics(build/(name+'-slow.bin'))
                    if phase['ticks']==phase['renders']:break
                assert phase['ticks']==phase['renders'],phase
                for field,value in trace[phase['ticks']-1].items():
                    assert phase[field]==value,(name,field,phase[field],value)
                assert phase['enemy_x']==state,(name,phase)
                if args.retrigger: assert phase['enemy_y']>4,phase
                _,rgba=subprocess.check_output([str(build/'png_rgba'),str(build/(name+'.png'))]).split(b'\n',1)
                pink=sum(rgba[i]>245 and 80<rgba[i+1]<125 and 170<rgba[i+2]<200 for i in range(0,len(rgba),4))
                assert (pink==0 if name=='hidden' else pink>20),(name,pink)
                record=dict(phase=name,tick=phase['ticks'],pink_pixels=pink)
                if args.beneath_route:
                    record['states']=[(phase['enemy_x']>>(4*i))&15 for i in range(3)]
                    record['frames']=[(phase['enemy_y']>>(4*i))&15 for i in range(3)]
                else:
                    record['frame']=phase['enemy_y']
                phases.append(record)
            report['phase_captures']=phases
        if args.waiting:
            phases=[]
            start_time=16.5-report['ticks']*0.034
            for name,target_tick in (('waiting',10),('carrying',40)):
                for attempt in range(3):
                    stamp=start_time+target_tick*0.034+0.012+attempt*0.006
                    env['COPPERLINE_DBG_AFTER']=str(round(stamp,6))
                    env['COPPERLINE_DBG_RAMDUMP']=f'C00000:80000:{build / (name+"-slow.bin")}'
                    with (build/(name+'.log')).open('w') as log:
                        subprocess.run([args.emulator,'--config',str(config),'--noaudio',
                            '--screenshot-after',str(round(stamp+0.004,6)),str(build/(name+'.png'))],
                            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
                    phase=read_diagnostics(build/(name+'-slow.bin'))
                    if phase['ticks']==phase['renders']:break
                assert phase['ticks']==phase['renders'] and 0<phase['ticks']<=len(trace),phase
                for field,value in trace[phase['ticks']-1].items():
                    assert phase[field]==value,(name,field,phase[field],value)
                assert phase['enemy_hits']==0 if name=='waiting' else phase['enemy_hits']>0
                phases.append(dict(phase=name,tick=phase['ticks'],player_x=phase['player_x'],
                    platform_x=phase['enemy_x'],carry_ticks=phase['enemy_hits']))
            report['phase_captures']=phases
        if args.crush:
            env['COPPERLINE_DBG_AFTER']='10.91'
            env['COPPERLINE_DBG_RAMDUMP']=f'C00000:80000:{build / "death-slow.bin"}'
            with (build/'death.log').open('w') as log:
                subprocess.run([args.emulator,'--config',str(config),'--noaudio',
                    '--screenshot-after','11',str(build/'death.png')],env=env,
                    stdout=log,stderr=subprocess.STDOUT,check=True)
            dying=read_diagnostics(build/'death-slow.bin')
            assert dying['ticks']==dying['renders'],'Death snapshot fell within an unfinished tick'
            assert 0<dying['ticks']<=len(trace),dying
            for field,value in trace[dying['ticks']-1].items():
                assert dying[field]==value,('death pause',field,dying[field],value)
            assert dying['death_timer']>0 and dying['deaths']==1 and dying['respawns']==0,dying
            assert dying['enemy_ticks']==1 and dying['enemy_y']==90,dying
            report['death_pause_tick_verified']=dying['ticks']
            report['death_player_pixels']=visible_player(build,build/'death.png')
            report['death_platform_pixels']=visible_enemy(build,build/'death.png')
        if args.pick_route:
            # Capture after reaching the second checkpoint but before restart.
            env['COPPERLINE_DBG_AFTER']='14.7'
            env['COPPERLINE_DBG_RAMDUMP']=f'C00000:80000:{build / "route-live-slow.bin"}'
            with (build/'route-live.log').open('w') as log:
                subprocess.run([args.emulator,'--config',str(config),'--noaudio',
                    '--screenshot-after','14.8',str(build/'route-live.png')],
                    stdout=log,stderr=subprocess.STDOUT,env=env,check=True)
            live=read_diagnostics(build/'route-live-slow.bin')
            reference=json.loads((ROOT/'build/amiga/pick-movement-reference.json').read_text())
            assert 124<=live['ticks']<=len(reference), live
            assert live['checkpoint']==2 and live['deaths']==0 and live['exits']==0, live
            for field,value in reference[live['ticks']-1].items():
                assert live[field]==value, ('desktop movement',field,live[field],value)
            report['desktop_movement_tick_verified']=live['ticks']
            report['checkpoint_reached_without_death']=True
        (build / 'smoke-report.json').write_text(json.dumps(report, indent=2) + '\n')
        print(json.dumps(report, indent=2))
        assert report['video_headroom_passed'], report
        print(f'PASS: emulator smoke assertions; capture: {build / "prototype.png"}')
    else:
        subprocess.run(command, check=True)


if __name__ == '__main__':
    main()
