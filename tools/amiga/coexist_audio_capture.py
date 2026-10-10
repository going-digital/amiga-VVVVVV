"""Native synthetic replay/SFX coexistence: gains, periods, mute and stopping."""
import math
import struct
from audio_capture import read_wav

def verify(report,ram,folder):
    data=ram.read_bytes();at=data.index(b'V6MX\0\0\0\1')
    count,violations=struct.unpack_from('>2I',data,at+8)
    assert (count,violations)==(7,0),(count,violations)
    rows=[struct.unpack_from('>6I',data,at+16+24*i) for i in range(7)]
    assert [r[0] for r in rows]==[1,80,120,160,200,240,280],rows
    assert [r[2:] for r in rows]==[(161,241,48,32),(161,241,24,16),
        (161,241,0,0),(161,241,24,16),(161,241,48,32),
        (251,181,48,32),(251,181,0,0)],rows
    assert all(b[1]-a[1]==b[0]-a[0] for a,b in zip(rows,rows[1:])),rows
    gains=[];frequencies=[]
    for channel in (2,3):
        rate,left,right=read_wav(folder/f'paula-{channel}.wav')
        wave=left if sum(v*v for v in left)>sum(v*v for v in right) else right
        onset=next(i for i,v in enumerate(wave) if abs(v)>.001)
        def window(stage):
            start=(rows[stage][0]-1)*.019968+.15
            end=(rows[stage+1][0]-1)*.019968-.15
            return wave[onset+round(start*rate):onset+round(end*rate)]
        def rms(values):return math.sqrt(sum(v*v for v in values)/len(values))
        energy=[rms(window(i)) for i in range(6)]
        assert energy[0]>.005 and energy[4]>.005,energy
        ratios=[energy[i]/energy[0] for i in (1,3,4)]
        assert abs(ratios[0]-.5)<.08 and abs(ratios[1]-.5)<.08 and abs(ratios[2]-1)<.1,ratios
        assert energy[2]<1e-5,energy # Music mute while SFX continues.
        for stage,period in ((0,rows[0][channel]),(5,rows[5][channel])):
            values=window(stage)
            # Hann-windowed Goertzel scan measures the fundamental despite
            # analogue-filter ringing and quantization around zero crossings.
            decimated=values[::8];sample_rate=rate/8
            tapered=[v*(.5-.5*math.cos(2*math.pi*i/(len(decimated)-1))) for i,v in enumerate(decimated)]
            def power(frequency):
                coefficient=2*math.cos(2*math.pi*frequency/sample_rate);a=b=0.0
                for v in tapered:a,b=v+coefficient*a-b,a
                return a*a+b*b-coefficient*a*b
            measured=max(range(150,451),key=power);expected=3546895/(period*64)
            assert abs(measured-expected)<5,(channel,stage,measured,expected)
            frequencies.append(round(measured,3))
        stop=onset+round(((280-1)*.019968+.2)*rate)
        assert len(wave)-stop>rate and max(map(abs,wave[stop:]),default=0)<1e-5
        gains.append([round(v,4) for v in ratios])
    report.update(synthetic_music_stages=7,synthetic_music_gain_ratios=gains,
        synthetic_music_frequencies=frequencies,synthetic_music_policy_violations=violations,
        scope='Native synthetic looping voices on channels 2/3 plus teleporter SFX on 0/1; guarded register/gain plans, mute, period changes and silence verified; no tracker module playback')
