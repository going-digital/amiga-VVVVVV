"""Private source flash/teleport cues at the shared PAL Paula sample period."""
import json
import re
from convert_audio import convert,PAL_CLOCK,PERIOD
from pack_rooms import ROOT

def source_files(cues=('FLASH','TELEPORT')):
    music=(ROOT/'desktop_version/src/Music.cpp').read_text()
    enums=(ROOT/'desktop_version/src/Music.h').read_text()
    loads=re.findall(r'add_builtin_sound\("(.*?)"\)',music[music.index('add_builtin_sound("jump")'):])
    return tuple(loads[int(re.search('Sound_'+cue+r'\s*=\s*(\d+)',enums)[1])]
        for cue in cues)

def export(archive,out):
    header='/* Private source teleporter cues: signed 8-bit mono PCM. */\n'
    manifest=[]
    for cue,name in zip(('flash','teleport'),source_files()):
        pcm,meta=convert(archive.read('sounds/'+name+'.wav'))
        meta.update(cue=cue,file=name+'.wav');manifest.append(meta)
        (out/('teleporter-'+cue+'.pcm')).write_bytes(pcm)
        from sample_pack import pack_pcm
        packed=pack_pcm(pcm)
        header+='#ifdef V6_NORTH_ROUTE\nstatic const unsigned char teleporter_'+cue+'_packed[]={'+','.join(map(str,packed))+'};\n#else\n'
        header+='static const unsigned char teleporter_'+cue+'[]={'+','.join(map(str,pcm))+'};\n#endif\n'
        header+='#define TELEPORTER_'+cue.upper()+'_BYTES '+str(len(pcm))+'\n'
    header+='#define TELEPORTER_PERIOD '+str(PERIOD)+'\n'
    (out/'teleporter_samples.h').write_text(header)
    (out/'teleporter-samples.json').write_text(json.dumps(dict(version=1,pal_clock=PAL_CLOCK,
        period=PERIOD,samples=manifest,scope='Private source enum/load-order mapping and existing 9 kHz signed 8-bit conversion; no normalization'),indent=2)+'\n')

def export_prize(archive,out):
    header='/* Private source Prize cues: signed 8-bit mono PCM. */\n'
    manifest=[]
    for cue,name in zip(('vanish','trinket'),source_files(('DISAPPEAR','TRINKET'))):
        pcm,meta=convert(archive.read('sounds/'+name+'.wav'))
        meta.update(cue=cue,file=name+'.wav');manifest.append(meta)
        (out/('prize-'+cue+'.pcm')).write_bytes(pcm)
        from sample_pack import pack_pcm
        packed=pack_pcm(pcm);meta['packed_bytes']=len(packed)
        header+='#ifdef V6_NORTH_ROUTE\nstatic const unsigned char prize_'+cue+'_packed[]={'+','.join(map(str,packed))+'};\n#else\n'
        header+='static const unsigned char prize_'+cue+'[]={'+','.join(map(str,pcm))+'};\n#endif\n'
        header+='#define PRIZE_'+cue.upper()+'_BYTES '+str(len(pcm))+'\n'
    header+='#define PRIZE_PERIOD '+str(PERIOD)+'\n'
    (out/'prize_samples.h').write_text(header)
    (out/'prize-samples.json').write_text(json.dumps(dict(version=1,pal_clock=PAL_CLOCK,
        period=PERIOD,samples=manifest,scope='Source enum/load-order mapping; shared 9 kHz low-pass signed 8-bit conversion, no normalization'),indent=2)+'\n')

def export_terminal(archive,out):
    header='/* Private original terminal contact and reading cues. */\n'
    manifest=[]
    for cue,name in zip(('touch','read'),source_files(('TERMINALTOUCH','TERMINALTEXT'))):
        pcm,meta=convert(archive.read('sounds/'+name+'.wav'))
        meta['file']=name+'.wav';manifest.append(meta)
        (out/('terminal-'+cue+'.pcm')).write_bytes(pcm)
        value=pcm
        symbol='terminal_'+cue+('_pcm' if cue=='read' else '')
        header+='static const unsigned char '+symbol+'[] __attribute__((aligned(4)))={'+','.join(map(str,value))+'};\n'
        header+='#define TERMINAL_'+cue.upper()+'_BYTES '+str(len(pcm))+'\n'
    header+='#define TERMINAL_PERIOD '+str(PERIOD)+'\n'
    (out/'terminal_samples.h').write_text(header)
    (out/'terminal-touch.json').write_text(json.dumps(manifest,indent=2)+'\n')
