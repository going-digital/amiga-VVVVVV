#!/usr/bin/env python3
import collections
import copy
import unittest
from retrigger_notes import split_attacks
from recover_short_notes import note_rows
from transcribe_tracker import working_module


def evidence(time=.2,**changes):
    e=dict(note_index=0,time=time,onset_probability=.85,note_probability=.6,
           fundamental_rise=4,harmonic_rise=3,pitch_ratio=1.7)
    e.update(changes)
    return e


class RetriggerTests(unittest.TestCase):
    def test_preserves_pitch_gain_release_and_quantized_coverage(self):
        notes=[[0,.6,64,.7],[0,.6,48,.8]];before=copy.deepcopy(notes)
        result,parents,review=split_attacks(notes,[evidence(.2),evidence(.4)])
        self.assertEqual(notes,before)
        self.assertEqual(parents,[0,0])
        self.assertEqual(result,[[0,.2,64,.7],notes[1],[.2,.4,64,.7],[.4,.6,64,.7]])
        def coverage(events):
            return collections.Counter((row,n[2]) for n in events for row in note_rows(n,7.5/92))
        self.assertEqual(coverage(notes),coverage(result))
        _,report=working_module(result,92,.8,roles=['harmony','bass','harmony','harmony'])
        self.assertEqual(report['note_starts'],4)
        self.assertEqual(report['unstarted_note_indices'],[])
        self.assertEqual(split_attacks(result,[evidence(.2),evidence(.4)])[0],result)

    def test_does_not_turn_noise_or_single_harmonic_rise_into_attack(self):
        notes=[[0,.6,64,.7]]
        for change in (dict(onset_probability=.4),dict(note_probability=.1),
                       dict(fundamental_rise=1),dict(harmonic_rise=1),dict(pitch_ratio=1)):
            self.assertEqual(split_attacks(notes,[evidence(**change)])[0],notes)
        self.assertEqual(split_attacks(notes,[evidence()],vibrato=[dict(speed=8,depth=2)])[0],notes)

    def test_duplicate_rows_and_edge_attacks_do_not_create_short_fragments(self):
        notes=[[0,.6,64,.7]]
        result,parents,review=split_attacks(notes,[evidence(.2),evidence(.21),evidence(.04),evidence(.58)])
        self.assertEqual(len(parents),1)
        self.assertEqual(result,[[0,.2,64,.7],[.2,.6,64,.7]])


if __name__=='__main__':unittest.main()
