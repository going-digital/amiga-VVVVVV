#!/usr/bin/env python3
"""Repeated-hit percussion candidates; labels are hypotheses, not ground truth.

Preserves low-frequency novelty that HPSS alone can suppress, clusters short
spectral/decay profiles and chooses representative rather than loudest hits.
"""
import argparse
import hashlib
import json
from pathlib import Path


def transient_signal(y, sr):
    """Suppress sustained partials while retaining low-frequency novelty."""
    import librosa
    import numpy as np
    from scipy.ndimage import median_filter
    if sr!=22050 or not len(y):
        raise ValueError('analysis requires nonempty 22,050 Hz audio')
    hop = 128
    spectrum = librosa.stft(y,n_fft=1024,hop_length=hop)
    magnitude = np.abs(spectrum)
    _, mask = librosa.decompose.hpss(magnitude,mask=True,margin=(2,1.5))
    frequencies = librosa.fft_frequencies(sr=sr,n_fft=1024)
    background = median_filter(magnitude,size=(1,41),mode='nearest')
    novelty_mask = np.clip((magnitude-background)/(magnitude+1e-8),0,1)
    low = (frequencies >= 40) & (frequencies < 300)
    mask[low] = np.maximum(mask[low],novelty_mask[low])
    mask[frequencies < 40] = 0
    clean = librosa.istft(spectrum*mask,hop_length=hop,length=len(y))
    return clean,spectrum,mask,frequencies


def analyze(y, sr):
    import librosa
    import numpy as np
    from sklearn.cluster import KMeans
    if sr!=22050 or not len(y):
        raise ValueError('analysis requires nonempty 22,050 Hz audio')
    hop = 128
    clean,spectrum,mask,frequencies=transient_signal(y,sr)
    cleaned_magnitude = np.abs(spectrum*mask)
    scale = np.maximum(np.percentile(cleaned_magnitude,75,axis=1),.005)
    whitened = np.minimum(cleaned_magnitude/scale[:,None],20)
    flux = np.r_[0,np.maximum(whitened[:,1:]-whitened[:,:-1],0).mean(axis=0)]
    frames = set(librosa.onset.onset_detect(onset_envelope=flux,sr=sr,hop_length=hop,
                                           backtrack=False).tolist())
    # Detect quieter hats independently instead of letting a strong low/mid
    # attack determine the normalization/threshold for every frequency band.
    for lo,hi in ((40,300),(300,4000),(4000,sr/2)):
        band = whitened[(frequencies>=lo)&(frequencies<hi)]
        if not len(band):
            continue
        envelope = np.r_[0,np.maximum(band[:,1:]-band[:,:-1],0).mean(axis=0)]
        frames.update(librosa.onset.onset_detect(onset_envelope=envelope,sr=sr,
                                               hop_length=hop,backtrack=False).tolist())
    frames = sorted(frames)
    candidates = []
    features = []
    bands = [(40,160),(160,500),(500,1500),(1500,4000),(4000,7000),(7000,11025)]
    for frame in frames:
        approximate = int(frame)*hop
        # Centered spectral frames can lead or lag the physical attack.
        # Search nearby energy rise without snapping to a music grid.
        first = max(0,approximate-round(.035*sr))
        last = min(len(clean),approximate+round(.04*sr))
        energy = np.convolve(clean[first:last]**2,np.ones(64)/64,mode='same')
        if len(energy)<128 or np.max(energy)<1e-6:
            continue
        before = clean[max(0,approximate-round(.08*sr)):max(0,approximate-round(.035*sr))]
        if len(before) and np.max(energy)<2*float(np.mean(before**2)):
            continue
        peak = int(np.argmax(energy))
        crossing = np.where(energy[:peak+1]>=np.max(energy)*.12)[0]
        onset = first+(int(crossing[0]) if len(crossing) else peak)
        clip = clean[onset:min(len(clean),onset+round(.24*sr))]
        if len(clip)<512:
            continue
        rms = float(np.sqrt(np.mean(clip**2)))
        if rms<.002:
            continue
        spectral = np.abs(librosa.stft(clip,n_fft=1024,hop_length=hop))**2
        profile = np.array([spectral[(frequencies>=lo)&(frequencies<hi),:min(16,spectral.shape[1])].sum()
                            for lo,hi in bands])
        profile /= max(1e-12,profile.sum())
        early = np.mean(clip[:round(.04*sr)]**2)
        late = np.mean(clip[max(round(.08*sr),len(clip)//2):]**2) if len(clip)>round(.08*sr) else np.mean(clip[len(clip)//2:]**2)
        decay = float(np.log1p(early/max(1e-12,late)))
        feature = np.r_[np.sqrt(profile),min(decay,5)*.1]
        candidate = dict(time=onset/sr,energy=rms,profile=profile.tolist(),clip=clip)
        if candidates and abs(candidate['time']-candidates[-1]['time'])<.06:
            if rms>candidates[-1]['energy']:
                candidates[-1]=candidate
                features[-1]=feature
        else:
            candidates.append(candidate)
            features.append(feature)
    if not candidates:
        return dict(samples=[],hits=[],candidates=[],method='no candidates'),clean
    matrix = np.array(features)
    count = min(3,len(np.unique(matrix,axis=0)))
    model = KMeans(n_clusters=count,n_init=20,random_state=0).fit(matrix)
    # Label by spectral brightness. These can be wrong when melodic leakage
    # forms a cluster; labels and individual hits remain editable/auditionable.
    brightness = [float(np.dot(model.cluster_centers_[i,:6]**2,[80,300,900,2500,5500,9000])) for i in range(count)]
    ordered = np.argsort(brightness)
    names = ['kick candidate','snare candidate','hat candidate'] if count==3 else ['transient '+str(i+1) for i in range(count)]
    from scipy.signal import resample_poly, butter, sosfilt
    samples = []
    for rank, cluster in enumerate(ordered):
        indexes = np.where(model.labels_==cluster)[0]
        # Exclude the quietest detections; choose the nearest cluster member.
        minimum = np.percentile([candidates[i]['energy'] for i in indexes],40)
        eligible = [i for i in indexes if candidates[i]['energy']>=minimum]
        exemplar = min(eligible,key=lambda i:np.linalg.norm(matrix[i]-model.cluster_centers_[cluster]))
        source = candidates[exemplar]['clip'].copy()
        if count==3:
            cutoff, kind = (700,'lowpass') if rank==0 else (180,'highpass') if rank==1 else (3000,'highpass')
            source = sosfilt(butter(3,cutoff,btype=kind,fs=sr,output='sos'),source)
        clip = resample_poly(source,11025,sr)
        clip *= np.minimum(np.arange(len(clip))/8,1)
        clip *= np.minimum(np.arange(len(clip))[::-1]/160,1)
        clip /= max(1e-12,float(np.max(np.abs(clip))))
        pcm = np.clip(np.rint(clip*105),-127,127).astype(np.int8)
        pcm = pcm[:len(pcm)//2*2];pcm[:2]=0
        samples.append(dict(name=names[rank],pcm=pcm.astype(np.uint8).tolist(),
                            source_time=candidates[exemplar]['time'],sample_rate=11025,
                            cluster_hits=len(indexes)))
    maxima = {int(cluster):max(candidates[i]['energy'] for i in range(len(candidates)) if model.labels_[i]==cluster)
              for cluster in ordered}
    hits = []
    summary = []
    for i, candidate in enumerate(candidates):
        cluster = int(model.labels_[i]);rank = int(np.where(ordered==cluster)[0][0])
        strength = min(1,max(.2,candidate['energy']/maxima[cluster]))
        hits.append(dict(time=candidate['time'],sample=rank,strength=strength))
        summary.append({k:v for k,v in candidate.items() if k!='clip'}|dict(sample=rank))
    return dict(samples=samples,hits=hits,candidates=summary,
                method='low-frequency novelty + HPSS; spectral/decay clustering; medoid-like exemplars',
                limitations='Kick/snare/hat labels are spectral guesses; melodic attacks and simultaneous drums can be misclassified.'),clean


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
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
    percussion,clean=analyze(y,sr)
    arrangement=json.loads(a.arrangement.read_text())
    arrangement['percussion']=percussion
    arrangement['percussion_source_sha256']=hashlib.sha256(a.audio.read_bytes()).hexdigest()
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    sf.write(a.out/'percussive-source.wav',clean,sr)
    for i,sample in enumerate(percussion['samples']):
        pcm=np.array(sample['pcm'],dtype=np.uint8).view(np.int8).astype(float)/128
        sf.write(a.out/('sample-'+str(i+1)+'.wav'),pcm,11025)
    print(json.dumps(dict(hits=len(percussion['hits']),samples=[{k:v for k,v in s.items() if k!='pcm'} for s in percussion['samples']]),indent=2))


if __name__=='__main__':
    main()
