"""Export source yellow rescue programs using the shared bounded compiler."""
import json
import re
from hallway_scripts import ROOT,ALLOWED,compile_script

def scripts():
    source=(ROOT/'desktop_version/src/Scripts.cpp').read_text();result={}
    for name in ('rescueyellow','skipyellow'):
        start=source.index(f'else if (SDL_strcmp(t, "{name}") == 0)')
        body=source[start:source.index('filllines(lines);',start)]
        literal=re.search(r'lines\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
        lines=[json.loads(s) for s in re.findall(r'"(?:\\.|[^"\\])*"',literal)]
        i=0
        while i<len(lines):
            match=re.fullmatch(r'(\w+)(?:\((.*?)\))?',lines[i])
            assert match and match[1] in ALLOWED|{'changetile'},(name,i,lines[i])
            if match[1]=='text':
                count=int(match[2].split(',')[3]);assert len(lines[i+1:i+1+count])==count;i+=count
            i+=1
        assert 'rescued(yellow)' in lines and 'companion(7)' in lines
        assert 'changeai(yellow,followplayer)' in lines and 'changetile(yellow,6)' in lines
        result[name]=dict(lines=lines)
    assert result['rescueyellow']['lines'][0]=='ifskip(skipyellow)'
    return result

def export(out):
    source=scripts();compiled={name:compile_script(value['lines'],'yellow','skipyellow',7) for name,value in source.items()}
    speeches=compiled['rescueyellow']['speeches']
    assert [len(s['lines']) for s in speeches]==[2,2,1,2,1,1,4,2,1,2,1]
    assert not compiled['skipyellow']['speeches']
    (out/'station-scripts.json').write_text(json.dumps(dict(version=1,scripts=source),indent=2)+'\n')
    (out/'station-rescue-programs.json').write_text(json.dumps(dict(version=1,programs=compiled),indent=2)+'\n')
    header='#include "rescue_script.h"\n/* Source yellow rescue; renderer/persistence integration pending. */\n'
    header+='static const V6RescueSpeech v6_station_rescue_speeches[]={\n'
    for index,speech in enumerate(speeches):
        text=[json.dumps(line) for line in speech['lines']]+['0']*(4-len(speech['lines']))
        header+='{'+f'{index},{int(speech["speaker"]=="player")},{len(speech["lines"])}'+',{'+','.join(text)+'}},\n'
    header+='};\n#define V6_STATION_RESCUE_SPEECHES '+str(len(speeches))+'\n'
    for name,program in compiled.items():
        header+=f'static const V6RescueOp v6_{name}_ops[]={{\n'
        for op in program['ops']:
            speech='0' if op['speech'] is None else '&v6_station_rescue_speeches['+str(op['speech'])+']'
            header+='{V6_R_'+op['op']+','+str(op['value'])+','+speech+'},\n'
        header+='};\n'
        header+='static const V6RescueProgram v6_'+name+'_program={v6_'+name+'_ops,'+str(len(program["ops"]))+'};\n'
    (out/'station_rescue_programs.h').write_text(header)
    return compiled
