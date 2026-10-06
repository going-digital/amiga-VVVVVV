#!/usr/bin/env python3
"""Private tower graphics conversion and host-rendered ring validation."""
import argparse
from collections import Counter
import ctypes as C
import hashlib
import json
import re
from pathlib import Path
import struct
import subprocess
import zipfile
from convert_assets import DEFAULT_DATA
from pack_rooms import ROOT
from probe_feasibility import tower_probe
from test_tower_stream import Stream
from test_tower_draw import Draw
from tower_gameplay_data import export,hallway_rooms


def paired_atlas(out,atlas,planes,names,prefix):
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text();allowed=set()
    for name in names:
        body=source[source.index('void towerclass::'+name+'('):]
        raw=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',body,re.S)[1]
        raw=re.sub(r'//[^\n]*|/\*.*?\*/','',raw,flags=re.S)
        tiles=[int(v) for v in raw.split(',') if v.strip()]
        allowed.update(zip(tiles[::2],tiles[1::2]))
    if prefix=='tower':
        for room in hallway_rooms():
            allowed.update(zip(room['tiles'][::2],room['tiles'][1::2]))
    offsets=[65535]*1024;patterns={};words=[]
    for a,b in sorted(allowed):
        assert a<30 and b<30
        pattern=tuple(atlas[a*planes*8+p*8+y]*256+atlas[b*planes*8+p*8+y]
            for p in range(planes) for y in range(8))
        if pattern not in patterns:
            patterns[pattern]=len(words);words.extend(pattern)
        offsets[a*32+b]=patterns[pattern]
    assert len(words)<65535
    (out/(prefix+'_pairs.h')).write_text(
        'static const uint16_t '+prefix+'_pair_offsets[1024]={'+','.join(map(str,offsets))+'};\n'+
        'static const uint16_t '+prefix+'_pairs['+str(len(words))+']={'+','.join(map(str,words))+'};\n'+
        '#define '+prefix.upper()+'_PAIR_WORDS '+str(len(words))+'\n')
    return dict(pairs=len(allowed),patterns=len(patterns),bytes=2*(1024+len(words)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=DEFAULT_DATA)
    parser.add_argument('--out',type=Path,default=ROOT/'build/amiga-feasibility')
    parser.add_argument('--bank',type=int,default=0)
    args=parser.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
    maps=tower_probe(out)
    export(out)
    decoder=out/'png_rgba'
    subprocess.run(['c++','-O2','-I'+str(ROOT/'third_party/lodepng'),str(ROOT/'tools/amiga/png_rgba.cpp'),
                    str(ROOT/'third_party/lodepng/lodepng.cpp'),'-o',str(decoder)],check=True)
    with zipfile.ZipFile(args.data) as archive:
        original=archive.read('graphics/tiles3.png')
        sprite_png=archive.read('graphics/sprites.png')
    sprite_path=out/'tower_sprites.png';sprite_path.write_bytes(sprite_png)
    sprite_header,sprite_rgba=subprocess.check_output([str(decoder),str(sprite_path)]).split(b'\n',1)
    sw,sh=map(int,sprite_header.split());frames=[]
    for tile in range(22):
        ox=(tile%(sw//32))*32;oy=(tile//(sw//32))*32
        assert oy+32<=sh
        frames.append([sum((sprite_rgba[((oy+y)*sw+ox+x)*4+3]>127 and
            max(sprite_rgba[((oy+y)*sw+ox+x)*4:((oy+y)*sw+ox+x)*4+3])>0)<<(31-x)
            for x in range(32)) for y in range(32)])
    (out/'tower_player_assets.h').write_text('static const uint32_t tower_player_rows[22][32]={\n'+
        ',\n'.join('{'+','.join(hex(v)+'UL' for v in frame)+'}' for frame in frames)+'};\n')
    path=out/'tiles3.png';path.write_bytes(original)
    header,rgba=subprocess.check_output([str(decoder),str(path)]).split(b'\n',1)
    width,height=map(int,header.split());assert len(rgba)==width*height*4
    assert width%8==height%8==0
    assert 0<=args.bank and (args.bank+1)*30<=width*height//64
    assert all(m['max_tile']<30 for m in maps['maps'])
    pixels=[];opacity=[]
    for tile in range(args.bank*30,(args.bank+1)*30):
        ox=(tile%(width//8))*8;oy=(tile//(width//8))*8
        row=[];opaque=[]
        for y in range(8):
            for x in range(8):
                r,g,b,a=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                assert a in (0,255), 'Partial alpha needs an explicit compositing policy'
                opaque.append(int(a==255 and tile%30!=0))
                row.append(tuple(round(v*a/255/17) for v in (r,g,b)))
        pixels.append(row);opacity.append(opaque)
    counts=Counter(c for tile in pixels for c in tile if c!=(0,0,0))
    palette=[(0,0,0)]+[c for c,_ in counts.most_common(3)]
    palette+=[(0,0,0)]*(4-len(palette))
    indices=[[min(range(4),key=lambda i:sum((palette[i][j]-c[j])**2 for j in range(3))) for c in tile] for tile in pixels]
    atlas=bytes(sum(((tile[y*8+x]>>plane)&1)<<(7-x) for x in range(8))
                for tile in indices for plane in range(2) for y in range(8))
    masks=bytes(sum(tile[y*8+x]<<(7-x) for x in range(8)) for tile in opacity for y in range(8))
    (out/'tower_masks.bin').write_bytes(masks)
    (out/'tower_tiles.bin').write_bytes(atlas)
    colors=[r<<8|g<<4|b for r,g,b in palette]
    (out/'tower_assets.h').write_text('/* Private converted graphics; do not redistribute. */\n'
        '#define TOWER_TILE_COUNT 30\n#define TOWER_COLOUR_BANK '+str(args.bank)+'\n'
        'static const unsigned short tower_palette[4]={'+','.join(hex(c) for c in colors)+'};\n'
        'static const unsigned char tower_tiles[480]={'+','.join(map(str,atlas))+'};\n')
    # One-plane backdrop: threshold source OCS intensity, independent of the
    # foreground palette reduction (which otherwise loses these dark details).
    backdrop=bytes(sum(int(sum(tile[y*8+x])>=3)<<(7-x) for x in range(8))
                   for tile in pixels for y in range(8))
    pair_report={'foreground':paired_atlas(out,atlas,2,('loadmap','loadminitower1','loadminitower2'),'tower'),
                 'background':paired_atlas(out,backdrop,1,('loadbackground',),'tower_background')}
    (out/'tower-pairs.json').write_text(json.dumps(pair_report,indent=2)+'\n')
    (out/'tower_backdrop.bin').write_bytes(backdrop)
    (out/'tower_backdrop.h').write_text('static const unsigned char tower_backdrop[240]={'
        +','.join(map(str,backdrop))+'};\n')
    blob=(out/'loadbackground.v6tr').read_bytes()
    (out/'tower_background_map.h').write_text('static const unsigned char tower_background_map[]={'
        +','.join(map(str,blob))+'};\n')
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC',
        '-fsanitize=undefined','-fno-sanitize-recover=all',
        *[str(ROOT/'amiga_version'/f) for f in ('tower_draw.c','tower_stream.c','room_codec.c')],
        '-o',str(out/'tower_graphics.so')],check=True)
    core=C.CDLL(str(out/'tower_graphics.so'));bp=C.POINTER(C.c_uint8)
    core.v6_tower_open.argtypes=[C.POINTER(Stream),C.c_char_p,C.c_size_t]
    core.v6_tower_draw_prepare.argtypes=[C.POINTER(Draw),bp,C.POINTER(Stream),C.c_int,bp,C.c_uint,C.c_void_p,C.c_void_p]
    blob=(out/'loadmap.v6tr').read_bytes();stream=Stream();assert core.v6_tower_open(C.byref(stream),blob,len(blob))
    ring=(C.c_uint8*20480)();draw=Draw();tiles=(C.c_uint8*480).from_buffer_copy(atlas)
    # Decode reference rows independently in Python from the file format.
    def row_values(row):
        row%=stream.height;offset,length=struct.unpack_from('>IH',blob,10+row*6)
        base=10+stream.height*6
        packet=blob[base+offset:base+offset+length];values=[];pos=0
        while pos<len(packet):
            token=struct.unpack_from('>H',packet,pos)[0];pos+=2;count=token&32767
            if token&32768:
                values += [struct.unpack_from('>H',packet,pos)[0]]*count;pos+=2
            else:
                values += list(struct.unpack_from('>'+str(count)+'H',packet,pos));pos+=2*count
        assert len(values)==40
        return values
    checks=0
    cameras=(0,1,7,8,249,255,256,5599,5600)
    for camera in cameras:
        assert core.v6_tower_draw_prepare(C.byref(draw),ring,C.byref(stream),camera//8,tiles,30,None,None)
        rgb=bytearray()
        for y in range(240):
            world_y=camera+y;row=row_values(world_y//8)
            for x in range(320):
                addr=(world_y&255)*40+x//8;bit=7-x%8
                index=((ring[addr]>>bit)&1)|(((ring[10240+addr]>>bit)&1)<<1)
                assert index==indices[row[x//8]][(world_y%8)*8+x%8]
                rgb.extend(v*17 for v in palette[index]);checks+=1
        if camera in (0,255,5599):
            ppm=out/f'tower-camera-{camera}.ppm';ppm.write_bytes(b'P6\n320 240\n255\n'+rgb)
            subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(ppm),'-frames:v','1',str(out/f'tower-camera-{camera}.png')],check=True)
    report=dict(bank=args.bank,source_sha256=hashlib.sha256(original).hexdigest(),atlas_bytes=len(atlas),
        palette=colors,source_ocs_colours=len(set(c for tile in pixels for c in tile)),pixel_checks=checks,cameras=cameras,
        scope='Actual tiles3 colour bank, alpha baked onto black and four-colour quantization; C planar ring vs converted pixels. Host only, no Copper/DMA, parallax, colour cycling or gameplay.')
    (out/'tower-assets.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))


if __name__=='__main__':main()
