#!/usr/bin/env python3
import cmath
import copy
import math
import unittest
from simplify_tracker_notes import merge_fragments
from transcribe_tracker import working_module
from prepare_tracker_edit import describe_module


def evidence(first,following,**changes):
    return dict(first=first,following=following,onset_probability=.5,harmonic_rises=[1,1,1],**changes)


class SimplificationTests(unittest.TestCase):
    def test_weak_chain_merges_without_removing_pitch_coverage(self):
        notes=[[0,.1,64,.7],[.1,.2,64,.5],[.2,.3,64,.6]];before=copy.deepcopy(notes)
        result,retained,review=merge_fragments(notes,['harmony']*3,[None]*3,[evidence(0,1),evidence(1,2)])
        self.assertEqual(result,[[0,.3,64,.7]]);self.assertEqual(retained,[0])
        self.assertEqual(notes,before)

    def test_preserves_attacks_vibrato_roles_and_unfilled_grid_gaps(self):
        notes=[[0,.1,64,.7],[.1,.2,64,.5]]
        for key,value in [('onset_probability',.8),('harmonic_rises',[1,2,1])]:
            e=evidence(0,1);e[key]=value
            self.assertEqual(merge_fragments(notes,['harmony']*2,[None]*2,[e])[0],notes)
        self.assertEqual(merge_fragments(notes,['harmony','lead'],[None]*2,[evidence(0,1)])[0],notes)
        self.assertEqual(merge_fragments(notes,['harmony']*2,[dict(speed=4,depth=2),None],[evidence(0,1)])[0],notes)
        # Source gap <25ms, but filling it would occupy an extra rounded row.
        gapped=[[0,.113,64,.7],[.126,.3,64,.5]]
        self.assertEqual(merge_fragments(gapped,['harmony']*2,[None]*2,[evidence(0,1)])[0],gapped)

    def test_waveform_spectra_and_fixed_volume_attacks(self):
        data,report=working_module([[.2,.35,64,.2],[.5,.7,64,.9]],92,.9,
            roles=['lead','lead'],waveform_profile='pulse-triangle',fixed_volume=32)
        info=describe_module(data);offset=info['sample_offset'];spectra={}
        for i,sample in enumerate(info['samples']):
            values=[x if x<128 else x-256 for x in data[offset:offset+sample['bytes']]];offset+=sample['bytes']
            if i in (4,9,14):
                harmonics=[abs(sum(v*cmath.exp(-2j*math.pi*k*j/len(values)) for j,v in enumerate(values))) for k in range(1,5)]
                spectra[sample['role']]=[x/harmonics[0] for x in harmonics]
        self.assertLess(spectra['bass'][1],.01);self.assertAlmostEqual(spectra['bass'][2],1/9,delta=.01)
        self.assertAlmostEqual(spectra['lead'][1],1/math.sqrt(2),delta=.01)
        self.assertLess(spectra['lead'][3],.01)
        self.assertLess(spectra['harmony'][1],.01);self.assertAlmostEqual(spectra['harmony'][2],1/3,delta=.01)
        attacks=[]
        for at in range(1084,info['sample_offset'],4):
            a,b,c,value=data[at:at+4]
            if (a&240)|(c>>4):attacks.append(c&15)
        self.assertEqual(attacks,[0,0]);self.assertEqual(data[20+5*30+25],38)
        for kwargs in (dict(fixed_volume=49),dict(waveform_profile='unknown')):
            with self.assertRaises(ValueError):working_module([],92,.5,**kwargs)


if __name__=='__main__':unittest.main()
