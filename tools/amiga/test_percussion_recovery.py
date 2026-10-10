#!/usr/bin/env python3
import copy
import unittest
from recover_percussion import add_recovered


def fixture():
    return dict(samples=[dict(name='kick reconstruction',pcm=[0,1],volume=38)],
                bar_template=dict(seconds=2,phase=0,bins=16),
                hits=[dict(time=b*2+.75,bar=b,position=6,sample=0,strength=.8) for b in range(4)])


def observation(time,kind='kick',raw_kind=None):
    return dict(time=time,kind=kind,raw_kind=raw_kind,strength=.8)


class RecoveryTests(unittest.TestCase):
    def test_preserves_baseline_and_replays_idempotently(self):
        source=fixture();before=copy.deepcopy(source);events=[observation(8.75)]
        result=add_recovered(source,events)
        self.assertEqual(source,before)
        self.assertEqual(result['samples'],source['samples'])
        self.assertEqual(result['bar_template'],source['bar_template'])
        self.assertTrue(all(h in result['hits'] for h in source['hits']))
        self.assertEqual(len(result['attack_recovery']['added_hits']),1)
        self.assertEqual(add_recovered(result,events),result)

    def test_no_new_positions_instruments_conflicts_or_collisions(self):
        result=add_recovered(fixture(),[observation(.75),observation(8.5),
            observation(8.75,'hat'),observation(10.75,raw_kind='snare'),observation(12.80)])
        self.assertEqual(result['attack_recovery']['added_hits'],[])

    def test_requires_distinct_accepted_bars(self):
        source=fixture();source['hits']=[source['hits'][0]]*8
        self.assertEqual(add_recovered(source,[observation(8.75)])['attack_recovery']['added_hits'],[])


if __name__=='__main__':
    unittest.main()
