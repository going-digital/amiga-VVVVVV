#!/usr/bin/env python3
"""Building Apport save on DF1, fresh boot and source-bank rejection."""
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib
from run_interactive_save import config,EMU
from run_tower_probe import ROOT,diagnostics
from save_disk import create_save_disk,read_record
BUILD=ROOT/'build/amiga-building-save'
def capture(name):
    dump=BUILD/(name+'.bin');dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='39',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (BUILD/(name+'.log')).open('w') as log:
        subprocess.run([EMU,'--config',str(BUILD/'interactive-save.toml'),'--floppy-drives','2','--noaudio',
            '--screenshot-after','40',str(BUILD/(name+'.png'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();offset=data.index(b'V6BS\0\0\0\1')
    return struct.unpack_from('>12I',data,offset+8),dump

def corrupt_centre(path):
    image=bytearray(path.read_bytes());record=read_record(path)
    offsets=[i for i in range(24,len(image)-44,512) if image[i:i+44]==record]
    assert len(offsets)==1,offsets
    at=offsets[0];block=at-24
    struct.pack_into('>I',image,at+8,157)
    struct.pack_into('>I',image,at+40,zlib.crc32(image[at:at+40]))
    struct.pack_into('>I',image,block+20,0)
    struct.pack_into('>I',image,block+20,(-sum(struct.unpack_from('>128I',image,block)))&0xffffffff)
    path.write_bytes(image)

def main():
    disk=BUILD/'capture-save-disk.adf';disk.unlink(missing_ok=True)
    create_save_disk(BUILD/'tower.adf',disk);config(BUILD,disk)
    boot=(BUILD/'tower.adf').read_bytes()
    first,dump=capture('save')
    display=diagnostics(dump)
    assert first[:3]==(1,0,0) and first[3:9]==(156,92,0,111,104,0),first
    assert display['status']==2 and display['error']==display['missed']==0 and display['max_work_lines']<=250,display
    record=read_record(disk);assert struct.unpack_from('>7iI',record,8)==(156,92,0,0,111,104,0,0)
    cold,cold_dump=capture('cold')
    cold_display=diagnostics(cold_dump)
    assert cold[:3]==(2,0,0) and cold[3:9]==first[3:9] and cold[9:]==(156,92,1),cold
    assert cold_display['status']==2 and cold_display['error']==cold_display['missed']==0 and cold_display['max_work_lines']<=250,cold_display
    assert read_record(disk)==record
    corrupt_centre(disk);before=disk.read_bytes()
    rejected,reject_dump=capture('invalid')
    assert rejected[:3]==(2,4,1),rejected
    raw=reject_dump.read_bytes();offset=raw.index(b'V6TP\0\0\0\6')
    assert struct.unpack_from('>I',raw,offset+8)[0]==0  # rejected before takeover
    assert disk.read_bytes()==before and (BUILD/'tower.adf').read_bytes()==boot
    report=dict(first=first,cold=cold,rejected=rejected,display=display,cold_display=cold_display,
        scope='Teleporter checkpoint DF1 commit, fresh-boot centre restore and CRC-valid wrong-centre rejection before takeover; native fixture accepts only Building Apport with zero story flags')
    (BUILD/'save-capture.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS Building save:',json.dumps(report))
if __name__=='__main__':main()
