#!/usr/bin/env python3
"""Fixed Building Apport composition with teleporter hardware sprites."""
import json
import os
from pathlib import Path
import subprocess
from test_teleporter_draw import ROOT,ASSETS,masks
from tower_gameplay_data import building_room
from test_tower_capture import EMU,reference_rows
from run_tower_probe import diagnostics
BUILD=ROOT/'build/amiga-teleporter-pixels'

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    config=BUILD/'tower.toml';config.write_text(f'''rom = {json.dumps(str(Path.home()/'amiga/KICK13.ROM'))}
[machine]
model = "A500"
[cpu]
model = "68000"
[memory]
chip = "512K"
slow = "512K"
fast = "0"
[chipset]
revision = "OCS"
video = "PAL"
[emulation]
pacing_budget = "cycles"
[floppy.df0]
path = {json.dumps(str(BUILD/'tower.adf'))}
write_protected = true
''')
    tiles=building_room();atlas=(ASSETS/'tower_tiles.bin').read_bytes()
    palette=json.loads((ASSETS/'tower-assets.json').read_text())['palette']
    rgb=lambda c:bytes(((c>>s)&15)*17 for s in (8,4,0))
    backdrop=reference_rows()[1];frames=masks();reports=[]
    for frame,tint in ((1,0x444),(6,0xaaf),(10,0xaaf)):
        flags=f'-DV6_TOWER_PAIRS -DV6_TOWER_HOLD=0 -DV6_TOWER_TELEPORTER_HOLD={frame} -DV6_TELEPORTER_TINT={tint}'
        with (BUILD/f'build-{frame}.log').open('w') as log:
            subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={BUILD}',f'CPPFLAGS={flags}',str(BUILD/'tower.adf')],stdout=log,stderr=subprocess.STDOUT,check=True)
        path=BUILD/f'frame-{frame}.png';dump=BUILD/f'frame-{frame}.bin'
        path.unlink(missing_ok=True);dump.unlink(missing_ok=True)
        env=dict(os.environ,COPPERLINE_DBG_AFTER='29',COPPERLINE_DBG_RAMDUMP=f'C00000:80000:{dump}')
        with (BUILD/f'capture-{frame}.log').open('w') as log:
            subprocess.run([EMU,'--config',str(config),'--noaudio','--screenshot-after','30',str(path)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        report=diagnostics(dump)
        assert report['error']==report['missed']==0 and report['max_work_lines']<=250
        dimensions,rgba=subprocess.check_output([str(ASSETS/'png_rgba'),str(path)]).split(b'\n',1)
        assert dimensions==b'716 540'
        mask=frames[8 if frame>9 else max(1,frame)];pixels=0
        for y in range(240):
            for x in range(320):
                tile=tiles[(y//8)*40+x//8]
                value=((atlas[tile*16+y%8]>>(7-x%8))&1)|(((atlas[tile*16+8+y%8]>>(7-x%8))&1)<<1)
                expected=rgb(palette[value])
                if not value:
                    expected=rgb(0x111) if backdrop[(200+y)%960][x*3:x*3+3]!=bytes(3) else rgb(0x010)
                sx=x-112;sy=y-48
                if 0<=sx<96 and 0<=sy<96:
                    if frames[0][sy][sx]:expected=rgb(0x111)
                    if mask[sy][sx]:expected=rgb(tint)
                px=15+((2*x+1)*686)//640;offset=((30+2*y)*716+px)*4
                assert rgba[offset:offset+3]==expected,(frame,x,y,rgba[offset:offset+3],expected)
                pixels+=1
        reports.append(dict(frame=frame,tint=tint,pixels=pixels,display=report))
    (BUILD/'teleporter-capture.json').write_text(json.dumps(reports,indent=2)+'\n')
    print('PASS native teleporter captures:',json.dumps(reports))
if __name__=='__main__':main()
