#!/usr/bin/env python3
"""Reviewed mutable setup guard and independent PNG masks for Prize actors."""
import argparse,re,struct,subprocess
from pathlib import Path
from pack_rooms import ROOT,prize_record,extract

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build',type=Path,required=True)
    args=parser.parse_args();build=args.build.resolve()
    source=(ROOT/'desktop_version/src/Spacestation2.cpp').read_text()
    start=source.index('case rn(49,43):');end=source.index('case rn(',start+5)
    body=source[start:end]
    meta,raw,_=prize_record();tiles=struct.unpack('>1200H',raw)
    assert len(tiles)==1200 and max(tiles)==1122 and meta['mode']=='normal'
    assert all(tiles[x+8*40]==9 for x in range(23,37))
    assert all(r[0]['enclosing_label']!='case rn(49,43)' for r in extract()
               if r[0]['source'].endswith('/Spacestation2.cpp'))
    mutations=(('static short contents[]','static const short contents[]'),
        ('120, 72, 3, 747','120, 80, 3, 747'),('120, 112, 3, 747','120, 112, 3, 707'),
        ('120, 128, 3, 747','120, 128, 3, 707'),('88, 72, 2, 15, 4','88, 72, 2, 15, 5'),
        ('192, 128, 9, 6','192, 128, 9, 7'),('240, 136, 10, 0, 443490','240, 136, 10, 1, 443490'),
        ('obj.platformtile = 747','obj.platformtile = 707'),('23+14','23+13'),
        ('? 0 : 9','? 9 : 0'),('result = contents;','obj.createentity(1,2,3); result = contents;'))
    for a,b in mutations:
        assert a in body
        altered=source[:start]+body.replace(a,b,1)+source[end:]
        try:prize_record(altered)
        except ValueError:pass
        else:raise AssertionError((a,b))
    header=(build/'prototype_assets.h').read_text()
    def matrix(name):
        match=re.search(r'\b'+name+r'\[\d+\]\[\d+\]\s*=\s*\{(.*?)\};',header,re.S)
        assert match,name
        return [[int(x.strip().removesuffix('UL'),0) for x in row.split(',')]
                for row in re.findall(r'\{([^}]+)\}',match[1])]
    def png(name):
        info,data=subprocess.check_output([str(build/'png_rgba'),str(build/name)]).split(b'\n',1)
        w,h=map(int,info.split());assert len(data)==w*h*4
        return w,h,data
    w,h,rgba=png('tiles.png');checks=0
    disappearing=matrix('disappearing_tiles')
    def mask(tile,row):
        ox,oy=tile%(w//8)*8,tile//(w//8)*8
        return sum((rgba[((oy+row)*w+ox+x)*4+3]>127 and
                    max(rgba[((oy+row)*w+ox+x)*4:((oy+row)*w+ox+x)*4+3])>0)<<(7-x) for x in range(8))
    assert len(disappearing)==w//8*(h//8)-747
    for frame,rows in enumerate(disappearing):
        for row,value in enumerate(rows):
            assert value==mask(747+frame,row);checks+=8
    platform=re.search(r'platform_rows\[32\]\s*=\s*\{([^}]+)\}',header)
    rows=[int(x.strip().removesuffix('UL'),0) for x in platform[1].split(',')]
    assert rows[:8]==[mask(747,y)*0x01010101 for y in range(8)] and not any(rows[8:]);checks+=256
    w,h,rgba=png('sprites.png');ox,oy=22%(w//32)*32,22//(w//32)*32
    sprite=matrix('sprite_rows')[22]
    for row,value in enumerate(sprite):
        expected=sum((rgba[((oy+row)*w+ox+x)*4+3]>127 and
                      max(rgba[((oy+row)*w+ox+x)*4:((oy+row)*w+ox+x)*4+3])>0)<<(31-x) for x in range(32))
        assert value==expected
        assert not(value&0xffff) and (row<16 or value==0);checks+=32
    assert '#define TRINKET_SOUND_BYTES 5866' in header
    print(f'PASS Prize export: 1200 normal-mode tiles, {len(mutations)} rejected setup mutations, {checks} independent actor-mask pixels')
if __name__=='__main__':main()
