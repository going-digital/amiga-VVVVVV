#!/usr/bin/env python3
"""Stock A500 firststeps dialogue, canonical V7 save and once-only cold reload."""
import argparse,json,struct,subprocess,os
from pathlib import Path
from test_player import ROOT
from run_map_input import capture
from save_disk import create_save_disk,read_record

def firststeps(data):
 entries=[];at=0
 while True:
  at=data.find(b'V6FS\0\0\0\1',at)
  if at<0:break
  v=struct.unpack_from('>11I',data,at)
  if v[2]in(0,1) and v[3]in(0,1) and v[5]in(0,1) and v[8]==0 and v[10]==18:entries.append(v)
  at+=8
 assert len(entries)==1,entries
 return entries[0]

def check(result):
 d=result['display'];assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
 return d

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cppflags',required=True);p.add_argument('--follower',action='store_true');p.add_argument('--case',choices=('story','edges','pixels'),default='story');a=p.parse_args()
 def build(name,extra):
  b=ROOT/'build'/name;b.mkdir(exist_ok=True)
  with (b/'solitude-build.log').open('w') as f:subprocess.run(['make',f'BUILD={b}',f'CPPFLAGS={a.cppflags} {extra}',str(b/'tower.adf')],cwd=ROOT/'amiga_version',stdout=f,stderr=subprocess.STDOUT,check=True)
  return b
 if a.case=='edges':
  reports={}
  for index,target,name in ((17,18,'down'),(18,17,'up')):
   b=build('amiga-solitude-'+name,f'-DV6_NORTH_START={index} -DV6_LEAP_SHAFT=2'+(' -DV6_SOLITUDE_SEEN' if index==18 else ''))
   disk=b/'edge-save.adf';disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk)
   r=capture(b,disk,'edge',['--key-after','82','0x44','500','--key-after','85','0x4f','500','--key-after','86','0x40','500','--key-after','94','0x44','500'],end=100)
   d=check(r);ram=(b/'edge.bin').read_bytes();route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'))
   assert route[2]==target and route[3]>=6 and route[6]==0,route
   assert r['ui']['saves']==1 and r['ui']['errors']==0,r['ui']
   reports[name]=dict(display=d,route=route)
   print('PASS Solitude vertical crossing and staged PCM ownership:',name,d,flush=True)
   if name=='up':
    from run_tower_probe import EMU
    from run_interactive_save import config
    dump=b/'restored-chip.bin';cfg=config(b,disk)
    env=dict(os.environ,COPPERLINE_DBG_AFTER='90',COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
    with (b/'restored-chip.log').open('w') as f:subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio','--screenshot-after','90.01',str(b/'restored-chip.png')],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
    chip=dump.read_bytes();assets=ROOT/'build/amiga-feasibility'
    original=(assets/'prize-trinket.pcm').read_bytes()
    assert chip.find(original)>=0 and chip.find((assets/'firststeps-cry.pcm').read_bytes())<0,'shared jingle PCM restored on exit'
    print('PASS restored original jingle PCM:',len(original),'bytes',flush=True)
  (ROOT/'build/solitude-edges-report.json').write_text(json.dumps(reports,indent=2)+'\n')
  return
 if a.case=='pixels':
  from run_interactive_save import config
  from run_tower_probe import EMU
  from run_copperline import audio_peak
  from firststeps_script import script
  from test_map_draw import arrays
  b=build('amiga-north-solitude','-DV6_NORTH_START=18')
  disk=b/'pixels-save.adf';disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk);cfg=config(b,disk)
  dump=b/'firststeps-chip.bin';wav=b/'firststeps.wav'
  env=dict(os.environ,COPPERLINE_DBG_AFTER='65',COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
  with (b/'firststeps-chip.log').open('w') as f:subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio','--key-after','62','0x40','500','--audio-wav',str(wav),'--screenshot-after','65.02',str(b/'firststeps-chip.png')],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
  assets=ROOT/'build/amiga-feasibility';font=arrays(assets/'dialogue_font.h','dialogue_font');expected=bytearray()
  for lines in script()['speeches']:
   ink=bytearray(1920)
   for x in range(1,39):ink[4*40+x]=ink[43*40+x]=255
   for y in range(5,43):ink[y*40+1]=128;ink[y*40+38]=1
   for line,text in enumerate(lines):
    x=(40-len(text))//2
    for i,c in enumerate(text):
     for y in range(8):ink[(16+line*8+y)*40+x+i]=font[ord(c)*8+y]
   expected+=bytes([255])*1920+ink
  chip=dump.read_bytes();at=chip.find(expected);assert at>=0 and chip.find(expected,at+1)<0,'both exact source caption banks'
  cry=(assets/'firststeps-cry.pcm').read_bytes();assert chip.find(cry)>=0 and chip.find((assets/'prize-trinket.pcm').read_bytes())<0,'cry owns shared jingle bank'
  peak=audio_peak(wav,62,64);assert peak>0.01,peak
  print('PASS firststeps native captions:',len(expected),'bytes; original cry PCM:',len(cry),'bytes; audible cry peak:',peak,flush=True)
  return
 b=build('amiga-north-solitude'+('-follower' if a.follower else ''),'-DV6_NORTH_START=18'+(' -DV6_NORTH_FOLLOWER' if a.follower else ''))
 disk=b/'firststeps-save.adf';disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk)
 inputs=['--key-after','62','0x40','500','--key-after','65','0x40','500','--key-after','70','0x44','500','--key-after','73','0x4f','500','--key-after','74','0x40','500','--key-after','80','0x44','500']
 r=capture(b,disk,'firststeps',inputs,end=84);d=check(r);v=firststeps((b/'firststeps.bin').read_bytes())
 assert v[2:4]==(1,0) and v[5:9]==(0,2,1,0),v
 assert r['ui']['saves']==1 and r['ui']['errors']==0 and r['ui']['before_hash']==r['ui']['after_hash'],r['ui']
 record=read_record(disk);assert record[5]==7 and record[138:140]==b'\0\1' and struct.unpack_from('>7i',record,8)==(148,161,0,1,115,105,441530)
 print('PASS original firststeps, both pages/cues, V7 flag and source checkpoint:',d,flush=True)
 load=build('amiga-solitude-load','-DV6_VSTITCH_HINT_LOAD')
 subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_menu_reload.py'),'--build',str(b),'--load-build',str(load),'--save-disk',str(disk)],check=True)
 v2=firststeps((load/'menu-reload.bin').read_bytes());assert v2[2:4]==(1,0) and v2[6:9]==(0,0,0),v2
 print('PASS firststeps suppressed after cold V7 reload:',v2,flush=True)
 (b/'solitude-report.json').write_text(json.dumps(dict(display=d,firststeps=v,reloaded=v2),indent=2)+'\n')
if __name__=='__main__':main()
