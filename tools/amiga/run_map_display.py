#!/usr/bin/env python3
"""Native original minimap/fog, cursor DMA and physical menu regression."""
import argparse,ctypes as C,json,os,struct,subprocess
from pathlib import Path
from run_map_input import capture
from run_interactive_save import config
from run_tower_probe import diagnostics,EMU
from save_disk import create_save_disk,read_record
from run_vstitch_hint import expected
from test_map_draw import libraries,arrays

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    p.add_argument('--dirty',action='store_true',help='Check the controlled adjacent-room exploration refresh')
    a=p.parse_args();build=a.build.resolve();ref=expected();source=libraries()
    disk=build/'map-display-save.adf';disk.unlink(missing_ok=True);create_save_disk(build/'tower.adf',disk)
    boot=(build/'tower.adf').read_bytes()
    inputs=['--key-after','62','0x44','2000','--key-after','62.1','0x4f','1200',
        '--key-after','65','0x4f','800',
        '--key-after','66','0x40','1200','--key-after','74','0x40','600',
        '--joy-after','77.5','fire','1500','--key-after','78','0x44','2000',
        '--key-after','82','0x43','1000','--key-after','85','0x44','500']
    result=capture(build,disk,'map-display',inputs)
    d=result['display'];v=result['values'];ui=result['ui']
    assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
    assert d['chip_bytes']==367190,d
    assert result['records']==ref and v[2:7]==(2,1,2,1,0) and v[8]==v[11]==0,(v,ui)
    assert ui['actions']==ui['saves']==1 and ui['loads']==ui['errors']==ui['busy']==0,ui
    assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
    data=(build/'map-display.bin').read_bytes();at=data.index(b'V6MP\0\0\0\1')
    transition_at=data.index(b'V6MT\0\0\0\1')
    transition_count=struct.unpack_from('>I',data,transition_at+8)[0]
    transitions=[struct.unpack_from('>7I',data,transition_at+12+28*i) for i in range(transition_count)]
    moving=[r for r in transitions if r[1]!=r[2]]
    assert len(moving)==40,transitions
    assert any(r[5]&2 for r in moving[:10]),moving[:10] # Held arrow during opening is ignored.
    for cycle in range(4):
        group=moving[cycle*10:(cycle+1)*10]
        closing=cycle%2
        assert len({r[0] for r in group})==1,group # Frozen gameplay throughout.
        for tick,(_,previous,offset,direction,active,buttons,done) in enumerate(group):
            wanted=min(240,25*(tick+1)) if closing else max(0,240-25*(tick+1))
            assert offset==wanted and direction==closing and done==int(closing and tick==9),group
            assert previous==(min(240,25*tick) if closing else max(0,240-25*tick)),group
            assert active==int(not done),group
    display_values=struct.unpack_from('>5I',data,at+8);count=struct.unpack_from('>I',data,at+28)[0]
    frames=[struct.unpack_from('>6I',data,at+32+24*i) for i in range(count)]
    assert display_values[0]==(480 if a.dirty else 240) and display_values[1]>=128 and display_values[3:]==(184,84),display_values
    modes=set()
    for state,delay,mode,index,sprite,colour in frames:
        wanted=2 if state==2 and delay//15%2==0 else 1 if state==1 and delay//4%2==0 else 0
        assert mode==wanted and index in (0,1) and colour==(0xfff if mode==1 else 0x1ee),(state,delay,mode,index,sprite,colour)
        modes.add(mode)
    assert modes=={0,1,2},modes
    record=read_record(disk);assert record[5]==5 and struct.unpack_from('>7i',record,8)==(60,73,0,1,112,107,443501)
    assert struct.unpack_from('>I',record,36)[0]==120
    assert sum(b.bit_count() for b in record[40:90])==(2 if a.dirty else 1)
    before=disk.read_bytes();cfg=config(build,disk);dump=build/'map-display-chip.bin'
    env=dict(os.environ,COPPERLINE_DBG_AFTER='62.48',COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
    with (build/'map-display-visual.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
            '--key-after','62','0x44','2000','--screenshot-after','62.49',str(build/'explored-map.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    pixels=(C.c_uint8*76800)();source.reference_pixels.argtypes=[C.POINTER(C.c_uint8),C.POINTER(C.c_uint8)]
    exploration=(C.c_uint8*50).from_buffer_copy(record[40:90]);source.reference_pixels(exploration,pixels)
    bitmap=bytes(sum(((pixels[y*320+x*8+i]>>p)&1)<<(7-i) for i in range(8)) for p in range(5) for y in range(240) for x in range(40))
    chip=dump.read_bytes();offset=chip.find(bitmap)
    assert offset>=0 and chip.find(bitmap,offset+1)<0,'native source map bitmap'
    palette=arrays(build.parents[1]/'build/amiga-feasibility/map_assets.h','map_palette')
    cursor_addresses={f[4] for f in frames};lists=[];at=0;shown=0
    while True:
        at=chip.find(bytes.fromhex('2c01fffe01005200'),at)
        if at<0:break
        words=struct.unpack_from('>138H',chip,at);registers=dict(zip(words[::2],words[1::2]))
        assert registers[0x104]==0x20 and registers[0x108]==registers[0x10a]==0
        for plane in range(5):assert registers[0xe0+plane*4]<<16|registers[0xe2+plane*4]==offset+plane*9600
        for i,c in enumerate(palette):
            if i!=17:assert registers[0x180+i*2]==c
        sprite=registers[0x120]<<16|registers[0x122];assert sprite in cursor_addresses
        w=struct.unpack_from('>22H',chip,sprite)
        if w[0]:
            mode=1 if registers[0x1a2]==0xfff else 2
            assert w[:2]==(0x889c,0x9100),(w[:2],mode)
            for y in range(9):
                bits=sum((int(mode==1 and (y in (0,8) or x in (0,11))) or int(2<=y<7 and 2<=x<10 and (y in (2,6) or x in (2,9))))<<(15-x) for x in range(12))
                assert w[2+y*2:4+y*2]==(bits,0),(y,w,mode)
            assert w[20:22]==(0,0);shown+=1
        lists.append(at);at+=1
    assert len(lists)==2 and shown>=1,(lists,shown)
    _,photo=subprocess.check_output([str(build.parents[1]/'build/amiga-feasibility/png_rgba'),str(build/'explored-map.png')]).split(b'\n',1)
    white_pixels=sum(photo[i:i+3]==b'\xff\xff\xff' for i in range(0,len(photo),4))
    # Palette 17 is cursor-only. The full outline must remain in front of
    # opaque fog/map tiles, not merely show through black minimap pixels.
    assert white_pixels>=100,white_pixels
    assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
    report=dict(transition_frames=transitions,controls=result,map_values=display_values,cursor_frames=frames,bitmap_address=offset,copper_lists=lists,visible_cursor_banks=shown,cursor_white_pixels=white_pixels,compared_bytes=len(bitmap),source_explored_rooms=sum(b.bit_count() for b in record[40:90]),
        scope='Original normal-world minimap/fog/frame/tabs and room title, RGB12 quantization with no colour reduction at source glow=0. Resident V Stitch current-room sprite cursor. Original ten-tick native transition input lock and world pause; visible movement remains pending. Other tabs retain control captions; palette glow, tower cursor, legends and general room admission remain pending.')
    (build/'map-display-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native explored map:',json.dumps(dict(display=d,bitmap_address=offset,compared_bytes=len(bitmap),cursor_frames=len(frames),explored_rooms=report['source_explored_rooms'],scope=report['scope'])))
if __name__=='__main__':main()
