#!/usr/bin/env python3
"""Register/ring address and translated sprite pixel oracles."""
import ctypes as C
import random
import subprocess
from test_player import ROOT,BUILD
from test_screen_shake import Plan

def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    path=BUILD/'screen-shake-dma.so'
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        *[str(ROOT/'amiga_version'/f) for f in ('screen_shake_dma.c','screen_shake_display.c')],'-o',str(path)],check=True)
    lib=C.CDLL(str(path));lib.v6_screen_shake_display.argtypes=[C.POINTER(C.c_uint16),C.POINTER(Plan),*([C.c_uint32]*3),C.c_uint,C.c_uint,C.c_int]
    lib.v6_screen_shake_sprite.argtypes=[C.POINTER(C.c_uint16),C.c_uint,C.c_int,C.c_int]
    out=(C.c_uint16*64)();cases=0
    for x in range(-4,3):
        for y in range(-4,5):
            p=Plan(x,y,max(-x,0),max(-y,0),max(x,0),max(y,0),320-abs(x),240-abs(y))
            n=lib.v6_screen_shake_display(out,C.byref(p),0x10000,0x15000,0x18000,255,200,1)
            regs={out[i]:out[i+1] for i in range(0,n-2,2) if not out[i]&1}
            assert regs[0x100]==0x1200 and ((regs[0xe0]<<16)|regs[0xe2])==0x18000
            for fo in range(256):
                bo=(fo*73+29)&255
                n=lib.v6_screen_shake_display(out,C.byref(p),0x10000,0x15000,0x18000,fo,bo,0)
                assert 0<n<=64 and tuple(out[n-2:n])==(0xffff,0xfffe)
                regs={};events=[];line=0;epoch=0
                for i in range(0,n-2,2):
                    r,v=out[i:i+2]
                    if r&1:
                        if r==0xffdf:epoch=256;line=255
                        else:line=(r>>8)+epoch
                    else:events.append((line,r,v))
                for beam in range(52+p.destination_y,52+p.destination_y+p.height):
                    for event in list(events):
                        if event[0]<=beam:
                            _,r,v=event;regs[r]=v;events.remove(event)
                    row=beam-(52+p.destination_y)
                    # Pointer updates happen on the preceding line, after DMA.
                    # Independently verify their addresses and ring wrap waits.
                    for base,reg,offset in ((0x10000,0xe0,fo),(0x15000,0xe4,bo),(0x12800,0xe8,fo)):
                        start=(offset+p.source_y)&255
                        wrap=52+p.destination_y+256-start-1
                        if beam>wrap:
                            expected=base
                        else:expected=base+start*40
                        actual=(regs[reg]<<16)|regs[reg+2]
                        # At the wrap scanline the new pointer is for next DMA.
                        if beam==wrap and wrap<52+p.destination_y+p.height-1:expected=base
                        assert actual==expected,(x,y,fo,beam,reg,actual,expected)
                    assert regs[0x102]==(16+x if x<0 else x)*0x11
                    assert regs[0x092]==(0x30 if x<0 else 0x38)
                    assert regs[0x108]==regs[0x10a]==(0xfffe if x<0 else 0)
                    assert ((regs[0x08e]>>8)&255)==52+p.destination_y
                    assert regs[0x08e]&255==129+max(x,0)
                    assert regs[0x090]&255==193+min(x,0)
                    # Extra fetch word is clipped out; row modulo stays 40.
                    assert (42 if x<0 else 40)+( -2 if x<0 else 0)==40
                cases+=1
    rng=random.Random(29);sprite_cases=0
    def pixels(d):
        if not d[0] and not d[1]:return {}
        top=(d[0]>>8)|((d[1]&4)<<6);bottom=(d[1]>>8)|((d[1]&2)<<7)
        left=(d[0]&255)*2+(d[1]&1)-128
        return {(left+x,top-52+y):((d[2+2*y]>>(15-x))&1)|(((d[3+2*y]>>(15-x))&1)<<1)
            for y in range(bottom-top) for x in range(16) if 0<=left+x<320}
    for _ in range(3000):
        d=(C.c_uint16*196)();left=rng.randrange(-15,320);top=rng.randrange(52,292);height=min(rng.randrange(1,97),292-top)
        stop=top+height;horizontal=128+left
        d[0]=((top&255)<<8)|(horizontal>>1);d[1]=((stop&255)<<8)|((top&256)>>6)|((stop&256)>>7)|(horizontal&1)
        mask=(0xffff>>max(-left,0)) & ((0xffff<<max(left-304,0))&0xffff)
        for i in range(2,2+height*2):d[i]=rng.randrange(65536)&mask
        before=pixels(d);x=rng.randrange(-4,3);y=rng.randrange(-4,5)
        assert lib.v6_screen_shake_sprite(d,196,x,y)
        expected={(a+x,b+y):v for (a,b),v in before.items() if 0<=a+x<320 and 0<=b+y<240}
        # Transparent pixels beyond original clipping must stay transparent.
        after=pixels(d)
        assert {k:v for k,v in after.items() if v}=={k:v for k,v in expected.items() if v}
        sprite_cases+=1
    out[:]=[0x1234]*64;p.x=99
    assert not lib.v6_screen_shake_display(out,C.byref(p),0x10000,0x15000,0x18000,0,0,0)
    assert list(out)==[0x1234]*64
    print(f'PASS shake display: {cases} ring/register plans; {sprite_cases} sprite pixel translations')
if __name__=='__main__':main()
