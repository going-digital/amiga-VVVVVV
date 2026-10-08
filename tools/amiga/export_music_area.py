#!/usr/bin/env python3
"""Generate the immutable source music map; no soundtrack assets included."""
import argparse
from pathlib import Path
from audit_music import catalogue

def export(out):
    values=catalogue()['area_map']
    text='/* Generated from Music.cpp areamap; regenerate through Makefile. */\n'
    text+='static const signed char v6_music_area_map[400]={\n'
    text+='\n'.join(' '+','.join(map(str,values[i:i+20]))+',' for i in range(0,400,20))
    text+='\n};\n'
    out.mkdir(parents=True,exist_ok=True);path=out/'music_area_map.h'
    if not path.exists() or path.read_text()!=text:path.write_text(text)
    return path

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    print(export(p.parse_args().out))
if __name__=='__main__':main()
