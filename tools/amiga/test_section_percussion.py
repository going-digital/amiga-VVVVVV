#!/usr/bin/env python3
import copy
import unittest
from section_percussion import refine_sections


def hit(bar,position,sample=0):
    return dict(bar=bar,position=position,time=bar*2+position/8,sample=sample,strength=.8)


def fixture():
    return dict(samples=[dict(name='snare',data=[0,1],volume=39)],
                bar_template=dict(seconds=2,phase=0,bins=16),
                hits=[hit(bar,4) for bar in range(8)],
                unregularized_hits=[hit(bar,9) for bar in range(2,6)])


class SectionTests(unittest.TestCase):
    def test_preservation_and_idempotence(self):
        source=fixture();before=copy.deepcopy(source)
        result=refine_sections(source,16)
        self.assertEqual(source,before)
        self.assertEqual(result['samples'],source['samples'])
        self.assertEqual(result['bar_template'],source['bar_template'])
        self.assertTrue(all(h in result['hits'] for h in source['hits']))
        self.assertEqual(len(result['section_refinement']['added_hits']),4)
        self.assertEqual(refine_sections(result,16),result)

    def test_missing_bar_is_not_filled(self):
        source=fixture();source['unregularized_hits']=[hit(b,9) for b in (1,2,4,5)]
        extras=refine_sections(source,16)['section_refinement']['added_hits']
        self.assertEqual([h['bar'] for h in extras],[1,2,4,5])

    def test_roll_sparse_support_late_fills_and_collisions(self):
        source=fixture()
        source['unregularized_hits']=[hit(1,9) for _ in range(8)]+[hit(b,15) for b in range(8)]+[hit(b,6) for b in (0,2,4,6)]
        self.assertEqual(refine_sections(source,16)['section_refinement']['added_hits'],[])
        source=fixture();source['hits'].append(hit(2,9,1))
        extras=refine_sections(source,16)['section_refinement']['added_hits']
        self.assertEqual([h['bar'] for h in extras],[3,4,5])


if __name__=='__main__':
    unittest.main()
