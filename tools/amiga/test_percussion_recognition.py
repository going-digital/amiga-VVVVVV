#!/usr/bin/env python3
"""Controlled repeated drums under sustained pitched tones; optional audio deps."""
import numpy as np
from scipy.signal import butter, sosfilt
from recognize_percussion import analyze


def main():
    sr=22050
    t=np.arange(sr*8)/sr
    melody=.05*np.sin(2*np.pi*98*t)+.02*np.sin(2*np.pi*392*t)
    y=melody.copy()
    rng=np.random.default_rng(7)
    expected=[]
    for repeat in range(3):
        for offset,kind in ((.6,'kick'),(1.4,'snare'),(2.2,'hat')):
            when=repeat*2.4+offset
            u=np.arange(round(.2*sr))/sr
            if kind=='kick':
                frequency=55+110*np.exp(-u/.025)
                pulse=np.sin(2*np.pi*np.cumsum(frequency)/sr)*np.exp(-u/.065)*.6
            else:
                pulse=rng.normal(size=len(u))*np.exp(-u/(.045 if kind=='snare' else .012))*.3
                if kind=='hat':
                    pulse=sosfilt(butter(3,5000,fs=sr,btype='highpass',output='sos'),pulse)
            at=round(when*sr)
            y[at:at+len(pulse)]+=pulse
            expected.append((when,kind))
    percussion,_=analyze(y,sr)
    for time,kind in expected:
        nearest=min(percussion['hits'],key=lambda h:abs(h['time']-time))
        assert abs(nearest['time']-time)<.06,(kind,time,nearest)
        name=percussion['samples'][nearest['sample']]['name']
        assert name==kind+' candidate',(kind,time,name)
    assert len(percussion['hits'])==len(expected),len(percussion['hits'])
    for sample in percussion['samples']:
        assert len(sample['pcm'])%2==0
        assert sample['pcm'][:2]==[0,0]
    sustained,_=analyze(melody,sr)
    assert not sustained['hits'], sustained['hits']
    empty,_=analyze(np.zeros(sr),sr)
    assert not empty['hits'] and not empty['samples']
    print('PASS repeated kick/snare/hat attacks beneath sustained tones: 9 hits, labels, timing, sample layout and silent input')


if __name__=='__main__':
    main()
