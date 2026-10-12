#!/usr/bin/env python3
"""Native upper V Stitch trigger, source-positioned caption and fade."""
import argparse,ctypes as C,json,os,re,struct,subprocess
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

def presentation(data,reference):
    at=data.index(b'V6VD\0\0\0\1');count,compositions=struct.unpack_from('>2I',data,at+8)
    actual=[struct.unpack_from('>7i',data,at+16+i*28) for i in range(count)]
    elapsed=tick=0;wanted=[]
    while tick<67:
        elapsed+=19968
        if elapsed>=34000:elapsed-=34000;tick+=1
        if tick and reference[tick-1][8]:
            level=reference[tick-1][10];previous=5 if tick==2 else reference[tick-2][10]
            grey=int(174*(previous+(level-previous)*elapsed/34000)/10+1e-9)
            fill=((grey//6+8)//17)*0x111;ink=((grey+8)//17)*0x111
            wanted.append((tick,previous,level,elapsed,(fill<<16)|ink))
    assert count==len(wanted)==111 and compositions==2,(count,compositions)
    for i,(row,expected_row) in enumerate(zip(actual,wanted)):
        assert row[:5]==expected_row and row[6]==1,(i,row,expected_row)
        assert row[5] in (0,1) and (not i or row[5]==(actual[i-1][5]^1)),(i,row)
    return actual

def visual(build,cfg,display):
    # Derive boot duration from the emulated PAL frame counter so the second
    # capture lands inside the 65-tick hint, regardless of floppy load time.
    moment=90-display['frames']/50+1.2
    dump=build/'vstitch-caption-chip.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER=str(moment),COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
    with (build/'vstitch-caption-visual.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio','--screenshot-after',str(moment+.01),str(build/'vstitch-caption.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    data=dump.read_bytes();assets=ROOT/'build/amiga-feasibility'
    def array(path,name):
        header=path.read_text();body=re.search(name+r'\[[^;]+?=\{(.*?)\};',header,re.S)[1]
        return [int(v) for v in re.findall(r'\d+',body)]
    font=(C.c_uint8*1024)(*array(assets/'dialogue_font.h','dialogue_font'))
    border=(C.c_uint8*64)(*array(assets/'pickup_assets.h','pickup_border'))
    source=C.CDLL(str(ROOT/'build/amiga-vstitch-hint-draw/reference.so'))
    bp=C.POINTER(C.c_uint8);source.render.argtypes=[bp,bp,bp,C.POINTER(C.c_int)]
    pixels=(C.c_uint8*(320*240))();geometry=(C.c_int*3)();source.render(font,border,pixels,geometry)
    mask=bytes(sum(bool(pixels[(155+y)*320+x*8+b])<<(7-b) for b in range(8)) for y in range(33) for x in range(40))
    ink=bytes(sum((pixels[(155+y)*320+x*8+b]==5)<<(7-b) for b in range(8)) for y in range(33) for x in range(40))
    atlas=array(assets/'vstitch_assets.h','vstitch_atlas')
    tiles=json.loads((assets/'vstitch-graphics.json').read_text())['display_tiles']
    foreground=[bytes(atlas[tiles[(y//8)*40+x]*16+p*8+y%8] for y in range(155,188) for x in range(40)) for p in range(2)]
    expected_a=bytes((f&(~m&255))|k for f,m,k in zip(foreground[0],mask,ink))
    expected_b=bytes(f&(~m&255) for f,m in zip(foreground[1],mask))
    locations=[];start=0
    while True:
        at=data.find(mask,start)
        if at<0:break
        bank=at-6080;locations.append(bank)
        assert bank>=0 and data[bank:bank+1320]==expected_a and data[bank+3040:bank+4360]==expected_b,(bank,'native caption pixels')
        start=at+1
    assert len(locations)==2,locations
    return dict(capture_time=moment,bank_addresses=locations,compared_bytes=2*3*1320,geometry=list(geometry))

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
    report=dict(display=display,records=rows,scope='Upper checkpoint 443501 start; original-source player and trigger/state/textbox timing reference. Normal movement continues during the hint. Source-positioned ENTER caption, interpolated grey fade and preservation outside the box are verified. Interactive input binding, campaign flag persistence and general room admission remain pending.')
    (build/'vstitch-hint-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280 and display['chip_bytes']==296150,display
    assert count==COUNT,count
    for tick,(actual,wanted) in enumerate(zip(rows,reference),1):assert actual==wanted,(tick,actual,wanted)
    report['presentation']=presentation(data,reference)
    report['visual']=visual(build,cfg,display)
    (build/'vstitch-hint-report.json').write_text(json.dumps(report,indent=2)+'\n')
    assert (build/'tower.adf').read_bytes()==boot and disk.read_bytes()==before
    print('PASS native V Stitch upper hint lifecycle:',json.dumps(dict(display=display,compared_fields=COUNT*16,presentation_frames=len(report['presentation']),visual=report['visual'],scope=report['scope'])))
if __name__=='__main__':main()
