"""Verify Prize cue requests, reserved voices and captured sample identity."""
import json
import math
import struct
from audio_capture import ROOT,read_wav

def verify(data,folder):
    at=data.index(b'V6PA\0\0\0\1');values=struct.unpack_from('>5I',data,at+8)
    assert values==(2,1,0,1,0),values
    records=[struct.unpack_from('>4I',data,at+28+16*i) for i in range(3)]
    assert [r[:2] for r in records]==[(42,2),(97,2),(152,3)],records
    assert all(r[2] in (2,3) for r in records),records
    at=data.index(b'V6AP\0\0\0\1');assert struct.unpack_from('>3I',data,at+8)==(12,0,0)
    at=data.index(b'V6TA\0\0\0\1');assert struct.unpack_from('>7I',data,at+8)==(0,3,3,6,3,0,1)
    manifest=json.loads((ROOT/'build/amiga-feasibility/prize-samples.json').read_text())
    templates=[[(v if v<128 else v-256) for v in (ROOT/'build/amiga-feasibility'/('prize-'+cue+'.pcm')).read_bytes()] for cue in ('vanish','trinket')]
    correlations=[]
    for channel in range(4):
        rate,left,right=read_wav(folder/f'paula-{channel}.wav')
        samples=left if sum(v*v for v in left)>sum(v*v for v in right) else right
        requests=[r for r in records if r[2]==channel]
        if not requests:
            assert max(map(abs,samples),default=0)<1e-6
            continue
        blocks=[i for i in range(0,len(samples),256) if max(map(abs,samples[i:i+256]),default=0)>.002]
        bursts=[]
        for i in blocks:
            if not bursts or i-bursts[-1][1]>rate*.08:bursts.append([i,i+256])
            else:bursts[-1][1]=i+256
        assert len(bursts)==len(requests),(channel,bursts,requests)
        for (begin,end),request in zip(bursts,requests):
            cue=request[1]-2;template=templates[cue]
            n=math.ceil(len(template)*manifest['period']*rate/manifest['pal_clock'])
            ref=[template[min(len(template)-1,int(i*manifest['pal_clock']/(manifest['period']*rate)))] for i in range(n)]
            first=next(i for i,v in enumerate(ref) if abs(v)>=2);best=-1
            for origin in range(begin-first-int(rate*.012),begin-first+int(rate*.012),4):
                dot=aa=bb=0
                for i in range(64,n-64,16):
                    if 0<=origin+i<len(samples):
                        a=ref[i];b=samples[origin+i];dot+=a*b;aa+=a*a;bb+=b*b
                if aa and bb:best=max(best,dot/math.sqrt(aa*bb))
            assert best>.7,(cue,best)
            audible=[i for i,v in enumerate(template) if v]
            expected_duration=(audible[-1]-audible[0]+1)*manifest['period']/manifest['pal_clock']
            assert abs((end-begin)/rate-expected_duration)<.08,(cue,(end-begin)/rate,expected_duration)
            correlations.append(round(best,5))
        assert len(samples)-bursts[-1][1]>rate
    print('PASS native Prize audio: two vanish cues, source trinket jingle, completion during pause, protected channels and PCM correlations',correlations)
