#!/usr/bin/env python3
"""Independently render a tracker module using a supplied local libxmp library.

No library is bundled. Output is bounded, stereo signed 16-bit PCM at 48 kHz.
The final libxmp buffer can include silence padding after the first loop.
"""
import argparse
import ctypes as c
import hashlib
import json
from pathlib import Path
import sys
import wave


def render(library, module, output, seconds=30):
    if not 0 < seconds <= 120:
        raise ValueError('preview limit must be 0..120 seconds')
    if sys.byteorder != 'little':
        raise ValueError('renderer currently requires a little-endian host')
    lib = c.CDLL(str(Path(library).resolve()))
    ctx_type = c.c_void_p
    lib.xmp_create_context.restype = ctx_type
    declarations = {
        'xmp_load_module': ([ctx_type, c.c_char_p], c.c_int),
        'xmp_start_player': ([ctx_type, c.c_int, c.c_int], c.c_int),
        'xmp_play_buffer': ([ctx_type, c.c_void_p, c.c_int, c.c_int], c.c_int),
        'xmp_end_player': ([ctx_type], None),
        'xmp_release_module': ([ctx_type], None),
        'xmp_free_context': ([ctx_type], None),
    }
    for name, (args, result) in declarations.items():
        fn = getattr(lib, name)
        fn.argtypes = args
        fn.restype = result
    ctx = lib.xmp_create_context()
    if not ctx:
        raise RuntimeError('libxmp context allocation failed')
    loaded = started = False
    frames = 0
    ended = False
    try:
        result = lib.xmp_load_module(ctx, str(Path(module).resolve()).encode())
        if result:
            raise ValueError('libxmp rejected module: '+str(result))
        loaded = True
        result = lib.xmp_start_player(ctx, 48000, 0)
        if result:
            raise RuntimeError('libxmp player failed: '+str(result))
        started = True
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output), 'wb') as wav:
            wav.setparams((2, 2, 48000, 0, 'NONE', 'not compressed'))
            limit = round(seconds*48000)
            while frames < limit:
                count = min(4800, limit-frames)
                buffer = c.create_string_buffer(count*4)
                result = lib.xmp_play_buffer(ctx, buffer, len(buffer), 1)
                if result not in (0, -1):
                    raise RuntimeError('libxmp replay failed: '+str(result))
                wav.writeframes(buffer.raw)
                frames += count
                if result == -1:
                    ended = True
                    break
    finally:
        if started:
            lib.xmp_end_player(ctx)
        if loaded:
            lib.xmp_release_module(ctx)
        lib.xmp_free_context(ctx)
    return dict(module_sha256=hashlib.sha256(Path(module).read_bytes()).hexdigest(),
                library_sha256=hashlib.sha256(Path(library).read_bytes()).hexdigest(),
                sample_rate=48000, channels=2, frames=frames, seconds=frames/48000,
                first_loop_reached=ended, padding_bound_seconds=.1)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('module', type=Path)
    p.add_argument('--library', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--seconds', type=float, default=30)
    a = p.parse_args()
    report = render(a.library, a.module, a.out, a.seconds)
    a.out.with_suffix('.render.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
