#!/usr/bin/env python3
"""Native upper V Stitch trigger lifecycle; caption rendering remains separate."""
import argparse,ctypes as C,json,os,struct,subprocess
from pathlib import Path
from run_tower_probe import diagnostics,EMU
from run_interactive_save import config
from save_disk import create_save_disk
from test_player import ROOT,Player,build_libraries
from test_vstitch_trigger import main as verify_source
from tower_gameplay_data import vstitch_room
COUNT=96

def expected():
    verify_source()
    core,player,_=build_libraries()
    source=C.CDLL(str(ROOT/'build/amiga-vstitch-trigger/reference.so'))
    p=Player();core.v6_player_init(C.byref(p),60,73,0)
    tiles=(C.c_uint16*1200)(*vstitch_room()['tiles']);player.reference_init(C.byref(p),tiles,0,0)
    active=1;pending=visible=timer=level=mode=contacts=hints=seen=0;rows=[]
    state=(C.c_int*6)();textbox=(C.c_int*4)()
    for tick in range(COUNT):
        if visible:
            source.reference_tick(textbox);timer,mode,visible,level=tuple(textbox)
        if pending:
            source.reference_dispatch(seen,state);seen=state[0];active=0;pending=0
            if state[2]:visible=1;timer=60;level=5;mode=0;hints+=1
        buttons=1 if tick<4 else 2 if tick<8 else 0
        player.reference_step(buttons);player.reference_read(C.byref(p))
        if active and not pending and source.reference_contact(p.x,p.y):pending=1;contacts+=1
        rows.append((p.x,p.y,p.gravity,-1,443501,seen,active,pending,visible,timer,level,mode,contacts,hints,p.flips,buttons))
    assert rows[0][5:14]==(0,1,1,0,0,0,0,1,0)
    assert rows[1][5:14]==(1,0,0,1,60,5,0,1,1)
    assert [i+1 for i,r in enumerate(rows) if r[8]][-1]==66
    assert len({r[0] for r in rows[:20]})>4
    return rows

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve();reference=expected()
    disk=build/'vstitch-hint-save.adf';disk.unlink(missing_ok=True);create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);boot=(build/'tower.adf').read_bytes();before=disk.read_bytes()
    dump=build/'vstitch-hint.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/'vstitch-hint.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio','--screenshot-after','91',str(build/'vstitch-hint.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();display=diagnostics(dump);at=data.index(b'V6VH\0\0\0\1')
    count=struct.unpack_from('>I',data,at+8)[0]
    rows=[struct.unpack_from('>16i',data,at+12+i*64) for i in range(count)]
    report=dict(display=display,records=rows,scope='Upper checkpoint 443501 start; original-source player and trigger/state/textbox timing reference. Normal movement continues during the hint. Caption pixels, input binding, campaign flag persistence and general room admission remain pending.')
    (build/'vstitch-hint-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280 and display['chip_bytes']==296150,display
    assert count==COUNT,count
    for tick,(actual,wanted) in enumerate(zip(rows,reference),1):assert actual==wanted,(tick,actual,wanted)
    assert (build/'tower.adf').read_bytes()==boot and disk.read_bytes()==before
    print('PASS native V Stitch upper hint lifecycle:',json.dumps(dict(display=display,compared_fields=COUNT*16,scope=report['scope'])))
if __name__=='__main__':main()
