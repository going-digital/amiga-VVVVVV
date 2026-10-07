#!/usr/bin/env python3
"""Audio plan guards, restart/one-shot state machine and source cue mapping."""
import ctypes as C
import io
import json
from pathlib import Path
import re
import struct
import subprocess
import wave
from convert_audio import convert,FILES
from test_player import block
ROOT=Path(__file__).resolve().parents[2]
class Sample(C.Structure):
    _fields_=[('address',C.c_uint32),('bytes',C.c_uint),('period',C.c_uint),('volume',C.c_uint)]
class Write(C.Structure):
    _fields_=[('reg',C.c_uint),('value',C.c_uint)]
class Plan(C.Structure):
    _fields_=[('writes',Write*16),('count',C.c_uint)]
class Audio(C.Structure):
    _fields_=[('sample',Sample),('silence',C.c_uint32),*[(n,C.c_uint) for n in 'state starts completed replaced error interrupts wait'.split()]]
def pairs(p):
    assert p.count<=16
    return [(p.writes[i].reg,p.writes[i].value) for i in range(p.count)]
def main():
    out=ROOT/'build/amiga-audio';out.mkdir(parents=True,exist_ok=True)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',str(ROOT/'amiga_version/audio.c'),'-o',str(out/'audio.so')],check=True)
    core=C.CDLL(str(out/'audio.so'))
    core.v6_audio_init.argtypes=[C.POINTER(Audio),C.c_uint32]
    core.v6_audio_request.argtypes=[C.POINTER(Audio),C.POINTER(Sample),C.POINTER(Plan)]
    core.v6_audio_tick.argtypes=[C.POINTER(Audio),C.c_int,C.POINTER(Plan)]
    core.v6_audio_stop.argtypes=[C.POINTER(Audio),C.POINTER(Plan)]
    a=Audio();p=Plan();sample=Sample(0x10000,2442,161,64)
    assert core.v6_audio_init(C.byref(a),0x20000)
    invalid=[Sample(0x10001,2442,161,64),Sample(0x80000-1000,2442,161,64),Sample(0x10000,2441,161,64),Sample(0x10000,1022,161,64),Sample(0x10000,131072,161,64),Sample(0x10000,2442,123,64),Sample(0x10000,2442,1025,64),Sample(0x10000,2442,161,65)]
    for s in invalid:
        before=bytes(a),bytes(p)
        assert not core.v6_audio_request(C.byref(a),C.byref(s),C.byref(p))
        assert before==(bytes(a),bytes(p))
    for repeat in range(6):
        assert core.v6_audio_request(C.byref(a),C.byref(sample),C.byref(p))
        assert pairs(p)==[(0x96,3),(0xa8,0),(0xb8,0),(0x9c,0x180)] and a.state==1
        core.v6_audio_tick(C.byref(a),1,C.byref(p));assert not p.count and a.state==1
        core.v6_audio_tick(C.byref(a),1,C.byref(p));assert a.state==2
        assert pairs(p)==[(0x9c,0x180),(0xa0,1),(0xa2,0),(0xa4,1221),(0xa6,161),(0xa8,64),(0xb0,1),(0xb2,0),(0xb4,1221),(0xb6,161),(0xb8,64),(0x96,0x8203)]
        for tick in range(3):core.v6_audio_tick(C.byref(a),0,C.byref(p));assert not p.count and a.state==2
        core.v6_audio_tick(C.byref(a),1,C.byref(p));assert a.state==3
        assert pairs(p)==[(0xa0,2),(0xa2,0),(0xa4,1),(0xb0,2),(0xb2,0),(0xb4,1),(0x9c,0x180)]
        core.v6_audio_tick(C.byref(a),0,C.byref(p));assert not p.count and a.state==3
        core.v6_audio_tick(C.byref(a),1,C.byref(p));assert a.state==0
    assert (a.starts,a.completed,a.interrupts)==(6,6,12)
    # New requests replace pending/playing/draining cues, then cool down.
    for target in (1,2,3):
        assert core.v6_audio_request(C.byref(a),C.byref(sample),C.byref(p))
        if target>=2:
            core.v6_audio_tick(C.byref(a),0,C.byref(p));core.v6_audio_tick(C.byref(a),0,C.byref(p))
        if target==3:core.v6_audio_tick(C.byref(a),1,C.byref(p))
        assert a.state==target
        assert core.v6_audio_request(C.byref(a),C.byref(sample),C.byref(p)) and a.state==1 and a.wait==1
        core.v6_audio_stop(C.byref(a),C.byref(p));assert a.state==0
    assert a.replaced==3
    # Independently derive Script -> enum index -> WAV load order.
    script=(ROOT/'desktop_version/src/Script.cpp').read_text();music=(ROOT/'desktop_version/src/Music.cpp').read_text();enums=(ROOT/'desktop_version/src/Music.h').read_text()
    loads=re.findall(r'add_builtin_sound\("(.*?)"\)',music[music.index('add_builtin_sound("jump")'):])
    for name,file in (('VERMILION','crew6'),('VIRIDIAN','crew1')):
        index=int(re.search('Sound_'+name+r'\s*=\s*(\d+)',enums)[1]);assert loads[index]==file
        assert 'music.playef(Sound_'+name+');' in script
    handler=block(script,script.index('else if (words[0] == "squeak")')).removeprefix('else ')
    sound_enum=block(enums,enums.rindex('enum',0,enums.index('Sound_FLIP')))+';'
    wrapper='#include <string>\n'+sound_enum+'\nstruct Music {int sound;void playef(int n){sound=n;}} music;\nextern "C" int cue(const char *speaker){std::string words[2]={"squeak",speaker};music.sound=-1;'+handler+'return music.sound;}\n'
    (out/'cue_reference.cpp').write_text(wrapper)
    subprocess.run(['c++','-O2','-shared','-fPIC',str(out/'cue_reference.cpp'),'-o',str(out/'cue_reference.so')],check=True)
    cue=C.CDLL(str(out/'cue_reference.so')).cue;cue.argtypes=[C.c_char_p]
    assert loads[cue(b'red')]=='crew6' and loads[cue(b'player')]=='crew1'
    assert FILES==('crew6','crew1')
    stream=io.BytesIO()
    with wave.open(stream,'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(44100)
        w.writeframes(struct.pack('<4096h',*([8192]*4096)))
    pcm,meta=convert(stream.getvalue())
    assert len(pcm)%2==0 and pcm[-2:]==bytes(2) and set(pcm[100:-100])=={32}
    report=dict(invalid_sample_cases=len(invalid),complete_one_shots=6,replacement_states=3,source_mapping=dict(red='crew6.wav',player='crew1.wav'),scope='Portable ordered register plans and guards; stereo Paula output checked in native captures')
    (out/'tests.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',report)
if __name__=='__main__':main()
