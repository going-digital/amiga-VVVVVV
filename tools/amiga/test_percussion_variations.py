#!/usr/bin/env python3
"""Keep anchors intact; require independent-bar support and observed pickups."""
import copy
import unittest
from regularize_percussion import regularize
from vary_percussion import add_variations


def fixture():
    samples=[dict(name='kick reconstruction',pcm=[0,0,80,0]),
             dict(name='snare reconstruction',pcm=[0,0,80,0])]
    hits=[]
    for bar in range(8):
        for sample,offset in ((0,0),(0,1),(1,.5),(1,1.5)):
            hits.append(dict(time=bar*2+offset,sample=sample,strength=.8))
    return dict(samples=samples,hits=hits)


class VariationsTests(unittest.TestCase):
    def test_supported_extras_without_moving_anchors(self):
        p=fixture()
        p['hits'] += [dict(time=bar*2+.75,sample=0,strength=.8) for bar in (1,2,5)]
        p['hits'] += [dict(time=bar*2+1.875,sample=1,strength=.8) for bar in (2,3,7)]
        base=regularize(p,2,16)
        before=copy.deepcopy(base)
        varied=add_variations(base,16)
        self.assertEqual(base,before)
        self.assertEqual(varied['bar_template'],base['bar_template'])
        self.assertEqual(varied['samples'],base['samples'])
        for anchor in base['hits']:
            self.assertIn(anchor,varied['hits'])
        added=varied['variations']['added_hits']
        self.assertEqual([(h['bar'],h['position']) for h in added],[(1,6),(2,6),(3,15),(5,6),(7,15)])
        # Reapplying must retain the same baseline and variation provenance.
        self.assertEqual(add_variations(varied,16),varied)

    def test_one_bar_roll_and_misalignment_do_not_create_fill(self):
        p=fixture()
        p['hits'] += [dict(time=1.875+i*.0001,sample=1,strength=1) for i in range(20)]
        # Three appearances off the approved grid are not consensus evidence.
        p['hits'] += [dict(time=bar*2+.80,sample=0,strength=1) for bar in (1,2,5)]
        varied=add_variations(regularize(p,2,16),16)
        self.assertEqual(varied['variations']['added_hits'],[])
        self.assertEqual(varied['variations']['rejected_alignment'],3)

    def test_phrase_pickup_priority_and_one_extra_per_bar(self):
        p=fixture()
        for bar in (1,3,5,7):
            p['hits'] += [dict(time=bar*2+.75,sample=0,strength=.8),
                          dict(time=bar*2+1.875,sample=1,strength=.8)]
        varied=add_variations(regularize(p,2,16),16)
        extras=varied['variations']['added_hits']
        self.assertEqual([(h['bar'],h['sample']) for h in extras],[(1,0),(3,1),(5,0),(7,1)])


if __name__=='__main__':
    unittest.main()
