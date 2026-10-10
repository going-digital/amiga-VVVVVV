#!/usr/bin/env python3
import copy
import unittest
from recover_note_gaps import extend_gaps


def evidence(first=0,following=1,**changes):
    entry=dict(first=first,following=following,note_mean=.3,note_min=.2,
               contour_mean=.25,contour_min=.2,pitch_ratio=2,internal_onset=.1)
    entry.update(changes)
    return entry


class GapTests(unittest.TestCase):
    def test_preserves_every_attack_and_input(self):
        notes=[[0,.2,60,.7],[.35,.6,60,.8]];before=copy.deepcopy(notes)
        updated,review=extend_gaps(notes,[evidence()])
        self.assertEqual(notes,before)
        self.assertEqual(updated,[[0,.35,60,.7],notes[1]])
        self.assertEqual(review[0]['old_end'],.2)
        self.assertEqual(extend_gaps(updated,[evidence()])[0],updated)

    def test_rejects_silence_different_pitch_and_internal_attack(self):
        notes=[[0,.2,60,.7],[.35,.6,60,.8]]
        for change in (dict(note_min=.05),dict(contour_min=.05),dict(pitch_ratio=1),dict(internal_onset=.6)):
            self.assertEqual(extend_gaps(notes,[evidence(**change)])[0],notes)
        notes[1][2]=61
        self.assertEqual(extend_gaps(notes,[evidence()])[0],notes)

    def test_voice_budget_and_no_effect_after_quantization(self):
        notes=[[0,.2,60,.7],[.35,.6,60,.8]]+[[.2,.35,p,.7] for p in range(40,47)]
        self.assertEqual(extend_gaps(notes,[evidence()])[0],notes)
        notes=[[0,.22,60,.7],[.245,.4,60,.8]]
        updated,review=extend_gaps(notes,[evidence()])
        self.assertEqual(updated,notes)
        self.assertEqual(review[0]['decision'],'no tracker-row gap to repair')


if __name__=='__main__':unittest.main()
