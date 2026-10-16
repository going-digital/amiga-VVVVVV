#!/usr/bin/env python3
"""Stock A500 Conundrum tutorial, live crossings, retained checkpoint and V8 reload."""
import argparse,json,os,struct,subprocess
from test_player import ROOT
from run_map_input import capture
from save_disk import create_save_disk,read_record
from run_solitude import check

def tutorial(data):
 entries=[];at=0
 while True:
  at=data.find(b'V6CN\0\0\0\1',at)
  if at<0:break
  v=struct.unpack_from('>16I',data,at)
  if v[2]<=7 and v[3]<=3 and v[4]<=3 and v[7]<=1 and v[11]==19:entries.append(v)
  at+=8
 assert len(entries)==1,entries
 return entries[0]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cppflags',required=True);p.add_argument('--case',choices=('all','tour','follower','edges','death','pixels','reload'),default='all');a=p.parse_args()
 reports={}
 def build(name,extra):
  b=ROOT/'build'/name;b.mkdir(exist_ok=True)
  with (b/'conundrum-build.log').open('w') as f:subprocess.run(['make',f'BUILD={b}',f'CPPFLAGS={a.cppflags} {extra}',str(b/'tower.adf')],cwd=ROOT/'amiga_version',stdout=f,stderr=subprocess.STDOUT,check=True)
  return b
 def disk(b):
  d=b/'conundrum-save.adf';d.unlink(missing_ok=True);create_save_disk(b/'tower.adf',d);return d
 def menu(open=70,close=80):
  return ['--key-after',str(open),'0x44','500','--key-after',str(open+3),'0x4f','500','--key-after',str(open+4),'0x40','500','--key-after',str(close),'0x44','500']
 def saved(b,d,name,inputs,end=84):
  r=capture(b,d,name,inputs,end=end);check(r)
  assert r['ui']['saves']==1 and not r['ui']['errors'] and r['ui']['before_hash']==r['ui']['after_hash'],r['ui']
  record=read_record(d)
  assert struct.unpack_from('>7i',record,8)==(148,161,0,1,115,105,441530),record[:40]
  raw=(b/(name+'.bin')).read_bytes();route=struct.unpack_from('>7I',raw,raw.index(b'V6RT'))
  assert not route[6],route
  return r,record,raw,route
 cases=('tour','follower','edges','death','pixels','reload') if a.case=='all' else (a.case,)
 for case in cases:
  if case in ('tour','follower'):
   b=build('amiga-conundrum'+('-follower' if case=='follower' else ''),'-DV6_NORTH_START=19 -DV6_SOLITUDE_SEEN -DV6_CONUNDRUM_TOUR'+(' -DV6_NORTH_FOLLOWER' if case=='follower' else ''))
   d=disk(b);r,record,raw,route=saved(b,d,'conundrum',menu(59),84)
   v=tutorial(raw)
   assert v[2:11]==(7,0,0,2,2,0,0,5,1) and v[15]==0,v
   assert record[5]==8 and record[138:140]==b'\0\7' and route[2]==19,(record[5],route)
   reports[case]=dict(display=r['display'],tutorial=v,route=route)
   print('PASS Conundrum ceiling traversal, both original triggers, timed hint/menu pause and V8 save:',case,reports[case],flush=True)
  elif case=='edges':
   for index,target,name in ((18,19,'west'),(19,18,'east')):
    b=build('amiga-conundrum-'+name,f'-DV6_NORTH_START={index} -DV6_SOLITUDE_SEEN -DV6_CONUNDRUM_EDGE')
    d=disk(b);r,record,raw,route=saved(b,d,'edge',menu(82,94),100)
    assert route[2]==target and route[3]>=6,route
    if target==19:assert record[139]&2 and record[5]==8
    reports[name]=dict(display=r['display'],route=route,flags=record[139])
    print('PASS Conundrum horizontal crossing and retained Solitude checkpoint:',name,reports[name],flush=True)
  elif case=='death':
   b=build('amiga-conundrum-death','-DV6_NORTH_START=19 -DV6_SOLITUDE_SEEN -DV6_CONUNDRUM_DEATH')
   d=disk(b);r,record,raw,route=saved(b,d,'death',menu(82,94),100)
   assert route[2]==18 and struct.unpack_from('>I',record,116)[0]>=1,(route,record[116:120])
   reports[case]=dict(display=r['display'],route=route,flags=record[139]);print('PASS Conundrum death returns to original Solitude checkpoint:',reports[case],flush=True)
  elif case=='pixels':
   from run_interactive_save import config
   from run_tower_probe import EMU
   from test_map_draw import arrays
   b=build('amiga-conundrum','-DV6_NORTH_START=19 -DV6_SOLITUDE_SEEN -DV6_CONUNDRUM_TOUR');d=disk(b);cfg=config(b,d)
   dump=b/'hint-chip.bin';env=dict(os.environ,COPPERLINE_DBG_AFTER='59',COPPERLINE_DBG_RAMDUMP=f'0:80000:{dump}')
   with (b/'hint-chip.log').open('w') as f:subprocess.run([EMU,'--config',str(cfg),'--floppy-drives','2','--noaudio','--screenshot-after','59.02',str(b/'hint-chip.png')],env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
   font=arrays(ROOT/'build/amiga-feasibility/dialogue_font.h','dialogue_font');expected=bytearray()
   for lines in (('Press SPACE / Z / V','to flip'),('','')):
    ink=bytearray(1920)
    for x in range(1,39):ink[4*40+x]=ink[43*40+x]=255
    for y in range(5,43):ink[y*40+1]=128;ink[y*40+38]=1
    for line,text in enumerate(lines):
     x=(40-len(text))//2
     for i,c in enumerate(text):
      for y in range(8):ink[(16+line*8+y)*40+x+i]=font[ord(c)*8+y]
    expected+=bytes([255])*1920+ink
   data=dump.read_bytes();at=data.find(expected);assert at>=0 and data.find(expected,at+1)<0,'both reused hint caption banks'
   dimensions,rgba=subprocess.check_output([str(ROOT/'build/amiga-feasibility/png_rgba'),str(b/'hint-chip.png')]).split(b'\n',1)
   width,height=map(int,dimensions.split());grey=0
   for y in range(60,min(height,170)):
    for x in range(35,min(width,680)):
     r,g,bl=rgba[(y*width+x)*4:(y*width+x)*4+3];grey+=r==g==bl and r>40
   assert grey>100,('visible grey hint ink/border',grey)
   reports[case]=dict(compared_bytes=len(expected),caption_address=at,grey_pixels=grey)
   print('PASS Conundrum native caption memory:',reports[case],flush=True)
  else:
   b=ROOT/'build/amiga-conundrum-follower';d=b/'conundrum-save.adf';record=read_record(d)
   assert record[5]==8 and record[139]==7,record[138:140]
   load=build('amiga-conundrum-load','-DV6_VSTITCH_HINT_LOAD -DV6_CONUNDRUM_REVISIT -DV6_CONUNDRUM_TOUR')
   subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_menu_reload.py'),'--build',str(b),'--load-build',str(load),'--save-disk',str(d),'--menu-after','82'],check=True)
   v=tutorial((load/'menu-reload.bin').read_bytes());assert v[2:11]==(7,0,0,2,2,0,0,0,0),v
   reports[case]=dict(tutorial=v);print('PASS V8 cold reload and Conundrum revisit suppress both triggers; retained save receipt',flush=True)
 (ROOT/('build/conundrum-'+a.case+'-report.json')).write_text(json.dumps(reports,indent=2)+'\n')
if __name__=='__main__':main()
