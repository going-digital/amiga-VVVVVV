"""Reviewed Solitude first-steps script and original cry sound mapping."""
import json,re
from pathlib import Path
from hallway_scripts import ROOT

def script():
 s=(ROOT/'desktop_version/src/Scripts.cpp').read_text();start=s.index('else if (SDL_strcmp(t, "firststeps") == 0)');body=s[start:s.index('filllines(lines);',start)]
 raw=re.search(r'lines\[\]\s*=\s*\{(.*?)\};',body,re.S)[1];lines=[json.loads(v) for v in re.findall(r'"(?:\\.|[^"\\])*"',raw)]
 assert lines[0:2]==['cutscene()','untilbars()'] and lines[-3:]==['endtext','endcutscene()','untilbars()']
 ops=[];speeches=[];i=0
 while i<len(lines):
  v=lines[i]
  if v.startswith('text('):
   assert v=='text(cyan,0,0,2)';text=lines[i+1:i+3];assert all(s.isascii() and len(s)<=36 for s in text)
   ops.append(('TEXT',0,len(speeches)));speeches.append(text);i+=2
  else:
   commands={'cutscene()':('BARS',1),'untilbars()':('WAIT_BARS',0),'squeak(player)':('CUE',1),'squeak(cry)':('CUE',2),'position(player,above)':('POSITION',1),'speak_active':('SHOW',0),'endtext':('HIDE',0),'endcutscene()':('BARS',0)}
   op,value=commands[v];ops.append((op,value,None))
  i+=1
 assert len(speeches)==2
 return dict(lines=lines,speeches=speeches,ops=ops)

def export(archive,out):
 from convert_audio import convert
 from convert_teleporter_audio import source_files
 from sample_pack import pack_pcm
 data=script();header='#include "rescue_script.h"\n/* Original Solitude firststeps program. Shared caption slots 0 and 1. */\n'
 header+='static const V6RescueSpeech v6_firststeps_speeches[2]={\n'
 for i,lines in enumerate(data['speeches']):header+='{'+f'{i},1,2'+',{'+','.join(json.dumps(s) for s in lines)+',0,0}},\n'
 header+='};\nstatic const V6RescueOp v6_firststeps_ops[]={\n'
 for op,value,speech in data['ops']:header+='{V6_R_'+op+','+str(value)+','+('0' if speech is None else '&v6_firststeps_speeches['+str(speech)+']')+'},\n'
 header+='};\nstatic const V6RescueProgram v6_firststeps_program={v6_firststeps_ops,'+str(len(data['ops']))+'};\n'
 name=source_files(('CRY',))[0];pcm,meta=convert(archive.read('sounds/'+name+'.wav'));packed=pack_pcm(pcm)
 header+='static const unsigned char firststeps_cry_packed[]={'+','.join(map(str,packed))+'};\n#define FIRSTSTEPS_CRY_BYTES '+str(len(pcm))+'\n'
 (out/'firststeps_program.h').write_text(header);(out/'firststeps-cry.pcm').write_bytes(pcm)
 meta.update(file=name+'.wav',packed_bytes=len(packed));data['cry']=meta
 (out/'firststeps-script.json').write_text(json.dumps(data,indent=2)+'\n')
