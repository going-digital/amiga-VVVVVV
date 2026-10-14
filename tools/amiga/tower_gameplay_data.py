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
    export_frown(out)
    export_shenanigan(out)
    export_prize(out)
    export_vstitch(out)
    export_prize_return_rooms(out)
    from hallway_scripts import export as export_scripts
    export_scripts(out)
    from station_scripts import export as export_station_scripts
    export_station_scripts(out)
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
    header+='#ifdef V6_TOWER_ENERGIZE\n#include "energize_collision.h"\nstatic V6Teleporter energize_teleporter={36,68,0,1,1,0};\n#endif\n'
    header+='#ifdef V6_TOWER_STATION\n#include "frown_collision.h"\n#ifdef V6_TOWER_SHENANIGAN\n#include "shenanigan_collision.h"\n#ifdef V6_TOWER_PRIZE\n#include "prize_collision.h"\n#ifdef V6_VSTITCH_INPUT_CAPTURE\n#include "vstitch_collision.h"\n#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE\n#include "deception_collision.h"\n#include "downunder_collision.h"\n#endif\n#endif\n#endif\n#endif\n#endif\n'
    header+='static const V6TowerRouteRoom tower_route_rooms[]={\n'
    header+='{109,109,0,0,tower_checkpoints,TOWER_CHECKPOINT_COUNT,0,0,2},\n'
    header+='{109,104,0,0,tower_checkpoints,TOWER_CHECKPOINT_COUNT,0,0,2},\n'
    for i,r in enumerate(hallway_rooms()):
        header+='{'+f'{r["x"]},{r["y"]},hallway{i}_packed,sizeof(hallway{i}_packed),hallway{i}_checkpoint,1,hallway{i}_tiles,0,2'+'},\n'
    header+='#ifdef V6_TOWER_BUILDING\n{111,104,building_packed,sizeof(building_packed),0,0,building_tiles,&building_teleporter,2},\n#endif\n#ifdef V6_TOWER_ENERGIZE\n{110,105,energize_packed,sizeof(energize_packed),0,0,energize_tiles,&energize_teleporter,0},\n#endif\n#ifdef V6_TOWER_STATION\n{111,105,frown_packed,sizeof(frown_packed),frown_checkpoint,1,frown_tiles,0,0},\n#ifdef V6_TOWER_SHENANIGAN\n{111,106,shenanigan_packed,sizeof(shenanigan_packed),shenanigan_checkpoint,2,shenanigan_tiles,0,0},\n#ifdef V6_TOWER_PRIZE\n{111,107,prize_packed,sizeof(prize_packed),prize_checkpoint,1,prize_tiles,0,0},\n#ifdef V6_VSTITCH_INPUT_CAPTURE\n{112,107,vstitch_packed,sizeof(vstitch_packed),vstitch_checkpoint,2,vstitch_tiles,0,0},\n#ifdef V6_PRIZE_RETURN_INPUT_CAPTURE\n{110,107,deception_packed,sizeof(deception_packed),deception_checkpoint,2,deception_tiles,0,0},\n{110,106,downunder_packed,sizeof(downunder_packed),downunder_checkpoint,2,downunder_tiles,0,0},\n#endif\n#endif\n#endif\n#endif\n#endif\n};\n#define TOWER_ROUTE_COUNT (sizeof(tower_route_rooms)/sizeof(tower_route_rooms[0]))\n'
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


def frown_room():
    """Source candidate adjacent to Energize; crew/script integration pending."""
    source=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    assert 'rx += 50 - 12;' in source and 'ry += 50 - 14;' in source
    start=source.index('case rn(49,41):');body=source[start:source.index('case rn(',start+5)]
    raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
    tiles=[int(v) for v in raw.split(',') if v.strip()]
    assert len(tiles)==1200 and max(tiles)==850
    assert re.findall(r'obj.createentity\(([^;]+)\);',body)==['192, 88, 10, 0, 441490','42, 86, 16, 0']
    assert re.findall(r'obj.createblock\(([^;]+)\);',body)==['1, 0, 0, 140, 240, 34']
    assert 'roomname = "Frown Upside Down";' in body
    assert 'if(!game.intimetrial || game.translator_exploring)' in body
    assert 'if(game.companion==0 && !obj.flags[10] &&  !game.crewstats[2])' in body
    return dict(x=111,y=105,tileset=0,tiles=tiles,name='Frown Upside Down',
        checkpoint=(192,88,20,441490),crew=(42,86,16,0),trigger=(0,0,140,240,34))

def export_frown(out):
    room=frown_room();tiles=room['tiles']
    (out/'frown_collision.h').write_text('/* Candidate source room; native admission pending crew/story/save support. */\n'+
        'static const uint16_t frown_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
        'static const uint8_t frown_packed[]={'+','.join(map(str,encode(tiles)))+'};\n'+
        'static V6Checkpoint frown_checkpoint[1]={{192,88,20,441490,0,0}};\n')
    (out/'frown-room.json').write_text(json.dumps({k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')
    return room


def shenanigan_room():
    from pack_rooms import enemy_record
    record=enemy_record(scene='shenanigan')
    return dict(x=111,y=106,tileset=0,tiles=list(struct.unpack('>1200H',record[1])),
        name='Shenanigan',checkpoints=[(144,168,21,442490),(24,112,20,442491)],
        conveyors=[(16,104,8,4,64),(104,184,9,4,64)])

def export_shenanigan(out):
    room=shenanigan_room();tiles=room['tiles']
    for x,y,_,_,width in room['conveyors']:
        assert tiles[(y//8)*40+x//8:(y//8)*40+(x+width)//8]==[0]*(width//8)
    (out/'shenanigan_collision.h').write_text('/* Source Shenanigan terrain and checkpoint bank. */\n'+
        'static const uint16_t shenanigan_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
        'static const uint8_t shenanigan_packed[]={'+','.join(map(str,encode(tiles)))+'};\n'+
        'static V6Checkpoint shenanigan_checkpoint[2]={{144,168,21,442490,0,0},{24,112,20,442491,0,0}};\n')
    (out/'shenanigan-room.json').write_text(json.dumps({k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')
    return room


def prize_room():
    from pack_rooms import prize_record
    source,raw,_=prize_record()
    return dict(x=111,y=107,tileset=0,tiles=list(struct.unpack('>1200H',raw)),
                name='Prize for the Reckless',source=source,
                checkpoints=[(240,136,20,443490)])

def export_prize(out):
    room=prize_room();tiles=room['tiles']
    for y in (72,112,128):
        assert tiles[y//8*40+15:y//8*40+19]==[0]*4
    (out/'prize_collision.h').write_text('/* Reviewed normal-mode mutable source room. */\n'+
        'static uint16_t prize_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
        'static const uint8_t prize_packed[]={'+','.join(map(str,encode(tiles)))+'};\n'+
        'static V6Checkpoint prize_checkpoint[1]={{240,136,20,443490,0,0}};\n')
    (out/'prize-room.json').write_text(json.dumps({k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')
    return room


def vstitch_room():
    """Literal source room; native scope is the lower checkpoint passage only."""
    source=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    start=source.index('case rn(50,43):');body=source[start:source.index('case rn(',start+5)]
    raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    tiles=[int(v) for v in raw.split(',') if v.strip()]
    assert len(tiles)==1200 and max(tiles)==851
    calls=re.findall(r'obj.createentity\(([^;]+)\);',body)
    assert calls==['280, 192, 10, 1, 443500','64, 80, 10, 1, 443501']
    assert re.findall(r'obj.createblock\(([^;]+)\);',body)==['1, 0, 0, 112, 112, 8']
    assert 'if(!game.nocutscenes)' in body and 'roomname = "V Stitch";' in body
    assert 'rx += 50 - 12;' in source and 'ry += 50 - 14;' in source
    return dict(x=112,y=107,tileset=0,tiles=tiles,name='V Stitch',
        checkpoints=[(280,192,21,443500),(64,80,21,443501)],trigger=(0,0,112,112,8))

def export_vstitch(out):
    room=vstitch_room();tiles=room['tiles']
    (out/'vstitch_collision.h').write_text('/* Lower-passage capture only; upper intro trigger remains pending. */\n'+
        'static const uint16_t vstitch_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
        'static const uint8_t vstitch_packed[]={'+','.join(map(str,encode(tiles)))+'};\n'+
        'static V6Checkpoint vstitch_checkpoint[2]={{280,192,21,443500,0,0},{64,80,21,443501,0,0}};\n')
    (out/'vstitch-room.json').write_text(json.dumps({k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')
    return room


def prize_return_room(name):
    """Literal west-route candidates; export does not admit them to the campaign."""
    cases={'deception':(48,43,'A Deception'), 'downunder':(48,42,'Down Under')}
    rx,ry,title=cases[name]
    source=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    start=source.index(f'case rn({rx},{ry}):')
    body=source[start:source.index('case rn(',start+5)]
    raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    tiles=[int(v) for v in raw.split(',') if v.strip()]
    calls=[tuple(int(v.strip()) for v in call.split(','))
           for call in re.findall(r'obj.createentity\(([^;]+)\);',body)]
    expected={
        'deception':[(152,32,10,1,443480),(152,184,10,0,443481),
            (272,120,1,2,8),(32,96,1,3,8),
            (104,80,2,10,4),(168,80,2,10,4),(232,80,2,8,4),
            (56,144,2,10,4),(120,144,2,10,4),(184,144,2,8,4)],
        'downunder':[(88,112,2,0,4,88,64,264,168),(136,112,2,1,4,88,64,264,168),
            (184,112,2,0,4,88,64,264,168),(232,112,2,1,4,88,64,264,168),
            (56,64,10,0,442480),(280,152,10,1,442481)]}
    assert len(tiles)==1200 and calls==expected[name]
    assert not re.findall(r'obj.createblock\(',body)
    assert f'roomname = "{title}";' in body
    assert 'rx += 50 - 12;' in source and 'ry += 50 - 14;' in source
    return dict(x=rx+62,y=ry+64,tileset=0,tiles=tiles,name=title,entities=calls,
        checkpoints=[(x,y,20+orientation,identifier)
                     for x,y,kind,orientation,identifier in (c for c in calls if c[2]==10)])


def deception_room():return prize_return_room('deception')
def downunder_room():return prize_return_room('downunder')


def export_prize_return_rooms(out):
    for name in ('deception','downunder'):
        room=prize_return_room(name);tiles=room['tiles']
        checkpoints=room['checkpoints']
        (out/(name+'_collision.h')).write_text(
            '/* West-route candidate only; actors, campaign/save admission pending. */\n'+
            'static const uint16_t '+name+'_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
            'static const uint8_t '+name+'_packed[]={'+','.join(map(str,encode(tiles)))+'};\n'+
            'static V6Checkpoint '+name+'_checkpoint[2]={'+
            ','.join('{'+','.join(map(str,(*r,0,0)))+'}' for r in checkpoints)+'};\n')
        (out/(name+'-room.json')).write_text(json.dumps(
            {k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')


def north_route_room(name):
    """Reviewed connected original neighbours north of V Stitch."""
    import ast
    cases={
        'reflect':(50,42,'Stop and Reflect',[(288,160,10,1,442500),
            (135,75,2,0,3,100,70,320,160),(185,110,2,0,3,100,70,320,160),
            (235,145,2,0,3,100,70,320,160)]),
        'yesmen':(50,41,'The Yes Men',[(122,8,1,0,3),(266,8,1,0,3),
            (122,204,1,1,3),(194,172,1,1,3),(194,40,1,0,3),
            (64,80,10,1,441501),(64,136,10,0,441502)]),
        'gantry':(50,40,'Gantry and Dolly',[(104,64,3,10),(136,64,3,10),
            (168,64,3,10),(56,104,10,1,440500),(56,152,2,3,3),
            (280,192,10,1,440501)])}
    rx,ry,title,expected=cases[name]
    source=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    start=source.index(f'case rn({rx},{ry}):');body=source[start:source.index('case rn(',start+5)]
    raw=re.search(r'static const short contents\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
    tiles=[int(v) for v in raw.split(',') if v.strip()]
    def integer(node):
        if isinstance(node,ast.Constant) and type(node.value) is int:return node.value
        if isinstance(node,ast.BinOp) and isinstance(node.op,(ast.Add,ast.Sub)):
            left,right=integer(node.left),integer(node.right)
            return left+right if isinstance(node.op,ast.Add) else left-right
        raise ValueError('Unexpected source entity expression')
    calls=[tuple(integer(ast.parse(v.strip(),mode='eval').body) for v in call.split(','))
           for call in re.findall(r'obj.createentity\(([^;]+)\);',body)]
    assert len(tiles)==1200 and calls==expected
    assert not re.findall(r'obj.createblock\(',body) and f'roomname = "{title}";' in body
    return dict(x=rx+62,y=ry+64,tileset=0,tiles=tiles,name=title,entities=calls,
        checkpoints=[(call[0],call[1],20+call[3],call[4]) for call in calls if call[2]==10])


def export_north_route(out):
    for name in ('reflect','yesmen','gantry'):
        room=north_route_room(name);tiles=room['tiles'];checkpoints=room['checkpoints']
        (out/(name+'_collision.h')).write_text('/* Reviewed original connected north route. */\n'+
            'static const uint16_t '+name+'_tiles[1200]={'+','.join(map(str,tiles))+'};\n'+
            'static const uint8_t '+name+'_packed[]={'+','.join(map(str,encode(tiles)))+'};\n'+
            'static V6Checkpoint '+name+'_checkpoint['+str(len(checkpoints))+']={'+
            ','.join('{'+','.join(map(str,(*r,0,0)))+'}' for r in checkpoints)+'};\n')
        (out/(name+'-room.json')).write_text(json.dumps({k:v for k,v in room.items() if k!='tiles'},indent=2)+'\n')
