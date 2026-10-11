#!/usr/bin/env python3
"""Bounded input-only Prize puzzle and pickup; explicit saved-checkpoint setup."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from run_tower_probe import diagnostics,EMU
from run_interactive_save import config
from save_disk import create_save_disk
from test_prize_collection_input import expected,COUNT

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve()
    reference=expected()
    disk=build/'prize-collection-input-save.adf';create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);boot=(build/'tower.adf').read_bytes();before=disk.read_bytes()
    dump=build/'prize-collection-input.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'prize-collection-input.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        '--screenshot-after','91',str(build/'prize-collection-input.png')],
                       env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();display=diagnostics(dump)
    at=data.index(b'V6PN\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
    rows=[struct.unpack_from('>24i',data,at+12+i*96) for i in range(count)]
    report=dict(display=display,records=rows,scope='Bounded Prize north entry (10,6,g0) with checkpoint 443490 already saved, completed Yellow rescue and empty collection bank. Ordinary fixed-tick movement/fire afterward, plus fresh fire after 94 released pickup UI ticks. Three collapses, one source spike death, local respawn, platform catch/carry, alcove flip and pickup. The campaign return journey to this entry is excluded.')
    (build/'prize-collection-input-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280 and display['chip_bytes']==296150,display
    assert count==COUNT,count
    for tick,(actual,wanted) in enumerate(zip(rows,reference),1):
        assert actual==wanted,(tick,actual,wanted)
    at=data.index(b'V6PA\0\0\0\1');audio=struct.unpack_from('>5I',data,at+8)
    assert audio==(3,1,0,1,0),audio
    records=[struct.unpack_from('>4I',data,at+28+i*16) for i in range(audio[0]+audio[1])]
    assert [r[:2] for r in records]==[(18,2),(36,2),(52,2),(130,3)],records
    assert all(r[2] in (2,3) for r in records),records
    at=data.index(b'V6CB\0\0\0\1')
    assert struct.unpack_from('>3I',data,at+8)==(8,1,0) and data[at+20:at+36]==bytes([64]+[0]*15)
    at=data.index(b'V6PS\0\0\0\1');pickup=struct.unpack_from('>12I',data,at+8)
    assert pickup[:6]==(1,95,1,1,15,95),pickup
    assert pickup[6]==pickup[7]==1 and pickup[8:]==(0,0,1,130),pickup
    # The paused actor snapshot and world hash stay fixed; dismissal adds no flip.
    at=data.index(b'V6PB\0\0\0\1');n=struct.unpack_from('>I',data,at+8)[0]
    presentation=[struct.unpack_from('>5I',data,at+44+i*20) for i in range(n)]
    assert n==110,n
    positions=[min(25*(i+1),361) for i in range(95)]+[max(361-25*(i+1),0) for i in range(15)]
    assert [r[1] for r in presentation]==positions,presentation
    assert presentation[15][3]==1 and presentation[95][3]==0,presentation
    report.update(pickup=pickup,audio=records,presentation=presentation)
    (build/'prize-collection-input-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert (build/'tower.adf').read_bytes()==boot and disk.read_bytes()==before
    print('PASS native Prize collection input route:',json.dumps(dict(display=display,trace_ticks=count,compared_fields=count*24,audio=records,pickup=pickup,scope=report['scope'])))
if __name__=='__main__':main()
