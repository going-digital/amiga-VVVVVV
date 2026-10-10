#!/usr/bin/env python3
import copy
import unittest
from audition_lead_roles import lead_role_audition


class RoleAuditionTests(unittest.TestCase):
    def setUp(self):
        self.notes=[[5.146,5.784,64,.55],[5.15,5.4,59,.6]]
        self.arrangement=dict(roles=['harmony','harmony'],role_levels=dict(bass=1,lead=1.2,harmony=.5),vibrato=[None,None],percussion=dict(hits=[dict(time=5.2)]))

    def test_only_requested_role_changes_and_volume_is_explicit(self):
        before=copy.deepcopy((self.notes,self.arrangement))
        result,changes=lead_role_audition(self.notes,self.arrangement,[(5.146,64)])
        self.assertEqual(result['roles'],['lead','harmony'])
        expected=copy.deepcopy(self.arrangement);expected['roles'][0]='lead'
        self.assertEqual(result,expected)
        self.assertEqual(changes[0]['old_volume'],13);self.assertEqual(changes[0]['volume'],32)
        self.assertEqual((self.notes,self.arrangement),before)

    def test_export_preserves_attack_pitches_and_exposes_bank_change(self):
        from transcribe_tracker import working_module
        result,_=lead_role_audition(self.notes,self.arrangement,[(5.146,64)])
        baseline,_=working_module(self.notes,92,6,roles=self.arrangement['roles'])
        audition,_=working_module(self.notes,92,6,roles=result['roles'])
        def attacks(data):
            found=[]
            for offset in range(1084,1084+4096,4):
                a,b,c,volume=data[offset:offset+4]
                sample=(a&240)|(c>>4)
                if sample:
                    found.append(((offset-1084)//32,((a&15)<<8)|b,(sample-1)%5,(sample-1)//5,volume))
            return sorted(found)
        old=attacks(baseline);new=attacks(audition)
        self.assertEqual([x[:3] for x in old],[x[:3] for x in new])
        self.assertEqual([x[3] for x in old],[2,2])
        self.assertEqual(sorted(x[3] for x in new),[1,2])
        self.assertEqual(baseline[1084+4096:],audition[1084+4096:])

    def test_ambiguous_missing_duplicate_or_calibrated_note_is_rejected(self):
        for request in [[(4,64)],[(5.146,64),(5.146,64)],[(float('nan'),64)],[(5.146,76)]]:
            with self.assertRaises(ValueError):lead_role_audition(self.notes,self.arrangement,request)
        with self.assertRaises(ValueError):lead_role_audition(self.notes+[self.notes[0]],dict(self.arrangement,roles=['harmony']*3),[(5.146,64)])
        with self.assertRaises(ValueError):lead_role_audition(self.notes,dict(self.arrangement,vibrato=[dict(speed=8,depth=2),None]),[(5.146,64)])
        with self.assertRaises(ValueError):lead_role_audition(self.notes,dict(self.arrangement,roles=['lead','harmony']),[(5.146,64)])


if __name__=='__main__':unittest.main()
