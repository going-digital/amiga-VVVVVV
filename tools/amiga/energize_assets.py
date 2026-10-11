"""Private compact Energize tiles; collision keeps original source IDs."""
from collections import Counter
import json
import struct
import subprocess
from tower_gameplay_data import energize_room
from pack_rooms import encode

def export(archive,out,decoder,room=None,name="energize"):
    room=energize_room() if room is None else room;ids=sorted(set(room['tiles']) | ({59} if name=='prize' else set()));assert len(ids)<=32
    path=out/(name+'-tiles.png');path.write_bytes(archive.read('graphics/tiles.png'))
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
    for ctype,symbol,values in [('uint8_t','energize_display',display),('uint8_t','energize_atlas',atlas),('uint16_t','energize_palette',colors),('uint16_t','energize_pair_offsets',offsets),('uint16_t','energize_pairs',words)]:
        symbol=symbol.replace('energize',name)
        header+=f'static const {ctype} {symbol}[]={{'+','.join(map(str,values))+'};\n'
    header+=f'#define {name.upper()}_TILE_COUNT {len(ids)}\n#define {name.upper()}_PAIR_WORDS {len(words)}\n'
    if name=='shenanigan':
        frames=[]
        for tile in (*range(68,72),*range(28,32)):
            ox=tile%(width//8)*8;oy=tile//(width//8)*8
            frame=[]
            for y in range(8):
                for x in range(8):
                    r,g,b,a=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                    assert a==255
                    colour=tuple(round(v/17) for v in (r,g,b))
                    frame.append(min(range(4),key=lambda i:sum((palette[i][j]-colour[j])**2 for j in range(3))))
            frames.append([sum(((frame[y*8+x]>>p)&1)<<(7-x) for x in range(8)) for p in range(2) for y in range(8)])
        assert len(set(tuple(f) for f in frames[:4]))==4
        header+='static const uint8_t shenanigan_treads[8][16]={'+','.join('{'+','.join(map(str,f))+'}' for f in frames)+'};\n'
    if name=='prize':
        frames=[];masks=[];waiting=[]
        for tile in range(747,1200):
            ox=tile%(width//8)*8;oy=tile//(width//8)*8
            frame=[];mask=[]
            for y in range(8):
                colours=[];alpha=[]
                for x in range(8):
                    r,g,b,a=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                    assert a in (0,255)
                    colour=tuple(round(v/17) for v in (r,g,b)) if a else (0,0,0)
                    colours.append(min(range(4),key=lambda i:sum((palette[i][j]-colour[j])**2 for j in range(3))))
                    alpha.append(a!=0)
                frame.append(colours);mask.append(sum(alpha[x]<<(7-x) for x in range(8)))
            frames.append([sum(((frame[y][x]>>p)&1)<<(7-x) for x in range(8)) for p in range(2) for y in range(8)])
            masks.append(mask)
        ox=747%(width//8)*8;oy=747//(width//8)*8
        waiting=[sum((rgba[((oy+y)*width+ox+x)*4+3]!=0 and
                      max(rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+3])>0)<<(7-x)
                     for x in range(8))*0x01010101 for y in range(8)]+[0]*24
        header+='#define PRIZE_GATE_FRAMES 453\n'
        for symbol,values in [('prize_gate_planes',frames),('prize_gate_masks',masks)]:
            header+='static const uint8_t '+symbol+'['+str(len(values))+']['+str(len(values[0]))+']={'+','.join('{'+','.join(map(str,f))+'}' for f in values)+'};\n'
        header+='static const uint32_t prize_waiting_rows[32]={'+','.join(hex(v)+'UL' for v in waiting)+'};\n'
        header+='static const uint8_t prize_death_tile[16]={'+','.join(map(str,atlas[mapping[59]*16:mapping[59]*16+16]))+'};\n'
    (out/(name+'_assets.h')).write_text(header)
    for filename,blob in [(name+'.v6tr',display),(name+'-atlas.bin',atlas)]: (out/filename).write_bytes(blob)
    (out/(name+'-graphics.json')).write_text(json.dumps(dict(source_ids=ids,palette=colors,pairs=len(words)//16,quantized_pixels=indices,display_tiles=tiles),indent=2)+'\n')
