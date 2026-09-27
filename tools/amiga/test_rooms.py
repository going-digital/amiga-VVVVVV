#!/usr/bin/env python3
"""Exercise the actual C decoder against every source initializer and bad packets."""
import ctypes
from pathlib import Path
import random
import struct
import subprocess
import tempfile

from pack_rooms import ROOT, encode, extract


def main():
    with tempfile.TemporaryDirectory(prefix='v6-codec-') as tmp:
        library = Path(tmp) / 'codec.so'
        subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        str(ROOT / 'amiga_version/room_codec.c'), '-o', str(library)], check=True)
        decode = ctypes.CDLL(str(library)).v6_unpack_room
        decode.argtypes = [ctypes.c_char_p, ctypes.c_size_t,
                           ctypes.POINTER(ctypes.c_uint16), ctypes.c_size_t]
        decode.restype = ctypes.c_int

        def check(packed, expected):
            dst = (ctypes.c_uint16 * (len(expected) + 2))()
            dst[0], dst[-1] = 0x1234, 0xabcd
            ptr = ctypes.cast(ctypes.byref(dst, 2), ctypes.POINTER(ctypes.c_uint16))
            assert decode(packed, len(packed), ptr, len(expected)) == 1
            assert list(dst)[1:-1] == expected
            assert dst[0] == 0x1234 and dst[-1] == 0xabcd

        records = extract()
        for meta, raw, packed in records:
            check(packed, list(struct.unpack('>1200H', raw)))
        rng = random.Random(6)
        for n in (0, 1, 2, 3, 1200, 32767, 32768):
            for values in ([65535] * n, [rng.randrange(65536) for _ in range(n)]):
                check(encode(values), values)
        dst = (ctypes.c_uint16 * 4)(1, 2, 3, 4)
        for bad in (b'', b'\x80', b'\x00\x00', b'\x80\x01',
                    b'\x80\x05\x00\x00', b'\x00\x04\x00\x00',
                    b'\x80\x04\x00\x00\xff'):
            assert decode(bad, len(bad), dst, 4) == 0, bad
        # Verify pack directory, deduplicated offsets, and checksums, not just codec.
        import zlib
        blob = (ROOT / 'build/amiga/rooms.v6rp').read_bytes()
        assert struct.unpack_from('>4sHHI', blob) == (b'V6RP', 1, len(records), 12)
        for i, (_, raw, _) in enumerate(records):
            offset, size, crc = struct.unpack_from('>III', blob, 12 + i * 12)
            assert offset >= 12 + len(records) * 12 and offset + size <= len(blob)
            assert crc == zlib.crc32(raw)
            check(blob[offset:offset + size], list(struct.unpack('>1200H', raw)))
        print(f'PASS: {len(records)} source arrays and pack records; run boundaries; malformed input')


if __name__ == '__main__':
    main()
