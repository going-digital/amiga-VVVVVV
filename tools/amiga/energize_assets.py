"""Private compact Energize tiles; collision keeps original source IDs."""
from collections import Counter
import json
import struct
import subprocess
from tower_gameplay_data import energize_room
from pack_rooms import encode

def export(archive,out,decoder):
    room=energize_room();ids=sorted(set(room['tiles']));assert len(ids)<=32
    path=out/'energize-tiles.png';path.write_bytes(archive.read('graphics/tiles.png'))
    header,rgba=subprocess.check_output([str(decoder),str(path)]).split(b'\n',1)
    width,height=map(int,header.split());assert width%8==height%8==0
    pixels=[]
    for tile in ids:
        ox=tile%(width//8)*8;oy=tile//(width//8)*8;assert oy+8<=height
        row=[]
        for y in range(8):
            for x in range(8):
                r,g,b,a=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                assert a in (0,255)
                row.append(tuple(round(v*a/255/17) for v in (r,g,b)) if tile else (0,0,0))
        pixels.append(row)
    counts=Counter(c for tile in pixels for c in tile if c!=(0,0,0))
    palette=[(0,0,0)]+[c for c,_ in counts.most_common(3)]
    palette+=[(0,0,0)]*(4-len(palette))
    indices=[[min(range(4),key=lambda i:sum((palette[i][j]-c[j])**2 for j in range(3))) for c in tile] for tile in pixels]
    atlas=bytes(sum(((tile[y*8+x]>>p)&1)<<(7-x) for x in range(8)) for tile in indices for p in range(2) for y in range(8))
    mapping={tile:i for i,tile in enumerate(ids)};tiles=[mapping[t] for t in room['tiles']]
    offsets=[65535]*1024;words=[]
    for a,b in sorted(set(zip(tiles[::2],tiles[1::2]))):
        offsets[a*32+b]=len(words)
        words.extend(atlas[a*16+p*8+y]*256+atlas[b*16+p*8+y] for p in range(2) for y in range(8))
    directory=b'';payload=b''
    for row in range(30):
        packet=encode(tiles[row*40:(row+1)*40]);directory+=struct.pack('>IH',len(payload),len(packet));payload+=packet
    display=struct.pack('>4sHHH',b'V6TR',1,40,30)+directory+payload
    colors=[r<<8|g<<4|b for r,g,b in palette]
    header='/* Private converted graphics; do not redistribute. */\n'
    for ctype,name,values in [('uint8_t','energize_display',display),('uint8_t','energize_atlas',atlas),('uint16_t','energize_palette',colors),('uint16_t','energize_pair_offsets',offsets),('uint16_t','energize_pairs',words)]:
        header+=f'static const {ctype} {name}[]={{'+','.join(map(str,values))+'};\n'
    header+=f'#define ENERGIZE_TILE_COUNT {len(ids)}\n#define ENERGIZE_PAIR_WORDS {len(words)}\n'
    (out/'energize_assets.h').write_text(header)
    for name,blob in [('energize.v6tr',display),('energize-atlas.bin',atlas)]: (out/name).write_bytes(blob)
    (out/'energize-graphics.json').write_text(json.dumps(dict(source_ids=ids,palette=colors,pairs=len(words)//16,quantized_pixels=indices,display_tiles=tiles),indent=2)+'\n')
