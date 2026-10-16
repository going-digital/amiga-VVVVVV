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
from tower_gameplay_data import export,hallway_rooms,building_room


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
    if prefix=='tower':
        tiles=building_room();allowed.update(zip(tiles[::2],tiles[1::2]))
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
        from convert_audio import export as export_audio
        export_audio(archive,out)
        export_audio(archive,out,station=True)
        from convert_teleporter_audio import export as export_teleporter_audio
        export_teleporter_audio(archive,out)
        from convert_teleporter_audio import export_prize,export_terminal
        export_prize(archive,out)
        export_terminal(archive,out)
        from firststeps_script import export as export_firststeps
        export_firststeps(archive,out)
        original=archive.read('graphics/tiles3.png')
        sprite_png=archive.read('graphics/sprites.png')
        font_png=archive.read('graphics/font.png')
        pickup_tiles=archive.read('graphics/tiles.png')
        teleporter_png=archive.read('graphics/teleporter.png')
        from energize_assets import export as export_energize_assets
        export_energize_assets(archive,out,decoder)
        from tower_gameplay_data import frown_room,shenanigan_room,prize_room,vstitch_room,deception_room,downunder_room
        export_energize_assets(archive,out,decoder,frown_room(),"frown")
        export_energize_assets(archive,out,decoder,shenanigan_room(),"shenanigan")
        export_energize_assets(archive,out,decoder,prize_room(),"prize")
        export_energize_assets(archive,out,decoder,vstitch_room(),"vstitch")
        export_energize_assets(archive,out,decoder,deception_room(),"deception")
        export_energize_assets(archive,out,decoder,downunder_room(),"downunder")
        from tower_gameplay_data import north_route_room
        for name in ('reflect','yesmen','gantry','security','linear','filter','traffic','leap','solitude','conundrum','welcome'):
            export_energize_assets(archive,out,decoder,north_route_room(name),name)
    tele_path=out/'teleporter.png';tele_path.write_bytes(teleporter_png)
    dimensions,tele_rgba=subprocess.check_output([str(decoder),str(tele_path)]).split(b'\n',1)
    tw,th=map(int,dimensions.split());assert (tw,th)==(960,96)
    # GraphicsResources loads TEX_WHITE: preserve alpha, discard source RGB.
    assert set(tele_rgba[3::4])=={0,255}
    tele_masks=[]
    for frame in range(10):
        tele_masks.append([[sum((tele_rgba[(y*tw+frame*96+c*16+x)*4+3]!=0)<<(15-x)
            for x in range(16)) for c in range(6)] for y in range(96)])
    (out/'teleporter_assets.h').write_text('static const uint16_t teleporter_masks[10][96][6]={'+
        ','.join('{'+','.join('{'+','.join(map(str,row))+'}' for row in frame)+'}' for frame in tele_masks)+'};\n')
    prepared=[]
    for frame in range(1,10):
        words=[]
        for channel in range(6):
            words.extend((100<<8|((128+112+channel*16)>>1),196<<8))
            for y in range(96):words.extend((tele_masks[0][y][channel]&~tele_masks[frame][y][channel],tele_masks[frame][y][channel]))
            words.extend((0,0))
        assert len(words)==1176;prepared.append(words)
    (out/'teleporter_prepared_assets.h').write_text('/* Private source-equivalent portal DMA at (112,48). */\nstatic const uint16_t north_portal_frames[9][1176]={'+','.join('{'+','.join(map(str,f))+'}' for f in prepared)+'};\n')
    font_path=out/'dialogue_font.png';font_path.write_bytes(font_png)
    header,font=subprocess.check_output([str(decoder),str(font_path)]).split(b'\n',1)
    fw,fh=map(int,header.split());glyphs=[]
    for ch in range(128):
        ox=ch%(fw//8)*8;oy=ch//(fw//8)*8;assert oy+8<=fh
        glyphs.append([sum((font[((oy+y)*fw+ox+x)*4+3]>127 and max(font[((oy+y)*fw+ox+x)*4:((oy+y)*fw+ox+x)*4+3])>0)<<(7-x)
            for x in range(8)) for y in range(8)])
    (out/'dialogue_font.h').write_text('static const uint8_t dialogue_font[128][8]={'+','.join('{'+','.join(map(str,row))+'}' for row in glyphs)+'};\n')
    pickup_path=out/'pickup-tiles.png';pickup_path.write_bytes(pickup_tiles)
    header,pixels=subprocess.check_output([str(decoder),str(pickup_path)]).split(b'\n',1)
    pw,ph=map(int,header.split());borders=[]
    for tile in range(40,48):
        ox=tile%(pw//8)*8;oy=tile//(pw//8)*8;assert oy+8<=ph
        # GraphicsResources.cpp TEX_WHITE retains alpha, including black RGB.
        borders.append([sum((pixels[((oy+y)*pw+ox+x)*4+3]>127)<<(7-x)
                            for x in range(8)) for y in range(8)])
    (out/'pickup_assets.h').write_text('/* Private source tiles 40..47, alpha only. */\n'
        'static const uint8_t pickup_border[8][8]={'+','.join('{'+','.join(map(str,row))+'}' for row in borders)+'};\n')
    sprite_path=out/'tower_sprites.png';sprite_path.write_bytes(sprite_png)
    sprite_header,sprite_rgba=subprocess.check_output([str(decoder),str(sprite_path)]).split(b'\n',1)
    sw,sh=map(int,sprite_header.split());frames=[]
    for tile in range(23):
        ox=(tile%(sw//32))*32;oy=(tile//(sw//32))*32
        assert oy+32<=sh
        frames.append([sum((sprite_rgba[((oy+y)*sw+ox+x)*4+3]>127 and
            max(sprite_rgba[((oy+y)*sw+ox+x)*4:((oy+y)*sw+ox+x)*4+3])>0)<<(31-x)
            for x in range(32)) for y in range(32)])
    (out/'tower_player_assets.h').write_text('static const uint32_t tower_player_rows[23][32]={\n'+
        ',\n'.join('{'+','.join(hex(v)+'UL' for v in frame)+'}' for frame in frames)+'};\n'+
        '/* Player animation frames 0..15, existing columns 6..21 in the high halfword. */\n'+
        'static const uint32_t tower_player_cropped_rows[16][32]={\n'+
        ',\n'.join('{'+','.join(hex(((v>>10)&65535)<<16)+'UL' for v in frame)+'}'
                    for frame in frames[:16])+'};\n')
    # Source Hitest uses red != 0, independently of alpha and visible RGB.
    # Keep the full 32x32 collision masks, including pixels outside hitboxes.
    def sprite_masks(tiles,collision=False):
        result=[]
        for tile in tiles:
            ox=tile%(sw//32)*32;oy=tile//(sw//32)*32
            assert oy+32<=sh
            result.append([sum((sprite_rgba[((oy+y)*sw+ox+x)*4]!=0 if collision else
                sprite_rgba[((oy+y)*sw+ox+x)*4+3]>127 and
                max(sprite_rgba[((oy+y)*sw+ox+x)*4:((oy+y)*sw+ox+x)*4+3])>0)<<(31-x)
                for x in range(32)) for y in range(32)])
        return result
    assets='/* Private source masks; red-channel collision is independent of visibility. */\n'
    for name,tiles,collision in (('return_player_collision',range(16),True),
            ('return_enemy_collision',range(92,96),True),('return_enemy_visible',range(92,96),False)):
        masks=sprite_masks(tiles,collision)
        assets+=('static const uint32_t '+name+'['+str(len(masks))+'][32]={\n'+
            ',\n'.join('{'+','.join(hex(v)+'UL' for v in mask)+'}' for mask in masks)+'};\n')
    (out/'prize_return_sprite_assets.h').write_text(assets)
    north='/* Private original north-route actor masks. */\n'
    tiles=north_route_room('yesmen')['tiles']
    def lane_wall(x,y,w=20,h=20):
        # Entity.cpp checkwall: corners, six-pixel side probes, middle column.
        div=lambda v:int(v/8)
        l,t,r,b=div(x),div(y),div(x+w-1),div(y+h-1)
        probes=[(l,t),(r,t),(l,b),(r,b)]
        for offset in range(6,19,6):
            if h<offset+6:continue
            row=div(y+offset)
            if row not in (t,b):probes.extend(((l,row),(r,row)))
        column=div(x+6)
        if w>=12 and column not in (l,r):probes.extend(((column,t),(column,b)))
        def solid(x,y):
            if x==-1:x=0
            if x==40:x=39
            if y==-1:y=0
            if y==29:y=28
            if not (0<=x<40 and 0<=y<29):return False
            tile=tiles[y*40+x]
            return tile==1 or 80<=tile<680 or tile==59
        return int(any(solid(x,y) for x,y in probes))
    north+='static const uint8_t north_yesmen_walls[3][272]={'+','.join(
        '{'+','.join(str(lane_wall(x,y)) for y in range(-16,256))+'}' for x in (122,266,194))+'};\n'

    tiles=north_route_room('traffic')['tiles']
    north+='static const uint8_t north_traffic_walls[3][272]={'+','.join(
        '{'+','.join(str(lane_wall(x,y,22,32)) for y in range(-16,256))+'}' for x in (45,205,125))+'};\n'

    tiles=north_route_room('reflect')['tiles']
    north+='static const uint8_t north_reflect_walls[3][272]={'+','.join(
        '{'+','.join(str(lane_wall(x,y,32,8)) for y in range(-16,256))+'}' for x in (135,185,235))+'};\n'
    tiles=north_route_room('gantry')['tiles']
    north+='static const uint8_t north_gantry_walls[336]={'+','.join(str(lane_wall(x,152,32,8)) for x in range(-16,320))+'};\n'

    tiles=north_route_room('linear')['tiles']
    north+='static const uint8_t north_linear_walls[2][336]={'+','.join(
        '{'+','.join(str(lane_wall(x,y,32,16)) for x in range(-16,320))+'}' for y in (88,128))+'};\n'

    for name,collision in (('north_enemy_visible',False),('north_enemy_collision',True)):
        masks=sprite_masks(range(40,44),collision)
        north+='static const uint32_t '+name+'[4][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in masks)+'};\n'
    for name,collision in (('north_drone_visible',False),('north_drone_collision',True)):
        masks=sprite_masks(range(36,40),collision)
        north+='static const uint32_t '+name+'[4][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in masks)+'};\n'
    for name,collision in (('north_traffic_visible',False),('north_traffic_collision',True)):
        masks=sprite_masks(range(28,32),collision)
        north+='static const uint32_t '+name+'[4][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in masks)+'};\n'
    for name,collision in (('north_linear_visible',False),('north_linear_collision',True)):
        masks=sprite_masks(range(32,36),collision)
        north+='static const uint32_t '+name+'[4][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in masks)+'};\n'
    north+='static const uint32_t north_terminal_visible[2][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in sprite_masks((16,17)))+'};\n'
    dims,rgba=subprocess.check_output([str(decoder),str(out/'reflect-tiles.png')]).split(b'\n',1)
    tile_width,tile_height=map(int,dims.split());gates=[];gate_colours=[]
    for tile in (*range(10,14),616):
        ox=tile%(tile_width//8)*8;oy=tile//(tile_width//8)*8;rows=[];colours=set()
        for y in range(8):
            row=0
            for x in range(8):
                r,g,b,a=rgba[((oy+y)*tile_width+ox+x)*4:((oy+y)*tile_width+ox+x)*4+4]
                if a:
                    assert a==255 and (r or g or b)
                    colours.add(((r+8)//17<<8)|((g+8)//17<<4)|((b+8)//17));row|=1<<(7-x)
            rows.append(row*0x01010101)
        assert len(colours)==1;gate_colours.append(colours.pop());gates.append(rows+[0]*24)
    north+='static const uint32_t north_platform_rows[5][32]={'+','.join('{'+','.join(hex(v)+'UL' for v in m)+'}' for m in gates)+'};\n'
    north+='static const uint16_t north_platform_colours[5]={'+','.join(hex(c) for c in gate_colours)+'};\n'
    def dma_body(mask,crop,width,height,parity):
        bits=[(v>>(16-crop))&((0xffff<<(16-width))&0xffff) for v in mask[:height]]
        return [word for v in bits for word in (v,v if parity else 0)]
    for name,masks,crops,widths,height in (
        ('north_enemy_dma',sprite_masks(range(40,44)),(0,16),(16,4),20),
        ('north_linear_dma',sprite_masks(range(32,36)),(0,16),(16,16),32),
        ('north_traffic_dma',sprite_masks(range(28,32)),(0,16),(16,6),32),
        ('north_platform_dma',gates,(0,16),(16,16),8)):
        frames=[[[dma_body(m,c,w,height,parity) for parity in (0,1)] for c,w in zip(crops,widths)] for m in masks]
        encode=lambda v:'{'+','.join(encode(a) if isinstance(a,list) else str(a) for a in v)+'}'
        north+='static const uint16_t '+name+'['+str(len(masks))+'][2][2]['+str(height*2)+']='+encode(frames)+';\n'
    for name,masks,crop,height in (('north_drone_dma',sprite_masks(range(36,40)),0,32),
                                  ('north_player_dma',sprite_masks(range(16)),6,32),
                                  ('north_checkpoint_dma',sprite_masks((20,21)),0,16),
                                  ('north_terminal_dma',sprite_masks((16,17)),0,16),
                                  ('north_crew_dma',sprite_masks((150,)),6,32)):
        values=[[dma_body(m,crop,16,height,parity) for parity in (0,1)] for m in masks]
        north+='static const uint16_t '+name+'['+str(len(masks))+'][2]['+str(height*2)+']='+encode(values)+';\n'
    (out/'north_actor_assets.h').write_text(north)
    from convert_terminal_layer import build as export_terminal_layer
    export_terminal_layer(out)
    # AI 17 remains still, tile 144 (sad), facing left: visual frame 147.
    # Export just this required frame rather than a full crew sprite sheet.
    tile=147;ox=(tile%(sw//32))*32;oy=(tile//(sw//32))*32
    assert oy+32<=sh
    crew=[sum((sprite_rgba[((oy+y)*sw+ox+x)*4+3]>127 and
        max(sprite_rgba[((oy+y)*sw+ox+x)*4:((oy+y)*sw+ox+x)*4+3])>0)<<(31-x)
        for x in range(32)) for y in range(32)]
    assert all(not (row & ~(((1<<16)-1)<<(32-6-16))) for row in crew), 'Crew crop loses source pixels'
    with (out/'tower_player_assets.h').open('a') as header:
        header.write('static const uint32_t tower_crew_rows[32]={'+','.join(hex(v)+'UL' for v in crew)+'};\n')
    tile=150;ox=(tile%(sw//32))*32;oy=(tile//(sw//32))*32
    yellow=[sum((sprite_rgba[((oy+y)*sw+ox+x)*4+3]>127 and
        max(sprite_rgba[((oy+y)*sw+ox+x)*4:((oy+y)*sw+ox+x)*4+3])>0)<<(31-x)
        for x in range(32)) for y in range(32)]
    assert all(not (row & ~(((1<<16)-1)<<(32-6-16))) for row in yellow)
    with (out/'tower_player_assets.h').open('a') as header:
        header.write('static const uint32_t station_crew_rows[32]={'+','.join(hex(v)+'UL' for v in yellow)+'};\n')
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
    # Static hallway banks share the existing one-plane background pattern.
    # Prove every source pixel of its six tile IDs has the expected dark tint
    # or grey detail before the native renderer uses those Copper colours.
    hallway_background_checks=0
    for bank,base in ((15,(0,1,1)),(10,(0,1,0))):
        for tile in range(6):
            index=bank*30+tile;ox=(index%(width//8))*8;oy=(index//(width//8))*8
            for y in range(8):
                for x in range(8):
                    r,g,b,a=rgba[((oy+y)*width+ox+x)*4:((oy+y)*width+ox+x)*4+4]
                    colour=tuple(round(v*a/255/17) for v in (r,g,b))
                    expected=(1,1,1) if (backdrop[tile*8+y]>>(7-x))&1 else base
                    assert colour==expected,(bank,tile,x,y,colour,expected)
                    hallway_background_checks+=1
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
        hallway_background_pixel_checks=hallway_background_checks,
        palette=colors,source_ocs_colours=len(set(c for tile in pixels for c in tile)),pixel_checks=checks,cameras=cameras,
        scope='Actual tiles3 colour bank, alpha baked onto black and four-colour quantization; C planar ring vs converted pixels. Host only, no Copper/DMA, parallax, colour cycling or gameplay.')
    (out/'tower-assets.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS:',json.dumps(report))
    from pack_regions import build as build_regions
    build_regions(out)


if __name__=='__main__':main()
