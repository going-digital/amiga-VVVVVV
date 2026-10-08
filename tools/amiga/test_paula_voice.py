#!/usr/bin/env python3
"""Single-channel Paula plans, isolation, overlap and one-shot draining."""
import ctypes as C
import subprocess
from test_audio import Audio,Sample,Plan,pairs,ROOT

class Voice(C.Structure):
    _fields_=[('audio',Audio),('channel',C.c_uint)]

def main():
    out=ROOT/'build/amiga-audio';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/audio.c'),
        str(ROOT/'amiga_version/paula_voice.c'),'-o',str(out/'paula-voice.so')],check=True)
    core=C.CDLL(str(out/'paula-voice.so'))
    core.v6_paula_init.argtypes=[C.POINTER(Voice),C.c_uint,C.c_uint32]
    core.v6_paula_request.argtypes=[C.POINTER(Voice),C.POINTER(Sample),C.POINTER(Plan)]
    core.v6_paula_tick.argtypes=[C.POINTER(Voice),C.c_int,C.POINTER(Plan)]
    core.v6_paula_stop.argtypes=[C.POINTER(Voice),C.POINTER(Plan)]
    voices=[Voice() for i in range(4)];p=Plan();dma=15;registers={};checks=0
    def apply(channel):
        nonlocal dma,checks
        before=dma;old=dict(registers);base=0xa0+16*channel
        for reg,value in pairs(p):
            if reg==0x96:
                assert value&15==1<<channel
                if value&0x8000:dma|=value&15
                else:dma&=~(value&15)
            elif reg==0x9c:assert value==0x80<<channel
            else:
                assert base<=reg<=base+8
                registers[reg]=value
        assert (dma^before)&~(1<<channel)==0
        assert all(registers[reg]==value for reg,value in old.items() if not base<=reg<=base+8)
        checks+=1
    for channel,v in enumerate(voices):
        assert core.v6_paula_init(C.byref(v),channel,0x1000)
        sample=Sample(0x2000+channel*4096,2048,161,64)
        assert core.v6_paula_request(C.byref(v),C.byref(sample),C.byref(p));apply(channel)
        assert pairs(p)==[(0x96,1<<channel),(0xa8+channel*16,0),(0x9c,0x80<<channel)]
        assert core.v6_paula_tick(C.byref(v),1,C.byref(p)) and not p.count
        assert core.v6_paula_tick(C.byref(v),0,C.byref(p));apply(channel)
        base=0xa0+16*channel
        assert pairs(p)==[(0x9c,0x80<<channel),(base,0),(base+2,sample.address),
            (base+4,1024),(base+6,161),(base+8,64),(0x96,0x8200|(1<<channel))]
        assert v.audio.state==2 and v.audio.starts==1
    assert dma==15 # All channels play concurrently, with separate registers.
    for channel,v in enumerate(voices):
        assert core.v6_paula_tick(C.byref(v),1,C.byref(p));apply(channel)
        base=0xa0+16*channel
        assert pairs(p)==[(base,0),(base+2,0x1000),(base+4,1),(0x9c,0x80<<channel)]
        assert v.audio.state==3
        assert core.v6_paula_tick(C.byref(v),0,C.byref(p)) and not p.count
        assert core.v6_paula_tick(C.byref(v),1,C.byref(p));apply(channel)
        assert (v.audio.state,v.audio.completed,v.audio.interrupts)==(0,1,2)
        assert core.v6_paula_stop(C.byref(v),C.byref(p));apply(channel)
    assert dma==0
    sample=Sample(0x2000,2048,161,64)
    for channel in range(4):
        v=Voice();assert core.v6_paula_init(C.byref(v),channel,0x1000)
        assert core.v6_paula_request(C.byref(v),C.byref(sample),C.byref(p))
        before=(bytes(v),bytes(p));sample.address=0x2001
        assert not core.v6_paula_request(C.byref(v),C.byref(sample),C.byref(p))
        assert before==(bytes(v),bytes(p));sample.address=0x2000
        v.channel=4;before=(bytes(v),bytes(p))
        assert not core.v6_paula_tick(C.byref(v),1,C.byref(p))
        assert not core.v6_paula_stop(C.byref(v),C.byref(p))
        assert not core.v6_paula_request(C.byref(v),C.byref(sample),C.byref(p))
        assert before==(bytes(v),bytes(p))
        assert not core.v6_paula_init(C.byref(v),4,0x1000) and before[0]==bytes(v)
        assert not core.v6_paula_tick(None,1,C.byref(p))
        assert not core.v6_paula_stop(C.byref(v),None)
    print(f'PASS Paula voices: four concurrent channels, {checks} isolated register plans, selective IRQ/DMA masks, one-shot drains and transactional rejection')
if __name__=='__main__':main()
