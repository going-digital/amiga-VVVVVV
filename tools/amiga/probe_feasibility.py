#!/usr/bin/env python3
"""Measure real tower rows and user-owned music; no target timing claims."""
import argparse
import ctypes as C
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import zipfile
from pack_rooms import ROOT, encode
from convert_assets import DEFAULT_DATA


def tower_probe(out):
    source=(ROOT/'desktop_version/src/Tower.cpp').read_text()
    functions={'loadmap':700,'loadbackground':120,'loadminitower1':100,'loadminitower2':100}
    library=out/'row_codec.so'
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-fsanitize=undefined',
                    '-fno-sanitize-recover=all',str(ROOT/'amiga_version/room_codec.c'),'-o',str(library)],check=True)
    decoder=C.CDLL(str(library)).v6_unpack_room
    decoder.argtypes=[C.c_char_p,C.c_size_t,C.POINTER(C.c_uint16),C.c_size_t]
    decoder.restype=C.c_int
    maps=[]
    for name,height in functions.items():
        body=source[source.index('void towerclass::'+name+'('):]
        match=re.search(r'static const short tmap\[\]\s*=\s*\{(.*?)\};',body,re.S)
        text=re.sub(r'//[^\n]*|/\*.*?\*/','',match[1],flags=re.S)
        assert re.fullmatch(r'[\s\d,]+',text)
        tiles=[int(x) for x in text.split(',') if x.strip()]
        assert len(tiles)==40*height
        rows=[tiles[y*40:(y+1)*40] for y in range(height)]
        payload=bytearray();directory=bytearray();seen={};packets=[]
        for row in rows:
            packet=encode(row);packets.append(packet)
            if packet not in seen:
                seen[packet]=len(payload);payload.extend(packet)
            directory.extend(struct.pack('>IH',seen[packet],len(packet)))
            decoded=(C.c_uint16*40)()
            assert decoder(packet,len(packet),decoded,40)==1 and list(decoded)==row
        # V6TR v1: magic/version/width/height, then height offset/length entries.
        blob=struct.pack('>4sHHH',b'V6TR',1,40,height)+directory+payload
        (out/(name+'.v6tr')).write_bytes(blob)
        # Exercise a 32-row ring, including wraps, reverse scrolling and jumps.
        cache={};loaded=0;worst=0;worst_packet=0;normal_rows=0;normal_bytes=0;camera=0;checks=0
        for tick in range(6000):
            camera+= (0,1,4,8,16,-1,-4,-8,-16)[(tick//61)%9]
            if tick%997==0:camera+=height*8-37
            # C++ truncates the pixel coordinate toward zero before POS_MOD.
            needed={int((camera+y*8)/8)%height for y in range(31)}
            missing=needed-cache.keys();cost=0
            for y in missing:
                offset,length=struct.unpack_from('>IH',blob,10+y*6)
                packet=blob[10+height*6+offset:10+height*6+offset+length]
                dst=(C.c_uint16*40)()
                assert decoder(packet,len(packet),dst,40)==1
                cache[y]=list(dst);cost+=length;loaded+=1
            cache={y:cache[y] for y in needed}
            assert len(cache)<=32
            for y in needed:assert cache[y]==rows[y];checks+=1
            if tick and tick%997:
                normal_rows=max(normal_rows,len(missing));normal_bytes=max(normal_bytes,cost)
            worst=max(worst,len(missing));worst_packet=max(worst_packet,cost)
        maps.append(dict(name=name,rows=height,raw_bytes=len(tiles)*2,max_tile=max(tiles),
            packed_bytes=len(blob),directory_bytes=len(directory),unique_rows=len(seen),
            max_row_packet_bytes=max(map(len,packets)),decoded_rows=loaded,
            ring_checks=checks,normal_max_refill_rows=normal_rows,normal_max_refill_bytes=normal_bytes,max_refill_rows=worst,max_refill_packet_bytes=worst_packet,
            sha256=hashlib.sha256(blob).hexdigest()))
    return dict(source_sha256=hashlib.sha256(source.encode()).hexdigest(),maps=maps,ring_tile_bytes=32*40*2,
        proposed_planar_ring_bytes=320*256*2//8,
        proposed_double_planar_ring_bytes=2*320*256*2//8,
        scope='Literal source rows; C decoder and host cache checks only. Camera input is synthetic. No Copper wrap, blitter, tower entities, parallax or A500 timing.')


def music_probe(data,out,track):
    # BinaryBlob.h: 128 records of 48-byte name, two int32 fields, valid byte,
    # three padding bytes. Payloads follow sequentially; start is unused.
    with zipfile.ZipFile(data) as archive:blob=archive.read('vvvvvvmusic.vvv')
    offset=128*60;tracks=[];selected=None
    for i in range(128):
        name,unused,size,valid=struct.unpack_from('<48siiB',blob,i*60)
        if valid==0:break
        assert valid==1 and size>0 and offset+size<=len(blob)
        name=name.split(b'\0',1)[0].decode('utf8')
        content=blob[offset:offset+size];assert content.startswith(b'OggS')
        tracks.append(dict(name=name,ogg_bytes=size))
        if name.endswith('/'+track):selected=content
        offset+=size
    assert offset==len(blob),'Unexpected archive tail; inspect format before accepting'
    assert selected is not None,track
    original=out/'music-source.ogg';original.write_bytes(selected)
    info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(original)]))
    duration=float(info['format']['duration'])
    conversions=[]
    for rate in (8000,11025,14000):
        pcm=out/f'music-{rate}.s8'
        subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(original),'-ac','1','-ar',str(rate),'-c:a','pcm_s8','-f','s8',str(pcm)],check=True)
        size=pcm.stat().st_size
        # Listening preview, converted back from the exact signed 8-bit stream.
        preview=out/f'music-{rate}-preview.wav'
        subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-f','s8','-ar',str(rate),'-ac','1','-i',str(pcm),'-t','20',str(preview)],check=True)
        period=round(3546895/rate)
        conversions.append(dict(rate=rate,pcm_bytes=size,bytes_per_second=rate,
            double_4096_buffer_bytes=8192,refill_deadline_seconds=4096/rate,
            paula_period_pal=period,actual_pal_rate=3546895/period,
            exceeds_whole_1MiB=size>1048576,sha256=hashlib.sha256(pcm.read_bytes()).hexdigest()))
    excerpt=(out/'music-11025.s8').read_bytes()[:8*11025]
    assert len(excerpt)==88200
    (out/'music_probe.h').write_text('/* Private user-supplied music excerpt; do not distribute. */\n'
        '#define MUSIC_PROBE_BYTES 88200\nstatic const unsigned char music_probe[] = {'
        +','.join(map(str,excerpt))+'};\n')
    return dict(track=track,archive_bytes=len(blob),tracks=tracks,source_duration_seconds=duration,
        source_streams=info['streams'],conversions=conversions,
        scope='Offline full-song conversion and storage/buffer arithmetic. No Paula music playback, disk I/O deadline measurement, compression decoder, loop/fade handling or quality approval.')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data',type=Path,default=DEFAULT_DATA)
    parser.add_argument('--out',type=Path,default=ROOT/'build/amiga-feasibility')
    parser.add_argument("--music",action="store_true",help="Optional historical PCM experiment; tracker playback is the working plan")
    parser.add_argument('--track',default='1pushingonwards.ogg')
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    report=dict(tower=tower_probe(args.out))
    if args.music:report['music']=music_probe(args.data,args.out,args.track)
    report_name='feasibility.json' if args.music else 'tower-feasibility.json'
    (args.out/report_name).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
