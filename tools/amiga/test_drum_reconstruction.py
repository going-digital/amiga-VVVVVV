#!/usr/bin/env python3
"""Reject pitched attack fixtures and check reconstructed percussion acoustics."""
import numpy as np
from scipy.signal import butter,sosfilt
from reconstruct_drums import measure_attack,classify,synthesize,reconstruct,classify_masked
from recognize_percussion import transient_signal


def main():
    sr=22050
    t=np.arange(round(.24*sr))/sr
    rng=np.random.default_rng(19)
    envelope=np.exp(-t/.045)
    fixtures={
        'kick':np.sin(2*np.pi*np.cumsum(55+130*np.exp(-t/.025))/sr)*np.exp(-t/.07),
        'snare':sosfilt(butter(3,[250,4500],fs=sr,btype='bandpass',output='sos'),rng.normal(size=len(t)))*envelope,
        'hat':sosfilt(butter(3,[5500,10000],fs=sr,btype='bandpass',output='sos'),rng.normal(size=len(t)))*np.exp(-t/.015),
    }
    for kind,clip in fixtures.items():
        metrics=measure_attack(clip,sr)
        detected,_=classify(metrics)
        assert detected==kind,(kind,detected,metrics)
        sample=synthesize(kind,metrics)
        pcm=np.array(sample['pcm'],dtype=np.uint8).view(np.int8)/128
        assert len(pcm)%2==0 and np.max(np.abs(pcm))>.5
        assert np.sqrt(np.mean(pcm[-100:]**2))<np.sqrt(np.mean(pcm[20:120]**2))*.2
        assert sample==synthesize(kind,metrics),'sample generation must be reproducible'
        if kind=='kick':
            spectrum=np.abs(np.fft.rfft(pcm*np.hanning(len(pcm))))**2
            f=np.fft.rfftfreq(len(pcm),1/11025)
            assert spectrum[f>600].sum()/spectrum.sum()<.01,'kick must not retain upper melodic partials'
    # Strong attacks and long pitched decays/chords must not become noise drums.
    for pitches in ((440,), (261.63,329.63,392), (98,146.83,196)):
        chord=sum(np.sin(2*np.pi*f*t) for f in pitches)/len(pitches)
        for decay in (.04,.2):
            detected,_=classify(measure_attack(chord*np.exp(-t/decay),sr))
            assert detected is None,(pitches,decay,detected)
            mixed=np.zeros(sr)
            start=round(.2*sr)
            mixed[start:start+len(chord)]=chord*np.exp(-t/decay)
            clean,_,_,_=transient_signal(mixed,sr)
            masked,_=classify_masked(measure_attack(mixed[start:start+len(chord)],sr),
                                     measure_attack(clean[start:start+len(chord)],sr))
            assert masked is None,('masked pitched attack',pitches,decay,masked)
    result=reconstruct(np.zeros(sr),sr,[dict(time=0,strength=1)])
    assert not result['hits'] and not result['samples']
    print('PASS noise/sweep classification; rejection of pitched attacks/chords; deterministic decaying samples; no upper melodic kick content; silence')


if __name__=='__main__':
    main()
