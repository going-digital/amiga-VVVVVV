#!/usr/bin/env python3
"""Stock A500 Welcome Aboard: regional crossings, retained checkpoint and reload."""
import argparse,json,struct,subprocess
from test_player import ROOT
from run_map_input import capture
from run_regions import diagnostics as regions
from run_solitude import check
from save_disk import create_save_disk,read_record

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cppflags',required=True);p.add_argument('--case',choices=('all','room','follower','edges','early-menu','death','reload'),default='all');a=p.parse_args();reports={}
 def build(name,extra):
  b=ROOT/'build'/name;b.mkdir(exist_ok=True)
  with (b/'welcome-build.log').open('w') as f:subprocess.run(['make',f'BUILD={b}',f'CPPFLAGS={a.cppflags} {extra}',str(b/'tower.adf')],cwd=ROOT/'amiga_version',stdout=f,stderr=subprocess.STDOUT,check=True)
  return b
 def run(b,name,target,open=70,close=80,end=84):
  disk=b/'welcome-save.adf';disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk)
  controls=['--key-after',str(open),'0x44','500','--key-after',str(open+3),'0x4f','500','--key-after',str(open+4),'0x40','500','--key-after',str(close),'0x44','500']
  r=capture(b,disk,name,controls,end=end);check(r);raw=(b/(name+'.bin')).read_bytes();regional=regions(raw)
  assert regional['errors']==regional['violations']==0 and regional['capacity']==24576,regional
  route=struct.unpack_from('>7I',raw,raw.index(b'V6RT'));assert route[2]==target and not route[6],route
  assert r['ui']['saves']==1 and not r['ui']['errors'] and r['ui']['before_hash']==r['ui']['after_hash'],r['ui']
  record=read_record(disk);assert struct.unpack_from('>7i',record,8)==(148,161,0,1,115,105,441530),record[:40]
  # Save exploration must include Welcome and the real remote checkpoint.
  for x,y in ((113,105),(115,105)):
   bit=(y-100)*20+x-100;assert record[40+bit//8]&(1<<(bit%8)),(x,y)
  reports[name]=dict(display=r['display'],regional=regional,route=route,flags=record[139])
  print('PASS Welcome Aboard:',name,reports[name],flush=True)
  return disk,record
 cases=('room','follower','edges','early-menu','death','reload') if a.case=='all' else (a.case,)
 for case in cases:
  if case in ('room','follower'):
   b=build('amiga-welcome'+('-follower' if case=='follower' else ''),'-DV6_NORTH_START=20 -DV6_SOLITUDE_SEEN'+(' -DV6_NORTH_FOLLOWER' if case=='follower' else ''))
   disk,record=run(b,case,20)
   assert record[5]==7 and record[139]==1 and reports[case]['regional']['room']==20
  elif case=='edges':
   for index,target,name in ((19,20,'west'),(20,19,'east')):
    b=build('amiga-welcome-'+name,f'-DV6_NORTH_START={index} -DV6_SOLITUDE_SEEN -DV6_WELCOME_EDGE')
    disk,record=run(b,name,target,82,94,100);reg=reports[name]['regional']
    assert reg['loads']==2 and reg['pauses']==1 and reg['room']==target,reg
    assert record[5]==8 and record[139]&4,record[138:140]
  elif case=='early-menu':
   from run_conundrum import tutorial
   b=build('amiga-welcome-east','-DV6_NORTH_START=20 -DV6_SOLITUDE_SEEN -DV6_WELCOME_EDGE -DV6_WELCOME_EARLY_MENU')
   disk=b/'early-save.adf';disk.unlink(missing_ok=True);create_save_disk(b/'tower.adf',disk)
   r=capture(b,disk,case,[],end=70);check(r)
   raw=(b/(case+'.bin')).read_bytes();v=tutorial(raw)
   assert v[7]==1 and not r['ui']['errors'],(v,r['ui'])
   reports[case]=dict(display=r['display'],tutorial=v)
   print('PASS early map opening with a live Conundrum hint after cold crossing:',reports[case],flush=True)
  elif case=='death':
   b=build('amiga-welcome-death','-DV6_NORTH_START=20 -DV6_SOLITUDE_SEEN -DV6_WELCOME_DEATH')
   disk,record=run(b,case,18,82,94,100);reg=reports[case]['regional']
   assert struct.unpack_from('>I',record,116)[0]>=1 and reg['room']==18 and reg['loads']==2 and reg['pauses']==1,(record[116:120],reg)
  else:
   b=ROOT/'build/amiga-welcome-follower';disk=b/'welcome-save.adf';record=read_record(disk)
   load=build('amiga-welcome-load','-DV6_VSTITCH_HINT_LOAD -DV6_WELCOME_REVISIT')
   subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_menu_reload.py'),'--build',str(b),'--load-build',str(load),'--save-disk',str(disk),'--menu-after','82'],check=True)
   raw=(load/'menu-reload.bin').read_bytes();reg=regions(raw);route=struct.unpack_from('>7I',raw,raw.index(b'V6RT'))
   assert reg['room']==20 and reg['loads']==2 and reg['errors']==reg['violations']==reg['pauses']==0 and route[2]==20 and not route[6],(reg,route)
   reports[case]=dict(regional=reg,route=route);print('PASS Welcome cold reload and revisit: retained original checkpoint, exploration and receipt',reports[case],flush=True)
 (ROOT/('build/welcome-'+a.case+'-report.json')).write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
