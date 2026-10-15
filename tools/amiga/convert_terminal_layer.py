"""Private terminal row packets, produced by the source-checked compositor."""
import ctypes as C
import subprocess
from terminal_scripts import export
from test_terminal_read import Page, Program, VM
from test_map_draw import arrays
from test_player import ROOT


def packet(data):
    out = bytearray()
    at = 0
    while at < len(data):
        end = at+1
        while end < len(data) and data[end] == data[at] and end-at < 128:
            end += 1
        if end-at >= 3:
            out.extend((128+end-at-1, data[at]))
            at = end
        else:
            start = at
            at = end
            while at < len(data) and at-start < 128:
                if at+2 < len(data) and data[at] == data[at+1] == data[at+2]:
                    break
                at += 1
            out.append(at-start-1)
            out.extend(data[start:at])
    return out


def build(out):
    data = export(out)
    library = out/'terminal-row-converter.so'
    subprocess.run(['cc', '-std=c99', '-O2', '-shared', '-fPIC',
                    str(ROOT/'amiga_version/terminal_read.c'), '-o', str(library)], check=True)
    lib = C.CDLL(str(library))
    pages = (Page*2)()
    strings = []
    for i, p in enumerate(data['pages']):
        text = [line.encode() for line in p['lines']]
        strings += text
        pages[i] = Page(p['x'], p['y'], p['flip'], len(text), (C.c_char_p*6)(*text))
    vm = VM()
    program = Program(pages, 2)
    lib.v6_terminal_read_start.argtypes = [C.POINTER(VM), C.POINTER(Program)]
    assert lib.v6_terminal_read_start(C.byref(vm), C.byref(program))
    assert [(b.x,b.y,b.w,b.h) for b in vm.boxes] == [(12,60,296,24),(36,86,248,69)]
    for b in vm.boxes:
        b.visible = 1
    font = (C.c_uint8*1024)(*arrays(out/'dialogue_font.h', 'dialogue_font'))
    border = (C.c_uint8*64)(*arrays(out/'pickup_assets.h', 'pickup_border'))
    row = (C.c_uint8*80)()
    lib.v6_terminal_read_row.argtypes = [C.POINTER(C.c_uint8), C.c_uint, C.POINTER(VM),
                                        C.POINTER(C.c_uint8), C.POINTER(C.c_uint8), C.c_int]
    offsets, encoded = [0], bytearray()
    for y in range(48, 168):
        assert lib.v6_terminal_read_row(row, y, C.byref(vm), font, border, 0)
        ink = bytearray(bytes(row)[40:])
        box = next((b for b in vm.boxes if b.y <= y < b.y+b.h), None)
        if box:
            local = y-box.y
            if local < 8 or local >= box.h-8:
                bottom = local >= box.h-8
                by = local-(box.h-8) if bottom else local
                tiles = (5,6,7) if bottom else (0,1,2)
                ink = bytearray([border[tiles[0]*8+by]] +
                    [border[tiles[1]*8+by]]*38 + [border[tiles[2]*8+by]])
            else:
                for x in (*range(box.x,box.x+8), *range(box.x+box.w-8,box.x+box.w)):
                    ink[x//8] &= ~(128 >> (x&7))
                by = (local-8)&7
                if box.h&7 and local>=box.h-16: by=local-(box.h-16)
                ink[0],ink[39] = border[24+by],border[32+by]
        encoded += packet(ink)
        offsets.append(len(encoded))
    assert len(encoded) < 65536
    (out/'terminal_layer_assets.h').write_text('/* Private full-width one-plane terminal rows. */\n'+
        'static const uint16_t terminal_row_offsets[121]={'+','.join(map(str,offsets))+'};\n'+
        'static const uint8_t terminal_row_packets[]={'+','.join(map(str,encoded))+'};\n')
    print('Terminal layer:', len(encoded), 'packet bytes; 120 source rows')
