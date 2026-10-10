#!/usr/bin/env python3
import unittest
import numpy as np
from detect_vibrato import fit_periodic,coherent
from transcribe_tracker import working_module


class VibratoTests(unittest.TestCase):
    def test_requires_periodic_agreement_not_pitch_drift(self):
        t=np.arange(0,.45,.005)
        a=fit_periodic(t,10*np.sin(2*np.pi*7.8*t)+3*t)
        b=fit_periodic(t,11*np.sin(2*np.pi*7.8*t+.1)-2*t)
        self.assertTrue(coherent(a,b,t[-1]))
        self.assertAlmostEqual(a['rate'],7.8,places=2)
        self.assertFalse(coherent(a,fit_periodic(t,10*np.sin(2*np.pi*5*t)),t[-1]))
        self.assertFalse(coherent(a,fit_periodic(t,100*t),t[-1]))

    def test_effects_preserve_attacks_releases_and_drum_time(self):
        notes=[[0,.5,72,.8],[.6,1,76,.7]]
        percussion=dict(samples=[dict(name='snare',pcm=[0,0,80,176]*100,volume=39)],
                        hits=[dict(time=.054,sample=0,strength=.8)],timing='ticks')
        base,_=working_module(notes,92,1.2,roles=['lead']*2,percussion=percussion)
        result,report=working_module(notes,92,1.2,roles=['lead']*2,percussion=percussion,
                                     vibrato=[dict(speed=8,depth=2),None],tick_multiplier=2)
        self.assertEqual(base[:1084],result[:1084])
        self.assertEqual(base[1084+2048:],result[1084+2048:])
        self.assertEqual(report['note_starts'],2)
        self.assertEqual(report['replay_speed'],6)
        self.assertEqual(result[1084+28+3],212)  # ED4 has same time as ED2 at twice the tempo.
        self.assertEqual(base[1084+28+3],210)
        for row in range(report['rows']):
            for ch in range(7):
                offset=1084+row*32+ch*4
                old,new=base[offset:offset+4],result[offset:offset+4]
                if row==0 and ch<2:continue  # Replay-clock commands only.
                if ((old[0]&15)<<8|old[1]):self.assertEqual(old,new)
                if old[2]&15==12 and old[3]==0:self.assertEqual(old,new)
                if old!=new:self.assertEqual(new,bytes([0,0,4,130]))

    def test_invalid_effect_or_clock_rejected(self):
        for effects in ([dict(speed=0,depth=2)],[],[dict(speed=8,depth=16)]):
            with self.assertRaises(ValueError):working_module([[0,.5,72,.8]],92,1,vibrato=effects)
        with self.assertRaises(ValueError):working_module([],150,1,tick_multiplier=2)


if __name__=='__main__':unittest.main()
