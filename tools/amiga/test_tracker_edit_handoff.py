#!/usr/bin/env python3
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from prepare_tracker_edit import describe_module, event_map, friendly_names, reduction_readiness
from transcribe_tracker import working_module


class EditHandoffTests(unittest.TestCase):
    def test_names_change_only_display_bytes_and_explain_tuning(self):
        notes=[[0,.3,64,.7]]
        data,_=working_module(notes,92,.5,roles=['lead'])
        renamed=friendly_names(data);masked=bytearray(renamed)
        masked[:20]=data[:20]
        for i in range(31):
            at=20+i*30;masked[at:at+22]=data[at:at+22]
        self.assertEqual(bytes(masked),data)
        samples=describe_module(renamed)['samples']
        self.assertEqual(samples[6]['name'],'Lead C4 P428')
        self.assertEqual(samples[6]['reference_midi'],60)
        with self.assertRaises(ValueError):describe_module(data[:-1])
        corrupted=bytearray(data);corrupted[20+22:20+24]=b'\0\1'
        with self.assertRaises(ValueError):describe_module(corrupted)

    def test_map_uses_actual_delayed_attack_and_accounts_for_lost_event(self):
        notes=[[0,.1,p,.7] for p in range(60,68)];notes[6][1]=.3
        before=copy.deepcopy(notes);roles=['harmony']*len(notes)
        data,report=working_module(notes,92,.5,roles=roles)
        mapping=event_map(data,notes,dict(roles=roles),report)
        self.assertEqual(len(mapping),8)
        self.assertEqual(mapping[6]['planned_global_row'],0)
        self.assertEqual(mapping[6]['actual_global_row'],1)
        self.assertEqual(mapping[6]['row_hex'],'01')
        self.assertEqual(mapping[6]['status'],'delayed')
        self.assertEqual(notes,before)
        short=[[0,.04,p,.7] for p in range(60,68)]
        data,report=working_module(short,92,.5,roles=roles)
        mapping=event_map(data,short,dict(roles=roles),report)
        self.assertEqual([e['note_index'] for e in mapping if e['status']=='unstarted'],[6])
        with self.assertRaises(ValueError):event_map(data,short,dict(roles=['lead']*8),report)

    def test_capacity_audit_counts_held_voices_and_releases(self):
        notes=[[0,.2,40,.7],[0,.1,68,.7],[0,.1,72,.7],[0,.2,60,.7]]
        data,report=working_module(notes,92,.4,roles=['bass','lead','lead','harmony'])
        result=reduction_readiness(data,report['rows'])
        self.assertEqual(result['peak_pitched_voices'],4)
        self.assertEqual(result['peak_foreground_voices'],3)
        self.assertEqual(result['rows_over_four_voice_budget'],1)
        self.assertEqual(result['rows_requiring_more_than_harmony_baking'],1)
        self.assertEqual(result['rows_over_three_voice_budget'],1)
        with self.assertRaises(ValueError):reduction_readiness(data,65)

    def test_existing_edit_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp);edited=out/'positive-force-edit.mod';edited.write_bytes(b'manual corrections')
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('prepare_tracker_edit.py')),
                '--baseline','missing','--reference','missing','--library','missing','--out',str(out)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('protect manual edits',result.stderr)
            self.assertEqual(edited.read_bytes(),b'manual corrections')
            self.assertEqual(list(out.iterdir()),[edited])


if __name__=='__main__':unittest.main()
