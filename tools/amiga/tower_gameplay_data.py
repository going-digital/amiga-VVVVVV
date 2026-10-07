"""Export the main tower's literal checkpoint setup in desktop entity order."""
import json
import re
import struct
from pack_rooms import encode
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
    export_route(out)
    export_building(out)
    export_energize(out)
    from hallway_scripts import export as export_scripts
    export_scripts(out)
    return rows

def hallway_rooms():
    source=(ROOT/'desktop_version/src/Finalclass.cpp').read_text();result=[]
    for x,y in ((108,109),(110,104)):
        start=source.index(f'case rn({x},{y}):');end=source.index('case rn(',start+5)
        body=source[start:end]
        raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
        raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
        tiles=[int(v) for v in raw.split(',') if v.strip()]
        assert len(tiles)==1200 and max(tiles)<30
        cp=re.findall(r'obj\.createentity\((\d+),\s*(\d+),\s*10,\s*([01]),\s*(\d+)\)',body)
        assert len(cp)==1
        cx,cy,orientation,identity=map(int,cp[0])
        result.append(dict(x=x,y=y,tiles=tiles,checkpoint=(cx,cy,20+orientation,identity)))
    return result

def export_route(out):
    header='/* Literal tower hallway terrain/checkpoints; crew/dialogue omitted. */\n'
    for i,r in enumerate(hallway_rooms()):
        tiles=r['tiles'];packed=encode(tiles)
        packets=[encode(tiles[row*40:(row+1)*40]) for row in range(30)]
        directory=b'';payload=b''
        for packet in packets:
            directory+=struct.pack('>IH',len(payload),len(packet));payload+=packet
        display=struct.pack('>4sHHH',b'V6TR',1,40,30)+directory+payload
        (out/f'hallway{i}.v6tr').write_bytes(display)
        (out/f'hallway{i}.bin').write_bytes(packed)
        header+=f'static const uint8_t hallway{i}_packed[]={{'+','.join(map(str,packed))+'};\n'
        header+=f'static const uint8_t hallway{i}_display[]={{'+','.join(map(str,display))+'};\n'
        header+=f'static const uint16_t hallway{i}_tiles[1200]={{'+','.join(map(str,tiles))+'};\n'
        header+=(f'static V6Checkpoint hallway{i}_checkpoint[1]={{'+
            '{'+','.join(map(str,(*r['checkpoint'],0,0)))+'}};\n')
    header+='#ifdef V6_TOWER_BUILDING\n#include "building_display.h"\nstatic V6Teleporter building_teleporter={112,48,0,1,1,0};\n#endif\n'
    header+='static const V6TowerRouteRoom tower_route_rooms[]={\n'
    header+='{109,109,0,0,tower_checkpoints,TOWER_CHECKPOINT_COUNT,0,0,2},\n'
    header+='{109,104,0,0,tower_checkpoints,TOWER_CHECKPOINT_COUNT,0,0,2},\n'
    for i,r in enumerate(hallway_rooms()):
        header+='{'+f'{r["x"]},{r["y"]},hallway{i}_packed,sizeof(hallway{i}_packed),hallway{i}_checkpoint,1,hallway{i}_tiles,0,2'+'},\n'
    header+='#ifdef V6_TOWER_BUILDING\n{111,104,building_packed,sizeof(building_packed),0,0,building_tiles,&building_teleporter,2},\n#endif\n};\n#define TOWER_ROUTE_COUNT (sizeof(tower_route_rooms)/sizeof(tower_route_rooms[0]))\n'
    (out/'tower_route_data.h').write_text(header)


def building_room():
    source=(ROOT/'desktop_version/src/Finalclass.cpp').read_text()
    start=source.index('case rn(111,104):');body=source[start:source.index('case rn(',start+5)]
    raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
    tiles=[int(v) for v in raw.split(',') if v.strip()]
    assert len(tiles)==1200 and max(tiles)<30
    calls=re.findall(r'obj.createentity\(([^;]+)\);',body)
    assert len(calls)==1 and re.sub(r'\s+','',calls[0])=='128-16,80-32,14'
    return tiles

def export_building(out):
    tiles=building_room();directory=b'';payload=b''
    for row in range(30):
        packet=encode(tiles[row*40:(row+1)*40])
        directory+=struct.pack('>IH',len(payload),len(packet));payload+=packet
    display=struct.pack('>4sHHH',b'V6TR',1,40,30)+directory+payload
    (out/'building_display.h').write_text('static const uint8_t building_display[]={'+','.join(map(str,display))+'};\n'+
        'static const uint16_t building_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
        'static const uint8_t building_packed[]={'+','.join(map(str,encode(tiles)))+'};\n')


def energize_room():
    # Spacestation2 translates main-world (110,105) to literal (48,41).
    source=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    assert 'rx += 50 - 12;' in source and 'ry += 50 - 14;' in source
    start=source.index('case rn(48,41):');body=source[start:source.index('case rn(',start+5)]
    raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
    tiles=[int(v) for v in raw.split(',') if v.strip()]
    assert len(tiles)==1200 and max(tiles)==805
    calls=re.findall(r'obj.createentity\(([^;]+)\);',body)
    assert len(calls)==1 and re.sub(r'\s+','',calls[0])=='(5*8)-4,(8*8)+4,14'
    assert 'roomname = "Energize";' in body
    # Normal mode has no blocks or moving entities; the trial barrier is excluded.
    assert re.findall(r'obj.createblock\(([^;]+)\);',body)==['1, 280, 0, 32, 240, 82']
    return dict(x=110,y=105,tileset=0,tiles=tiles,teleporter=(36,68,0),name='Energize')

def export_energize(out):
    room=energize_room();tiles=room['tiles']
    (out/'energize_collision.h').write_text('/* Source normal-mode collision data; renderer integration pending. */\n'+
        'static const uint16_t energize_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
        'static const uint8_t energize_packed[]={'+','.join(map(str,encode(tiles)))+'};\n')
    (out/'energize-room.json').write_text(json.dumps({k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')
