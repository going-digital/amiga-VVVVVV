"""Export the main tower's literal checkpoint setup in desktop entity order."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def checkpoints():
    text=(ROOT/'desktop_version/src/Map.cpp').read_text()
    start=text.index('    case 3: //The Tower')
    text=text[start:text.index('    case 4:',start)]
    rows=[(int(x),int(y),20+int(orientation),int(identifier)) for x,y,orientation,identifier in
        re.findall(r'obj\.createentity\((\d+),\s*(\d+),\s*10,\s*([01]),\s*(\d+)\)',text)]
    assert len(rows)==18 and len({r[3] for r in rows})==18
    return rows

def export(out):
    rows=checkpoints()
    (out/'tower_checkpoints.h').write_text('#define TOWER_CHECKPOINT_COUNT '+str(len(rows))+'\n'
        'static V6Checkpoint tower_checkpoints[TOWER_CHECKPOINT_COUNT]={\n'+
        ',\n'.join('{'+','.join(map(str,(*r,0,0)))+'}' for r in rows)+'};\n')
    (out/'tower-checkpoints.json').write_text(json.dumps(rows,indent=2)+'\n')
    return rows
