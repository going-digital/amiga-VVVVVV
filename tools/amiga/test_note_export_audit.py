#!/usr/bin/env python3
import unittest
from transcribe_tracker import working_module


class AuditTests(unittest.TestCase):
    def test_distinguishes_late_attack_from_completely_lost_note(self):
        notes=[[0,.1,p,.7] for p in range(60,68)]
        notes[6][1]=.3
        _,report=working_module(notes,92,.5,roles=['harmony']*8)
        self.assertEqual(report['unstarted_note_indices'],[])
        self.assertEqual(report['delayed_attacks'],[dict(note_index=6,planned_row=0,actual_row=1)])
        self.assertEqual(report['note_starts'],8)
        self.assertAlmostEqual(report['allocated_onset_max_error_ms'],1000*7.5/92)
        _,report=working_module([[0,.04,p,.7] for p in range(60,68)],92,.5,roles=['harmony']*8)
        self.assertEqual(report['unstarted_note_indices'],[6])
        self.assertEqual(report['delayed_attacks'],[])
        self.assertEqual(report['note_starts'],7)


if __name__=='__main__':unittest.main()
