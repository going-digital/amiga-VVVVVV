#!/usr/bin/env python3
"""Connected host route candidates; native admission and full return excluded."""
import ctypes as C
import json,subprocess
from test_prize_checkpoint import expected as checkpoint_expected
from tower_gameplay_data import ROOT,shenanigan_room,prize_room,vstitch_room,deception_room,downunder_room

def main():
    original=checkpoint_expected()
    out=ROOT/'build/amiga-prize-return-host';out.mkdir(parents=True,exist_ok=True)
    sources=('prize','platform_gate','disappearing','trinkets','checkpoints','platform',
        'enemy','player','terrain','blocks','tower_route','tower_session','tower_camera',
        'tower_gameplay','teleporter','room_codec','prize_return','prize_return_sprite',
        'animation','pixel_collision')
    subprocess.run(['cc','-std=c99','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        '-I'+str(ROOT/'build/amiga-feasibility'),str(ROOT/'tools/amiga/prize_return_route_fixture.c'),
        *[str(ROOT/'amiga_version'/(s+'.c')) for s in sources],'-o',str(out/'core.so')],check=True)
    core=C.CDLL(str(out/'core.so'));fn=core.prize_return_route_fixture
    fn.argtypes=[C.POINTER(C.c_uint16)]*5+[C.POINTER(C.c_uint),C.POINTER(C.c_int32),C.c_uint]
    rooms=[(C.c_uint16*1200)(*r()['tiles']) for r in
        (shenanigan_room,prize_room,vstitch_room,deception_room,downunder_room)]
    reports={}
    for name,buttons in (
        ('west-checkpoint',[0]*12+[5]+[1]*64+[4]+[0]*22+[1]*40+[0]*10),
        ('enemy-return',[0]*12+[5]+[1]*55+[4]+[0]*22+[1]*40+[0]*10)):
        count=195+len(buttons);trace=(C.c_int32*(count*32))()
        assert fn(*rooms,(C.c_uint*len(buttons))(*buttons),trace,count)
        rows=[tuple(trace[t*32:(t+1)*32]) for t in range(count)]
        assert [r[:24] for r in rows[:195]]==original[:195]
        assert all(r[31]==r[15]==r[17]==0 for r in rows)
        assert rows[251][:5]==(10,303,185,0,-1)
        if name=='west-checkpoint':
            assert [t+1 for t,r in enumerate(rows) if t>194 and r[5]!=rows[t-1][5]]==[299]
            assert rows[298][5:11]==(443481,148,182,1,110,107)
            assert all(r[4]==-1 and r[24]==0 for r in rows)
            assert {r[0] for r in rows}=={8,9,10,11}
            assert rows[-1][:5]==(11,18,166,1,-1)
        else:
            deaths=[t+1 for t,r in enumerate(rows) if r[4]==30]
            assert deaths==[276],deaths
            assert rows[275][:5]==(10,231,86,1,30) and rows[275][24]==1
            assert all(r[5:11]==(443490,236,134,1,111,107) for r in rows[194:])
            assert rows[305][:5]==(8,236,134,1,-1) and rows[305][23]==1
            assert rows[-1][0]==8 and rows[-1][24]==1
            # Ordinary death freezes actor motion but does not stop sprite animation.
            assert len({r[28:31] for r in rows[275:305]})==1
        reports[name]=rows
    (out/'prize-return-host-report.json').write_text(json.dumps(dict(
        scope='Host integration using port cores, private masks and fixed source approach. West checkpoint activation and pixel enemy death/remote return verified; full Prize-checkpoint-preserving return, native display/save admission, upper V Stitch trigger and pickup UI excluded.',traces=reports),indent=2)+'\n')
    print('PASS connected west host route: retained 195-tick V Stitch/Prize approach, source west checkpoint replacement, Down Under entry, pixel enemy death and remote Prize respawn; full return and native admission pending')
if __name__=='__main__':main()
