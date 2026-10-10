#!/usr/bin/env python3
"""Bias percussion towards recurring positions on a candidate four-beat bar.

Audio repetition estimates bar length; this does not confirm meter/downbeat.
A configurable simple backbeat prior competes with distinct-bar hit support.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path


def estimate_bar(y,sr):
    import librosa
    import numpy as np
    from scipy.signal import correlate,find_peaks
    hop=128
    power=np.abs(librosa.stft(y,n_fft=1024,hop_length=hop))**2
    frequency=librosa.fft_frequencies(sr=sr,n_fft=1024)
    scores=[]
    for lo,hi in ((40,180),(1000,10000)):
        energy=np.log1p(power[(frequency>=lo)&(frequency<hi)].sum(axis=0))
        onset=np.maximum(np.diff(energy,prepend=energy[0]),0)
        onset-=onset.mean()
        corr=correlate(onset,onset,mode='full',method='fft')[len(onset)-1:]
        scores.append(corr/max(1e-12,corr[0]))
    score=np.mean(scores,axis=0)
    peaks=[i for i in find_peaks(score)[0] if 1<=i*hop/sr<=4]
    if not peaks or max(score[i] for i in peaks)<=.05:
        raise ValueError('no convincing 1..4 second repeat; supply --bar-seconds')
    best=max(score[i] for i in peaks)
    i=min(i for i in peaks if score[i]>=best*.95)
    left,center,right=score[i-1:i+2]
    denominator=left-2*center+right
    adjustment=.5*(left-right)/denominator if abs(denominator)>1e-12 else 0
    seconds=(i+float(np.clip(adjustment,-.5,.5)))*hop/sr
    return seconds,dict(repeat_correlation=float(center),quarter_bpm=240/seconds,
                        assumption='Repeat interpreted as a four-beat bar; downbeat phase initially zero')


def regularize(percussion,bar_seconds,duration,phase=0,prior_weight=4):
    if not math.isfinite(bar_seconds) or not .5<=bar_seconds<=8 or not 0<duration<=120:
        raise ValueError('invalid bar length/duration')
    if not math.isfinite(phase) or not 0<=prior_weight<=20:
        raise ValueError('invalid phase/prior weight')
    result=copy.deepcopy(percussion)
    template=[]
    bins=16
    step=bar_seconds/bins
    support={}
    for hit in percussion['hits']:
        grid=math.floor((hit['time']-phase)/step+.5)
        if grid<0:
            continue
        bar,position=divmod(grid,bins)
        support.setdefault((hit['sample'],position),{})[bar]=max(
            hit['strength'],support.get((hit['sample'],position),{}).get(bar,0))
    evidence=[]
    for sample,instrument in enumerate(percussion['samples']):
        strengths=[h['strength'] for h in percussion['hits'] if h['sample']==sample]
        if not strengths:
            continue
        kind=instrument['name'].split()[0]
        prior=(0,8) if kind=='kick' else (4,12) if kind=='snare' else ()
        choices=[]
        for position in range(bins):
            bars=support.get((sample,position),{})
            # Each bar votes at most once, preventing rolls/fragments from
            # overpowering consistent placement in independent bars.
            votes=len(bars)
            score=votes+prior_weight*(position in prior)
            evidence.append(dict(sample=sample,position=position,bars=votes,score=score))
            if votes or (position in prior and percussion['hits']):
                choices.append((score,position in prior,position,bars))
        chosen=sorted(choices,key=lambda item:(-item[0],-item[1],item[2]))[:2]
        strength=sorted(strengths)[len(strengths)//2] if strengths else .7
        instrument['volume']=max(8,min(48,round(strength*48)))
        for _,_,position,bars in chosen:
            template.append(dict(sample=sample,position=position,strength=strength,
                                 supporting_bars=len(bars),prior_position=position in prior))
    hits=[]
    for bar in range(math.ceil((duration-phase)/bar_seconds)):
        for event in template:
            time=phase+(bar+event['position']/bins)*bar_seconds
            if 0<=time<duration:
                hits.append(dict(time=time,sample=event['sample'],strength=event['strength'],
                                 bar=bar,position=event['position']))
    result['unregularized_hits']=result['hits']
    result['hits']=sorted(hits,key=lambda h:h['time'])
    result['timing']='ticks'
    result['bar_template']=dict(seconds=bar_seconds,phase=phase,bins=bins,
                               prior_weight=prior_weight,events=template,evidence=evidence,
                               assumption='four-beat repeating pattern; fills misses and suppresses non-template hits; no fills/section variation')
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('audio',type=Path)
    p.add_argument('--arrangement',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--duration',type=float,default=24)
    p.add_argument('--bar-seconds',type=float)
    p.add_argument('--phase',type=float,default=0)
    p.add_argument('--prior-weight',type=float,default=4)
    a=p.parse_args()
    if not 0<a.duration<=120:
        p.error('duration must be 0..120 seconds')
    import librosa
    y,sr=librosa.load(a.audio,sr=22050,duration=a.duration)
    bar,estimate=(a.bar_seconds,dict(manual=True)) if a.bar_seconds else estimate_bar(y,sr)
    arrangement=json.loads(a.arrangement.read_text())
    if arrangement.get('percussion_source_sha256')!=hashlib.sha256(a.audio.read_bytes()).hexdigest():
        p.error('arrangement belongs to a different percussion source recording')
    arrangement['percussion']=regularize(arrangement['percussion'],bar,min(a.duration,len(y)/sr),a.phase,a.prior_weight)
    arrangement['percussion']['bar_estimate']=estimate
    a.out.mkdir(parents=True,exist_ok=True)
    (a.out/'arrangement.json').write_text(json.dumps(arrangement,indent=2)+'\n')
    print(json.dumps(dict(bar_seconds=bar,estimate=estimate,template=arrangement['percussion']['bar_template']['events'],hits=len(arrangement['percussion']['hits'])),indent=2))


if __name__=='__main__':
    main()
