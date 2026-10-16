#!/usr/bin/env python3
"""Fresh executable retains the V6 last-save receipt and current campaign totals."""
import argparse,struct
from pathlib import Path
from run_map_input import capture
from save_disk import read_record

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--load-build',type=Path,required=True);p.add_argument('--save-disk',type=Path,help='Source V6 save disk; defaults to the map capture disk');p.add_argument('--menu-after',type=float,default=62,help='Allow staged room/PCM loading before menu input');a=p.parse_args()
 build=a.build.resolve();load=a.load_build.resolve();source=a.save_disk.resolve() if a.save_disk else build/'map-display-save.adf';record=read_record(source)
 assert len(record)==144 and record[5] in (6,7,8)
 disk=load/'menu-reload-save.adf';disk.write_bytes(source.read_bytes());assert read_record(disk)==record
 before=disk.read_bytes();boot=(load/'tower.adf').read_bytes()
 result=capture(load,disk,'menu-reload',['--key-after',str(a.menu_after),'0x44','1000','--key-after',str(a.menu_after+3),'0x4f','500'],end=a.menu_after+12)
 d=result['display'];assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
 b=(load/'menu-reload.bin').read_bytes();at=b.index(b'V6MU\0\0\0\2');v=struct.unpack_from('>18I',b,at+8)
 assert v[2]==record[120] and v[3]>=struct.unpack_from('>I',record,116)[0],v
 assert v[9]==record[121] and v[10:12]==struct.unpack_from('>2H',record,130),v
 assert v[12:16]==struct.unpack_from('>4H',record,122) and v[16:18]==struct.unpack_from('>2H',record,134),v
 loaded_clock=struct.unpack_from('>4H',record,108);current=(v[7],v[4],v[5],v[8]);assert current>=loaded_clock,(current,loaded_clock)
 assert result['ui']['saves']==result['ui']['loads']==result['ui']['errors']==0,result['ui']
 assert disk.read_bytes()==before and (load/'tower.adf').read_bytes()==boot
 print('PASS native V6 reload: clock, deaths, all crew flags and exact last-save summary; disk unchanged;',d,flush=True)
if __name__=='__main__':main()
