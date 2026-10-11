#!/usr/bin/env python3
"""Translate caption/scene DMA rows across every shake and ring offset."""
import ctypes as C
import subprocess
from test_player import ROOT, BUILD
from test_screen_shake import Plan


def main():
    BUILD.mkdir(parents=True,exist_ok=True)
    path=BUILD/'shake-caption.so'
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),
        str(ROOT/'amiga_version/screen_shake_display.c'),'-o',str(path)],check=True)
    lib=C.CDLL(str(path));lib.v6_screen_shake_caption.argtypes=[C.POINTER(C.c_uint16),C.POINTER(Plan),
        *([C.c_uint32]*3),C.c_uint,C.c_uint,C.c_int,C.c_uint32,C.c_uint,C.c_uint,C.c_uint]
    out=(C.c_uint16*130)();cases=0;maximum=0
    for x in range(-4,3):
        for y in range(-4,5):
            p=Plan(x,y,max(-x,0),max(-y,0),max(x,0),max(y,0),320-abs(x),240-abs(y))
            for fo in range(256):
                bo=(fo*73+29)&255
                out[:]=[0x1234]*130
                n=lib.v6_screen_shake_caption(out,C.byref(p),0x10000,0x15000,0x18000,fo,bo,0,0x20000,0x6ff,0x123,0x456)
                assert 0<n<=128 and tuple(out[n-2:n])==(0xffff,0xfffe)
                assert tuple(out[128:])==(0x1234,0x1234)
                maximum=max(maximum,n)
                events=[];line=0;epoch=0
                for i in range(0,n-2,2):
                    r,v=out[i:i+2]
                    if r&1:
                        if r==0xffdf:epoch=256;line=255
                        else:line=(r>>8)+epoch
                    else:events.append((line,r,v))
                regs={};at=0
                for beam in range(52+p.destination_y,52+p.destination_y+p.height):
                    while at<len(events) and events[at][0]<beam:
                        _,r,v=events[at];regs[r]=v;at+=1
                    sy=beam-52-y;caption=16<=sy<64
                    assert regs[0x100]==(0x2200 if caption else 0x4600),(x,y,fo,beam,regs)
                    assert regs[0x102]==(16+x if x<0 else x)*0x11
                    assert regs[0x108]==regs[0x10a]==(0xfffe if x<0 else 0)
                    if caption:
                        expected={0xe0:0x20000+(sy-16)*40,0xe4:0x20780+(sy-16)*40}
                        assert regs[0x182]==0 and regs[0x186]==0x6ff
                    else:
                        expected={0xe0:0x10000+((fo+sy)&255)*40,
                                  0xe8:0x12800+((fo+sy)&255)*40,
                                  0xe4:0x15000+((bo+sy)&255)*40}
                        if sy>=64:assert regs[0x182]==0x123 and regs[0x186]==0x456
                    for r,address in expected.items():
                        assert (regs[r]<<16)|regs[r+2]==address,(x,y,fo,beam,r,regs,address)
                    # DDF/modulo consume exactly 40 bytes per fetched plane.
                    for r in ((0xe0,0xe4) if caption else (0xe0,0xe4,0xe8,0xec)):
                        address=((regs[r]<<16)|regs[r+2])+40
                        regs[r]=address>>16;regs[r+2]=address&65535
                cases+=1
            n=lib.v6_screen_shake_caption(out,C.byref(p),0x10000,0x15000,0x18000,255,200,1,0x20000,0x6ff,0x123,0x456)
            regs={out[i]:out[i+1] for i in range(0,n-2,2) if not out[i]&1}
            assert regs[0x100]==0x1200 and ((regs[0xe0]<<16)|regs[0xe2])==0x18000
            assert 0x186 not in regs # Flash replaces caption instead of overlaying text.
    for caption,tint,c1,c3 in ((0,0,0,0),(1,0,0,0),(0x1000000-3839,0,0,0),(0x20000,0x1000,0,0),(0x20000,0,0x1000,0),(0x20000,0,0,0x1000)):
        out[:]=[0x1234]*130
        assert not lib.v6_screen_shake_caption(out,C.byref(p),0x10000,0x15000,0x18000,0,0,0,caption,tint,c1,c3)
        assert list(out)==[0x1234]*130
    print(f'PASS shake caption: {cases} translated scene/caption DMA plans, flash coverage, invalid preservation; maximum {maximum}/128 words')
if __name__=='__main__':main()
