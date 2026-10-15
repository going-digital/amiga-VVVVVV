#!/usr/bin/env python3
"""Lossless boot expansion: exact private PCM, overlap, bounds and malformed input."""
import ctypes as C
from pathlib import Path
import random
import subprocess
from sample_pack import pack,pack_pcm
from test_player import ROOT


def main():
    build = ROOT/'build/amiga-sample-unpack'
    build.mkdir(parents=True, exist_ok=True)
    library = build/'sample_unpack.so'
    subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-shared', '-fPIC', '-fsanitize=undefined', '-fno-sanitize-recover=all',
                    str(ROOT/'amiga_version/sample_unpack.c'), '-o', str(library)], check=True)
    lib = C.CDLL(str(library))
    lib.v6_sample_unpack.argtypes = [C.c_void_p, C.c_uint, C.c_void_p, C.c_uint]
    lib.v6_sample_unpack_delta.argtypes = lib.v6_sample_unpack.argtypes
    rng = random.Random(8341)
    cases = [b'A'*20000, bytes(range(256))*40, b'ABCD'*1300,
             bytes(rng.randrange(256) for _ in range(20000))]
    cases += [bytes(rng.randrange(8) for _ in range(n)) for n in range(1, 80)]
    private = list((ROOT/'build/amiga-feasibility').glob('prize-*.pcm'))
    assert len(private) == 2, 'Run tower-assets first'
    cases += [p.read_bytes() for p in private]
    saved = 0
    for source in cases:
        encoded = pack(source)
        out = (C.c_uint8*(len(source)+2))()
        out[0] = out[-1] = 173
        assert lib.v6_sample_unpack(C.byref(out, 1), len(source), encoded, len(encoded))
        assert bytes(out)[1:-1] == source
        assert out[0] == out[-1] == 173
        assert not lib.v6_sample_unpack(C.byref(out, 1), len(source), encoded, len(encoded)-1)
        assert not lib.v6_sample_unpack(C.byref(out, 1), len(source), encoded+b'\0', len(encoded)+1)
        if len(source) > 1:
            assert not lib.v6_sample_unpack(C.byref(out, 1), len(source)-1, encoded, len(encoded))
        assert out[0] == out[-1] == 173
    # Independent hand-authored streams: one literal, overlapping match;
    # impossible first offset; output overflow; truncated match; missing flags.
    out = C.create_string_buffer(19)
    assert lib.v6_sample_unpack(out, 19, b'\x01A\x00\x0f', 4) and out.raw == b'A'*19
    for capacity, stream in [(3, b'\0\0\0'), (2, b'\x01A\0\0'),
                             (4, b'\x01A\0'), (1, b'')]:
        assert not lib.v6_sample_unpack(out, capacity, stream, len(stream))
    for path in private:
        source = path.read_bytes()
        saved += len(source)-len(pack_pcm(source))
    pcm_files=list((ROOT/'build/amiga-feasibility').glob('*.pcm'))
    for path in pcm_files:
        source=path.read_bytes();encoded=pack_pcm(source);out=C.create_string_buffer(len(source))
        assert lib.v6_sample_unpack_delta(out,len(source),encoded,len(encoded))
        assert out.raw==source,path.name
    print('PASS boot PCM:', len(cases), 'exact expansions, overlap and malformed/bounds checks;', saved, 'resident bytes saved;',len(pcm_files),'exact delta-PCM expansions')


if __name__ == '__main__':
    main()
