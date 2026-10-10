#!/usr/bin/env python3
"""Fit coherent fundamental/second-harmonic vibrato for an editing audition."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def fit_periodic(times,cents):
    import numpy as np
    t=np.asarray(times)-times[0];cents=np.asarray(cents)
    trend=np.column_stack((np.ones(len(t)),t))
    baseline=trend@np.linalg.lstsq(trend,cents,rcond=None)[0]
    variance=float(np.sum((cents-baseline)**2))
    best=None
    for rate in np.arange(3,10.001,.05):
        design=np.column_stack((trend,np.sin(2*np.pi*rate*t),np.cos(2*np.pi*rate*t)))
        coefficients=np.linalg.lstsq(design,cents,rcond=None)[0]
        score=1-float(np.sum((cents-design@coefficients)**2))/max(1e-9,variance)
        if best is None or score>best['score']:
            best=dict(score=score,rate=float(rate),depth_cents=float(np.hypot(*coefficients[2:])),
                      phase=float(np.arctan2(coefficients[3],coefficients[2])),
                      drift_cents_per_second=float(coefficients[1]))
    return best


def pitch_trace(magnitude,sr,n_fft,indices,frequency):
    import numpy as np
    frequencies=np.arange(magnitude.shape[0])*sr/n_fft
    bins=np.where((frequencies>=frequency*2**(-.6/12))&(frequencies<=frequency*2**(.6/12)) &
                  (np.arange(len(frequencies))>0) & (np.arange(len(frequencies))<len(frequencies)-1))[0]
    if not len(bins):return None
    peaks=bins[np.argmax(magnitude[bins][:,indices],axis=0)]
    a,b,c=[np.log(magnitude[peaks+offset,indices]+1e-9) for offset in (-1,0,1)]
    denominator=a-2*b+c
    delta=np.divide(.5*(a-c),denominator,out=np.zeros_like(a),where=np.abs(denominator)>1e-12)
    hz=(peaks+np.clip(delta,-.5,.5))*sr/n_fft
    return 1200*np.log2(hz/frequency)


def coherent(first,second,span):
    phase=abs(math.atan2(math.sin(first['phase']-second['phase']),math.cos(first['phase']-second['phase'])))
    return (min(first['score'],second['score'])>=.75 and
            abs(first['rate']-second['rate'])<=.3 and phase<=.4 and
            5<=first['depth_cents']<=35 and
            .6<=second['depth_cents']/first['depth_cents']<=1.6 and
            max(abs(first['drift_cents_per_second']),abs(second['drift_cents_per_second']))<=30 and
            span*min(first['rate'],second['rate'])>=2.5)


def calibrate(library,out,pitch,role,target,bpm=92):
    import librosa
    import numpy as np
    import soundfile as sf
    from transcribe_tracker import working_module
    from render_tracker import render
    frequency=440*2**((pitch-69)/12)
    def measure(speed,depth):
        module,_=working_module([[0,1.5,pitch,.8]],bpm,1.8,roles=[role],
                               vibrato=[dict(speed=speed,depth=depth)],tick_multiplier=2)
        path=out/f'calibration-{pitch}-{speed}-{depth}'
        path.with_suffix('.mod').write_bytes(module)
        render(library,path.with_suffix('.mod'),path.with_suffix('.wav'),3)
        audio,sr=sf.read(path.with_suffix('.wav'));audio=audio.mean(axis=1)
        magnitude=np.abs(librosa.stft(audio,n_fft=4096,hop_length=256))
        times=np.arange(magnitude.shape[1])*256/sr
        indices=np.where((times>=.25)&(times<=1.4))[0]
        trace=pitch_trace(magnitude,sr,4096,indices,frequency)
        return fit_periodic(times[indices],trace)
    approximate=target['rate']*64/((bpm/7.5)*5)
    speeds=sorted({max(1,min(15,math.floor(approximate))),max(1,min(15,math.ceil(approximate)))})
    trials=[dict(speed=speed,depth=1,measured=measure(speed,1)) for speed in speeds]
    trial=min(trials,key=lambda t:abs(t['measured']['rate']-target['rate']))
    depth=max(1,min(15,round(target['depth_cents']/max(.1,trial['measured']['depth_cents']))))
    measured=measure(trial['speed'],depth)
    return dict(speed=trial['speed'],depth=depth),dict(unit_depth_trials=trials,chosen=measured)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--notes',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--library',type=Path,required=True,help='Independent libxmp library for effect calibration')
    a=p.parse_args()
    notes=json.loads(a.notes.read_text());arrangement=json.loads(a.arrangement.read_text())
    if arrangement['notes_sha256']!=hashlib.sha256(a.notes.read_bytes()).hexdigest() or arrangement['source_sha256']!=hashlib.sha256(a.audio.read_bytes()).hexdigest():
        p.error('source/notes differ from arrangement')
    import librosa
    import numpy as np
    y,sr=librosa.load(a.audio,sr=22050,duration=24)
    spectrum=np.abs(librosa.stft(y,n_fft=2048,hop_length=128))
    times=np.arange(spectrum.shape[1])*128/sr
    a.out.mkdir(parents=True,exist_ok=True)
    effects=[None]*len(notes);review=[]
    for index,note in enumerate(notes):
        start,end,pitch,_=note
        if end-start<.4 or pitch<60:continue
        indices=np.where((times>=start+.045)&(times<=end-.045))[0]
        if len(indices)<30:continue
        frequency=440*2**((pitch-69)/12)
        traces=[pitch_trace(spectrum,sr,2048,indices,frequency*h) for h in (1,2)]
        if any(trace is None for trace in traces):continue
        fits=[fit_periodic(times[indices],trace) for trace in traces]
        accepted=coherent(*fits,float(times[indices[-1]]-times[indices[0]]))
        entry=dict(note_index=index,pitch=pitch,start=start,fundamental=fits[0],harmonic=fits[1],accepted=accepted)
        if accepted:
            effect,calibration=calibrate(a.library,a.out,pitch,arrangement['roles'][index],fits[0])
            entry['effect']=effect;entry['calibration']=calibration
            actual=calibration['chosen']
            if actual['score']<.6 or abs(actual['rate']-fits[0]['rate'])>.5 or not .5<=actual['depth_cents']/fits[0]['depth_cents']<=1.5:
                entry['accepted']=False
                entry['rejection']='independent effect calibration outside tolerance'
            else:effects[index]=effect
        review.append(entry)
    arrangement['vibrato_detection']=dict(review=review,
        calibration_library_sha256=hashlib.sha256(a.library.read_bytes()).hexdigest(),
        limitations='Coherent sinusoidal pitch evidence only; source phase/window attenuation and tracker depth quantization need audition; no arpeggio/percussion changes')
    arrangement['vibrato']=effects
    arrangement['tick_multiplier']=2
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps([entry for entry in review if entry['accepted']],indent=2))


if __name__=='__main__':main()
