#!/usr/bin/env python3
"""Repeating-bar consensus, missing-hit repair and tick delay encoding."""
import unittest
from regularize_percussion import regularize
from transcribe_tracker import working_module


class RhythmTests(unittest.TestCase):
    def test_repeat_and_fill_missing_bar(self):
        samples=[dict(name='kick reconstruction',pcm=[0,0,80,0]),
                 dict(name='snare reconstruction',pcm=[0,0,80,0])]
        hits=[]
        for bar in (0,1,3):
            for sample,offset in ((0,0),(0,1),(1,.5),(1,1.5)):
                hits.append(dict(time=bar*2+offset,sample=sample,strength=.8))
        # A roll in one bar must not outvote positions supported across bars.
        hits.extend(dict(time=.25+i*.001,sample=0,strength=1) for i in range(20))
        source=dict(samples=samples,hits=hits)
        output=regularize(source,2,8)
        self.assertEqual(len(output['hits']),16)
        for bar in range(4):
            events=[(h['sample'],h['position']) for h in output['hits'] if h['bar']==bar]
            self.assertEqual(events,[(0,0),(1,4),(0,8),(1,12)])
        self.assertEqual(source['hits'],hits)
        self.assertEqual(output['samples'][0]['pcm'],samples[0]['pcm'])

    def test_phase_and_no_events(self):
        p=dict(samples=[dict(name='kick reconstruction',pcm=[0,0])],hits=[])
        self.assertEqual(regularize(p,2,4)['hits'],[])
        p['hits']=[dict(time=.1,sample=0,strength=.8)]
        events=regularize(p,2,4,phase=.1)['hits']
        self.assertEqual([round(h['time'],2) for h in events],[.1,1.1,2.1,3.1])

    def test_subrow_delay_and_boundary(self):
        p=dict(samples=[dict(name='kick',pcm=[0,0,80,0],volume=30)],
               hits=[dict(time=.04,sample=0,strength=.8),dict(time=.19,sample=0,strength=.8)],timing='ticks')
        data,r=working_module([],150,.2,roles=[],percussion=p)
        # Speed 3 at 150 BPM: row 50ms, tick 16.667ms. Nearest is ED2.
        self.assertEqual(data[1084+28:1084+32],bytes([17,66,14,210]))
        self.assertEqual(r['percussion_hits'],1)
        self.assertEqual(r['percussion_boundary_skips'],1)
        self.assertEqual(r['percussion_row_collisions'],0)


if __name__=='__main__':
    unittest.main()
