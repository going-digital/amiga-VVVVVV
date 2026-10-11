#!/usr/bin/env python3
"""Compare native register shakes against identical unshifted scenes."""
import json
import subprocess
from pathlib import Path
from test_player import ROOT

FLAGS='-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP'

def pixels(path):
    header,data=subprocess.check_output([str(ROOT/'build/amiga-feasibility/png_rgba'),str(path)]).split(b'\n',1)
    assert header==b'716 540','Review Copperline presentation geometry'
    return [[data[((30+2*y)*716+15+((2*x+1)*686)//640)*4:((30+2*y)*716+15+((2*x+1)*686)//640)*4+3]
        for x in range(320)] for y in range(240)]

def main():
    reports=[]
    for ticks in (1,6,7):
        captures=[]
        for shake in (False,True):
            build=ROOT/f'build/amiga-shake-pixels-{ticks}-{int(shake)}';build.mkdir(parents=True,exist_ok=True)
            with (build/'build.log').open('w') as log:
                subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={build}',
                    f'CPPFLAGS={FLAGS} -DV6_ENERGIZE_CAPTURE_TICKS={ticks}'+(' -DV6_TOWER_SHAKE' if shake else ''),str(build/'tower.adf')],stdout=log,stderr=subprocess.STDOUT,check=True)
            with (build/'verify.log').open('w') as log:
                subprocess.run(['python3',str(ROOT/'tools/amiga/run_energize.py'),'--roundtrip','--capture-ticks',str(ticks),
                    '--build-dir',str(build),*(['--shake'] if shake else [])],stdout=log,stderr=subprocess.STDOUT,check=True)
            captures.append((pixels(build/'energize.png'),json.loads((build/'energize-capture.json').read_text())))
        source,_=captures[0];actual,report=captures[1];_,dx,dy=report['shake_records'][-1]
        assert (dx,dy)!=(0,0)
        for y in range(240):
            for x in range(320):
                sx,sy=x-dx,y-dy
                expected=source[sy][sx] if 0<=sx<320 and 0<=sy<240 else bytes(3)
                assert actual[y][x]==expected,(ticks,dx,dy,x,y,actual[y][x],expected)
        reports.append(dict(ticks=ticks,offset=[dx,dy],pixels=76800,display=report['display']))
        print('PASS native shake pixels:',ticks,dx,dy,flush=True)
    (ROOT/'build/amiga-teleporter-shake/shake-pixels.json').write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
