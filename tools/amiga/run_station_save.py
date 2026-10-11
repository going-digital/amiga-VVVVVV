#!/usr/bin/env python3
"""Station V3 save, fresh-boot restoration and native checkpoint rejection."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib
from run_interactive_save import config,EMU
from run_tower_probe import diagnostics
from save_disk import create_save_disk,read_record

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--interactive',action='store_true');args=parser.parse_args();build=args.build.resolve()
    disk=build/('save-disk.adf' if args.interactive else 'capture-save-disk.adf')
    if not args.interactive:disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk);cfg=config(build,disk);boot=(build/'tower.adf').read_bytes()
    if args.interactive:
        print('Move left to rescue Vitellary; fire advances dialogue. Left mouse exits and saves completed progress on',disk)
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--joystick','keyboard'],check=True);return
    def capture(name,early=False):
        dump=build/(name+'.bin');dump.unlink(missing_ok=True)
        env=dict(os.environ,COPPERLINE_DBG_AFTER='75',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
        with (build/(name+'.log')).open('w') as log:
            subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                *(['--click-after','35','left','200'] if early else []),'--screenshot-after','76',str(build/(name+'.png'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        data=dump.read_bytes();at=data.index(b'V6SP\0\0\0\1');state=struct.unpack_from('>18I',data,at+8)
        display={'status':struct.unpack_from('>I',data,data.index(b'V6TP\0\0\0\6')+8)[0]} if name=='invalid' else diagnostics(dump)
        return state,display,data
    early,_,_=capture('early',True)
    assert early[:3]==(1,1,0) and early[16]==1,early
    # Mid-script rejection leaves no promoted record.
    try:read_record(disk,b'station.v6cs')
    except AssertionError:pass
    else:raise AssertionError('Early quit published a mid-script save')
    first,display,_=capture('save')
    assert first[:3]==(1,0,0) and first[3:10]==(188,86,1,0,111,105,441490),first
    assert first[10:13]==(0,0,0) and first[13:]==(1,1,7,1,11),first
    record=read_record(disk,b'station.v6cs')
    assert struct.unpack_from('>4sHH7iI',record)==(b'V6CS',3,96,188,86,1,0,111,105,441490,56),record.hex()
    assert record[40+(111>>3)] & (1<<(111&7))
    cold,cold_display,data=capture('cold')
    assert cold[:3]==(2,0,0) and cold[3:10]==first[3:10] and cold[10:13]==(1,1,7),cold
    assert cold[13:]==(1,1,7,0,0),cold
    at=data.index(b'V6CT\0\0\0\1');crew=struct.unpack_from('>14I',data,at+16)
    assert crew[4:6]==(188,86) and crew[:3]==(1,1,0),crew
    assert read_record(disk,b'station.v6cs')==record
    for d in (display,cold_display):
        assert d['status']==2 and d['error']==d['missed']==0 and d['max_work_lines']<=250 and d['chip_bytes']==116214,d
    # Checksum-valid shifted spawn must fail before takeover, leaving disk intact.
    image=bytearray(disk.read_bytes());headers=[]
    # Follow the active file header: freed OFS data blocks can retain old bytes.
    for header in range(0,len(image),512):
        if struct.unpack_from('>I',image,header)[0]!=2 or struct.unpack_from('>I',image,header+508)[0]!=0xfffffffd:continue
        n=image[header+432]
        if image[header+433:header+433+n]==b'station.v6cs':headers.append(header)
    assert len(headers)==1,headers
    block=struct.unpack_from('>I',image,headers[0]+16)[0]*512;at=block+24
    assert image[at:at+96]==record
    struct.pack_into('>I',image,at+8,189);struct.pack_into('>I',image,at+92,zlib.crc32(image[at:at+92]))
    struct.pack_into('>I',image,block+20,0);struct.pack_into('>I',image,block+20,(-sum(struct.unpack_from('>128I',image,block)))&0xffffffff);disk.write_bytes(image)
    before=disk.read_bytes();rejected,reject_display,_=capture('invalid')
    assert rejected[:3]==(2,4,1) and reject_display['status']==0,rejected
    assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
    report=dict(first=first,cold=cold,early=early,rejected=rejected,display=display,cold_display=cold_display,
        scope='Separate DF1 V3 commit, complete yellow story/map/checkpoint fresh-boot restoration, no repeated rescue/idle crew, mid-script rejection and checksum-valid shifted checkpoint rejection before takeover')
    (build/'station-save-capture.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native station persistence:',json.dumps(report))
if __name__=='__main__':main()
