#!/usr/bin/env python3
"""Actual DF1 V5 hint save, then fresh-boot load without repeating the caption."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from run_tower_probe import diagnostics,EMU
from run_interactive_save import config,KEYS
from save_disk import create_save_disk,read_record
from run_vstitch_hint import expected

def capture(build,disk,name,inputs=()):
    cfg=config(build,disk);dump=build/(name+'.bin');dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/(name+'.log')).open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,'--screenshot-after','91',str(build/(name+'.png'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();display=diagnostics(dump)
    assert display['status']==1 and display['error']==display['missed']==0 and display['max_work_lines']<=280,display
    assert display['chip_bytes']==296150,display
    at=data.index(b'V6VH\0\0\0\1');n=struct.unpack_from('>I',data,at+8)[0]
    assert n==96,n
    rows=[struct.unpack_from('>16i',data,at+12+64*i) for i in range(n)]
    at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    at=data.index(b'V6VD\0\0\0\1');caption_frames=struct.unpack_from('>I',data,at+8)[0]
    return dict(display=display,records=rows,ui=ui,caption_frames=caption_frames)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True);parser.add_argument('--load-build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve();load=args.load_build.resolve();reference=expected()
    disk=build/'hint-v5-save.adf';disk.unlink(missing_ok=True);create_save_disk(build/'tower.adf',disk)
    boot=(build/'tower.adf').read_bytes()
    saved=capture(build,disk,'hint-v5-save',('--click-after','62','right','600'))
    assert saved['records']==reference and saved['caption_frames']==111
    ui=saved['ui'];assert ui['saves']==1 and ui['loads']==ui['errors']==ui['busy']==0 and ui['last_result']==0,ui
    assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
    record=read_record(disk);assert record[5]==5 and struct.unpack_from('>7i',record,8)==(60,73,0,1,112,107,443501)
    assert struct.unpack_from('>I',record,36)[0]==120 and record[40+19]&1 and record[90:108]==bytes(18),record.hex()
    # Boot the loader variant from DF0 and mount an independent copy of the
    # actual saved filesystem on DF1. The trace proves that the loader ran.
    fresh=load/'hint-v5-load.adf';fresh.write_bytes(disk.read_bytes())
    assert read_record(fresh)==record
    before=fresh.read_bytes();loadboot=(load/'tower.adf').read_bytes()
    loaded=capture(load,fresh,'hint-v5-load')
    for tick,(actual,original) in enumerate(zip(loaded['records'],reference),1):
        expected_row=list(original);expected_row[5]=1;expected_row[8:12]=[0,0,0,0];expected_row[13]=0
        assert actual==tuple(expected_row),(tick,actual,expected_row)
    assert loaded['caption_frames']==0,loaded['caption_frames']
    assert loaded['ui']['saves']==loaded['ui']['loads']==loaded['ui']['errors']==0,loaded['ui']
    assert fresh.read_bytes()==before and (build/'tower.adf').read_bytes()==boot and (load/'tower.adf').read_bytes()==loadboot
    report=dict(saved=saved,loaded=loaded,record=record.hex(),scope='Physical right-mouse V5 save after the original hint, followed by boot-time source-bank-validated recovery on a fresh executable. Flag 13 prevents any repeat caption. ENTER binding and general campaign/renderer admission remain pending.')
    (load/'hint-v5-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native V5 hint persistence:',json.dumps(dict(save=saved['display'],load=loaded['display'],flag=1,record_bytes=len(record),compared_fields=3072,scope=report['scope'])))
if __name__=='__main__':main()
