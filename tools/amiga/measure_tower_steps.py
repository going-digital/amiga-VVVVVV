#!/usr/bin/env python3
"""Measure synthetic camera steps; overruns are findings, not passing timing tests."""
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
reports=[]
for step in (4,8,16):
    build=ROOT/f'build/amiga-tower-step{step}'
    build.mkdir(parents=True,exist_ok=True)
    with (build/'build.log').open('w') as log:
        subprocess.run(['make','-C',str(ROOT/'amiga_version'),f'BUILD={build}',
            f'CPPFLAGS=-DV6_TOWER_STEP={step}',str(build/'tower.adf')],
            stdout=log,stderr=subprocess.STDOUT,check=True)
    subprocess.run(['python3',str(ROOT/'tools/amiga/run_tower_probe.py'),
        '--build',str(build),'--step',str(step),'--measure'],check=True)
    reports.append(json.loads((build/'capture.json').read_text()))
(ROOT/'build/amiga-tower/step-measurements.json').write_text(json.dumps(reports,indent=2)+'\n')
