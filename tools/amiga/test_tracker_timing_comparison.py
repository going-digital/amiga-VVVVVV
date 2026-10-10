#!/usr/bin/env python3
import copy
import unittest
from compare_tracker_timing import finer_arrangement
from transcribe_tracker import working_module


class TimingTests(unittest.TestCase):
    def test_comparison_preserves_input_samples_and_accepted_tick_time(self):
        source=dict(tick_multiplier=2,percussion=dict(timing='ticks',
            samples=[dict(name='snare',pcm=[0,0,80,176]*100,volume=39)],
            hits=[dict(time=.054,sample=0,strength=.8)]))
        before=copy.deepcopy(source);fine=finer_arrangement(source)
        self.assertEqual(source,before)
        self.assertEqual(fine['percussion']['samples'],source['percussion']['samples'])
        baseline,_=working_module([],92,.4,roles=[],percussion=source['percussion'],tick_multiplier=2)
        comparison,_=working_module([],184,.4,roles=[],percussion=fine['percussion'])
        self.assertEqual(baseline[1084+31],212) # ED4, row 0 on 184-BPM ticks.
        self.assertEqual(comparison[1084+32+31],209) # ED1, row 1 on the same ticks.

    def test_late_event_is_included_in_actual_onset_error(self):
        notes=[[0,.1,p,.7] for p in range(60,68)];notes[6][1]=.3
        _,report=working_module(notes,92,.5,roles=['harmony']*8)
        self.assertEqual(report['onset_max_error_ms'],0)
        self.assertGreater(report['allocated_onset_max_error_ms'],80)

    def test_invalid_clock_assumptions_rejected(self):
        with self.assertRaises(ValueError):finer_arrangement(dict(tick_multiplier=1))
        with self.assertRaises(ValueError):finer_arrangement(dict(tick_multiplier=2),150)


if __name__=='__main__':unittest.main()
