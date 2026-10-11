#!/usr/bin/env python3
"""West-route candidate geometry codec and pixels; native admission excluded."""
import ctypes as C
import subprocess
from tower_gameplay_data import ROOT,prize_return_room,export_prize_return_rooms
from pack_rooms import encode
from test_energize_graphics import main as graphics

def main():
    out=ROOT/'build/amiga-feasibility';export_prize_return_rooms(out)
    shim=out/'prize-return-data.c'
    shim.write_text('#include "checkpoints.h"\n#include "room_codec.h"\n'+
        '#include "deception_collision.h"\n#include "downunder_collision.h"\n'+
        'int exported_room(unsigned n,uint16_t *out) {return n ? '+
        'v6_unpack_room(downunder_packed,sizeof(downunder_packed),out,1200) : '+
        'v6_unpack_room(deception_packed,sizeof(deception_packed),out,1200); }\n'+
        'int exported_tile(unsigned n,unsigned i) {return n ? downunder_tiles[i] : deception_tiles[i];}\n'+
        'int exported_checkpoint(unsigned n,unsigned i,unsigned field) {\n'+
        'V6Checkpoint *p=n?&downunder_checkpoint[i]:&deception_checkpoint[i];\n'+
        'switch(field){case 0:return p->x;case 1:return p->y;case 2:return p->tile;default:return p->id;}}\n')
    subprocess.run(['cc' ,'-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        '-I'+str(ROOT/'amiga_version'),str(shim),str(ROOT/'amiga_version/room_codec.c'),'-o',str(out/'prize-return-codec.so')],check=True)
    core=C.CDLL(str(out/'prize-return-codec.so'))
    core.v6_unpack_room.argtypes=[C.c_char_p,C.c_size_t,C.POINTER(C.c_uint16),C.c_size_t]
    core.exported_room.argtypes=[C.c_uint,C.POINTER(C.c_uint16)]
    for index,(name,position) in enumerate((('deception',(110,107)),('downunder',(110,106)))):
        room=prize_return_room(name);assert (room['x'],room['y'])==position
        raw=encode(room['tiles']);decoded=(C.c_uint16*1200)()
        assert core.v6_unpack_room(raw,len(raw),decoded,1200)
        assert list(decoded)==room['tiles']
        assert core.exported_room(index,decoded)
        assert list(decoded)==room['tiles']==[core.exported_tile(index,i) for i in range(1200)]
        assert room['checkpoints']==[tuple(core.exported_checkpoint(index,i,j) for j in range(4)) for i in range(2)]
        assert len(room['checkpoints'])==2
        assert len(set(r[3] for r in room['checkpoints']))==2
        graphics(name,lambda:room)
        print(f'PASS {room["name"]}: 1200 C-decoded source tiles, {len(raw)} packed bytes, '
              f'{len(room["entities"])} ordered entity calls; candidate only')
if __name__=='__main__':main()
