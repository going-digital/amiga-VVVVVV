#!/usr/bin/env python3
"""Source user/control truncation and ownership-isolated Paula gain plans."""
import ctypes as C
from fractions import Fraction
import itertools
import subprocess
from test_audio import ROOT,Plan,pairs

def main():
    out=ROOT/'build/amiga-music';out.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/music_gain.c'),'-o',str(out/'music-gain.so')],check=True)
    source=(ROOT/'desktop_version/src/Music.cpp').read_text()
    begin=source.index('void musicclass::set_music_volume(int volume)')
    body=source[begin:source.index('\nvoid musicclass::set_sound_volume',begin)]
    refsrc='''#define USER_VOLUME_MAX 256
#define VVV_MAX_VOLUME 128
static int result;
struct {bool muted,musicmuted;} game;
struct MusicTrack {static void SetVolume(int v){result=v;}};
struct musicclass {int user_music_volume,controlVolume;void set_music_volume(int);void set_sound_volume(int){};void updatemutestate();};
'''+body+'\n'+source[source.index('void musicclass::updatemutestate(void)'):source.index('\n}',source.index('void musicclass::updatemutestate(void)'))+2]+'''
extern "C" int reference(int control,int user){musicclass m;m.user_music_volume=user;m.set_music_volume(control);return result;}
extern "C" int reference_muted(int control,int user,int mute,int musicmute){musicclass m;m.user_music_volume=user;m.controlVolume=control;game.muted=mute;game.musicmuted=musicmute;m.updatemutestate();return result;}
'''
    path=out/'music-gain-reference.cpp';path.write_text(refsrc)
    subprocess.run(['c++','-std=c++11',*flags,str(path),'-o',str(out/'music-gain-reference.so')],check=True)
    core=C.CDLL(str(out/'music-gain.so'));ref=C.CDLL(str(out/'music-gain-reference.so'))
    Array=C.c_uint*4
    core.v6_music_gain_plan.argtypes=[C.c_uint,C.c_uint,C.POINTER(C.c_uint),C.c_uint,C.c_uint,C.c_int,C.c_int,C.POINTER(Plan)]
    p=Plan();checks=0
    # Every source control/user gain pair and every Paula instrument volume.
    # Four instruments per call cover all 65 levels with an independent rational
    # oracle; scaling truncates twice, deliberately not one combined product.
    for control,user in itertools.product(range(129),range(257)):
        gain=ref.reference(control,user)
        assert gain==int(Fraction(control*user,256))
        for start in range(0,65,4):
            volumes=[min(start+i,64) for i in range(4)]
            assert core.v6_music_gain_plan(15,0,Array(*volumes),control,user,0,0,C.byref(p))
            assert pairs(p)==[(0xa8+16*i,int(Fraction(v*gain,128))) for i,v in enumerate(volumes)]
            checks+=len(volumes)
    masks=0;instrument=Array(64,32,17,1)
    for music,sfx,muted,music_muted in itertools.product(range(16),range(16),range(2),range(2)):
        p.count=13;before=bytes(p)
        ok=core.v6_music_gain_plan(music,sfx,instrument,128,256,muted,music_muted,C.byref(p))
        if music&sfx:assert not ok and bytes(p)==before;continue
        assert ok
        gain=ref.reference_muted(128,256,muted,music_muted)
        expected=[(0xa8+16*i,instrument[i]*gain//128) for i in range(4) if music>>i&1]
        assert pairs(p)==expected
        # Applying to a fake register map preserves every non-music register.
        registers={0x96:0x820f,0x9c:0x780,**{0xa8+16*i:55 for i in range(4)}}
        old=dict(registers);registers.update(pairs(p))
        assert all(registers[reg]==value for reg,value in old.items() if reg not in {r for r,_ in expected})
        masks+=1
    assert list(instrument)==[64,32,17,1]
    for args in ((16,0,instrument,128,256,0,0),(1,16,instrument,128,256,0,0),
        (1,0,None,128,256,0,0),(1,0,instrument,129,256,0,0),
        (1,0,instrument,128,257,0,0),(1,0,instrument,128,256,2,0),
        (1,0,instrument,128,256,0,-1),(1,0,Array(65,0,0,0),128,256,0,0)):
        before=bytes(p);assert not core.v6_music_gain_plan(*args,C.byref(p));assert bytes(p)==before
    assert not core.v6_music_gain_plan(1,0,instrument,128,256,0,0,None)
    print(f'PASS music gain: {checks} source/fraction gain comparisons, {masks} partition/mute plans; reserved registers and instrument state preserved')
if __name__=='__main__':main()
