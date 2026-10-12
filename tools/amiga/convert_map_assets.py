#!/usr/bin/env python3
"""Private original minimap/fog conversion to a shared OCS palette."""
import argparse,ctypes as C,json,subprocess,zipfile
from pathlib import Path
from convert_assets import DEFAULT_DATA
from pack_rooms import ROOT

def build(data,out):
    out.mkdir(parents=True,exist_ok=True)
    decoder=ROOT/'build/amiga-feasibility/png_rgba'
    if not decoder.exists():
        decoder.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['c++','-O2','-I'+str(ROOT/'third_party/lodepng'),str(ROOT/'tools/amiga/png_rgba.cpp'),str(ROOT/'third_party/lodepng/lodepng.cpp'),'-o',str(decoder)],check=True)
    palette=[0];palette.extend([None]*31)
    palette[17]=0xfff  # Sprite 0 cursor colour; no bitmap pixel uses this slot.
    def index(rgb):
        colour=sum(((v+8)//17)<<(8-4*i) for i,v in enumerate(rgb))
        if colour in palette and palette.index(colour)!=17:return palette.index(colour)
        at=palette.index(None);palette[at]=colour;return at
    arrays={}
    with zipfile.ZipFile(data) as z:
        def png(name):
            path=out/Path(name).name;path.write_bytes(z.read(name))
            header,pixels=subprocess.check_output([str(decoder),str(path)]).split(b'\n',1)
            return tuple(map(int,header.split())),pixels
        for name,size in [('minimap',(240,180)),('covered',(12,9))]:
            p=out/(name+'.png');p.write_bytes(z.read('graphics/'+name+'.png'))
            header,pixels=subprocess.check_output([str(decoder),str(p)]).split(b'\n',1)
            assert tuple(map(int,header.split()))==size
            assert all(pixels[i]==255 for i in range(3,len(pixels),4))
            arrays[name]=[index(pixels[i:i+3]) for i in range(0,len(pixels),4)]
        (fw,fh),font_pixels=png('graphics/font.png');font=[]
        for ch in range(128):
            ox=ch%(fw//8)*8;oy=ch//(fw//8)*8;assert oy+8<=fh
            for y in range(8):
                font.append(sum((font_pixels[((oy+y)*fw+ox+x)*4+3]>127 and max(font_pixels[((oy+y)*fw+ox+x)*4:((oy+y)*fw+ox+x)*4+3])>0)<<(7-x) for x in range(8)))
        (tw,th),tiles=png('graphics/tiles.png');border=[]
        for tile in range(40,48):
            ox=tile%(tw//8)*8;oy=tile//(tw//8)*8;assert oy+8<=th
            for y in range(8):border.append(sum((tiles[((oy+y)*tw+ox+x)*4+3]>127)<<(7-x) for x in range(8)))
    semantic=[index(c) for c in ((0,0,0),(10,24,26),(65//6,185//6,207//6),(65,185,207),(196,196,255),(64,64,64))]
    palette=[p if p is not None else 0 for p in palette]
    text='#include <stdint.h>\n/* Private user-supplied graphics, never committed. Palette 17 is cursor-only. */\n'
    for name,values in arrays.items():text+=f'static const uint8_t map_{name}[{len(values)}]={{'+','.join(map(str,values))+'};\n'
    packed=[];offsets=[]
    for row in range(180):
        offsets.append(len(packed));line=arrays['minimap'][row*240:(row+1)*240];start=0
        for x in range(1,241):
            if x==240 or line[x]!=line[start]:packed.extend((x-start,line[start]));start=x
    offsets.append(len(packed))
    text+='static const uint8_t map_minimap_rle['+str(len(packed))+']={'+','.join(map(str,packed))+'};\n'
    text+='static const uint16_t map_minimap_offsets[181]={'+','.join(map(str,offsets))+'};\n'
    text+='static const uint16_t map_palette[32]={'+','.join(hex(c) for c in palette)+'};\n'
    text+='static const uint8_t map_ui_colours[6]={'+','.join(map(str,semantic))+'};\n'
    # Pack the source-equivalent all-revealed menu offline. The portable
    # renderer is checked against extracted desktop statements in the suite.
    library=out/'map_packer.so'
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC',str(ROOT/'amiga_version/map_draw.c'),'-o',str(library)],check=True)
    lib=C.CDLL(str(library));bp=C.POINTER(C.c_uint8)
    lib.v6_map_draw_row.argtypes=[bp,C.c_uint,bp,bp,bp,bp,bp,bp,C.c_char_p]
    mini=(C.c_uint8*43200)(*arrays['minimap']);fog=(C.c_uint8*108)(*arrays['covered'])
    glyphs=(C.c_uint8*1024)(*font);borders=(C.c_uint8*64)(*border);colours=(C.c_uint8*6)(*semantic)
    explored=(C.c_uint8*50)(*([255]*50));row=(C.c_uint8*200)();template=[];template_offsets=[]
    for y in range(240):
        assert lib.v6_map_draw_row(row,y,explored,mini,fog,glyphs,borders,colours,b'V Stitch')
        template_offsets.append(len(template));start=0
        for x in range(1,201):
            if x==200 or row[x]!=row[start]:template.extend((x-start,row[start]));start=x
    template_offsets.append(len(template));assert len(template)<65536
    text+='static const uint8_t map_template_rle['+str(len(template))+']={'+','.join(map(str,template))+'};\n'
    text+='static const uint16_t map_template_offsets[241]={'+','.join(map(str,template_offsets))+'};\n'
    fog_bits=[[sum(((arrays['covered'][y*12+x]>>p)&1)<<(15-x) for x in range(12)) for p in range(5)] for y in range(9)]
    text+='static const uint16_t map_fog_bits[9][5]={'+','.join('{'+','.join(map(str,r))+'}' for r in fog_bits)+'};\n'
    (out/'map_assets.h').write_text(text)
    (out/'map-assets.json').write_text(json.dumps(dict(palette=palette,semantic=semantic,colours=len(set(palette)),packed_template_bytes=len(template),template_offsets_bytes=482,fog_mask_bytes=90,source='Original minimap.png and covered.png; nearest RGB12 component quantization, no colour reduction; V Stitch template at source glow=0.'),indent=2)+'\n')
    print('Map assets:',len(set(palette)),'OCS colours;',len(template),'packed template bytes; sprite palette slot 17 reserved')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,default=DEFAULT_DATA);p.add_argument('--out',type=Path,default=ROOT/'build/amiga-feasibility');a=p.parse_args();build(a.data,a.out)
