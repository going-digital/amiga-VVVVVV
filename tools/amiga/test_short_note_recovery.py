#!/usr/bin/env python3
"""Regression checks for conservative recovery of omitted short attacks."""
import copy
import unittest
from recover_short_notes import choose_additions


def candidate(start=0,pitch=60,**changes):
    entry=dict(note=[start,start+.09,pitch,.6],onset_probability=.8,pitch_ratio=2)
    entry.update(changes)
    return entry


class RecoveryTests(unittest.TestCase):
    def test_existing_notes_and_input_are_preserved(self):
        base=[[0,.2,60,.7]]
        evidence=[candidate(),candidate(.3),candidate(.3)]
        before=copy.deepcopy((base,evidence))
        additions,review=choose_additions(base,evidence)
        self.assertEqual(additions,[evidence[1]['note']])
        self.assertEqual((base,evidence),before)
        self.assertEqual(sum(e['decision']=='already covered by accepted pitch' for e in review),2)

    def test_vibrato_and_weak_attacks_remain_for_review(self):
        additions,review=choose_additions([[0,.3,60,.7]],
            [candidate(pitch=61),candidate(pitch=67,onset_probability=.3),
             candidate(pitch=72,pitch_ratio=1),candidate(pitch=75,note=[0,.3,75,.8])])
        self.assertEqual(additions,[])
        self.assertIn('adjacent pitch ambiguity; possible vibrato',[e['decision'] for e in review])

    def test_source_disjoint_same_pitch_cannot_overlap_after_rounding(self):
        # Trim the candidate to end exactly when the accepted note starts.
        entry=candidate(.06);entry['note'][1]=.115
        additions,review=choose_additions([[.115,.2,60,.7]],[entry])
        self.assertEqual(additions,[])
        self.assertEqual(review[0]['decision'],'same-pitch collision after tracker quantization')

    def test_quantized_voice_budget_protects_accepted_notes(self):
        # All seven held pitches occupy the rounded row, despite no time overlap
        # with this attack. The eighth channel remains reserved for percussion.
        base=[[0,.03,p,.7] for p in range(40,47)]
        additions,review=choose_additions(base,[candidate(.035,72),candidate(.3,72)])
        self.assertEqual(additions,[candidate(.3,72)['note']])
        self.assertEqual(review[0]['decision'],'would crowd accepted seven pitched voices')


if __name__=='__main__':
    unittest.main()
