#!/usr/bin/env python3
"""Native shifted caption/scene pixels versus an identical unshifted reference."""
import json
import os
import struct
import subprocess
from run_interactive_save import ROOT, EMU, config, KEYS
from run_tower_probe import diagnostics
from save_disk import create_save_disk
from run_menu_travel import verify_travel
from run_shake import pixels

FLAGS='-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_UI_SAVE -DV6_TOWER_ENERGIZE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_MENU_TRAVEL -DV6_TOWER_SHAKE -DV6_TOWER_TRAVEL_AUDIO -DV6_TRAVEL_SFX_MASK=3 -DV6_TOWER_BUILDING_REPLAY -DV6_TELE_MENU_CAPTURE -DV6_MENU_EXPLORED_CAPTURE -DV6_MENU_EFFECT_HOLD=32'


def main():
    captures=[]
    for reference in (True,False):
        build=ROOT/('build/amiga-menu-pixels-reference' if reference else 'build/amiga-menu-pixels-shifted')
        build.mkdir(parents=True,exist_ok=True)
        with (build/'build.log').open('w') as log:
            subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={build}',
                f'CPPFLAGS={FLAGS}'+(' -DV6_MENU_SHAKE_REFERENCE' if reference else ''),str(build/'tower.adf')],
                stdout=log,stderr=subprocess.STDOUT,check=True)
        disk=build/'pixels-disk.adf';disk.unlink(missing_ok=True)
        create_save_disk(build/'tower.adf',disk);cfg=config(build,disk)
        before=disk.read_bytes();boot=(build/'tower.adf').read_bytes()
        dump=build/'pixels.bin';dump.unlink(missing_ok=True)
        env=dict(os.environ,COPPERLINE_DBG_AFTER='45',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
        inputs=['--joy-after','35','down','200','--joy-after','35','fire','200',
                '--joy-after','36','left','200','--joy-after','37','fire','200',
                '--click-after','37.4','right','200','--click-after','39.6','right','200']
        with (build/'pixels.log').open('w') as log:
            subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,
                '--screenshot-after','46',str(build/'pixels.png')],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        data=dump.read_bytes();display=diagnostics(dump)
        assert display['status']==1 and display['error']==display['missed']==0 and display['max_work_lines']<=250,display
        assert display['chip_bytes']==147556,display
        assert display['logic_ticks']*34000+display['logic_remainder']==display['logic_frames']*19968
        fields,_=verify_travel(data,ticks=32)
        at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
        assert ui['actions']==ui['busy']==2 and ui['pauses']==ui['resumes']==0,ui
        at=data.index(b'V6MH\0\0\0\1');count,seed=struct.unpack_from('>2I',data,at+8)
        assert count==32 and seed==19,(count,seed)
        timer,dx,dy=struct.unpack_from('>3i',data,at+16+31*12)
        assert timer==81 and (dx,dy)==((0,0) if reference else (1,-2)),(timer,dx,dy)
        at=data.index(b'V6TA\0\0\0\1');assert struct.unpack_from('>7I',data,at+8)==(0,3,3,6,3,0,2)
        assert disk.read_bytes()==before and (build/'tower.adf').read_bytes()==boot
        captures.append((pixels(build/'pixels.png'),display,fields))
    source=captures[0][0];actual=captures[1][0];dx,dy=1,-2
    for y in range(240):
        for x in range(320):
            sx,sy=x-dx,y-dy
            expected=source[sy][sx] if 0<=sx<320 and 0<=sy<240 else bytes(3)
            assert actual[y][x]==expected,(x,y,actual[y][x],expected)
    # Verify a visible cyan caption, rather than merely comparing two bare scenes.
    assert sum(source[y][x]==bytes((102,255,255)) for y in range(16,64) for x in range(320))>100
    report=dict(pixels=76800,offset=[dx,dy],translated_caption=True,disks_unchanged=True,
                trace_fields=sum(c[2] for c in captures),displays=[c[1] for c in captures])
    (ROOT/'build/amiga-menu-effects/menu-caption-pixels.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS native caption/scene shift:',json.dumps(report))
if __name__=='__main__':main()
