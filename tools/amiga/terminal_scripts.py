"""Reviewed original station terminal script, preserving whitespace and layout."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def station_terminal():
    source=(ROOT/'desktop_version/src/TerminalScripts.cpp').read_text()
    start=source.index('if (SDL_strcmp(t, "terminal_station_1") == 0)')
    body=source[start:source.index('filllines(lines);',start)]
    raw=re.search(r'lines\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    commands=[json.loads(v) for v in re.findall(r'"(?:\\.|[^"\\])*"',raw)]
    expected=['cutscene()','untilbars()','squeak(terminal)','text(gray,0,60,1)',
        'position(centerx)','backgroundtext','flipme','speak','text(gray,0,120,6)',
        'position(center)','speak','endtext','endcutscene()','untilbars()']
    pages=[];ops=[];i=0
    while i<len(commands):
        line=commands[i];ops.append(line)
        m=re.fullmatch(r'text\(gray,0,(\d+),(\d+)\)',line)
        if m:
            y,n=map(int,m.groups());text=commands[i+1:i+n+1]
            assert len(text)==n and all(s.isascii() and len(s)<=36 for s in text)
            pages.append(dict(x=-500,y=y if len(pages)==0 else -500,flip=int(not pages),lines=text));i+=n
        i+=1
    assert ops==expected and [len(p['lines']) for p in pages]==[1,6]
    return dict(name='terminal_station_1',commands=commands,pages=pages)

def export(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True);data=station_terminal()
    (out/'terminal-station.json').write_text(json.dumps(data,indent=2)+'\n')
    header='#include "terminal_read.h"\n/* Original station terminal; preserve significant spaces. */\n'
    header+='static const V6TerminalPage v6_station_terminal_pages[2]={\n'
    for p in data['pages']:
        lines=[json.dumps(s) for s in p['lines']]+['0']*(6-len(p['lines']))
        header+='{'+f'{p["x"]},{p["y"]},{p["flip"]},{len(p["lines"])}'+',{'+','.join(lines)+'}},\n'
    header+='};\nstatic const V6TerminalReadProgram v6_station_terminal_program={v6_station_terminal_pages,2};\n'
    (out/'terminal_station_program.h').write_text(header)
    return data
