#!/usr/bin/env python3
"""All SDR words, physical key lifetimes, aliases and protocol messages."""
import ctypes as C
import random
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
class Keyboard(C.Structure):
    _fields_=[('down',C.c_uint8*16)]
def wire(code):
    # Reference transmitter sends bits 6,5,4,3,2,1,0,7 active-low.
    bits=[(code>>bit)&1 for bit in (6,5,4,3,2,1,0,7)]
    return sum((1-bit)<<(7-i) for i,bit in enumerate(bits))
def main():
    out=ROOT/'build/amiga-keyboard';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/keyboard.c'),'-o',str(out/'keyboard.so')],check=True)
    lib=C.CDLL(str(out/'keyboard.so'))
    lib.v6_keyboard_decode.argtypes=[C.c_uint]
    lib.v6_keyboard_receive.argtypes=[C.POINTER(Keyboard),C.c_uint]
    lib.v6_keyboard_map_buttons.argtypes=[C.POINTER(Keyboard)]
    for code in range(256):assert lib.v6_keyboard_decode(wire(code))==code
    def check(k,held):
        assert bytes(k)==bytes(sum((key in held)<<bit for bit,key in enumerate(range(i*8,i*8+8))) for i in range(16))
        expected=(1 if held&{0x43,0x44} else 0)|(2 if 0x4f in held else 0)|(4 if 0x4e in held else 0)|(8 if held&{0x40,0x31,0x34} else 0)
        assert lib.v6_keyboard_map_buttons(C.byref(k))==expected
    k=Keyboard();held=set()
    rng=random.Random(443501)
    stream=[0x43,0x44,0xc3,0xc4,0x40,0x31,0x34,0xc0,0xb1,0xb4]+[rng.randrange(256) for _ in range(20000)]
    for code in stream:
        key=code&127
        if key>=0x78:
            if code in (0xf9,0xfa,0xfc,0xfd):held.clear()
        elif code&128:held.discard(key)
        else:held.add(key)
        lib.v6_keyboard_receive(C.byref(k),wire(code));check(k,held)
    print('PASS keyboard: 256 manual transmission vectors; 20,010 physical key/protocol events, independent aliases and binding masks')
if __name__=='__main__':main()
