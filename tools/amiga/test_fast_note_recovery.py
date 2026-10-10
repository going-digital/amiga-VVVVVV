#!/usr/bin/env python3
import copy
import unittest
from recover_fast_notes import choose_fast


def evidence(start=.1,pitch=64,**changes):
    e=dict(note=[start,start+.07,pitch,.35],onset_probability=.7,contour_mean=.25,pitch_ratio=2)
    e.update(changes)
    return e


def run():return [[0,.08,60,.7],[.2,.28,67,.7]]


class FastTests(unittest.TestCase):
    def test_requires_accepted_run_and_preserves_inputs(self):
        notes=run();events=[evidence(),evidence()];before=copy.deepcopy((notes,events))
        added,review=choose_fast(notes,events)
        self.assertEqual(added,[events[0]['note']])
        self.assertEqual((notes,events),before)
        self.assertEqual(choose_fast([],events)[0],[])
        self.assertEqual(choose_fast([[.1,.2,60,.8],[.1,.2,67,.8]],events)[0],[])

    def test_rejects_noise_vibrato_and_overload(self):
        for change in (dict(onset_probability=.2),dict(contour_mean=.1),dict(pitch_ratio=1)):
            self.assertEqual(choose_fast(run(),[evidence(**change)])[0],[])
        notes=run()+[[.1,.2,65,.7]]
        self.assertEqual(choose_fast(notes,[evidence()])[0],[])
        notes=run()+[[.08,.18,p,.7] for p in range(40,47)]
        self.assertEqual(choose_fast(notes,[evidence()])[0],[])

    def test_phrase_support_needs_distinct_accepted_repetitions(self):
        period=3.428
        notes=[[.1,.2,64,.7],[.1+period,.2+period,64,.7]]
        e=evidence(.1+2*period)
        additions,review=choose_fast(notes,[e],context='recurring-phrase',bar_seconds=period/2)
        self.assertEqual(additions,[e['note']])
        self.assertEqual(len(review[0]['recurrence_matches']),2)
        self.assertEqual(choose_fast([notes[0]]*4,[e],context='recurring-phrase',bar_seconds=period/2)[0],[])
        shifted=evidence(e['note'][0]+.08)
        self.assertEqual(choose_fast(notes,[shifted],context='recurring-phrase',bar_seconds=period/2)[0],[])

    def test_candidates_cannot_create_their_own_support(self):
        self.assertEqual(choose_fast([], [evidence(0,60),evidence(.1,64),evidence(.2,67)])[0],[])


if __name__=='__main__':unittest.main()
