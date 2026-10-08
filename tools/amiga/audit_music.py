#!/usr/bin/env python3
"""Source music catalogue and conservative four-channel ProTracker intake audit.

This measures MOD storage/activity, not LSP output size, timing or compatibility.
Blank channels still require cooperation from the actual replay driver.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
ROOT=Path(__file__).resolve().parents[2]

def catalogue():
    header=(ROOT/'desktop_version/src/Music.h').read_text()
    names=re.findall(r'(Music_\w+)\s*=\s*(\d+)',header)
    files=re.findall(r'FOREACH_TRACK\(blob, "([^"]+)"\)',(ROOT/'desktop_version/src/BinaryBlob.h').read_text())
    source=(ROOT/'desktop_version/src/Music.cpp').read_text()
    play=source[source.index('bool musicclass::play(int t)'):source.index('bool musicclass::playid')]
    special=play[play.index('if (currentsong == Music_PATHCOMPLETE'):play.index('// No fade in or repeat')]
    one_shots=set(re.findall(r'Music_\w+',special))
    assert len(names)==len(files)==16 and [int(n) for _,n in names]==list(range(16))
    area=re.search(r'static const int areamap\[\] = \{(.*?)\};',source,re.S)
    areas=[int(n) for n in re.findall(r'-?\d+',area[1])]
    assert len(areas)==400 and all(-3<=n<16 for n in areas)
    return dict(version=1,tracks=[dict(id=int(n),symbol=name,source_file=file,
        module_file=f'{int(n):02d}.mod',loop=name not in one_shots)
        for (name,n),file in zip(names,files)],area_map=areas,
        source_sha256={name:hashlib.sha256((ROOT/'desktop_version/src'/name).read_bytes()).hexdigest()
        for name in ('Music.h','Music.cpp','BinaryBlob.h')},
        player='Lightspeedplayer; integration pending',
        scope='Base soundtrack IDs and loop policy; alternate soundtrack/custom assets excluded')

def audit(data,reserved_mask=0):
    if not 0<=reserved_mask<=15:raise ValueError('reserved mask must be 0..15')
    if len(data)<1084:raise ValueError('truncated MOD header')
    if data[1080:1084] not in (b'M.K.',b'M!K!'):raise ValueError('expected 31-instrument four-channel ProTracker MOD')
    orders=data[950]
    if not 1<=orders<=128:raise ValueError('invalid song length')
    order_table=list(data[952:1080])
    if max(order_table)>127:raise ValueError('invalid pattern index')
    patterns=max(order_table)+1;sample_offset=1084+patterns*1024
    samples=[]
    for i in range(31):
        at=20+i*30
        length=struct.unpack_from('>H',data,at+22)[0]*2
        fine,volume=data[at+24:at+26]
        start,loop=struct.unpack_from('>HH',data,at+26);start*=2;loop*=2
        if fine>15 or volume>64:raise ValueError('invalid sample tuning or volume')
        if loop>2 and start+loop>length:raise ValueError('sample loop exceeds sample data')
        samples.append(dict(id=i+1,bytes=length,loop_start=start,loop_bytes=loop))
    total=sum(s['bytes'] for s in samples)
    if len(data)<sample_offset+total:raise ValueError('truncated pattern/sample data')
    used=sorted(set(order_table[:orders]));activity=[0]*4;effects=set();instruments=set()
    # Inspect all stored patterns for malformed instrument references, but count
    # activity only in the song's order list. No reachability/tempo simulation.
    for pattern in range(patterns):
        for row in range(64):
            for channel in range(4):
                at=1084+pattern*1024+row*16+channel*4
                a,b,c,d=data[at:at+4];instrument=(a&240)|(c>>4)
                if instrument>31:raise ValueError('invalid instrument reference')
                if pattern not in used:continue
                if instrument:instruments.add(instrument)
                if a or b or c or d:activity[channel]+=1
                if (c&15) or d:effects.add(c&15)
    mask=sum(1<<i for i,n in enumerate(activity) if n)
    return dict(sha256=hashlib.sha256(data).hexdigest(),file_bytes=len(data),
        orders=orders,stored_patterns=patterns,ordered_patterns=used,
        sample_bytes=total,pattern_bytes=patterns*1024,trailing_bytes=len(data)-sample_offset-total,
        instruments_used=sorted(instruments),effect_commands=sorted(effects),
        channel_event_counts=activity,active_mask=mask,reserved_mask=reserved_mask,
        conflicting_channels=[i for i in range(4) if mask&reserved_mask&(1<<i)],samples=samples,
        scope='MOD sample bytes are not converted LSP bank bytes; static activity is not replay safety or peak CPU evidence')

def main():
    p=argparse.ArgumentParser();p.add_argument('--module',type=Path,action='append',default=[])
    p.add_argument('--reserved-mask',type=lambda s:int(s,0),default=0)
    p.add_argument('--out',type=Path,default=ROOT/'build/amiga-music/music-intake.json')
    args=p.parse_args()
    if not 0<=args.reserved_mask<=15:p.error('--reserved-mask must be 0..15')
    report=catalogue();report['modules']=[]
    for path in args.module:
        try:entry=audit(path.read_bytes(),args.reserved_mask)
        except (OSError,ValueError) as exc:p.error(f'{path}: {exc}')
        entry['file']=str(path);report['modules'].append(entry)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,indent=2)+'\n')
    print(f'Music intake: {len(report["tracks"])} source tracks, {len(report["modules"])} modules audited; {args.out}')
if __name__=='__main__':main()
