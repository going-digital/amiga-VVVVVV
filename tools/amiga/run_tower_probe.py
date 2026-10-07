#!/usr/bin/env python3
"""Capture the standalone tower on Copperline's PAL A500 profile."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build/amiga-tower'
EMU = '/Applications/Copperline.app/Contents/MacOS/copperline'


def diagnostics(path):
    data = path.read_bytes()
    for offset in range(0, len(data)-104+1, 2):
        if data[offset:offset+8] == b'V6TP\0\0\0\6':
            values = struct.unpack_from('>26I', data, offset)
            if values[2] in (1, 2):
                return dict(zip(('magic', 'version', 'status', 'frames', 'camera',
                                 'max_work_lines', 'missed', 'error', 'chip_bytes', 'forward_wraps',
                                 'reverse_wraps', 'max_rows', 'max_copied', 'step', 'route_min', 'route_max',
                                 'visited_min', 'visited_max', 'logic_ticks', 'logic_frames',
                                 'logic_remainder', 'camera_mode', 'recovery_calls', 'recovery_life',
                                 'recovery_delay', 'recovery_seek_frames'), values))
    raise RuntimeError('No live tower diagnostics')


def main():
    global BUILD
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=BUILD)
    parser.add_argument('--step', type=int, choices=(1,4,8,12,16), default=1)
    parser.add_argument('--measure', action='store_true', help='Report frame overruns without treating them as test failures')
    parser.add_argument('--controller', action='store_true', help='Validate the normal descending camera at the 34 ms logic cadence')
    parser.add_argument('--recovery', action='store_true', help='Validate scripted native camera recovery against extracted desktop blocks')
    parser.add_argument("--play", action="store_true", help="Validate live physics and natural death/respawn replay")
    parser.add_argument("--interactive", action="store_true", help="Run the built disk with joystick controls until mouse exit")
    parser.add_argument("--world", action="store_true", help="Validate tower checkpoints and horizontal boundaries")
    parser.add_argument('--wrap',action='store_true',help='Validate normal-input horizontal wrap replay')
    parser.add_argument('--route',action='store_true',help='Validate tower/hallway crossings and staged display loads')
    parser.add_argument('--upper-route',action='store_true',help='Validate upper entry and natural hazard remote checkpoint return')
    args = parser.parse_args()
    if args.upper_route: args.route=True
    if args.wrap or args.route: args.world=True
    if args.world:
        args.play=True
    if args.recovery or args.play:
        args.controller = True
    BUILD = args.build.resolve()
    config = BUILD / 'tower.toml'
    config.write_text(f'''rom = {json.dumps(str(Path.home() / 'amiga/KICK13.ROM'))}
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
''')
    if args.interactive:
        subprocess.run([EMU,"--config",str(config),"--noaudio"],check=True)
        return
    env = dict(os.environ, COPPERLINE_DBG_AFTER='41',
               COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{BUILD / "slow.bin"}')
    for name in ('slow.bin','tower.clstate','tower.png','capture.json'):
        (BUILD/name).unlink(missing_ok=True)
    with (BUILD / 'capture.log').open('w') as log:
        subprocess.run([EMU, '--config', str(config), '--noaudio',
                        '--save-state-after', '40', str(BUILD / 'tower.clstate'),
                        '--screenshot-after', '42', str(BUILD / 'tower.png')],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    report = diagnostics(BUILD / 'slow.bin')
    if args.play:
        data=(BUILD/'slow.bin').read_bytes()
        offset=data.index(b'V6PF\0\0\0\1')
        values=struct.unpack_from('>8I',data,offset)
        report['profile']=dict(zip(('max_logic','max_render','peak_logic','peak_render','peak_tick','peak_rows'),values[2:]))
        timing=report['profile']
        assert timing['peak_logic']+timing['peak_render']==report['max_work_lines'],report
        assert timing['peak_logic']<=timing['max_logic'] and timing['peak_render']<=timing['max_render'],report
    assert report['step'] == (0 if args.controller else args.step), report
    if args.controller:
        assert report['logic_ticks'] > 100, report
        assert report['logic_ticks']*34000+report['logic_remainder'] == report['logic_frames']*19968, report
        assert 0 <= report['logic_remainder'] < 34000, report
        if args.route:
            from tower_route_trace import verify
            verify(report, BUILD/'slow.bin',args.upper_route)
        elif args.world:
            from tower_world_trace import verify
            verify(report, BUILD / "slow.bin",args.wrap)
        elif args.play:
            from tower_play_trace import verify
            verify(report, BUILD / "slow.bin")
        elif args.recovery:
            from tower_recovery_trace import verify
            verify(report, BUILD / 'slow.bin')
        else:
            assert report['camera'] == min(5368, 2*(report['logic_ticks']-1)), report
    elif report['route_min'] == 0:
        assert report['visited_min'] == 0 and report['visited_max'] == report['route_max'], report
    assert report['status'] == 1 and report['error'] == 0, report
    assert report['frames'] > 256 and report['max_work_lines'] > 0, report
    if not args.measure:
        assert report['missed'] == 0 and report['max_work_lines'] < 312, report
        if args.play:
            assert report['max_work_lines'] <= 250, report
    if args.play:
        visible_capture=BUILD/'tower.png'
        if args.world:
            visible_capture=BUILD/'tower-live.png'
            visible_capture.unlink(missing_ok=True)
            with (BUILD/'live-capture.log').open('w') as log:
                subprocess.run([EMU,'--config',str(config),'--noaudio','--screenshot-after','15',str(visible_capture)],
                    env=dict(os.environ),stdout=log,stderr=subprocess.STDOUT,check=True)
        decoder=ROOT/'build/amiga-feasibility/png_rgba'
        header,pixels=subprocess.check_output([str(decoder),str(visible_capture)]).split(b'\n',1)
        width,height=map(int,header.split())
        assert len(pixels)==width*height*4
        report['visible_player_pixels']=sum(1 for i in range(0,len(pixels),4)
            if pixels[i+1]>150 and pixels[i+2]>150 and pixels[i]<pixels[i+1]*0.8)
        assert report['visible_player_pixels']>20,report
        if args.world:
            report['visible_active_checkpoint_pixels']=sum(1 for i in range(0,len(pixels),4)
                if pixels[i+1]>150 and pixels[i+1]>pixels[i]*1.5 and pixels[i+1]>pixels[i+2]*1.5)
            if not args.route: assert report['visible_active_checkpoint_pixels']>20,report
        report['headroom_20_percent']=report['max_work_lines']<=250
    if not args.controller:
        assert report['forward_wraps'] >= 1 and report['reverse_wraps'] >= 1, report
    if not args.play:
        assert report['max_rows'] <= (2*args.step+7)//8 + (args.step+7)//8, report
    assert report['chip_bytes'] == (64128 if args.play else 61696), report
    env.update(COPPERLINE_DBG_AFTER='43',
               COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{BUILD / "exit.bin"}')
    for name in ('exit.bin','exit.png'):
        (BUILD/name).unlink(missing_ok=True)
    with (BUILD / 'exit.log').open('w') as log:
        subprocess.run([EMU, '--config', str(config), '--noaudio',
                        '--load-state', str(BUILD / 'tower.clstate'),
                        '--click-after', '41', 'left', '100',
                        '--screenshot-after', '44', str(BUILD / 'exit.png')],
                       env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    stopped = diagnostics(BUILD / 'exit.bin')
    assert stopped['status'] == 2 and stopped['error'] == 0, stopped
    report['restored'] = True
    report['synthetic_step'] = None if args.controller else args.step
    report['within_frame_budget'] = report['missed'] == 0 and report['max_work_lines'] < 312
    report['scope'] = 'Three-plane hardware parallax: forward/reverse source-map seam and exit smoke test; moving screenshot not pixel-compared; synthetic route defined by route_min/route_max'
    if args.controller:
        report['scope'] = 'Native normal descending camera at 34 ms logic cadence using 19968 us PAL accounting; held positions between ticks, no interpolation, player or recovery integration'
    if args.recovery:
        report['scope'] = 'Native same-tower player checkpoint respawn; first 128 camera/player ticks and final camera state checked; no live player physics or sprite display'
    if args.play:
        report['scope'] = 'Native tower input/physics, sprite and natural damage/recovery; 128 ticks match host integration; isolated source differential tests verify physics; no full desktop entity loop'
    if args.world:
        report['scope'] = 'Main-tower checkpoint-area normal-input route to a second checkpoint and natural recovery; 128 camera/player/checkpoint ticks match host integration; room exits request a load but are not yet loaded'
        if args.wrap:
            report['scope']='Main-tower normal-input horizontal wraps in both directions and natural recovery; 128 camera/player/checkpoint ticks match host integration; adjacent room loads remain pending'
        if args.route:
            report['scope']=('Upper entrance and Seeing Red checkpoint contact through ordinary input; natural spike death after tower re-entry restores saved hallway; ' if args.upper_route else 'Lower tower/hallway crossings and natural checkpoint recovery; ')+ 'staged display loads and first 128 ticks match host integration; crew/scripts omitted'
    (BUILD / 'capture.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
