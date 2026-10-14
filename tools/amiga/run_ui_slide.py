#!/usr/bin/env python3
"""Native full-tab closing slide: source header translation and frozen gameplay."""
import argparse,os,subprocess
from pathlib import Path
from run_map_input import capture
from run_interactive_save import config
from run_tower_probe import EMU
from save_disk import create_save_disk

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--page',type=int,choices=(0,1,2,3),default=3);a=p.parse_args();build=a.build.resolve()
 disk=build/'ui-slide-save.adf';disk.unlink(missing_ok=True);create_save_disk(build/'tower.adf',disk)
 controls=['--key-after','62','0x44','1000']
 if a.page==3:controls+=['--key-after','65','0x4f','500','--key-after','66','0x40','500']
 elif a.page:
  controls+=['--key-after','65','0x4e','400']
  if a.page==2:controls+=['--key-after','66','0x4e','400']
 result=capture(build,disk,'ui-slide-controls',controls+['--key-after','74','0x44','500'],end=80)
 d=result['display'];assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
 assert result['ui']['saves']==int(a.page==3) and result['ui']['errors']==0,result['ui']
 if a.page==3:assert result['ui']['before_hash']==result['ui']['after_hash'] and result['ui']['ticks_before']==result['ui']['ticks_after'],result['ui']
 cfg=config(build,disk);photos=[];decoder=build.parents[1]/'build/amiga-feasibility/png_rgba'
 for name,time,keys in [('full',77,[]),('partial',78.12,['--key-after','78','0x44','500'])]:
  # Each capture must repeat the same first-save transaction. Reusing the
  # timing run's mutated OFS disk changes DOS work and the visible result.
  disk.unlink(missing_ok=True);create_save_disk(build/'tower.adf',disk)
  dump=build/f'ui-slide-{name}.bin';photo=build/f'ui-slide-{name}.png'
  env=dict(os.environ,COPPERLINE_DBG_AFTER=str(time),COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
  with (build/f'ui-slide-{name}.log').open('w') as log:
   subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio',*controls,*keys,'--screenshot-after',str(time+.01),str(photo)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
  header,pixels=subprocess.check_output([str(decoder),str(photo)]).split(b'\n',1);width,height=map(int,header.split());photos.append(pixels)
 full,partial=photos;matches=[]
 for shift in range(1,min(240,(height-32-48)//2+1)):
  if all(full[(32+y)*width*4+x*4:(32+y)*width*4+x*4+3]==partial[(32+shift*2+y)*width*4+x*4:(32+shift*2+y)*width*4+x*4+3] for y in range(2,48) for x in range(80,650,4)):matches.append(shift)
 assert len(matches)==1,matches
 print('PASS native page',a.page,'slide:',matches[0],'translated rows, 6578 header pixels; work lines',d['max_work_lines'])
if __name__=='__main__':main()
