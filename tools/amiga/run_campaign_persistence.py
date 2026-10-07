#!/usr/bin/env python3
"""Boot a private writable ADF twice: rescue/save, then checkpoint restart."""
import argparse
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import zlib
from run_tower_probe import diagnostics,EMU,ROOT
BUILD=ROOT/'build/amiga-tower-persistence'
KEYS='stage read_result write_result validation_error restarted completed x y gravity dir checkpoint companion triggered rescued requests audio_starts crew_visible following'.split()
def capture(config,name,reject=False):
    dump=BUILD/f'{name}.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='41',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (BUILD/f'{name}.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio','--screenshot-after','42',str(BUILD/f'{name}.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();offset=data.index(b'V6SV\0\0\0\1')
    state=dict(zip(KEYS,struct.unpack_from('>18I',data,offset+8)))
    if reject:
        assert state['stage']==2 and state['completed']==0 and state['restarted']==0,state
        assert state['validation_error']==1,state
        display_offset=data.index(b'V6TP\0\0\0\6')
        assert struct.unpack_from('>I',data,display_offset+8)[0]==0  # no takeover
        state['before_takeover_verified']=True
        return state
    state['display']=diagnostics(dump)
    assert state['completed']==1 and state['validation_error']==0,state
    assert state['display']['status']==2 and state['display']['error']==0,state
    assert state['display']['missed']==0 and state['display']['max_work_lines']<=250,state
    return state
def main():
    global BUILD
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,default=BUILD)
    parser.add_argument('--replace-mode',type=int,choices=(0,1,2,3),default=0)
    args=parser.parse_args();BUILD=args.build.resolve()
    expected_dir=0 if args.replace_mode in (1,3) else 1
    disk=BUILD/'persistence.adf';shutil.copyfile(BUILD/'tower.adf',disk)
    config=BUILD/'persistence.toml'
    config.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
[machine]
model = "A500"
[cpu]
model = "68000"
[memory]
chip = "512K"
slow = "512K"
fast = "0"
[chipset]
revision = "OCS"
video = "PAL"
[emulation]
pacing_budget = "cycles"
[floppy.df0]
path = {json.dumps(str(disk))}
write_protected = false
''')
    first=capture(config,'save')
    from tower_route_trace import verify
    verify(first['display'],BUILD/'save.bin',False,True,True,False)
    assert first['stage']==1 and first['write_result']==0 and first['requests']==1 and first['audio_starts']==6,first
    assert (first['checkpoint'],first['companion'],first['triggered'],first['rescued'])==(505147,9,1,1),first
    second=capture(config,'restart')
    assert second['stage']==2 and second['read_result']==0 and second['restarted']==1,second
    assert (second['x'],second['y'],second['gravity'],second['dir'],second['checkpoint'])==(140,1822,1,expected_dir,505147),second
    assert (second['companion'],second['triggered'],second['rescued'],second['following'])==(9,1,1,1),second
    assert second['requests']==0 and second['audio_starts']==0 and second['crew_visible']==0,second
    from tower_gameplay_data import checkpoints
    data=(BUILD/'restart.bin').read_bytes();offset=data.index(b'V6WG\0\0\0\1')
    world=struct.unpack_from('>13I',data,offset+8)
    checkpoint_index=next(i for i,c in enumerate(checkpoints()) if c[3]==505147)
    assert world[6]==1<<checkpoint_index and world[7]==0,world
    second['active_checkpoint_verified']=True
    # Follow the named OFS file header, excluding freed backup/data blocks.
    image=disk.read_bytes();headers=[]
    for block in range(0,len(image),512):
        if struct.unpack_from('>I',image,block)[0]!=2 or struct.unpack_from('>I',image,block+508)[0]!=0xfffffffd:continue
        length=image[block+432]
        if image[block+433:block+433+length]==b'campaign.v6cs':headers.append(block)
    assert len(headers)==1,headers
    header=headers[0];assert sum(struct.unpack_from('>128I',image,header))&0xffffffff==0
    block=struct.unpack_from('>I',image,header+16)[0]*512
    assert struct.unpack_from('>I',image,block)[0]==8 and struct.unpack_from('>I',image,block+12)[0]==44
    record_offset=block+24;records=[image[record_offset:record_offset+44]]
    assert zlib.crc32(records[0][:40])==struct.unpack_from('>I',records[0],40)[0]
    fields=struct.unpack_from('>7iI',records[0],8)
    assert fields==(140,1822,1,expected_dir,109,109,505147,7),fields
    (BUILD/'campaign.v6cs').write_bytes(records[0])
    # OFS data blocks have a six-long header and a checksum over 512 bytes.
    block=record_offset&~511
    assert record_offset-block==24 and struct.unpack_from('>I',image,block)[0]==8
    assert sum(struct.unpack_from('>128I',image,block))&0xffffffff==0
    rejected={}
    for name,valid_crc in (() if args.replace_mode else (('bad-crc',False),('bad-checkpoint',True))):
        bad=bytearray(image);bad[record_offset+11]^=1  # x=141 instead of checkpoint x=140
        if valid_crc:struct.pack_into('>I',bad,record_offset+40,zlib.crc32(bad[record_offset:record_offset+40]))
        struct.pack_into('>I',bad,block+20,0)
        checksum=(-sum(struct.unpack_from('>128I',bad,block)))&0xffffffff
        struct.pack_into('>I',bad,block+20,checksum)
        bad_disk=BUILD/f'{name}.adf';bad_disk.write_bytes(bad)
        bad_config=BUILD/f'{name}.toml'
        bad_config.write_text(config.read_text().replace(str(disk),str(bad_disk)))
        rejected[name]=capture(bad_config,name,reject=True)
        assert rejected[name]['read_result']==(0 if valid_crc else 4),rejected[name]
        assert bad_disk.read_bytes()==bytes(bad)  # rejected loads do not rewrite the save

    report=dict(replacement_mode=args.replace_mode,save=first,restart=second,rejected=rejected,disk_record_verified=True,scope='Bounded AmigaDOS save/replacement and rename-boundary recovery on cold boot; full campaign fields and interactive save actions pending')
    (BUILD/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
