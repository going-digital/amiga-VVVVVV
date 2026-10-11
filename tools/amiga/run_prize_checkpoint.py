#!/usr/bin/env python3
"""Native input-only checkpoint traversal; no placement or death injection."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from run_tower_probe import diagnostics,EMU
from run_interactive_save import config
from save_disk import create_save_disk
from test_prize_checkpoint import expected,COUNT

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve()
    reference=expected()
    disk=build/'prize-checkpoint-save.adf';create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);boot=(build/'tower.adf').read_bytes();before=disk.read_bytes()
    dump=build/'prize-checkpoint.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'prize-checkpoint.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        '--screenshot-after','91',str(build/'prize-checkpoint.png')],
                       env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();display=diagnostics(dump)
    at=data.index(b'V6PN\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
    rows=[struct.unpack_from('>24i',data,at+12+i*96) for i in range(count)]
    report=dict(display=display,records=rows,scope='Canonical V Stitch lower checkpoint start; fixed-tick left/right/fire inputs thereafter. Lower passage, west crossing, Prize checkpoint activation, source spike death and local respawn. Upper intro trigger and pickup excluded; V Stitch is admitted only in this capture.')
    (build/'prize-checkpoint-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280 and display['chip_bytes']==296150,display
    assert count==COUNT,count
    for tick,(actual,wanted) in enumerate(zip(rows,reference),1):
        assert actual==wanted,(tick,actual,wanted)
    at=data.index(b'V6PA\0\0\0\1');audio=struct.unpack_from('>5I',data,at+8)
    assert audio==(0,0,0,0,0),audio
    records=[struct.unpack_from('>4I',data,at+28+i*16) for i in range(audio[0])]
    assert not records,records
    assert all(r[2] in (2,3) for r in records),records
    assert (build/'tower.adf').read_bytes()==boot and disk.read_bytes()==before
    print('PASS native Prize checkpoint route:',json.dumps(dict(display=display,trace_ticks=count,compared_fields=count*24,audio=records,scope=report['scope'])))
if __name__=='__main__':main()
