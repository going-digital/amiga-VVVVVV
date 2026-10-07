"""Private Viridian/Vermilion WAVs to signed 8-bit PAL Paula PCM."""
import hashlib
import io
import json
import math
import struct
import wave
PAL_CLOCK=3546895
PERIOD=161
FILES=('crew6','crew1') # Script speaker 0=red, 1=player.

def convert(raw):
    with wave.open(io.BytesIO(raw)) as w:
        assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getcomptype()=='NONE'
        rate=w.getframerate();frames=w.getnframes()
        source=struct.unpack('<'+str(frames)+'h',w.readframes(frames))
    count=math.ceil(frames*PAL_CLOCK/(rate*PERIOD));pcm=[]
    # Offline 63-tap Blackman-windowed sinc, cutoff 9 kHz. Normalize each
    # phase's weights; zero extension at the source boundaries.
    cutoff=9000/rate
    for n in range(count):
        at=n*rate*PERIOD/PAL_CLOCK;base=math.floor(at);value=weight=0.0
        for i in range(base-31,base+32):
            d=i-at
            if abs(d)>31:continue
            sinc=2*cutoff if d==0 else math.sin(2*math.pi*cutoff*d)/(math.pi*d)
            window=.42+.5*math.cos(math.pi*d/31)+.08*math.cos(2*math.pi*d/31)
            tap=sinc*window;weight+=tap
            if 0<=i<frames:value+=source[i]*tap
        pcm.append(max(-128,min(127,round(value/weight/256))))
    # Last DMA word is silent, including any length alignment pad.
    if len(pcm)&1:pcm.append(0)
    pcm.extend((0,0))
    data=bytes(v&255 for v in pcm)
    return data,dict(source_frames=frames,source_rate=rate,pcm_bytes=len(data),period=PERIOD,
        source_sha256=hashlib.sha256(raw).hexdigest(),pcm_sha256=hashlib.sha256(data).hexdigest(),
        source_duration=frames/rate,pcm_duration=len(data)*PERIOD/PAL_CLOCK)

def export(archive,out):
    manifest=[];header='/* Private source cues: red then player; signed 8-bit PCM. */\n'
    total=2 # Separate silent DMA word.
    for speaker,name in enumerate(FILES):
        pcm,meta=convert(archive.read('sounds/'+name+'.wav'));meta.update(speaker=speaker,file=name+'.wav')
        (out/(name+'.pcm')).write_bytes(pcm)
        header+='static const unsigned char cue_'+name+'[]={'+','.join(map(str,pcm))+'};\n'
        header+='#define CUE_'+name.upper()+'_BYTES '+str(len(pcm))+'\n'
        total+=len(pcm);manifest.append(meta)
    header+='#define CUE_PERIOD '+str(PERIOD)+'\n#define CUE_DMA_BYTES '+str(total)+'\n'
    (out/'cue_samples.h').write_text(header)
    (out/'cue-samples.json').write_text(json.dumps(dict(version=1,pal_clock=PAL_CLOCK,samples=manifest,
        chip_bytes=total,scope='Private source WAVs, 9 kHz low-pass resampling, signed 8-bit quantization; no normalization'),indent=2)+'\n')
    return total
