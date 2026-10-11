#!/usr/bin/env python3
"""Native connected-room and two-checkpoint fixture; placements are test-only."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from run_tower_probe import diagnostics,EMU

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve()
    from run_interactive_save import config as save_config
    from save_disk import create_save_disk
    disk=build/'shenanigan-save.adf';disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk)
    config=save_config(build,disk)
    boot=(build/'tower.adf').read_bytes()
    dump=build/'shenanigan.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='60',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'shenanigan.log').open('w') as log:
        subprocess.run([EMU,'--config',str(config),'--noaudio','--floppy-drives','2','--screenshot-after','61',str(build/'shenanigan.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert (build/'tower.adf').read_bytes()==boot
    display=diagnostics(dump)
    assert display['status']==1 and display['error']==display['missed']==0,display
    data=dump.read_bytes();at=data.index(b'V6SN\0\0\0\1')
    count=struct.unpack_from('>I',data,at+8)[0];assert count==160,count
    records=[struct.unpack_from('>14i',data,at+12+i*56) for i in range(count)]
    assert display['max_work_lines']<=250,display
    assert any(row[0]==7 and row[12]==2 for row in records)
    assert any(row[0]==6 for row in records[50:65]),records[50:65]
    for identity,spawn in ((442490,(140,161,0)),(442491,(20,110,1))):
        matching=[row for row in records if row[5]==identity]
        assert matching and all(tuple(row[6:11])==(*spawn,111,106) for row in matching),matching
    assert all(row[11]==0 for row in records if row[0]==7)
    assert any(row[0]==7 for row in records[65:])
    from run_interactive_save import KEYS
    from save_disk import read_record
    at=data.index(b'V6UI\0\0\0\1')
    ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    assert ui['saves']==ui['loads']==1 and ui['last_result']==0,ui
    assert (ui['loaded_x'],ui['loaded_y'])==(20,110),ui
    at=data.index(b'V6IT\0\0\0\1');events=struct.unpack_from('>I',data,at+8)[0]
    assert events==2,events
    for i in range(events):
        action,result,before_hash,after_hash,fb,fa,tb,ta,_,_=struct.unpack_from('>10I',data,at+16+i*40)
        assert result==0 and tb==ta and fa-fb<=4
        if action==1:assert before_hash==after_hash

    record=read_record(disk)
    assert struct.unpack_from('>4sHH7iI',record)==(b'V6CS',3,96,20,110,1,1,111,106,442491,56)
    assert record[40+(131>>3)] & (1<<(131&7))
    print('PASS native Shenanigan:',json.dumps(dict(display=display,ui=ui,trace_ticks=count)))
    # Fresh live binary boots in Frown; physical load restores the saved new room.
    live=build.parent/'amiga-station-effects-live'
    cold_config=save_config(live,disk);cold=build/'shenanigan-cold.bin'
    cold.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='85',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{cold}')
    before=disk.read_bytes()
    with (build/'shenanigan-cold.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cold_config),'--floppy-drives','2','--noaudio',
            '--joy-after','45','fire','600','--click-after','45','right','600',
            '--click-after','70','left','200','--screenshot-after','86',str(build/'shenanigan-cold.png')],
            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    cold_display=diagnostics(cold)
    assert cold_display['status']==2 and cold_display['error']==cold_display['missed']==0,cold_display
    assert cold_display['max_work_lines']<=250,cold_display
    cold_data=cold.read_bytes();at=cold_data.index(b'V6UI\0\0\0\1')
    cold_ui=dict(zip(KEYS,struct.unpack_from('>18I',cold_data,at+8)))
    assert cold_ui['loads']==1 and cold_ui['last_result']==0,cold_ui
    assert (cold_ui['loaded_x'],cold_ui['loaded_y'])==(20,110),cold_ui
    assert disk.read_bytes()==before
    print('PASS cold Shenanigan load:',json.dumps(dict(display=cold_display,ui=cold_ui)))
    (build/'shenanigan-route-report.json').write_text(json.dumps(dict(display=display,ui=ui,cold_display=cold_display,cold_ui=cold_ui,records=records,scope='Native connected-room fixture with test-only placements at both checkpoints and north return; menu save/load and fresh physical-input cold load, not a complete normal-input traversal'),indent=2)+'\n')
if __name__=='__main__':main()
