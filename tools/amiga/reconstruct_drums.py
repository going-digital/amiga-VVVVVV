#!/usr/bin/env python3
"""Conservative attack classification and parameterized drums, never source chops.

These are percussion hypotheses. Source noise/modulation can still be ambiguous;
rejected events and measured parameters are retained for review.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def measure_attack(clip, sr):
    import numpy as np
    import librosa
    from scipy.signal import find_peaks
    spectrum=np.abs(librosa.stft(clip,n_fft=1024,hop_length=128))**2
    frequency=librosa.fft_frequencies(sr=sr,n_fft=1024)
    body=spectrum[:,1:min(13,spectrum.shape[1])]
    power=np.mean(body,axis=1)
    noise=body[frequency>=300]
    high_fraction=float(power[frequency>=5000].sum()/max(1e-12,power[frequency>=300].sum()))
    if high_fraction>.75:
        noise=body[frequency>=5000]
    cumulative=np.cumsum(np.mean(noise,axis=1))
    if cumulative[-1]>1e-12:
        useful=(cumulative>=cumulative[-1]*.05)&(cumulative<=cumulative[-1]*.95)
        if np.count_nonzero(useful)>=4:
            noise=noise[useful]
    flatness=float(np.median(np.exp(np.mean(np.log(noise+1e-12),axis=0))/np.mean(noise+1e-12,axis=0)))
    peaks=find_peaks(power)[0]
    mask=np.zeros(len(power),bool)
    for i in sorted(peaks,key=lambda i:-power[i])[:12]:
        mask[max(0,i-1):i+2]=True
    concentration=float(power[mask].sum()/max(1e-12,power.sum()))
    low=(frequency>=40)&(frequency<300)
    low_fraction=float(power[low].sum()/max(1e-12,power.sum()))
    low_indexes=np.where(low)[0]
    first=np.mean(spectrum[low,1:5],axis=1)
    last=np.mean(spectrum[low,8:13],axis=1)
    f0=float(frequency[low_indexes[np.argmax(first)]])
    f1=float(frequency[low_indexes[np.argmax(last)]])
    noise_power=spectrum[frequency>=1500].sum(axis=0)
    early=float(np.mean(noise_power[1:7]))
    late=float(np.mean(noise_power[15:30])) if len(noise_power)>15 else early
    decay_db=10*math.log10(max(1e-12,early)/max(1e-12,late))
    brightness=float(np.sum(power*frequency)/max(1e-12,power.sum()))
    # Exponential amplitude envelope: power drops by exp(-2*t/tau).
    tau=max(.008,min(.14,2*.1/max(.5,decay_db*math.log(10)/10)))
    low_power=spectrum[low].sum(axis=0)
    low_baseline=float(np.median(low_power[-6:]))
    residual=np.maximum(0,low_power-low_baseline)
    peak=int(np.argmax(residual[:8]))
    indices=np.arange(peak,min(len(residual),peak+15))
    indices=indices[residual[indices]>max(1e-12,residual[peak]*.1)]
    low_tau=.06
    if len(indices)>=3:
        slope=float(np.polyfit(indices*128/sr,np.log(residual[indices]),1)[0])
        if slope<0:
            low_tau=max(.025,min(.12,-2/slope))
    return dict(flatness=flatness,peak_concentration=concentration,
                low_fraction=low_fraction,high_fraction=high_fraction,frequency_start=f0,frequency_end=f1,
                low_decay_seconds=low_tau,
                decay_db=decay_db,brightness=brightness,decay_seconds=tau)


def classify(metrics):
    if (metrics['low_fraction']>.15 and metrics['frequency_start']>=metrics['frequency_end']*1.3
            and 35<=metrics['frequency_end']<=160 and metrics['frequency_start']<=260):
        return 'kick','low-frequency downward sweep'
    if metrics['flatness']>=.12 and metrics['peak_concentration']<.6 and metrics['decay_db']>=1:
        return ('hat' if metrics['high_fraction']>.75 else 'snare'),'decaying broadband attack'
    return None,'tonal, sustained or ambiguous attack'


def synthesize(kind, parameters, seed=7):
    import numpy as np
    from scipy.signal import butter,sosfilt
    if kind not in ('kick','snare','hat'):
        raise ValueError('unknown percussion kind')
    sr=11025
    tau=parameters['low_decay_seconds'] if kind=='kick' else parameters['decay_seconds']
    tau=float(np.clip(tau,.025,.12) if kind=='kick' else np.clip(tau,.012,.10) if kind=='snare' else np.clip(tau,.006,.035))
    length=round(min(.4,max(.08,tau*6))*sr)//2*2
    t=np.arange(length)/sr
    if kind=='kick':
        start=float(np.clip(parameters['frequency_start'],70,220))
        end=float(np.clip(parameters['frequency_end'],40,100))
        frequency=end+(start-end)*np.exp(-t/.025)
        wave=np.sin(2*np.pi*np.cumsum(frequency)/sr)*np.exp(-t/tau)
    else:
        noise=np.random.default_rng(seed).normal(size=length)
        if kind=='hat':
            noise=sosfilt(butter(3,[3000,5000],fs=sr,btype='bandpass',output='sos'),noise)
        else:
            noise=sosfilt(butter(3,[250,4500],fs=sr,btype='bandpass',output='sos'),noise)
        wave=noise*np.exp(-t/tau)
    wave*=np.minimum(np.arange(length)/6,1)
    wave*=np.minimum(np.arange(length)[::-1]/64,1)
    wave/=max(1e-12,float(np.max(np.abs(wave))))
    pcm=np.clip(np.rint(wave*105),-127,127).astype(np.int8)
    pcm[:2]=0
    return dict(name=kind+' reconstruction',pcm=pcm.astype(np.uint8).tolist(),
                sample_rate=sr,parameters=parameters,decay_seconds=tau,
                method='single swept oscillator' if kind=='kick' else 'seeded filtered noise')


def reconstruct(y,sr,candidates):
    import numpy as np
    if sr!=22050 or not len(y):
        raise ValueError('reconstruction requires nonempty 22,050 Hz audio')
    observations=[]
    for hit in candidates:
        start=max(0,round(hit['time']*sr))
        clip=y[start:start+round(.24*sr)]
        if len(clip)<round(.18*sr):
            continue
        metrics=measure_attack(clip,sr)
        kind,reason=classify(metrics)
        observations.append(dict(time=hit['time'],strength=hit.get('strength',.7),
                                 kind=kind,reason=reason,metrics=metrics))
    samples=[]
    hits=[]
    for kind in ('kick','snare','hat'):
        accepted=[o for o in observations if o['kind']==kind]
        if not accepted:
            continue
        parameters={key:float(np.median([o['metrics'][key] for o in accepted]))
                    for key in accepted[0]['metrics']}
        sample=len(samples)
        samples.append(synthesize(kind,parameters))
        hits.extend(dict(time=o['time'],strength=o['strength'],sample=sample) for o in accepted)
    return dict(samples=samples,hits=sorted(hits,key=lambda h:h['time']),observations=observations,
                skipped_short_clips=len(candidates)-len(observations),
                method='attack gates then measured sweep/decay; synthesized samples without source waveform',
                limitations='Conservative heuristic classification; no confirmed real-song drum identities; filtered noise/single oscillator timbres approximate source.')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--candidates',type=Path,required=True)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    a=p.parse_args()
    if not 0<a.duration<=120:
        p.error('duration must be 0..120 seconds')
    import librosa
    import numpy as np
    import soundfile as sf
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    candidate_file=json.loads(a.candidates.read_text())
    source_digest=hashlib.sha256(a.audio.read_bytes()).hexdigest()
    if candidate_file.get('percussion_source_sha256')!=source_digest:
        p.error('candidate timestamps belong to a different source file')
    candidates=candidate_file['percussion']['hits']
    arrangement=json.loads(a.arrangement.read_text())
    percussion=reconstruct(y,sr,candidates)
    arrangement['percussion']=percussion
    arrangement['percussion_source_sha256']=source_digest
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    for sample in percussion['samples']:
        pcm=np.array(sample['pcm'],dtype=np.uint8).view(np.int8).astype(float)/128
        sf.write(a.out/(sample['name'].split()[0]+'.wav'),pcm,11025)
    counts={kind:sum(o['kind']==kind for o in percussion['observations']) for kind in (None,'kick','snare','hat')}
    print(json.dumps(dict(classification_counts=counts,samples=[{k:v for k,v in s.items() if k!='pcm'} for s in percussion['samples']]),indent=2))


if __name__=='__main__':
    main()
