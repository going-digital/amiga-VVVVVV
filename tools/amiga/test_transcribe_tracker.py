#!/usr/bin/env python3
"""Structural and independent pitch checks for the experimental MOD sketch."""
import math
import struct
import unittest
from transcribe_tracker import module, working_module
from audit_music import audit
from arrange_tracker import role_map


class TrackerTests(unittest.TestCase):
    def test_reserved_channels_and_pitch(self):
        data, report = module([[0, .5, 48, .8], [0, .5, 72, .9]], 150, 1, True)
        self.assertEqual(report['active_mask'], 12)
        self.assertEqual(report['conflicting_channels'], [])
        self.assertEqual(report['sample_bytes'], 96)
        for row in range(report['stored_patterns']*64):
            self.assertEqual(data[1084+row*16:1084+row*16+8], bytes(8))
        for ch, cycle, midi in [(2,64,48), (3,32,72)]:
            a,b,_,_ = data[1084+ch*4:1088+ch*4]
            period = (a & 15)*256+b
            frequency = 3546895/(period*cycle)
            cents = 1200*math.log2(frequency/(440*2**((midi-69)/12)))
            self.assertLess(abs(cents), 10)
        # Sustained voices must be explicitly silenced after note release.
        row = math.ceil(.5/(7.5/150))
        for ch in (2,3):
            self.assertEqual(data[1084+row*16+ch*4:1088+row*16+ch*4], bytes([0,0,12,0]))

    def test_four_voices_and_loop(self):
        notes = [[0,1,p,.8] for p in (40,55,60,67,72)]
        data, report = module(notes, 125, 1)
        self.assertEqual(report['active_mask'], 15)
        self.assertGreater(report['omitted_note_rows'], 0)
        row = report['rows']-1
        self.assertEqual(data[1084+row*16+14] & 15, 11)
        self.assertEqual(audit(data)['trailing_bytes'], 0)

    def test_eight_channel_master_retains_pitches_and_held_lanes(self):
        # New lower note must not reshuffle/retrigger seven sustained notes.
        notes = [[0, .8, pitch, .8] for pitch in (24,36,48,55,60,67,84)]
        notes.append([.2, .6, 30, .8])
        data, report = working_module(notes, 150, 1)
        self.assertEqual(data[1080:1084], b'8CHN')
        self.assertEqual(report['note_starts'], 8)
        self.assertEqual(report['omitted_note_rows'], 0)
        self.assertEqual(len(data), 1084+2048+report['sample_bytes'])
        cycles = (16,32,64,128,256)
        for ch, note in enumerate((notes[0], notes[6], *notes[1:6])):
            a,b,c,_ = data[1084+ch*4:1088+ch*4]
            instrument = (a & 240) | (c >> 4)
            frequency = 3546895/(((a & 15)*256+b)*cycles[instrument-1])
            expected = 440*2**((note[2]-69)/12)
            self.assertLess(abs(1200*math.log2(frequency/expected)), 10)
        for ch in range(7):
            self.assertEqual(data[1084+4*32+ch*4:1088+4*32+ch*4], bytes(4))

    def test_nearest_grid_preserves_short_notes(self):
        data, report = working_module([[.061,.062,60,.8]], 150, .3)
        # A one-millisecond recognition must survive as one tracker row;
        # nearest rounding starts at 50 ms rather than delaying to 100 ms.
        self.assertNotEqual(data[1084+32:1088+32], bytes(4))
        self.assertEqual(data[1084+64:1088+64], bytes([0,0,12,0]))
        self.assertEqual(report['note_starts'], 1)
        self.assertAlmostEqual(report['onset_max_error_ms'], 11)

    def test_role_banks_and_reserved_percussion_lane(self):
        notes = [[0,.5,p,.8] for p in (40,60,73)]
        roles = role_map(notes)
        self.assertEqual(roles,['bass','harmony','lead'])
        drums = dict(samples=[dict(name='hit',pcm=[0,0,80,0,176,0])],
                     hits=[dict(time=.1,sample=0,strength=.8)])
        data, report = working_module(notes,150,1,roles=roles,percussion=drums)
        def instrument(row,ch):
            a,_,c,_ = data[1084+row*32+ch*4:1088+row*32+ch*4]
            return (a & 240) | (c >> 4)
        self.assertIn(instrument(0,0),range(1,6))
        self.assertIn(instrument(0,2),range(6,11))
        self.assertIn(instrument(0,4),range(11,16))
        self.assertEqual(instrument(2,7),16)
        self.assertEqual(report['note_starts'],3)
        self.assertEqual(report['percussion_hits'],1)
        self.assertEqual(report['omitted_note_rows'],0)
        # Drum instrument has a non-looping two-byte restart region.
        self.assertEqual(struct.unpack_from('>HH',data,20+15*30+26),(0,1))
        with self.assertRaises(ValueError):
            working_module(notes,150,1,roles=['bass'])

    def test_bounds(self):
        for bpm, duration in [(0,1), (256,1), (125,0), (125,121)]:
            with self.assertRaises(ValueError):
                module([], bpm, duration)


if __name__ == '__main__':
    unittest.main()
