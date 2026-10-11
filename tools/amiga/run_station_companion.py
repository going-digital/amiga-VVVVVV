#!/usr/bin/env python3
"""Native Energize restraint trace against original yellow AI and physics."""
import ctypes as C
import json
import os
import struct
import subprocess
from run_tower_probe import ROOT,EMU,diagnostics
from test_player import Player
from test_tower_player import OUT
from tower_gameplay_data import energize_room
from run_interactive_save import config

def main():
    build=ROOT/'build/amiga-station-companion';cfg=config(build,build/'unused.adf')
    cfg.write_text(cfg.read_text().split('[floppy.df1]')[0])
    dump=build/'companion.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='75',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'capture.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--noaudio','--screenshot-after','76',str(build/'companion.png'),'--click-after','78','left','200'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    display=diagnostics(dump);assert display['error']==display['missed']==0 and display['max_work_lines']<312,display
    data=dump.read_bytes();at=data.index(b'V6CT\0\0\0\1');assert struct.unpack_from('>I',data,at+8)[0]==128
    records=[struct.unpack_from('>14I',data,at+16+56*i) for i in range(128)]
    source=C.CDLL(str(OUT/'station_crew_reference.so'));source.crew_init.argtypes=[C.POINTER(Player),C.POINTER(C.c_uint16)];source.crew_tick.argtypes=[C.c_int]*5+[C.POINTER(Player),C.POINTER(C.c_int)]
    body=Player();body.x=body.old_x=320;body.y=body.old_y=86;body.gravity=1;body.dir=0
    tiles=(C.c_uint16*1200)(*energize_room()['tiles']);source.crew_init(C.byref(body),tiles);frame=C.c_int()
    for tick,record in enumerate(records):
        source.crew_tick(64,110,105,1,-1,C.byref(body),C.byref(frame))
        assert record[:3]==(1,1,0)
        expected=tuple(value&0xffffffff for value in (body.x,body.y,body.vx,body.vy,body.dir))
        assert record[4:9]==expected,(tick,record[4:9],expected)
    # Inertia crosses the threshold, then settles; do not clamp to x=155.
    assert records[-1][4]<155 and records[-1][6]==0,records[-1]
    report=dict(headroom_20_percent=display['max_work_lines']<=250,source_fields_compared=128*5,resting_x=records[-1][4],display=display,scope='Native station room-110,105 entry and AI-1 restraint against extracted source; no rescue replay')
    (build/'companion-capture.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native yellow companion:',json.dumps(report))
if __name__=='__main__':main()
