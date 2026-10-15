#!/usr/bin/env python3
"""Physical Return/read/advance/map/save checks in the live north campaign."""
import argparse
import json
import os
import subprocess
from pathlib import Path
import struct
from run_map_input import capture
from run_interactive_save import config
from run_tower_probe import EMU
from run_copperline import audio_peak
from test_map_draw import arrays
from save_disk import create_save_disk
from test_player import ROOT

FIELDS=('opens closes cues activity_w activity_h clipped warm_stage warm_row '
        'bitmap caption world copper bars visible phase flips control enemy0 enemy1 pcm_bytes').split()

def read(data):
    at=data.index(b'V6NR\0\0\0\1')
    return dict(zip(FIELDS,struct.unpack_from('>20I',data,at+8)))

def sprite_windows(chip,registers):
    masked=0
    for channel in range(8):
        reg=0x120+channel*4;at=(registers[reg]<<16)|registers[reg+2];end=at+392
        while at+4<=end:
            pos,control=struct.unpack_from('>HH',chip,at)
            if not(pos|control):break
            first=(pos>>8)|((control&4)<<6);last=(control>>8)|((control&2)<<7)
            assert first<last<=268 and last-first<=32
            assert at+4+(last-first)*4<=end
            for y in range(first,last):
                if 112<=y<136 or 138<=y<207:
                    assert chip[at+4+(y-first)*4:at+8+(y-first)*4]==bytes(4)
                    masked+=1
            at+=4+(last-first)*4
    assert masked>0
    return masked

def visual(build,terminal):
    """Paired deterministic Chip capture: actual caption DMA, resumed world and PCM."""
    chipfile=build/'terminal-chip.bin';wav=build/'terminal.wav'
    cfg=config(build,build/'terminal-reading-save.adf')
    env=dict(os.environ,COPPERLINE_DBG_AFTER='65',COPPERLINE_DBG_RAMDUMP=f'0:80000:{chipfile}')
    with (build/'terminal-chip.log').open('w') as log:
        subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',
            '--key-after','62','0x44','500','--audio-wav',str(wav),
            '--screenshot-after','65.02',str(build/'terminal-chip.png')],
            env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    chip=chipfile.read_bytes();assets=ROOT/'build/amiga-feasibility'
    offsets=arrays(assets/'terminal_layer_assets.h','terminal_row_offsets')
    packed=bytes(arrays(assets/'terminal_layer_assets.h','terminal_row_packets'))
    for row in range(120):
        data=packed[offsets[row]:offsets[row+1]];ink=bytearray();at=0
        while at<len(data):
            token=data[at];at+=1;count=(token&127)+1
            if token&128:ink.extend(bytes([data[at]])*count);at+=1
            else:ink.extend(data[at:at+count]);at+=count
        address=terminal['caption']+(row+48)*40
        assert chip[address:address+40]==ink,('native caption row',row)
    bitmap=terminal['bitmap']
    for y in (*range(16),*range(224,240)):
        for plane in range(3):
            address=bitmap+plane*9600+y*40
            assert chip[address:address+40]==bytes([255 if plane else 0])*40
    states=[];regs={};line=epoch=0
    for i in range(0,512,2):
        r,v=struct.unpack_from('>HH',chip,terminal['copper']+i*2)
        if r==65535:break
        if r&1:
            states.append((line,dict(regs)))
            if r==0xffdf:epoch=256;line=255
            else:line=epoch+(r>>8)
        else:regs[r]=v
    states.append((line,dict(regs)))
    def state(y):return [v for line,v in states if line<=y][-1]
    def pointer(r,reg):return (r[reg]<<16)|r[reg+2]
    for y in (60,86):
        r=state(51+y);assert r[0x100]==0x1200
        assert pointer(r,0xe0)==terminal['caption']+y*40
        assert (r[0x180],r[0x182])==(0x222,0xaaa)
    for y in (16,84,155):
        r=state(51+y);assert r[0x100] in (0x3600,0x5600)
        assert pointer(r,0xe0)==terminal['world']+y*40,('resumed foreground',y)
        assert pointer(r,0xe4)==terminal['world']+20480+((200+y)&255)*40
    masked=sprite_windows(chip,regs)
    samples={}
    for name in ('crew1','crew4','teleporter-flash','teleporter-teleport','prize-vanish','prize-trinket','terminal-touch','terminal-read'):
        pcm=(assets/(name+'.pcm')).read_bytes();assert chip.count(pcm)==1,('native PCM',name)
        samples[name]=len(pcm)
    peak=audio_peak(wav,62.5,64.5);assert peak>0.01,peak
    print('PASS native caption DMA: 4800 ink bytes, one-plane windows, exact world/background resume, eight original PCM buffers and audible read cue',flush=True)
    return dict(caption_bytes=4800,masked_sprite_rows=masked,samples=samples,audio_peak=peak,screenshot=str(build/'terminal-chip.png'))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build',type=Path,default=ROOT/'build/amiga-terminal-campaign')
    p.add_argument('--case',choices=('all','reading','closed','menu'),default='all')
    a=p.parse_args();b=a.build.resolve();results={}
    for case in ('reading','closed','menu') if a.case=='all' else [a.case]:
        disk=b/('terminal-'+case+'-save.adf');disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk)
        controls=['--key-after','62','0x44','500']
        if case!='reading':controls+=['--key-after','66','0x40','1500']
        if case=='menu':controls+=['--key-after','70','0x44','500','--key-after','72','0x4f','500',
                                  '--key-after','73','0x40','500','--key-after','78','0x44','500']
        end={'reading':65,'closed':70,'menu':82}[case]
        result=capture(b,disk,'terminal-'+case,controls,end=end)
        ram=(b/('terminal-'+case+'.bin')).read_bytes();d=read(ram);display=result['display']
        assert display['status']==1 and display['error']==display['missed']==0 and display['max_work_lines']<=280,display
        assert d['opens']==d['cues']==1 and d['activity_w']==d['activity_h']==d['flips']==0,d
        assert d['clipped']>0 and d['warm_stage']==2,d
        assert (d['visible'],d['bars'],d['closes'])==((1,361,0) if case=='reading' else (0,0,1)),d
        at=ram.index(b'V6TA');audio=struct.unpack_from('>42I',ram,at)
        assert audio[2:5]==(0,2,2) and audio[6:8]==(2,0),audio
        assert audio[11]==5 and audio[15]==6 and audio[12] in (2,3) and audio[16] in (2,3),audio
        assert result['ui']['errors']==0 and result['ui']['saves']==int(case=='menu'),result['ui']
        results[case]=dict(display=display,terminal=d,audio=audio)
        print('PASS live campaign terminal:',case,display['max_work_lines'],'scanlines; original actors, one read cue, no flip on held advance',flush=True)
    if a.case=='all':results['native']=visual(b,results['reading']['terminal'])
    (b/'terminal-campaign-report.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
