"""Boot-only lossless PCM storage: LSB literal flags, 12-bit offset, 4-bit length."""
from collections import defaultdict, deque


def pack_pcm(data):
    return pack(bytes((v-(data[i-1] if i else 0)) & 255 for i,v in enumerate(data)))


def pack(data):
    history = defaultdict(deque)
    out = bytearray()
    at = 0
    while at < len(data):
        flag_at = len(out)
        out.append(0)
        for bit in range(8):
            if at == len(data):
                break
            key = data[at:at+3]
            candidates = history[key]
            while candidates and at-candidates[0] > 4096:
                candidates.popleft()
            length, distance = 0, 0
            for previous in reversed(candidates):
                n = 3
                while n < 18 and at+n < len(data) and data[previous+n] == data[at+n]:
                    n += 1
                if n > length:
                    length, distance = n, at-previous
                if length == 18:
                    break
            if length >= 3:
                token = ((distance-1) << 4) | (length-3)
                out.extend((token >> 8, token & 255))
                end = at+length
            else:
                out[flag_at] |= 1 << bit
                out.append(data[at])
                end = at+1
            while at < end:
                positions = history[data[at:at+3]]
                positions.append(at)
                if len(positions) > 64:
                    positions.popleft()
                at += 1
    return bytes(out)
