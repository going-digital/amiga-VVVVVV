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

def export(out):
    values=scripts()
    (out/'hallway-scripts.json').write_text(json.dumps(dict(version=1,scripts=values),indent=2)+'\n')
    header='/* Source Seeing Red script lines; presentation/execution not yet linked. */\n'
    for name,value in values.items():
        lines=value['lines'];header+=f'#define V6_{name.upper()}_LINES {len(lines)}\n'
        header+=f'static const char *const v6_{name}_lines[]={{'+','.join(json.dumps(v) for v in lines)+'};\n'
    (out/'hallway_scripts.h').write_text(header)
    return values
