#!/usr/bin/env python3
"""Stock A500 north-room movement, real edges, menu slides and V6 reload."""
import argparse
import json
import struct
import subprocess
from pathlib import Path
from run_map_input import capture
from save_disk import create_save_disk
from test_player import ROOT

LINEAR_CASES=['room14','linear-contact','linear-follower','edge13right','edge14left','linear-reload']
TRAFFIC_CASES=['room16','traffic-follower','edge15right','edge16left','traffic-reload']
FILTER_CASES=['room15','filter-follower','edge14right','edge15left','filter-reload']
CASES=[*TRAFFIC_CASES,*FILTER_CASES,'room10','room11','room12','room13',*LINEAR_CASES,'follower','security-follower','movement',
       'edge10up','edge11up','edge10down','edge11down','edge12down','edge12up','edge13down','reload','security-reload']

def timing(result):
    d=result['display']
    assert d['status']==1 and d['error']==d['missed']==0 and d['max_work_lines']<=280,d
    return d

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cppflags',required=True)
    parser.add_argument('--case',choices=['all','linear','filter','traffic','bob',*CASES],default='all')
    args=parser.parse_args()
    def build(name,extra):
        folder=ROOT/'build'/name;folder.mkdir(parents=True,exist_ok=True)
        command=['make',f'BUILD={folder}',f'CPPFLAGS={args.cppflags} {extra}',str(folder/'tower.adf')]
        with (folder/'north-build.log').open('w') as log:
            subprocess.run(command,cwd=ROOT/'amiga_version',stdout=log,stderr=subprocess.STDOUT,check=True)
        return folder
    def slide(folder,page=3):
        subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_slide.py'),'--build',str(folder),'--page',str(page)],check=True)
    def menu_controls(folder):
        # Slide pixels are checked in the dedicated live-room/follower cases.
        # Edge/reload cases need one actual input/save/close transaction.
        disk=folder/'ui-slide-save.adf';disk.unlink(missing_ok=True)
        create_save_disk(folder/'tower.adf',disk)
        result=capture(folder,disk,'ui-slide-controls',[
            '--key-after','62','0x44','1000','--key-after','65','0x4f','500',
            '--key-after','66','0x40','500','--key-after','74','0x44','500'],end=80)
        timing(result)
        assert result['ui']['saves']==1 and result['ui']['errors']==0,result['ui']
        assert result['ui']['before_hash']==result['ui']['after_hash'],result['ui']
    if args.case=='bob':
        folder=build('amiga-north-bob','-DV6_NORTH_START=11 -DV6_NORTH_FOLLOWER -DV6_NORTH_BOB')
        disk=folder/'bob-validation.adf';create_save_disk(folder/'tower.adf',disk)
        result=capture(folder,disk,'bob-validation',[
            '--key-after','62','0x44','600','--key-after','64','0x44','600',
            '--key-after','66','0x44','600'],end=68)
        ram=(folder/'bob-validation.bin').read_bytes()
        values=struct.unpack_from('>14I',ram,ram.index(b'V6NB'))
        assert result['display']['status']==1 and result['display']['error']==0,result['display']
        assert values[3]>=2 and values[4]==0,values
        result['native_bob']=values
        result['scope']='Explicit uncached DMA/mask reference comparisons; production frame timing is tested without this diagnostic fixture.'
        (folder/'bob-validation-report.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PASS native sprite-DMA/BOB reference comparisons:',values,flush=True)
        return
    reports={}
    selected=CASES if args.case=='all' else TRAFFIC_CASES if args.case=='traffic' else FILTER_CASES if args.case=='filter' else LINEAR_CASES if args.case=='linear' else [args.case]
    for case in selected:
        if case.startswith('room'):
            index=int(case[4:]);folder=build(f'amiga-north-live-{index}',f'-DV6_NORTH_START={index}')
            slide(folder)
        elif case=='linear-contact':
            folder=build('amiga-north-linear-contact','-DV6_NORTH_START=14 -DV6_NORTH_TERMINAL_CONTACT -DV6_NORTH_FOLLOWER')
            subprocess.run(['python3',str(ROOT/'tools/amiga/run_terminal_campaign.py'),'--build',str(folder)],check=True)
            reports[case]=json.loads((folder/'terminal-campaign-report.json').read_text())
            continue
        elif case in ('follower','security-follower','linear-follower','filter-follower','traffic-follower'):
            index=16 if case=='traffic-follower' else 15 if case=='filter-follower' else 14 if case=='linear-follower' else 13 if case=='security-follower' else 11
            folder=build('amiga-north-'+case,f'-DV6_NORTH_START={index} -DV6_NORTH_FOLLOWER')
            slide(folder)
        elif case=='movement':
            folder=build('amiga-north-follower','-DV6_NORTH_START=11 -DV6_NORTH_FOLLOWER')
            disk=folder/'north-movement-save.adf';create_save_disk(folder/'tower.adf',disk)
            result=capture(folder,disk,'north-movement',[
                '--key-after','60','0x4e','2500','--key-after','61','0x40','500',
                '--key-after','63.5','0x4f','2500','--key-after','65','0x40','500'],end=70)
            d=timing(result);ram=(folder/'north-movement.bin').read_bytes()
            route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'))
            assert route[3]>=4 and route[4]>=2 and route[6]==0,route
            reports[case]=dict(display=d,route=route)
            print('PASS live north movement/flip/death/room loading:',d,flush=True)
            continue
        elif case in ('edge13right','edge14left','edge14right','edge15left','edge15right','edge16left'):
            index=int(case[4:6]);target=index+(1 if case.endswith('right') else -1)
            folder=build('amiga-north-'+case,f'-DV6_NORTH_START={index} -DV6_NORTH_CORRIDOR={3 if case=="edge15right" else 2 if case=="edge14right" else 1}');menu_controls(folder)
            ram=(folder/'ui-slide-controls.bin').read_bytes();route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'))
            assert route[2]==target and route[3]>=3 and route[6]==0,(case,route)
            print('PASS actual corridor crossing:',index,'->',target,flush=True)
        elif case.startswith('edge'):
            reverse=case.endswith('down');index=int(case[4:6]);target=index+(-1 if reverse else 1)
            extra=f'-DV6_NORTH_START={index} -DV6_NORTH_SHAFT'+(' -DV6_NORTH_SHAFT_REVERSE' if reverse else '')
            folder=build(f'amiga-north-{case}',extra);slide(folder)
            ram=(folder/'ui-slide-controls.bin').read_bytes();route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'))
            assert route[2]==target and route[3]>=3 and route[6]==0,(case,route)
            print('PASS actual shaft crossing:',index,'->',target,flush=True)
        else:
            index=16 if case=='traffic-reload' else 15 if case=='filter-reload' else 14 if case=='linear-reload' else 13 if case=='security-reload' else 11
            saved=build(f'amiga-north-live-{index}',f'-DV6_NORTH_START={index}')
            if case in ('linear-reload','filter-reload','traffic-reload'):menu_controls(saved)
            else:slide(saved)
            folder=build('amiga-north-load-native','-DV6_VSTITCH_HINT_LOAD')
            subprocess.run(['python3',str(ROOT/'tools/amiga/run_ui_menu_reload.py'),
                '--build',str(saved),'--load-build',str(folder),'--save-disk',str(saved/'ui-slide-save.adf')],check=True)
            ram=(folder/'menu-reload.bin').read_bytes();route=struct.unpack_from('>7I',ram,ram.index(b'V6RT'))
            assert route[2]==index and route[6]==0,(case,route)
        report=folder/('menu-reload-report.json' if case.endswith('reload') else 'ui-slide-controls-report.json')
        reports[case]=json.loads(report.read_text())['display']
    (ROOT/'build/north-capture-report.json').write_text(json.dumps(reports,indent=2)+'\n')

if __name__=='__main__':main()
