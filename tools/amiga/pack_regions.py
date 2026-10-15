#!/usr/bin/env python3
"""Private, endian-explicit northern region packs; no original assets are committed."""
from pathlib import Path
import json
import struct
import zlib
from test_map_draw import arrays
from tower_gameplay_data import north_route_room
from test_player import ROOT

REGIONS=(('reflect','yesmen'),('gantry','security'),('linear','filter'))

def build(out):
    manifest=[]
    for region,names in enumerate(REGIONS):
        directory=bytearray();payload=bytearray();offset=16+32*len(names)
        for name in names:
            room=north_route_room(name);path=out/(name+'_assets.h')
            display=bytes(arrays(path,name+'_display'))
            values=[room['tiles'],arrays(path,name+'_palette'),arrays(path,name+'_pair_offsets'),arrays(path,name+'_pairs')]
            data=b''.join(struct.pack('>'+str(len(v))+'H',*v) for v in values)+display
            data+=bytes(len(data)&1)
            ident=10+('reflect','yesmen','gantry','security','linear','filter').index(name)
            directory.extend(struct.pack('>8H4I',ident,room['x'],room['y'],room['tileset'],len(values[2])//32,len(values[3]),len(display),len(values[2]),offset,len(data),0,0))
            payload.extend(data);offset+=len(data)
        size=offset+4
        data=struct.pack('>4s4HI',b'V6RG',1,region,len(names),0,size)
        data+=directory+payload;data+=struct.pack('>I',zlib.crc32(data))
        assert len(data)==size<=12288
        (out/f'north{region}.v6rg').write_bytes(data)
        manifest.append(dict(region=region,rooms=list(names),bytes=size,crc32=f'{zlib.crc32(data[:-4]):08x}'))
    (out/'regions.json').write_text(json.dumps(dict(version=1,slots=2,slot_bytes=12288,regions=manifest),indent=2)+'\n')
    header='/* Private disk-region bindings, generated alongside their packs. */\n'
    for names in REGIONS:
        for name in names:
            for field in ('display','palette','pair_offsets','pairs'):
                target='offsets' if field=='pair_offsets' else field
                header+=f'#define {name}_{field} (north_content->{target})\n'
            header+=f'#define {name.upper()}_TILE_COUNT (north_content->tile_count)\n#define {name.upper()}_PAIR_WORDS (north_content->pair_words)\n'
    (out/'region_bindings.h').write_text(header)
    print('Regional content:',manifest,'; two fixed 12288-byte slots')

if __name__=='__main__':build(ROOT/'build/amiga-feasibility')
