#!/usr/bin/env python3
"""Four-voice PCM mixing, desktop slot allocation and source travel cue overlap."""
import ctypes as C
from fractions import Fraction
import itertools
import json
import math
import random
import subprocess
import zipfile
from test_player import ROOT,BUILD
from convert_assets import DEFAULT_DATA
from convert_teleporter_audio import export,source_files

class Voice(C.Structure):
    _fields_=[('pcm',C.POINTER(C.c_uint8)),('bytes',C.c_size_t),('position',C.c_size_t)]
class Mixer(C.Structure):
    _fields_=[('voices',Voice*4)]+[(n,C.c_uint) for n in ('starts','completed','dropped')]

def libraries():
    BUILD.mkdir(parents=True,exist_ok=True)
    flags=['-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all']
    subprocess.run(['cc','-std=c99',*flags,str(ROOT/'amiga_version/sfx_mixer.c'),'-o',str(BUILD/'sfx-mixer.so')],check=True)
    core=C.CDLL(str(BUILD/'sfx-mixer.so'))
    core.v6_sfx_init.argtypes=[C.POINTER(Mixer)]
    core.v6_sfx_play.argtypes=[C.POINTER(Mixer),C.POINTER(C.c_uint8),C.c_size_t]
    core.v6_sfx_render.argtypes=[C.POINTER(Mixer),C.POINTER(C.c_uint8),C.c_size_t]
    music=(ROOT/'desktop_version/src/Music.cpp').read_text()
    begin=music.index('        for (int i = 0; i < VVV_MAX_CHANNELS; i++)',music.index('    void Play(void)'))
    prefix=music[begin:music.index('                if (SDL_memcmp',begin)]
    code='''#define VVV_MAX_CHANNELS 4
unsigned busy;int voices[]={0,1,2,3};
struct FAudioVoiceState {unsigned BuffersQueued;};
void FAudioSourceVoice_GetState(int i,FAudioVoiceState *s,int){s->BuffersQueued=(busy>>i)&1;}
extern "C" int reference(unsigned mask){busy=mask;
'''+prefix+'return i;\n}}return -1;}\n'
    path=BUILD/'sfx-slot-reference.cpp';path.write_text(code)
    subprocess.run(['c++','-std=c++11',*flags,str(path),'-o',str(BUILD/'sfx-slot-reference.so')],check=True)
    ref=C.CDLL(str(BUILD/'sfx-slot-reference.so')).reference;ref.argtypes=[C.c_uint]
    return core,ref

def main():
    core,slot=libraries();one=(C.c_uint8*1)(127)
    for mask in range(16):
        m=Mixer();core.v6_sfx_init(C.byref(m))
        for i in range(4):
            if mask>>i&1:m.voices[i]=Voice(one,1,0)
        expected=slot(mask);before=tuple(bytes(v) for v in m.voices)
        result=core.v6_sfx_play(C.byref(m),one,1)
        if expected<0:assert not result and m.dropped==1 and before==tuple(bytes(v) for v in m.voices)
        else:
            assert result and m.starts==1 and m.voices[expected].pcm
            assert all(bytes(m.voices[i])==before[i] for i in range(4) if i!=expected)
    # Independent fractional-sum oracle exercises sign, headroom and rounding.
    m=Mixer();cases=0
    for values in itertools.product((-128,-127,-3,0,3,126,127),repeat=4):
        core.v6_sfx_init(C.byref(m));samples=[]
        for value in values:
            data=(C.c_uint8*1)(value&255);samples.append(data)
            assert core.v6_sfx_play(C.byref(m),data,1)
        output=(C.c_uint8*2)(77,77)
        assert core.v6_sfx_render(C.byref(m),output,2)
        assert list(output)==[int(sum(Fraction(v,4) for v in values))&255,0]
        assert m.starts==m.completed==4 and not m.dropped and all(not v.pcm for v in m.voices)
        cases+=1
    # Rendering in uneven chunks must preserve the same overlapping waveform.
    rng=random.Random(9);inputs=[bytes(rng.randrange(256) for _ in range(n)) for n in (1,41,177,523)]
    arrays=[(C.c_uint8*len(b)).from_buffer_copy(b) for b in inputs]
    def render(chunks):
        m=Mixer();core.v6_sfx_init(C.byref(m))
        for a in arrays:assert core.v6_sfx_play(C.byref(m),a,len(a))
        result=b''
        for n in chunks:
            data=(C.c_uint8*n)();assert core.v6_sfx_render(C.byref(m),data,n);result+=bytes(data)
        assert m.completed==4 and not m.dropped
        return result
    assert render([600])==render([1,0,17,101,481])
    # Invalid arguments/state must never partially advance output or voices.
    m=Mixer();core.v6_sfx_init(C.byref(m));before=bytes(m)
    assert not core.v6_sfx_play(C.byref(m),None,1) and bytes(m)==before
    assert not core.v6_sfx_play(C.byref(m),one,0) and bytes(m)==before
    assert not core.v6_sfx_play(None,one,1)
    output=(C.c_uint8*8)(*([77]*8))
    assert not core.v6_sfx_render(None,output,8) and bytes(output)==bytes([77]*8)
    assert not core.v6_sfx_render(C.byref(m),None,8) and bytes(m)==before
    assert core.v6_sfx_render(C.byref(m),None,0) and bytes(m)==before
    for v in (Voice(one,0,0),Voice(one,1,1),Voice(None,1,0),Voice(None,0,1)):
        m.voices[3]=v;before=bytes(m),bytes(output)
        assert not core.v6_sfx_render(C.byref(m),output,8)
        assert before==(bytes(m),bytes(output))
    # Private asset conversion and staged source event schedule; fixed logic
    # pauses for 62 PAL fields after each destination handoff.
    out=ROOT/'build/amiga-teleporter-audio';out.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(DEFAULT_DATA) as archive:export(archive,out)
    assert source_files()==('preteleport','teleport')
    meta=json.loads((out/'teleporter-samples.json').read_text())
    payloads=[(out/('teleporter-'+cue+'.pcm')).read_bytes() for cue in ('flash','teleport')]
    assert all(len(b)>=1024 and not len(b)%2 and b[-2:]==bytes(2) for b in payloads)
    assert [s['source_duration'] for s in meta['samples']]==[16956/44100,66560/44100]
    pcms=[(C.c_uint8*len(b)).from_buffer_copy(b) for b in payloads]
    events=[(1,0),(11,1),(23,0),(38,1),(65,0),(75,1),(87,0),(102,1)]
    rate=meta['pal_clock']/meta['period']
    def sample_at(tick):
        # Playback schedules are field-quantized; this is a host timeline
        # oracle, not a claim of native request/DMA latency equivalence.
        fields=math.ceil(tick*34000/19968)+62*sum(tick>edge for edge in (22,86))
        return round(fields*.019968*rate)
    starts=[(sample_at(tick),cue) for tick,cue in events]
    total=max(at+len(payloads[cue]) for at,cue in starts)+1024
    core.v6_sfx_init(C.byref(m));cursor=0;peak=0;mixed=bytearray();active=[]
    for at,cue in starts+[(total,None)]:
        count=at-cursor;data=(C.c_uint8*count)()
        assert core.v6_sfx_render(C.byref(m),data,count)
        expected=[]
        for position in range(cursor,at):
            values=[payloads[c][position-origin] for origin,c in active if position-origin<len(payloads[c])]
            values=[v if v<128 else v-256 for v in values]
            expected.append(int(sum(Fraction(v,4) for v in values))&255)
        assert bytes(data)==bytes(expected)
        mixed.extend(data);cursor=at
        if cue is not None:
            assert core.v6_sfx_play(C.byref(m),pcms[cue],len(pcms[cue]))
            active.append((at,cue));peak=max(peak,sum(bool(v.pcm) for v in m.voices))
    assert (m.starts,m.completed,m.dropped)==(8,8,0) and peak==3
    assert mixed[-1024:]==bytes(1024)
    (out/'roundtrip-mix.pcm').write_bytes(mixed)
    report=dict(source_files=list(source_files()),cue_starts=8,cue_completed=8,dropped=0,
        peak_voices=peak,source_slot_cases=16,rounding_cases=cases,mixed_bytes=len(mixed),
        scope='Portable overlap core and source asset mapping; field-quantized host timeline, quarter gain; native stereo DMA integration pending')
    (out/'mixer-tests.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS teleporter mixer:',json.dumps(report))
if __name__=='__main__':main()
