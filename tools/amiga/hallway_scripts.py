"""Export the bounded Seeing Red rescue scripts without interpreting prose."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ALLOWED={'ifskip','cutscene','tofloor','changemood','untilbars','rescued','squeak',
         'text','position','speak_active','endtext','fadeout','untilfade','delay',
         'fadein','companion','endcutscene','changeai'}
def scripts():
    source=(ROOT/'desktop_version/src/Scripts.cpp').read_text();result={}
    for name in ('rescuered','skipred'):
        start=source.index(f'else if (SDL_strcmp(t, "{name}") == 0)')
        body=source[start:source.index('filllines(lines);',start)]
        literal=re.search(r'lines\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
        lines=[json.loads(s) for s in re.findall(r'"(?:\\.|[^"\\])*"',literal)]
        speeches=[];i=0
        while i<len(lines):
            command=lines[i];match=re.fullmatch(r'(\w+)(?:\((.*?)\))?',command)
            assert match and match[1] in ALLOWED,(name,i,command)
            if match[1]=='text':
                colour,x,y,count=match[2].split(',');count=int(count)
                speech=lines[i+1:i+1+count];assert len(speech)==count
                speeches.append(dict(speaker=colour,lines=speech));i+=count
            i+=1
        assert 'rescued(red)' in lines and 'companion(9)' in lines
        assert 'changeai(red,followplayer)' in lines
        result[name]=dict(lines=lines,speeches=speeches)
    assert result['rescuered']['lines'][0]=='ifskip(skipred)'
    assert [len(s['lines']) for s in result['rescuered']['speeches']]==[1,3,1,1,2,2]
    return result

def compile_script(lines):
    ops=[];speeches=[];i=0
    simple={'ifskip':('IF_SKIP',0),'cutscene':('BARS',1),'endcutscene':('BARS',0),
        'tofloor':('FLOOR',0),'untilbars':('WAIT_BARS',0),'rescued':('RESCUED',0),
        'speak_active':('SHOW',0),'endtext':('HIDE',0),'fadeout':('FADE',1),
        'fadein':('FADE',-1),'untilfade':('WAIT_FADE',0),'changeai':('FOLLOW',0)}
    while i<len(lines):
        match=re.fullmatch(r'(\w+)(?:\((.*?)\))?',lines[i]);name=match[1];args=(match[2] or '').split(',')
        value=0;speech=None
        if name=='text':
            assert args[0] in ('red','player') and args[1:3]==['0','0']
            count=int(args[3]);assert 1<=count<=3
            text=lines[i+1:i+1+count]
            assert all(len(line)<=36 and line.isascii() for line in text)
            speech=len(speeches);speeches.append(dict(speaker=args[0],lines=text));i+=count;op='TEXT'
        elif name=='squeak':
            assert args[0] in ('red','player');op='CUE';value=args[0]=='player'
        elif name=='position':
            assert args[0] in ('red','player') and args[1]=='above';op='POSITION';value=args[0]=='player'
        elif name=='changemood':
            assert args==['red','0'];op='MOOD'
        elif name=='delay':op='DELAY';value=int(args[0]);assert 0<=value<=32767
        elif name=='companion':op='COMPANION';value=int(args[0]);assert value==9
        else:
            assert name in simple,name
            if name=='ifskip':assert args==['skipred']
            if name=='rescued':assert args==['red']
            if name=='changeai':assert args==['red','followplayer']
            op,value=simple[name]
        ops.append(dict(op=op,value=int(value),speech=speech));i+=1
    return dict(ops=ops,speeches=speeches)

def export(out):
    values=scripts()
    (out/'hallway-scripts.json').write_text(json.dumps(dict(version=1,scripts=values),indent=2)+'\n')
    header='/* Source Seeing Red script lines; bounded rescue runner data. */\n'
    for name,value in values.items():
        lines=value['lines'];header+=f'#define V6_{name.upper()}_LINES {len(lines)}\n'
        header+=f'static const char *const v6_{name}_lines[]={{'+','.join(json.dumps(v) for v in lines)+'};\n'
    (out/'hallway_scripts.h').write_text(header)
    compiled={name:compile_script(value['lines']) for name,value in values.items()}
    (out/'rescue-programs.json').write_text(json.dumps(dict(version=1,programs=compiled),indent=2)+'\n')
    header='#include "rescue_script.h"\n'
    speeches=compiled['rescuered']['speeches']
    header+='static const V6RescueSpeech v6_rescue_speeches[]={\n'
    for index,speech in enumerate(speeches):
        text=[json.dumps(line) for line in speech['lines']]+['0']*(3-len(speech['lines']))
        header+='{'+f'{index},{int(speech["speaker"]=="player")},{len(speech["lines"])}'+',{'+','.join(text)+'}},\n'
    header+='};\n#define V6_RESCUE_SPEECHES '+str(len(speeches))+'\n'
    for name,program in compiled.items():
        header+=f'static const V6RescueOp v6_{name}_ops[]={{\n'
        for op in program['ops']:
            speech='0' if op['speech'] is None else '&v6_rescue_speeches['+str(op['speech'])+']'
            header+='{V6_R_'+op['op']+','+str(op['value'])+','+speech+'},\n'
        header+='};\n'
        header+='static const V6RescueProgram v6_'+name+'_program={v6_'+name+'_ops,'+str(len(program['ops']))+'};\n'
    (out/'rescue_programs.h').write_text(header)
    return values
