#!/usr/bin/env python3
"""Actual native Save prompt and write-protected DF1 failure presentation."""
import argparse,json,os,struct,subprocess
from pathlib import Path
from run_interactive_save import config,KEYS
from run_tower_probe import EMU
from save_disk import create_save_disk
from test_map_draw import arrays

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);a=p.parse_args();b=a.build.resolve()
 assets=b.parents[1]/'build/amiga-feasibility';palette=arrays(assets/'save_assets.h','save_palette');reports=[]
 for failed in (False,True):
  name='failure' if failed else 'prompt';disk=b/('save-'+name+'.adf');disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk)
  before=disk.read_bytes();cfg=config(b,disk)
  if failed:cfg.write_text(cfg.read_text().replace('write_protected = false','write_protected = true'))
  inputs=['--key-after','62','0x44','2000','--key-after','65','0x4f','800']
  if failed:inputs+=['--key-after','66','0x40','600','--key-after','68','0x40','300']
  slow=b/('save-'+name+'-slow.bin');chip=b/('save-'+name+'-chip.bin');image=b/('save-'+name+'.png');end=69 if failed else 66.5
  # Independent runs read Slow diagnostics and actual immutable Chip data.
  for address,dump in [('C00000',slow),('0',chip)]:
   env=dict(os.environ,COPPERLINE_DBG_AFTER=str(end),COPPERLINE_DBG_RAMDUMP=f'{address}:80000:{dump}')
   with (b/('save-'+name+'-'+address+'.log')).open('w') as log:
    subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*inputs,'--screenshot-after',str(end+.01),str(image)],env=env,stdout=log,stderr=log,check=True)
  data=slow.read_bytes();at=data.index(b'V6TP\0\0\0\6');raw=struct.unpack_from('>26I',data,at)
  d=dict(status=raw[2],frames=raw[3],max_work_lines=raw[5],missed=raw[6],error=raw[7],chip_bytes=raw[8])
  assert d['status'] in (0,1) and d['error']==d['missed']==0 and d['max_work_lines']<=280 and d['chip_bytes']==424790,d
  at=data.index(b'V6SD\0\0\0\1');values=struct.unpack_from('>4I',data,at+8);assert values[failed]>0,values
  if failed:
   at=data.index(b'V6MI\0\0\0\1');v=struct.unpack_from('>12I',data,at+8)
   assert v[5]==1 and v[6]!=0 and v[8]==v[11]==0,v # Held/repeated action cannot retry failure.
   at=data.index(b'V6UI\0\0\0\1');ui=dict(zip(KEYS,struct.unpack_from('>18I',data,at+8)))
   assert ui['actions']==ui['errors']==1 and ui['saves']==ui['loads']==0,ui
   assert ui['before_hash']==ui['after_hash'] and ui['ticks_before']==ui['ticks_after'],ui
  ram=chip.read_bytes()
  for index,label in enumerate(('prompt','failure')):
   golden=(assets/('save-'+label+'.bin')).read_bytes();assert ram[values[2+index]:values[2+index]+28800]==golden,label
  marker=bytes.fromhex('2c01fffe01003200');at=0;lists=[]
  while True:
   at=ram.find(marker,at)
   if at<0:break
   words=struct.unpack_from('>130H',ram,at-64);r=dict(zip(words[::2],words[1::2]))
   for plane in range(3):assert r[0xe0+plane*4]*65536+r[0xe2+plane*4]==values[2+failed]+plane*9600
   for i,c in enumerate(palette):assert r[0x180+i*2]==c
   assert r[0x104]==0x20 and r[0x108]==r[0x10a]==0
   lists.append(at);at+=1
  assert len(lists)==2,lists
  assert disk.read_bytes()==before,'read-only/idle disk changed'
  reports.append(dict(state=name,display=d,values=values,copper_lists=lists,compared_bytes=57600,screenshot=str(image)))
 (b/'save-display-report.json').write_text(json.dumps(reports,indent=2)+'\n');print('PASS native Save pages:',json.dumps(reports))
if __name__=='__main__':main()
