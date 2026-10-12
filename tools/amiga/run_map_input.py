#!/usr/bin/env python3
"""Physical keyboard map-control fixture, pause, DF1 save and OS return."""
import argparse,json,os,re,struct,subprocess
from pathlib import Path
from run_tower_probe import diagnostics,EMU
from run_interactive_save import config,KEYS
from save_disk import create_save_disk,read_record
from run_vstitch_hint import expected
from run_vstitch_hint_save import capture as capture_load

def visual(build,disk):
    cfg=config(build,disk);dump=build/'map-tab-chip.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='66.5',COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
    with (build/'map-tab-visual.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
            '--key-after','62','0x44','2000','--key-after','65','0x4f','800',
            '--screenshot-after','66.51',str(build/'map-save-tab.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    header=(build.parents[1]/'build/amiga-feasibility/dialogue_font.h').read_text()
    font=[int(v) for v in re.findall(r'\d+',re.search(r'dialogue_font\[[^;]+?=\{(.*?)\};',header,re.S)[1])]
    lines=[['Map','Left/right: tabs; ENTER: return'],['Crew','Left/right: tabs; ENTER: return'],
        ['Stats','Left/right: tabs; ENTER: return'],['Save tab','Space or fire: quicksave','ENTER: return to game'],
        ['Game saved','ENTER: return to game'],['Save failed','ENTER: return to game']]
    bank=bytearray()
    for text in lines:
        ink=bytearray(1920)
        for x in range(1,39):ink[4*40+x]=ink[43*40+x]=255
        for y in range(5,43):ink[y*40+1]=128;ink[y*40+38]=1
        top=(48-len(text)*8)//2
        for line,s in enumerate(text):
            x=(40-len(s))//2
            for i,c in enumerate(s):
                for y in range(8):ink[(top+line*8+y)*40+x+i]=font[ord(c)*8+y]
        bank.extend(bytes([255])*1920+ink)
    data=dump.read_bytes();at=data.find(bank)
    assert at>=0 and data.find(bank,at+1)<0,'native map caption bank'
    return dict(caption_address=at,compared_bytes=len(bank),screenshot=str(build/'map-save-tab.png'))

def capture(build,disk,name,inputs,end=100):
    cfg=config(build,disk);dump=build/(name+'.bin');dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER=str(end),COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    with (build/(name+'.log')).open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,
            '--screenshot-after',str(end+1),str(build/(name+'.png'))],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();display=diagnostics(dump)
    at=data.index(b'V6MI\0\0\0\1');values=struct.unpack_from('>12I',data,at+8);n=struct.unpack_from('>I',data,at+56)[0]
    events=[struct.unpack_from('>8I',data,at+60+32*i) for i in range(n)]
    at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    at=data.index(b'V6VH\0\0\0\1');n=struct.unpack_from('>I',data,at+8)[0]
    rows=[struct.unpack_from('>16i',data,at+12+64*i) for i in range(n)]
    report=dict(display=display,values=values,events=events,ui=ui,records=rows)
    (build/(name+'-report.json')).write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--load-build',type=Path,help='Fresh-boot V5 loader executable for the keyboard-produced save')
    p.add_argument('--run',action='store_true',help='Play the bounded upper V Stitch keyboard/menu fixture')
    a=p.parse_args();build=a.build.resolve()
    if a.run:
        disk=build/'map-play-save.adf';create_save_disk(build/'tower.adf',disk)
        cfg=config(build,disk)
        print('Return/keypad ENTER: menu; arrows: move/tabs; Space/Z/V or fire: flip/save; left mouse: exit. Saves:',disk)
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--joystick','keyboard'],check=True)
        return
    reference=expected();disk=build/'map-input-save.adf';disk.unlink(missing_ok=True);create_save_disk(build/'tower.adf',disk)
    boot=(build/'tower.adf').read_bytes()
    inputs=['--key-after','62','0x44','2000','--key-after','65','0x4f','800',
        '--key-after','66','0x40','1200','--key-after','74','0x40','600',
        '--joy-after','77.5','fire','1500','--key-after','78','0x44','2000','--key-after','82','0x43','1000',
        '--key-after','85','0x44','500']
    r=capture(build,disk,'map-input',inputs)
    d=r['display'];v=r['values'];ui=r['ui']
    assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
    assert d['chip_bytes']==319190,d
    assert v[2:7]==(2,1,2,1,0) and v[7]>300 and v[8]==0,v
    assert v[0]>=12 and v[9]==v[10] and v[11]==0,v
    assert r['records']==reference
    assert ui['actions']==ui['saves']==1 and ui['loads']==ui['busy']==ui['errors']==0,ui
    assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
    events=[row[2] for row in r['events'] if row[2]]
    assert events==[1,2,4,3,1,3],events
    assert all(row[7]==0 for row in r['events'])
    record=read_record(disk);assert record[5]==5 and struct.unpack_from('>7i',record,8)==(60,73,0,1,112,107,443501)
    assert struct.unpack_from('>I',record,36)[0]==120
    assert (build/'tower.adf').read_bytes()==boot
    before=disk.read_bytes()
    idle=capture(build,disk,'map-input-idle',[],55)
    assert idle['records']==reference and idle['ui']['actions']==0
    start=55-idle['display']['frames']/50
    early=capture(build,disk,'map-input-hint-pause',[
        '--key-after',str(start+.7),'0x44','700',
        '--key-after',str(start+4.7),'0x44','700'],start+9)
    assert early['display']['status']==1 and early['display']['error']==early['display']['missed']==0,early['display']
    assert early['records']==reference and early['ui']['actions']==0
    assert early['values'][2]==early['values'][4]==1 and early['values'][8]==0,early['values']
    assert 2<early['values'][9]==early['values'][10]<66,early['values']
    assert disk.read_bytes()==before
    exited=capture(build,disk,'map-input-exit',['--key-after','62','0x44','700',
        '--key-after','64','0x44','1000','--click-after','68','left','200'],75)
    assert exited['display']['status']==2 and exited['display']['error']==exited['display']['missed']==0,exited['display']
    assert exited['values'][2]==exited['values'][4]==1 and exited['values'][8]==0,exited['values']
    assert exited['ui']['actions']==0 and disk.read_bytes()==before
    assert (build/'tower.adf').read_bytes()==boot
    picture=visual(build,disk)
    assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
    loaded=None
    if a.load_build:
        load=a.load_build.resolve();fresh=load/'map-keyboard-load.adf';fresh.write_bytes(before)
        loadboot=(load/'tower.adf').read_bytes();loaded=capture_load(load,fresh,'map-keyboard-load')
        for actual,original in zip(loaded['records'],reference):
            wanted=list(original);wanted[5]=1;wanted[8:12]=[0,0,0,0];wanted[13]=0
            assert actual==tuple(wanted),(actual,wanted)
        assert loaded['caption_frames']==0 and loaded['ui']['actions']==0
        assert fresh.read_bytes()==before and (load/'tower.adf').read_bytes()==loadboot
    report=dict(saved=r,early_hint_pause=early,exited=exited,visual=picture,loaded=loaded,record=record.hex(),scope='Physical Return/keypad ENTER, left arrow, Space and joystick fire. Caption-only four-tab control fixture, not full map rendering or menu transitions. Paused gameplay and source hint/player trace, V5 disk save, held/released dismissal and clean OS return.')
    (build/'map-input-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native map controls:',json.dumps(dict(display=d,values=v,events=events,compared_fields=1536,scope=report['scope'])))
if __name__=='__main__':main()
