#!/usr/bin/env python3
"""North original-room terrain through the paired Amiga tile renderer."""
from test_energize_graphics import main as compare
from tower_gameplay_data import north_route_room

def main():
    for name in ('reflect','yesmen','gantry','security','linear','filter','traffic','leap'):
        compare(name,lambda name=name:north_route_room(name))

if __name__=='__main__':main()
