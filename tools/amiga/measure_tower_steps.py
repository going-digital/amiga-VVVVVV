#!/usr/bin/env python3
"""Measure synthetic camera steps; overruns are findings, not passing timing tests."""
import argparse
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--full',action='store_true',help='Cover the entire source map in both directions at 12 and 16 pixels/frame')
args=parser.parse_args()
reports=[]
for step in ((12,16) if args.full else (4,8,12,16)):
    build=ROOT/f'build/amiga-tower-{"full" if args.full else "step"}{step}'
    build.mkdir(parents=True,exist_ok=True)
    with (build/'build.log').open('w') as log:
        subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={build}',
            f'CPPFLAGS=-DV6_TOWER_STEP={step}'+(' -DV6_TOWER_FULL_ROUTE' if args.full else ''),str(build/'tower.adf')],
            stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['python3',str(ROOT/'tools/amiga/run_tower_probe.py'),
        '--build',str(build),'--step',str(step),'--measure'],check=True)
    reports.append(json.loads((build/'capture.json').read_text()))
(ROOT/('build/amiga-tower/full-measurements.json' if args.full else 'build/amiga-tower/step-measurements.json')).write_text(json.dumps(reports,indent=2)+'\n')
