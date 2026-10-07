"""Verify native Paula stereo output against converted private cue waveforms."""
import array
import json
import math
from pathlib import Path
import struct
import sys
ROOT=Path(__file__).resolve().parents[2]

def read_wav(path):
    data=path.read_bytes();assert data[:4]==b'RIFF' and data[8:12]==b'WAVE'
    at=12;fmt=payload=None
    while at+8<=len(data):
        tag,n=struct.unpack_from('<4sI',data,at)
        if tag==b'fmt ':fmt=data[at+8:at+8+n]
        if tag==b'data':payload=data[at+8:at+8+n]
        at+=8+n+(n&1)
    code,channels,rate,_,alignment,bits=struct.unpack_from('<HHIIHH',fmt)
    if code==65534:code=struct.unpack_from('<H',fmt,24)[0]
    assert code==3 and channels in (1,2) and bits==32 and alignment==channels*4
    samples=array.array('f');samples.frombytes(payload)
    if sys.byteorder!='little':samples.byteswap()
    return (rate,samples[::2],samples[1::2]) if channels==2 else (rate,samples,samples)

def verify(report,ram,wav,skip=False):
    data=ram.read_bytes();offset=data.index(b'V6AU\0\0\0\1')
    state,starts,completed,replaced,error,interrupts,consumed=struct.unpack_from('>7I',data,offset+8)
    expected=1 if skip else 6
    assert (state,starts,completed,replaced,error,interrupts,consumed)==(0,expected,expected,0,0,expected*2,expected)
    folder=wav if wav.is_dir() else None
    rate,left,right=read_wav(wav/"paula.wav" if folder else wav);active=[]
    # RMS-sized blocks bridge brief waveform zero crossings without merging
    # separate cues. A 20ms quiet gap closes each burst.
    for at in range(0,len(left),256):
        if max(map(abs,left[at:at+256]),default=0)>.002:active.append(at)
    bursts=[]
    for at in active:
        if not bursts or at-bursts[-1][1]>rate*.02:bursts.append([at,at+256])
        else:bursts[-1][1]=at+256
    assert len(bursts)==expected,(bursts,expected)
    manifest=json.loads((ROOT/'build/amiga-feasibility/cue-samples.json').read_text())
    programs=json.loads((ROOT/'build/amiga-feasibility/rescue-programs.json').read_text())
    order=[op['value'] for op in programs['programs']['skipred' if skip else 'rescuered']['ops'] if op['op']=='CUE']
    assert len(order)==expected
    correlations=[];stereo=[];durations=[]
    for (begin,end),speaker in zip(bursts,order):
        sample=manifest['samples'][speaker]
        pcm=(ROOT/'build/amiga-feasibility'/sample['file'].replace('.wav','.pcm')).read_bytes()
        pcm=[v if v<128 else v-256 for v in pcm]
        # Zero-order DAC template. Allow the analogue filter's phase delay;
        # compare both voices so correct speaker selection is also checked.
        def correlation(template):
            n=math.ceil(len(template)*sample['period']*rate/manifest['pal_clock'])
            ref=[template[min(len(template)-1,int(i*manifest['pal_clock']/(sample['period']*rate)))] for i in range(n)]
            first=next(i for i,v in enumerate(ref) if abs(v)>=2)
            best=-1.0
            for origin in range(begin-first-int(rate*.012),begin-first+int(rate*.012),4):
                dot=aa=bb=0.0
                for i in range(64,n-64,8):
                    at=origin+i
                    if not 0<=at<len(left):continue
                    a=ref[i];b=left[at];dot+=a*b;aa+=a*a;bb+=b*b
                if aa and bb:best=max(best,dot/math.sqrt(aa*bb))
            return best
        correct=correlation(pcm)
        other=manifest['samples'][1-speaker]
        alternate=(ROOT/'build/amiga-feasibility'/other['file'].replace('.wav','.pcm')).read_bytes()
        wrong=correlation([v if v<128 else v-256 for v in alternate])
        assert correct>.7 and correct>wrong+.1,(speaker,correct,wrong)
        correlations.append(round(correct,5))
        dot=sum(left[i]*right[i] for i in range(begin,end,8))
        aa=sum(left[i]**2 for i in range(begin,end,8));bb=sum(right[i]**2 for i in range(begin,end,8))
        similarity=dot/math.sqrt(aa*bb);assert similarity>.98
        stereo.append(round(similarity,5));durations.append(round((end-begin)/rate,5))
        assert .06<(end-begin)/rate<.15,('Repeated or truncated cue',begin,end,rate)
    if folder:
        for channel in (2,3):
            _,silent,_=read_wav(folder/("paula-"+str(channel)+".wav"))
            assert max(map(abs,silent),default=0)<1e-6,("Unexpected other-channel audio",channel)
    assert len(left)-bursts[-1][1]>rate, 'No sustained silence after final cue'
    report.update(audio_starts=starts,audio_completed=completed,audio_interrupts=interrupts,
        audio_speaker_order=order,audio_waveform_correlations=correlations,audio_stereo_correlations=stereo,
        audio_burst_durations=durations,audio_capture_rate=rate)
