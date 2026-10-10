#!/usr/bin/env python3
import copy
import unittest
from recover_local_lead import refine_lead


def event(start=.1,pitch=74):
    return dict(note=[start,start+.05,pitch,.4],onset_probability=.7,contour_mean=.25,
                bands=[dict(rise=3,isolation=3,stable=True,median_cents=10) for _ in range(3)])


class LeadTests(unittest.TestCase):
    def test_distinct_stable_attack_and_input_preservation(self):
        n=[[0,.09,73,.7],[.15,.3,75,.7]];e=[event()];before=copy.deepcopy((n,e))
        result,changes,review=refine_lead(n,e)
        self.assertEqual(result,n+[e[0]['note']]);self.assertEqual(changes,[])
        self.assertEqual((n,e),before)

    def test_contiguous_fragment_advances_existing_attack_without_new_voice(self):
        e=event(.206,76);n=[[.256,.44,76,.7],[.206,.3,64,.7]]
        result,changes,review=refine_lead(n,[e])
        self.assertEqual(len(result),len(n));self.assertEqual(result[0],[.206,.44,76,.7])
        self.assertEqual(changes[0]['old_start'],.256)
        self.assertEqual(review[0]['decision'],'advance accepted same-pitch attack')

    def test_new_overtone_noise_and_glide_are_excluded(self):
        e=event()
        for difference in (12,19,24):
            n=[[.1,.3,74-difference,.7]]
            self.assertEqual(refine_lead(n,[e])[0],n)
        for field,value in [('rise',1),('isolation',1),('stable',False),('median_cents',40)]:
            weak=copy.deepcopy(e)
            for band in weak['bands'][1:]:band[field]=value
            self.assertEqual(refine_lead([],[weak])[0],[])
        weak=copy.deepcopy(e);weak['note'][3]=.2
        self.assertEqual(refine_lead([],[weak])[0],[])

    def test_capacity_and_quantized_duplicates(self):
        e=event();n=[[0,.3,p,.7] for p in range(48,55)]
        self.assertEqual(refine_lead(n,[e])[0],n)
        n=[[.12,.3,74,.7]]
        # Contiguous qualifying fragment advances the existing note; a gap
        # beyond the merge tolerance must not become another quantized voice.
        e=event(.055);e['note'][1]=.09
        self.assertEqual(refine_lead(n,[e])[0],n)
        e=event();n=[[.11,.3,73,.7]]
        self.assertEqual(refine_lead(n,[e])[0],n)


if __name__=='__main__':unittest.main()
