#!/usr/bin/env python3
"""Tracker word plans: ownership isolation, ordering and transactional validation."""
import ctypes as C
import itertools
import subprocess
from test_audio import ROOT,Plan,pairs

def plan(writes):
    p=Plan();p.count=len(writes)
    for i,(r,v) in enumerate(writes):p.writes[i].reg=r;p.writes[i].value=v
    return p

def main():
    out=ROOT/'build/amiga-music';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/music_registers.c'),
        '-o',str(out/'music-registers.so')],check=True)
    core=C.CDLL(str(out/'music-registers.so'))
    core.v6_music_register_plan.argtypes=[C.POINTER(Plan),C.c_uint,C.c_uint,C.POINTER(Plan)]
    tests=0
    for music,sfx in itertools.product(range(16),repeat=2):
        for setbit,dma,irq in itertools.product((0,32768),range(16),range(16)):
            writes=[(0x96,setbit|dma)]+[(0xa0+16*i,0) for i in range(4)]+[(0xa6+16*i,161+i) for i in range(4)]+[(0x9c,setbit|(irq<<7))]
            p=plan(writes);result=plan([(123,456)]);old=bytes(result)
            ok=core.v6_music_register_plan(C.byref(p),music,sfx,C.byref(result))
            if music&sfx:assert not ok and bytes(result)==old;continue
            assert ok
            expected=[]
            for r,v in writes:
                if r==0x96:
                    if dma&music:expected.append((r,setbit|(dma&music)))
                elif r==0x9c:
                    if irq&music:expected.append((r,setbit|((irq&music)<<7)))
                elif music>>((r-0xa0)//16)&1:expected.append((r,v))
            assert pairs(result)==expected
            # Model set/clear writes with reserved channels actively enabled and
            # pending. Every non-music register, DMA and IRQ bit must survive.
            dma_state=15;irq_state=0x780;registers={r:77 for r in range(0xa0,0xe0,2)}
            before=dict(registers)
            for r,v in pairs(result):
                if r==0x96:dma_state=(dma_state|v&15) if v&32768 else (dma_state&~(v&15))
                elif r==0x9c:irq_state=(irq_state|v&0x780) if v&32768 else (irq_state&~(v&0x780))
                else:registers[r]=v
            assert (dma_state^15)&~music==0 and (irq_state^0x780)&~(music<<7)==0
            assert all(registers[r]==v for r,v in before.items() if not music>>((r-0xa0)//16)&1)
            inplace=plan(writes);assert core.v6_music_register_plan(C.byref(inplace),music,sfx,C.byref(inplace))
            assert pairs(inplace)==expected;tests+=1
    # Each accepted word register, maximum plan size and volume limits.
    for channel,offset in itertools.product(range(4),(0,2,4,6,8)):
        p=plan([(0xa0+channel*16+offset,64 if offset==8 else 65535)]*16);result=Plan()
        assert core.v6_music_register_plan(C.byref(p),1<<channel,15^(1<<channel),C.byref(result))
        assert pairs(result)==pairs(p)
    bad_writes=[(0x96,0x8201),(0x96,0x200),(0x9c,0x4080),(0x9a,0x80),
        (0xa1,0),(0xaa,0),(0xae,0),(0xe0,0),(0xa8,65),(0xd8,65535),(0xa0,65536)]
    for write in bad_writes:
        p=plan([(0xa0,3),write]);result=plan([(99,88)]);before=bytes(result)
        assert not core.v6_music_register_plan(C.byref(p),1,14,C.byref(result)) and bytes(result)==before
        before=bytes(p);assert not core.v6_music_register_plan(C.byref(p),1,14,C.byref(p)) and bytes(p)==before
    p=Plan();p.count=17;result=Plan();before=bytes(result)
    assert not core.v6_music_register_plan(C.byref(p),15,0,C.byref(result)) and bytes(result)==before
    p=Plan()
    for music,sfx in ((16,0),(0,16),(1,1)):
        assert not core.v6_music_register_plan(C.byref(p),music,sfx,C.byref(result))
    assert not core.v6_music_register_plan(None,15,0,C.byref(result))
    assert not core.v6_music_register_plan(C.byref(p),15,0,None)
    print(f'PASS music register boundary: {tests} partition/DMA/IRQ plans and in-place checks; active reserved bits preserved, malformed streams rejected transactionally')
if __name__=='__main__':main()
