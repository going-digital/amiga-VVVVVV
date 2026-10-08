"""Private source flash/teleport cues at the shared PAL Paula sample period."""
import json
import re
from convert_audio import convert,PAL_CLOCK,PERIOD
from pack_rooms import ROOT

def source_files():
    music=(ROOT/'desktop_version/src/Music.cpp').read_text()
    enums=(ROOT/'desktop_version/src/Music.h').read_text()
    loads=re.findall(r'add_builtin_sound\("(.*?)"\)',music[music.index('add_builtin_sound("jump")'):])
    return tuple(loads[int(re.search('Sound_'+cue+r'\s*=\s*(\d+)',enums)[1])]
        for cue in ('FLASH','TELEPORT'))

def export(archive,out):
    header='/* Private source teleporter cues: signed 8-bit mono PCM. */\n'
    manifest=[]
    for cue,name in zip(('flash','teleport'),source_files()):
        pcm,meta=convert(archive.read('sounds/'+name+'.wav'))
        meta.update(cue=cue,file=name+'.wav');manifest.append(meta)
        (out/('teleporter-'+cue+'.pcm')).write_bytes(pcm)
        header+='static const unsigned char teleporter_'+cue+'[]={'+','.join(map(str,pcm))+'};\n'
        header+='#define TELEPORTER_'+cue.upper()+'_BYTES '+str(len(pcm))+'\n'
    header+='#define TELEPORTER_PERIOD '+str(PERIOD)+'\n'
    (out/'teleporter_samples.h').write_text(header)
    (out/'teleporter-samples.json').write_text(json.dumps(dict(version=1,pal_clock=PAL_CLOCK,
        period=PERIOD,samples=manifest,scope='Private source enum/load-order mapping and existing 9 kHz signed 8-bit conversion; no normalization'),indent=2)+'\n')
