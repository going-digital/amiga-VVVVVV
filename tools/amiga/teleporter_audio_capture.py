"""Native independently panned cue voices: counters, order and captured PCM."""
import json
import math
import struct
from audio_capture import ROOT,read_wav

def verify(report,ram,folder,reserved=False):
    data=ram.read_bytes();at=data.index(b'V6TA\0\0\0\1')
    values=struct.unpack_from('>8I',data,at+8)
    assert values[:7]==((0,8,7,15,8,0,2) if reserved else (0,8,8,16,8,0,3)),values
    if reserved or b'V6AP\0\0\0\1' in data:
        policy_at=data.index(b'V6AP\0\0\0\1')
        policy=struct.unpack_from('>3I',data,policy_at+8)
        assert policy==((3,1,0) if reserved else (15,0,0)),policy
    records=[struct.unpack_from('>4I',data,at+40+16*i) for i in range(8)]
    expected=[(1,0),(11,1),(23,0),(38,1),(65,0),(75,1),(87,0),(102,1)]
    assert [r[:2] for r in records]==expected,records
    assert [r[2] for r in records]==([0,1,0,0,1,1,0,0] if reserved else [0,1,0,0,1,2,0,0]),records
    manifest=json.loads((ROOT/'build/amiga-feasibility/teleporter-samples.json').read_text())
    payloads=[(ROOT/'build/amiga-feasibility'/('teleporter-'+cue+'.pcm')).read_bytes()
        for cue in ('flash','teleport')]
    templates=[[v if v<128 else v-256 for v in payload] for payload in payloads]
    correlations=[];durations=[];channel_waves=[]
    for channel in range(4):
        rate,left,right=read_wav(folder/('paula-'+str(channel)+'.wav'))
        # Channel stems can be mono or panned stereo. Use the active side.
        wave=left if sum(v*v for v in left)>sum(v*v for v in right) else right
        channel_waves.append(wave)
        channel_records=[r for r in records if r[2]==channel]
        order=[r[1] for r in channel_records]
        if not order:
            assert max(map(abs,wave),default=0)<1e-6
            continue
        active=[i for i in range(0,len(wave),256) if max(map(abs,wave[i:i+256]),default=0)>.002]
        bursts=[]
        for i in active:
            if not bursts or i-bursts[-1][1]>rate*.02:bursts.append([i,i+256])
            else:bursts[-1][1]=i+256
        assert len(bursts)==len(order),(channel,bursts,order)
        def correlate(template,begin,duration):
            n=min(math.ceil(len(template)*manifest['period']*rate/manifest['pal_clock']),round(duration*rate))
            ref=[template[min(len(template)-1,int(i*manifest['pal_clock']/(manifest['period']*rate)))] for i in range(n)]
            first=next(i for i,v in enumerate(ref) if abs(v)>=2);best=-1.0
            for origin in range(begin-first-int(rate*.012),begin-first+int(rate*.012),4):
                dot=aa=bb=0.0
                for i in range(64,n-64,16):
                    at=origin+i
                    if 0<=at<len(wave):
                        a=ref[i];b=wave[at];dot+=a*b;aa+=a*a;bb+=b*b
                if aa and bb:best=max(best,dot/math.sqrt(aa*bb))
            return best
        for index,((begin,end),cue) in enumerate(zip(bursts,order)):
            expected_duration=manifest['samples'][cue]['pcm_duration']
            if reserved and channel_records[index][0]==65:
                assert channel_records[index+1][0]==75
                expected_duration=min(expected_duration,(channel_records[index+1][3]-channel_records[index][3]-2)*.019968)
            correct=correlate(templates[cue],begin,expected_duration);wrong=correlate(templates[1-cue],begin,expected_duration)
            assert correct>.7 and correct>wrong+.1,(channel,cue,correct,wrong)
            duration=(end-begin)/rate
            assert abs(duration-expected_duration)<.08,(channel,cue,duration)
            if reserved and channel_records[index][0]==65:
                assert duration<manifest['samples'][cue]['pcm_duration']-.04,duration
            correlations.append(round(correct,5));durations.append(round(duration,5))
        assert len(wave)-bursts[-1][1]>rate,'No sustained silence after final cue'
    stereo_rate,left,right=read_wav(folder/'paula.wav')
    assert stereo_rate==rate and all(len(w)==len(left)==len(right) for w in channel_waves)
    def pan_correlation(output,channels):
        dot=aa=bb=0.0
        for i in range(0,len(output),16):
            a=output[i];b=sum(channel_waves[c][i] for c in channels)
            dot+=a*b;aa+=a*a;bb+=b*b
        return dot/math.sqrt(aa*bb) if aa and bb else 0.0
    panning=[]
    for output,correct,wrong in ((left,(0,3),(1,2)),(right,(1,2),(0,3))):
        actual=pan_correlation(output,correct);alternate=pan_correlation(output,wrong)
        assert actual>.75 and actual>alternate+.3,(actual,alternate)
        panning.append(round(actual,5))
    report.update(audio_channels=[r[2] for r in records],audio_completed=values[2],audio_peak_voices=values[6],audio_replaced=1 if reserved else 0,
        audio_reserved_mask=12 if reserved else 0,audio_policy_violations=0,
        audio_panning_correlations=panning,audio_waveform_correlations=correlations,audio_burst_durations=durations)
