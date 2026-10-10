#!/usr/bin/env python3
"""Optional independent libxmp playback check; requires numpy and local library."""
import argparse
import json
import math
from pathlib import Path
import tempfile
import wave
from render_tracker import render
from transcribe_tracker import working_module


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--library', type=Path, required=True)
    args = p.parse_args()
    import numpy as np
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        pitches = (24,48,55,72,84)
        notes = [[i*.8, i*.8+.5, pitch, .9] for i,pitch in enumerate(pitches)]
        module, _ = working_module(notes, 150, 4)
        (root/'check.mod').write_bytes(module)
        report = render(args.library, root/'check.mod', root/'check.wav', 5)
        assert report['first_loop_reached'], report
        with wave.open(str(root/'check.wav')) as wav:
            audio = np.frombuffer(wav.readframes(wav.getnframes()), dtype='<i2').reshape(-1,2)/32768
        results = []
        for i, midi in enumerate(pitches):
            start, end = i*.8+.1, i*.8+.4
            y = audio[round(start*48000):round(end*48000)].mean(axis=1)
            spectrum = np.abs(np.fft.rfft(y*np.hanning(len(y)), n=262144))
            frequencies = np.fft.rfftfreq(262144, 1/48000)
            expected = 440*2**((midi-69)/12)
            region = np.where((frequencies > expected*.9) & (frequencies < expected*1.1))[0]
            actual = frequencies[region[np.argmax(spectrum[region])]]
            cents = 1200*math.log2(actual/expected)
            assert abs(cents) < 12, (midi, actual, cents)
            assert np.sqrt(np.mean(y*y)) > .01
            results.append(dict(midi=midi, frequency=actual, error_cents=cents))
        # Note-off commands must produce sustained silence between notes.
        silent = audio[round(.6*48000):round(.7*48000)]
        assert np.max(np.abs(silent)) <= 2/32768, np.max(np.abs(silent))
        # Independent playback must honor ED2 rather than firing at row start.
        drum = dict(name='test hit', pcm=[0,0]+[80,0,176,0]*400, volume=40)
        percussion = dict(samples=[drum],hits=[dict(time=.04,sample=0,strength=.8)],timing='ticks')
        delayed,_ = working_module([],150,.4,roles=[],percussion=percussion)
        (root/'delayed.mod').write_bytes(delayed)
        render(args.library,root/'delayed.mod',root/'delayed.wav',1)
        with wave.open(str(root/'delayed.wav')) as wav:
            delayed_audio=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,2)/32768
        assert np.max(np.abs(delayed_audio[:round(.025*48000)])) <= 2/32768
        assert np.sqrt(np.mean(delayed_audio[round(.045*48000):round(.07*48000)]**2)) > .01
        # Twice the tick clock must preserve an accepted ED2 onset as ED4.
        clocks=[]
        for multiplier in (1,2):
            clocked,_=working_module([],92,.4,roles=[],percussion=dict(
                samples=[drum],hits=[dict(time=.054,sample=0,strength=.8)],timing='ticks'),
                tick_multiplier=multiplier)
            path=root/('clock-'+str(multiplier))
            path.with_suffix('.mod').write_bytes(clocked)
            render(args.library,path.with_suffix('.mod'),path.with_suffix('.wav'),1)
            with wave.open(str(path.with_suffix('.wav'))) as wav:
                samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,2)
            clocks.append(int(np.where(np.max(np.abs(samples),axis=1)>3)[0][0]))
        assert abs(clocks[0]-clocks[1])<=1,clocks
        # Finer rows at the same doubled tick clock must retain drum onset time.
        fine,_=working_module([],184,.4,roles=[],percussion=dict(samples=[drum],
            hits=[dict(time=2*(7.5/92)/3,sample=0,strength=.8)],timing='ticks'))
        (root/'fine.mod').write_bytes(fine)
        render(args.library,root/'fine.mod',root/'fine.wav',1)
        with wave.open(str(root/'fine.wav')) as wav:
            samples=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,2)
        onset=int(np.where(np.max(np.abs(samples),axis=1)>3)[0][0])
        assert abs(onset-clocks[1])<=1,(onset,clocks)

        # Corrupt eight-channel storage must be rejected by independent loader.
        (root/'broken.mod').write_bytes(module[:1084])
        try:
            render(args.library, root/'broken.mod', root/'broken.wav', 1)
        except ValueError:
            pass
        else:
            raise AssertionError('libxmp accepted a truncated pattern stream')
        print(json.dumps(dict(pitch_checks=results, silence=True, corrupt_rejected=True, note_delay=True), indent=2))


if __name__ == '__main__':
    main()
