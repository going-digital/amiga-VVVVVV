#!/usr/bin/env python3
"""Stock A500 regional disk misses, cache eviction, checkpoint return and reload."""
import argparse
import json
from pathlib import Path
import struct
import subprocess
from adf_files import get,put,checksum,name_hash
from run_map_input import capture
from save_disk import create_save_disk,read_record
from test_player import ROOT

FIELDS='magic version loads hits errors pauses drain_fields room region capacity violations'.split()
def diagnostics(data):
    at=data.index(b'V6RC\0\0\0\1')
    return dict(zip(FIELDS,struct.unpack_from('>11I',data,at)))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cppflags',required=True)
    p.add_argument('--case',choices=('all','replay','cross','faults','reload'),default='all');a=p.parse_args();reports={}
    flags=a.cppflags
    if '-DV6_REGIONAL_CONTENT' not in flags:flags+=' -DV6_REGIONAL_CONTENT'
    def build(name,extra):
        folder=ROOT/'build'/name;folder.mkdir(exist_ok=True)
        with (folder/'regional-build.log').open('w') as log:
            subprocess.run(['make',f'BUILD={folder}',f'CPPFLAGS={flags} {extra}',str(folder/'tower.adf')],cwd=ROOT/'amiga_version',stdout=log,stderr=subprocess.STDOUT,check=True)
        return folder
    def check(folder,name,controls,end=100):
        disk=folder/(name+'-save.adf');disk.unlink(missing_ok=True);create_save_disk(folder/'tower.adf',disk)
        result=capture(folder,disk,name,controls,end=end);d=result['display'];ram=(folder/(name+'.bin')).read_bytes();region=diagnostics(ram)
        assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
        assert region['errors']==region['violations']==0 and region['capacity']==24576,region
        result['regional']=region;reports[name]=result
        print('PASS regional native:',name,d['max_work_lines'],'scanlines;',region,flush=True)
        return result,ram,disk
    if a.case in ('all','replay','reload'):
        replay=build('amiga-region-replay','-DV6_NORTH_START=11 -DV6_NORTH_FOLLOWER -DV6_REGION_REPLAY')
        result,ram,saved=check(replay,'region-replay',[
            '--key-after','90','0x44','500','--key-after','93','0x4f','500',
            '--key-after','94','0x40','500','--key-after','102','0x44','500'],end=108)
        region=result['regional'];route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'))
        assert (region['loads'],region['hits'],region['pauses'],region['room'])==(4,1,3,11) and region['drain_fields']>0,region
        audio=struct.unpack_from('>10I',ram,ram.index(b'V6TA'))
        assert audio[2]==0 and audio[3]==audio[4] and audio[4]>=1 and audio[7]==0,audio
        assert route[2]==11 and route[6]==0 and result['ui']['saves']==1 and result['ui']['errors']==0,result
        record=read_record(saved);assert len(record)==144
        # Actual death/respawn returns to the original region after it was evicted.
        assert result['display']['logic_ticks']>150 and result['display']['recovery_calls']>150
        if a.case in ('all','reload'):
            load=build('amiga-region-load','-DV6_VSTITCH_HINT_LOAD')
            subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_menu_reload.py'),'--build',str(replay),'--load-build',str(load),'--save-disk',str(saved)],check=True)
            d=diagnostics((load/'menu-reload.bin').read_bytes())
            assert d['loads']==1 and d['room']==11 and d['pauses']==d['errors']==d['violations']==0,d
            reports['reload']=d
    if a.case in ('all','cross','faults'):
        folder=build('amiga-region-cross','-DV6_NORTH_START=13 -DV6_NORTH_CORRIDOR')
        if a.case in ('all','cross'):
            result,ram,disk=check(folder,'region-cross',[
                '--key-after','62','0x44','1000','--key-after','65','0x4f','500',
                '--key-after','66','0x40','500','--key-after','74','0x44','500'],end=80)
            d=result['regional'];assert (d['loads'],d['pauses'],d['room'])==(2,1,14),d
            assert result['ui']['saves']==1 and result['ui']['errors']==0,result['ui']
        if a.case in ('all','faults'):
            original=(folder/'tower.adf').read_bytes()
            for fault in ('missing','corrupt'):
                image=bytearray(original);root=len(image)//1024;bucket=6+name_hash(b'north2.v6rg');header=get(image,root,bucket)
                assert image[header*512+433:header*512+444]==b'north2.v6rg'
                if fault=='missing':put(image,root,bucket,get(image,header,124));checksum(image,root,5)
                else:
                    data=get(image,header,4);image[data*512+24]^=1;checksum(image,data,5)
                try:
                    (folder/'tower.adf').write_bytes(image)
                    disk=folder/(fault+'-save.adf');disk.unlink(missing_ok=True);create_save_disk(folder/'tower.adf',disk)
                    result=capture(folder,disk,'region-'+fault,[],end=80)
                    ram=(folder/('region-'+fault+'.bin')).read_bytes();d=diagnostics(ram)
                    route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'));display=result['display']
                    assert display['status']==2 and display['error']==6 and display['missed']==0,display
                    assert d['loads']==2 and d['errors']==1 and d['violations']==0 and route[2]==13 and route[6]==1,(d,route)
                    reports[fault]=dict(display=display,regional=d,route=route)
                    print('PASS regional fault:',fault,'rejected before room commit; clean DOS return',flush=True)
                finally:(folder/'tower.adf').write_bytes(original)
    report_path=ROOT/'build/regional-capture-report.json'
    if a.case!='all' and report_path.exists():
        previous=json.loads(report_path.read_text());previous.update(reports);reports=previous
    report_path.write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':main()
