#!/usr/bin/env python3
"""Native Prize route fixture; checkpoint/platform placements are test-only."""
import argparse,json,os,struct,subprocess,zlib
from run_tower_probe import diagnostics,EMU
from pathlib import Path

def check_legacy_migration(build,live,disk,record):
    from run_interactive_save import config,KEYS
    from save_disk import read_record
    cold_boot=(live/'tower.adf').read_bytes();before=disk.read_bytes()
    from save_disk import replace_record_fixture
    migration=build/'prize-v3-migration.adf';migration.write_bytes(disk.read_bytes())
    legacy=bytearray(record[:90]);legacy[5]=3;legacy[7]=96
    struct.pack_into('>7i',legacy,8,188,86,1,1,111,105,441490)
    legacy+=bytes(2);legacy+=struct.pack('>I',zlib.crc32(legacy))
    replace_record_fixture(migration,bytes(legacy))
    migration_cfg=config(live,migration);migration_dump=build/'prize-v3-migration.bin'
    migration_dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='105',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{migration_dump}')
    with (build/'prize-v3-migration.log').open('w') as log:
        subprocess.run([EMU,'--config',str(migration_cfg),'--floppy-drives','2','--noaudio',
                        '--joy-after','55','fire','600','--click-after','55','right','600',
                        '--click-after','75','right','600','--click-after','90','left','200',
                        '--screenshot-after','106',str(build/'prize-v3-migration.png')],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    migration_display=diagnostics(migration_dump);migration_data=migration_dump.read_bytes()
    assert migration_display['status']==2 and migration_display['error']==migration_display['missed']==0,migration_display
    at=migration_data.index(b'V6UI\0\0\0\1')
    migration_ui=dict(zip(KEYS,struct.unpack_from('>18I',migration_data,at+8)))
    assert migration_ui['saves']==migration_ui['loads']==1 and migration_ui['errors']==migration_ui['last_result']==0,migration_ui
    assert (migration_ui['loaded_x'],migration_ui['loaded_y'])==(188,86),migration_ui
    upgraded=read_record(migration)
    expected=bytearray(legacy[:90]);expected[5]=4;expected[7]=112
    expected+=bytes(18);expected+=struct.pack('>I',zlib.crc32(expected))
    assert upgraded==bytes(expected)
    assert (live/'tower.adf').read_bytes()==cold_boot and disk.read_bytes()==before
    print('PASS native V3 to V4 migration:',json.dumps(dict(display=migration_display,ui=migration_ui)))
    return migration_display,migration_ui

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--v4',action='store_true')
    args=parser.parse_args();build=args.build.resolve()
    from run_interactive_save import config
    from save_disk import create_save_disk
    disk=build/'prize-route-save.adf';disk.unlink(missing_ok=True)
    create_save_disk(build/'tower.adf',disk)
    cfg=config(build,disk);boot=(build/'tower.adf').read_bytes();before=disk.read_bytes()
    dump=build/'prize-route.bin';dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
    stems=build/'prize-audio-stems'
    if args.v4:
        stems.mkdir(exist_ok=True)
        for wav in stems.glob('*.wav'):wav.unlink()
    with (build/'prize-route.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        *(['--audio-stems',str(stems),'--audio-stems-mode','source,channel'] if args.v4 else []),
                        '--screenshot-after','91',str(build/'prize-route.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    assert (build/'tower.adf').read_bytes()==boot
    if not args.v4:assert disk.read_bytes()==before
    display=diagnostics(dump);data=dump.read_bytes()
    at=data.index(b'V6PR\0\0\0\1');count=struct.unpack_from('>I',data,at+8)[0]
    rows=[struct.unpack_from('>24i',data,at+12+i*96) for i in range(count)]
    (build/'prize-route-report.json').write_text(json.dumps(dict(display=display,records=rows),indent=2)+'\n')
    assert display['status']==1 and display['error']==display['missed']==0,display
    assert display['max_work_lines']<=280,display
    assert count==224,count
    pickup=None
    if args.v4:
        at=data.index(b'V6PS\0\0\0\1')
        pickup=struct.unpack_from('>12I',data,at+8)
        assert pickup[0]==pickup[2]==pickup[3]==1 and pickup[4]==15 and pickup[1]==pickup[5]>=20,pickup
        assert pickup[6]==pickup[7] and pickup[8:]==(0,0,1,152),pickup
        at=data.index(b'V6PB\0\0\0\1')
        total=struct.unpack_from('>I',data,at+8)[0]
        presentation=[struct.unpack_from('>5I',data,at+44+i*20) for i in range(total)]
        assert total==pickup[1]+15,(total,presentation)
        positions=[min(25*(i+1),361) for i in range(pickup[1])]+[max(361-25*(i+1),0) for i in range(15)]
        assert [r[1] for r in presentation]==positions,presentation
        assert presentation[15][3]==1 and presentation[pickup[1]][3]==0,presentation
        at=data.index(b'V6PI\0\0\0\1')
        n=struct.unpack_from('>I',data,at+8)[0]
        interpolated=[struct.unpack_from('>7I',data,at+12+i*28) for i in range(n)]
        assert 30<n<96,n
        for tick,frame,old,current,phase,position,bank in interpolated:
            expected=(old*(34000-phase)+current*phase)//34000 if current else 0
            assert phase<34000 and bank<2 and position==expected,(tick,frame,old,current,phase,position,bank)
        positions=[r[5] for r in interpolated];peak=positions.index(361)
        assert positions[-1]==0 and all(a<=b for a,b in zip(positions[:peak],positions[1:peak+1]))
        assert all(a>=b for a,b in zip(positions[peak:],positions[peak+1:]))
        assert any(r[2]<r[5]<r[3] for r in interpolated),interpolated
        assert any(r[3]<r[5]<r[2] for r in interpolated),interpolated
        print('PASS native pickup interpolation:',n,'changed PAL positions; source phases, smooth entry/retreat and final hide')
        at=data.index(b'V6FF\0\0\0\1')
        n=struct.unpack_from('>I',data,at+8)[0]
        fades=[struct.unpack_from('>8I',data,at+12+i*32) for i in range(n)]
        assert 8<n<64,(n,fades)
        for tick,mode,old,current,phase,visible,colours,stopped in fades:
            gray=174*(old*(34000-phase)+current*phase)//340000
            expected=((((gray//6+8)//17)*0x111)<<16)|((gray+8)//17)*0x111 if visible else 0
            assert phase<34000 and colours==expected,(tick,mode,old,current,phase,visible,hex(colours),stopped)
        assert any(r[1]==0 and r[5] and r[7] for r in fades),fades
        assert any(r[6]==0x2220aaa and r[7] for r in fades),fades
        assert any(r[1]==2 and r[5] and not r[7] and r[0]>152 for r in fades),fades
        assert fades[-1][0]==156 and fades[-1][5:]==(0,0,0),fades
        print('PASS native pickup fades:',n,'palette changes; source interpolation, visible fade after gameplay resumes, five-tick removal')
        from prize_audio_capture import verify
        verify(data,stems)
    assert any(row[0]==7 for row in rows[:20]) and any(row[0]==8 for row in rows[20:30])
    assert all(row[11]==0 for row in rows if row[0]==8)
    assert any(row[0]==8 and row[14]==1 and row[13]>88 for row in rows)
    assert any(row[16]==1 and row[19]==59 for row in rows)
    matching=[row for row in rows if row[5]==443490]
    assert matching and all(row[6:11]==(236,134,1,111,107) for row in matching)
    assert rows[174][15:18]==(1,1,1),rows[174]
    assert any(row[0]==7 for row in rows[175:190])
    assert any(row[0]==8 for row in rows[190:]) and all(row[17]==1 and row[18]==0 and row[19]==59
                                      for row in rows[190:] if row[0]==8)
    assert rows[149 if args.v4 else -1][23]>=2,rows[149 if args.v4 else -1]
    assert rows[60][13]==152,rows[60]
    assert all(row[13]==rows[60][13] and row[20]==4 for row in rows[60:90])
    # A V3-supported Shenanigan checkpoint cannot silently discard trinket 6.
    assert any(row[5]==442490 and row[17]==1 for row in rows[185:190])
    from run_interactive_save import KEYS
    at=data.index(b'V6UI\0\0\0\1')
    ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
    if args.v4:
        assert ui['saves']==ui['loads']==1 and ui['errors']==ui['last_result']==0,ui
        assert (ui['loaded_x'],ui['loaded_y'])==(236,134),ui
        assert any(row[17]==0 and row[18]==1 for row in rows[160:166])
        assert all(row[17]==1 and row[18]==0 for row in rows[166:175]),rows[166:175]
        from save_disk import read_record
        record=read_record(disk)
        assert struct.unpack_from('>4sHH7iI',record)==(b'V6CS',4,112,236,134,1,1,111,107,443490,56)
        assert record[40+(151>>3)] & (1<<(151&7))
        assert record[90:103]==bytes([64])+bytes(12)
        at=data.index(b'V6IT\0\0\0\1');events=struct.unpack_from('>I',data,at+8)[0]
        assert events==2,events
        for i in range(events):
            action,result,bh,ah,fb,fa,tb,ta,_,_=struct.unpack_from('>10I',data,at+16+i*40)
            assert result==0 and tb==ta and fa-fb<=4
            if action==1:assert bh==ah
    else:
        assert ui['errors']==1 and ui['saves']==ui['loads']==0 and ui['last_result']==1,ui
        assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
    at=data.index(b'V6WG\0\0\0\1');sprite_channels=struct.unpack_from('>I',data,at+8+12*4)[0]
    assert sprite_channels==5,sprite_channels
    at=data.index(b'V6PF\0\0\0\1')
    profile=dict(zip(('magic','version','max_logic','max_render','peak_logic','peak_render','peak_tick','peak_rows'),
                     struct.unpack_from('>8I',data,at)))
    if args.v4:before=disk.read_bytes()
    # Quit by physical mouse after the same replay; teardown must restore the OS.
    quit_dump=build/'prize-route-quit.bin';quit_dump.unlink(missing_ok=True)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='65',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{quit_dump}')
    with (build/'prize-route-quit.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
                        '--click-after','60','left','200','--screenshot-after','66',str(build/'prize-route-quit.png')],
                        env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    quit_display=diagnostics(quit_dump)
    assert quit_display['status']==2 and quit_display['error']==quit_display['missed']==0,quit_display
    assert (build/'tower.adf').read_bytes()==boot
    if args.v4:assert read_record(disk)==record
    else:assert disk.read_bytes()==before
    cold_display=cold_ui=cold_collection=None
    if args.v4:
        live=build.parent/'amiga-prize-route'
        cold_boot=(live/'tower.adf').read_bytes()
        cold_cfg=config(live,disk);cold_dump=build/'prize-v4-cold.bin';cold_dump.unlink(missing_ok=True)
        env=dict(os.environ,COPPERLINE_DBG_AFTER='100',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{cold_dump}')
        before=disk.read_bytes()
        with (build/'prize-v4-cold.log').open('w') as log:
            subprocess.run([EMU,'--config',str(cold_cfg),'--floppy-drives','2','--noaudio',
                            '--joy-after','55','fire','600','--click-after','55','right','600',
                            '--click-after','85','left','200','--screenshot-after','101',str(build/'prize-v4-cold.png')],
                            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        cold_display=diagnostics(cold_dump);cold_data=cold_dump.read_bytes()
        assert cold_display['status']==2 and cold_display['error']==cold_display['missed']==0,cold_display
        assert cold_display['max_work_lines']<=280,cold_display
        at=cold_data.index(b'V6UI\0\0\0\1')
        cold_ui=dict(zip(KEYS,struct.unpack_from('>18I',cold_data,at+8)))
        assert cold_ui['loads']==1 and cold_ui['saves']==cold_ui['errors']==cold_ui['last_result']==0,cold_ui
        assert (cold_ui['loaded_x'],cold_ui['loaded_y'])==(236,134),cold_ui
        at=cold_data.index(b'V6CB\0\0\0\1')
        cold_collection=struct.unpack_from('>3I',cold_data,at+8)
        assert cold_collection==(8,0,0),cold_collection
        assert cold_data[at+20:at+33]==bytes([64])+bytes(12)
        assert disk.read_bytes()==before and (live/'tower.adf').read_bytes()==cold_boot
        print('PASS cold V4 Prize load:',json.dumps(dict(display=cold_display,ui=cold_ui,collection=cold_collection)))
    migration_display=migration_ui=None
    if args.v4:
        migration_display,migration_ui=check_legacy_migration(build,live,disk,record)
    report=dict(display=display,profile=profile,quit_display=quit_display,ui=ui,pickup=pickup,sprite_channels=sprite_channels,cold_display=cold_display,cold_ui=cold_ui,cold_collection=cold_collection,migration_display=migration_display,migration_ui=migration_ui,records=rows,
                scope='Connected route with test-only placements; pickup caption, frozen player/actors, held action dismissal, collection/terrain retention, optional V4 save/load and fresh physical-input disk load. No room audio or complete normal-input traversal.')
    (build/'prize-route-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native Prize route:',json.dumps(dict(display=display,trace_ticks=count,
        pickup=pickup,scope='Source boundary handling with test-only checkpoint/gate/pickup placements; pickup pause/caption/dismissal and retained death terrain/collection. V4 disk persistence checked when requested; full normal-input traversal excluded; source OCS textbox fades and PAL bar interpolation verified; source Prize effects verified with captured PCM.')))
if __name__=='__main__':main()
