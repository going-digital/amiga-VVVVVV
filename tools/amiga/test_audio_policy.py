#!/usr/bin/env python3
"""Exhaustive reserved-channel and priority allocation, plus real voice replacement."""
import ctypes as C
import itertools
import json
import math
import subprocess
from test_audio import ROOT, Sample, Plan, pairs
from test_paula_voice import Voice

def main():
    out=ROOT/'build/amiga-audio';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/name) for name in ('audio_policy.c','audio.c','paula_voice.c')],
        '-o',str(out/'audio-policy.so')],check=True)
    core=C.CDLL(str(out/'audio-policy.so'));Array=C.c_uint*4
    core.v6_audio_choose.argtypes=[C.c_uint,C.c_uint,C.POINTER(C.c_uint),C.POINTER(C.c_uint),C.c_uint]
    cases=0
    for allowed,busy in itertools.product(range(16),repeat=2):
        for priorities in itertools.product(range(3),repeat=4):
            for incoming in range(3):
                ages=(1,9,9,4);p=Array(*priorities);a=Array(*ages)
                candidates=[i for i in range(4) if allowed>>i&1]
                idle=[i for i in candidates if not busy>>i&1]
                victims=[i for i in candidates if priorities[i]<incoming]
                expected=min(idle) if idle else min(victims,key=lambda i:(priorities[i],-ages[i],i)) if victims else -1
                before=(bytes(p),bytes(a))
                actual=core.v6_audio_choose(allowed,busy,p,a,incoming)
                assert actual==expected,(allowed,busy,priorities,incoming,actual,expected)
                assert before==(bytes(p),bytes(a));cases+=1
    # Every oldest-channel permutation and unsigned wrap-derived age.
    for ages in itertools.permutations((0,1,2,0xffffffff)):
        assert core.v6_audio_choose(15,15,Array(1,1,1,1),Array(*ages),2)==ages.index(0xffffffff)
    for allowed,busy,p,a in ((16,0,Array(),Array()),(0,16,Array(),Array()),
        (15,15,None,Array()),(15,15,Array(),None)):
        assert core.v6_audio_choose(allowed,busy,p,a,1)==-2
    # Composition with real channel plans: replace at every one-shot stage,
    # preserving the caller's three reserved voices and their DMA/IRQ bits.
    core.v6_paula_init.argtypes=[C.POINTER(Voice),C.c_uint,C.c_uint32]
    core.v6_paula_request.argtypes=[C.POINTER(Voice),C.POINTER(Sample),C.POINTER(Plan)]
    core.v6_paula_tick.argtypes=[C.POINTER(Voice),C.c_int,C.POINTER(Plan)]
    replacements=0
    for channel,state in itertools.product(range(4),(1,2,3)):
        voices=[Voice() for _ in range(4)];plan=Plan();sample=Sample(0x2000,2048,161,64)
        for i,v in enumerate(voices):
            assert core.v6_paula_init(C.byref(v),i,0x1000)
            assert core.v6_paula_request(C.byref(v),C.byref(sample),C.byref(plan))
            if state>=2:
                assert core.v6_paula_tick(C.byref(v),0,C.byref(plan))
                assert core.v6_paula_tick(C.byref(v),0,C.byref(plan))
            if state==3:assert core.v6_paula_tick(C.byref(v),1,C.byref(plan))
        before=[bytes(v) for v in voices];chosen=core.v6_audio_choose(1<<channel,15,Array(1,1,1,1),Array(4,3,2,1),2)
        assert chosen==channel
        replacement=Sample(0x4000,4096,161,64)
        assert core.v6_paula_request(C.byref(voices[chosen]),C.byref(replacement),C.byref(plan))
        assert pairs(plan)==[(0x96,1<<channel),(0xa8+16*channel,0),(0x9c,0x80<<channel)]
        assert all(bytes(v)==before[i] for i,v in enumerate(voices) if i!=chosen)
        assert voices[chosen].audio.replaced==1
        assert core.v6_paula_tick(C.byref(voices[chosen]),1,C.byref(plan)) and not plan.count
        assert core.v6_paula_tick(C.byref(voices[chosen]),0,C.byref(plan))
        assert voices[chosen].audio.sample.address==0x4000 and voices[chosen].audio.state==2
        replacements+=1
    # Reuse the native capture's request times and converted sample durations.
    # Add two cooldown fields plus one field for polling the final drain IRQ.
    # This is a policy budget simulation; it does not simulate music playback.
    import struct
    capture=ROOT/'build/amiga-teleporter-paula/energize.bin'
    if capture.exists():
        data=capture.read_bytes();at=data.index(b'V6TA\0\0\0\1')
        events=[struct.unpack_from('>4I',data,at+40+16*i) for i in range(8)]
        manifest=json.loads((ROOT/'build/amiga-feasibility/teleporter-samples.json').read_text())
        durations=[math.ceil(sample['pcm_duration']/.019968)+3 for sample in manifest['samples']]
        budgets=[]
        for allowed in (1,3,7,15):
            accepted=dropped=stolen=0;ends=[0]*4;priorities=[0]*4;begins=[0]*4
            for tick,cue,recorded_channel,field in events:
                busy=sum(1<<i for i in range(4) if ends[i]>field)
                ages=[field-begin for begin in begins]
                incoming=1+cue # Experimental: teleport outranks flash.
                chosen=core.v6_audio_choose(allowed,busy,Array(*priorities),Array(*ages),incoming)
                if chosen<0:dropped+=1;continue
                stolen+=bool(busy>>chosen&1);accepted+=1
                ends[chosen]=field+durations[cue];begins[chosen]=field;priorities[chosen]=incoming
            budgets.append(dict(sfx_channels=allowed.bit_count(),accepted=accepted,dropped=dropped,stolen=stolen))
        assert budgets[0]==dict(sfx_channels=1,accepted=6,dropped=2,stolen=1)
        assert budgets[1]==dict(sfx_channels=2,accepted=8,dropped=0,stolen=1)
        assert budgets[2]==dict(sfx_channels=3,accepted=8,dropped=0,stolen=0)
        assert budgets[3]==dict(sfx_channels=4,accepted=8,dropped=0,stolen=0)
        (out/'audio-policy-budgets.json').write_text(json.dumps(budgets,indent=2)+'\n')
        print('Captured-request budget simulation:',json.dumps(budgets))
    print(f'PASS audio policy: {cases} exhaustive allocations, 24 age permutations, {replacements} channel-local replacements; reserved channels protected')
if __name__=='__main__':main()
