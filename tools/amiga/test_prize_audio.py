#!/usr/bin/env python3
"""Source cue bindings and equivalent PCM decoding before Paula resampling."""
import io
import struct
import wave
from convert_audio import convert
from convert_teleporter_audio import source_files

def wav(values,width,channels):
    out=io.BytesIO()
    with wave.open(out,'wb') as w:
        w.setnchannels(channels);w.setsampwidth(width);w.setframerate(44100)
        w.writeframes(bytes(values) if width==1 else struct.pack('<'+'h'*len(values),*values))
    return out.getvalue()

def main():
    assert source_files(('DISAPPEAR','TRINKET'))==('vanish','souleyeminijingle')
    values=[0,1,32,64,127,128,129,192,224,254,255]*32
    canonical=[(v-128)*256 for v in values]
    expected,_=convert(wav(canonical,2,1))
    for width,channels in ((1,1),(1,2),(2,1),(2,2)):
        v=values if width==1 else canonical
        interleaved=[x for sample in v for x in [sample]*channels]
        actual,meta=convert(wav(interleaved,width,channels))
        assert actual==expected and actual[-2:]==b'\0\0'
        assert meta['source_channels']==channels and meta['source_width']==width
    stereo=[x for sample in canonical for x in (sample//2+128,sample//2-128)]
    actual,_=convert(wav(stereo,2,2));reference,_=convert(wav([v//2 for v in canonical],2,1))
    assert actual==reference
    print('PASS Prize audio: source enum/load order, 8/16-bit mono/stereo equivalence, downmix amplitude and silent DMA tail')

if __name__=='__main__':main()
