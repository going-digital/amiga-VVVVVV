#!/usr/bin/env python3
"""Full-width one-plane captions, sprite clipping, bars and Copper restoration."""
import ctypes as C
import random
import subprocess
from test_map_draw import arrays
from test_player import ROOT

class Overlay(C.Structure):
    _fields_=[('bitmap',C.c_uint32),('blank',C.c_uint32),('start',C.c_uint16),('stop',C.c_uint16),('colour',C.c_uint16)]

class Prefix(C.Structure):
    _fields_=[(n,C.c_uint16) for n in ('words','c0','c1')]+[('blocks',(C.c_uint16*24)*7),('sizes',C.c_uint16*7)]
class Span(C.Structure):
    _fields_=[('actor',C.c_uint8),('channel',C.c_uint8)]+[(n,C.c_uint16) for n in ('first','last','left','start','stop','words','clip')]
class Plan(C.Structure):
    _fields_=[('spans',Span*14),('count',C.c_uint16),('used',C.c_uint16*8)]
class Actor(C.Structure):
    _fields_=[('rows',C.c_void_p),('x',C.c_int16),('y',C.c_int16)]+[(n,C.c_uint16) for n in ('crop','width','height','colour')]

def main():
    build=ROOT/'build/amiga-terminal-layer';build.mkdir(exist_ok=True)
    library=build/'layer.so'
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
                    '-fsanitize=undefined','-fno-sanitize-recover=all',
                    str(ROOT/'amiga_version/terminal_layer.c'),'-o',str(library)],check=True)
    lib=C.CDLL(str(library))
    lib.v6_terminal_layer_decode.argtypes=[C.c_void_p,C.c_void_p,C.c_uint]
    lib.v6_terminal_layer_occlude.argtypes=[C.c_void_p]
    lib.v6_terminal_layer_bars.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint]
    lib.v6_terminal_layer_copper.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,*([C.c_uint32]*4),C.POINTER(Overlay),C.c_int,C.c_uint]
    assets=ROOT/'build/amiga-feasibility'
    fixture=ROOT/'build/amiga-terminal-native/terminal_fixture_assets.h'
    original=bytes(arrays(fixture,'fixture_world'));expected=bytes(arrays(fixture,'fixture_read'))
    border=arrays(assets/'pickup_assets.h','pickup_border')
    offsets=arrays(assets/'terminal_layer_assets.h','terminal_row_offsets')
    packets=bytes(arrays(assets/'terminal_layer_assets.h','terminal_row_packets'))
    row=(C.c_uint8*40)()
    for y in range(48,168):
        encoded=packets[offsets[y-48]:offsets[y-47]]
        assert lib.v6_terminal_layer_decode(row,encoded,len(encoded))
        assert not lib.v6_terminal_layer_decode(row,encoded,len(encoded)-1)
        box=next((b for b in ((12,60,296,24),(36,86,248,69)) if b[1]<=y<b[1]+b[3]),None)
        if not box:assert bytes(row)==bytes(40);continue
        x,top,w,h=box;local=y-top
        if local<8 or local>=h-8:
            bottom=local>=h-8;by=local-(h-8) if bottom else local;tiles=(5,6,7) if bottom else (0,1,2)
            assert bytes(row)==bytes([border[tiles[0]*8+by]]+[border[tiles[1]*8+by]]*38+[border[tiles[2]*8+by]])
        else:
            # Interior glyph pixels agree with the independent source compositor.
            for px in range(x+8,x+w-8):
                at=y*40+px//8;bit=128>>(px&7)
                assert bool(row[px//8]&bit)==bool(expected[9600+at]&bit),(px,y)
    for bad in (b'',bytes([168,0]),bytes([39])+bytes(39),bytes([167])):
        assert not lib.v6_terminal_layer_decode(row,bad,len(bad))
    rng=random.Random(218);clipped=0
    for y in range(0,240):
        first,last=52+y,52+y+32
        dma=(C.c_uint16*68)(((first&255)<<8),((last&255)<<8)|((first&256)>>6)|((last&256)>>7),*[rng.randrange(65536) for _ in range(64)],0,0)
        want=list(dma)
        for sy in range(32):
            if 60<=y+sy<84 or 86<=y+sy<155:want[2+sy*2:4+sy*2]=[0,0]
        clipped+=lib.v6_terminal_layer_occlude(dma);assert list(dma)==want
    world=bytearray(20480)
    for p in range(2):world[p*10240:p*10240+9600]=original[p*9600:(p+1)*9600]
    world=C.create_string_buffer(bytes(world));bitmap=C.create_string_buffer(original);previous=0
    for position in [*range(0,361,25),361,*range(350,-1,-25),0]:
        lib.v6_terminal_layer_bars(bitmap,world,position,previous);previous=position
        want=bytearray(original)
        for py in (*range(16),*range(224,240)):
            for px in range(320):
                at=py*40+px//8;bit=128>>(px&7)
                bar=px<position if py<16 else px>=360-position
                for p in range(3):
                    value=bool(p) if bar else bool(original[p*9600+at]&bit)
                    if value:want[p*9600+at]|=bit
                    else:want[p*9600+at]&=~bit
        assert bitmap.raw[:28800]==want,position
    commands=[(0x100,0x3600),(0x180,0x123),(0x182,0x456),(0xe0,1),(0xe2,0),
              (0xe8,1),(0xea,10240),(0xe4,1),(0xe6,20480+8000),
              (0x63d1,0xfffe),(0x1a2,0x6ff),(0x6bdf,0xfffe),(0xe4,1),(0xe6,20480),
              (0x82d1,0xfffe),(0xf0,4),(0xf2,0),(0x100,0x5600),
              (0xd2d1,0xfffe),(0x100,0x3600),(0xffdf,0xfffe),(0xffff,0xfffe)]
    source=(C.c_uint16*(len(commands)*2))(*[v for pair in commands for v in pair]);npc=Overlay(0x40000,0x8000,131,211,0xff4)
    prefix_source=(C.c_uint16*10)(0x100,0x3600,0x180,0x123,0x182,0x456,0x2c01,0xfffe,0xffff,0xfffe)
    prefix=Prefix();lib.v6_terminal_scene_prefix.argtypes=[C.POINTER(Prefix),C.c_void_p,C.c_uint]
    assert lib.v6_terminal_scene_prefix(C.byref(prefix),prefix_source,10)
    assert (prefix.words,prefix.c0,prefix.c1)==(6,0x123,0x456)
    lib.v6_terminal_scene_windows.argtypes=[C.POINTER(Prefix),*([C.c_uint32]*4)]
    lib.v6_terminal_scene_windows(C.byref(prefix),0x30000,0x50000,0x10000,0x8000)
    plan=Plan();plan.count=2;plan.spans[0]=Span(0,0,0,16,128,100,116,0,65535);plan.spans[1]=Span(1,0,0,32,128,180,212,0,65535)
    actors=(Actor*2)();actors[0].colour=0x6ff;actors[1].colour=0x9f9
    lib.v6_terminal_scene_copper.argtypes=[C.c_void_p,C.POINTER(Prefix),C.POINTER(Plan),C.POINTER(Actor),C.POINTER(Overlay),*([C.c_uint32]*4),C.c_int,C.c_uint]
    for fast in (False,True):
      for visible in (0,1):
        out=(C.c_uint16*512)();n=lib.v6_terminal_layer_copper(out,source,len(source),0x30000,0x50000,0x10000,0x8000,C.byref(npc),visible,174)
        if fast:
            C.memmove(out,prefix_source,prefix.words*2)
            n=lib.v6_terminal_scene_copper(out,C.byref(prefix),C.byref(plan),actors,C.byref(npc),0x30000,0x50000,0x10000,0x8000,visible,174)
        assert n and n<=512
        epoch=line=barriers=0;states=[];regs={}
        for r,v in zip(list(out)[:n:2],list(out)[1:n:2]):
            if r==0xffff:break
            if r&1:
                states.append((line,dict(regs)))
                if r==0xffdf:epoch=256;line=255;barriers+=1
                else:line=epoch+(r>>8);assert line==44 or r&255>=0xd1
            else:regs[r]=v
        states.append((line,dict(regs)));assert barriers==1
        def state(y):return [v for line,v in states if line<=y][-1]
        def pointer(r,reg):return (r[reg]<<16)|r[reg+2]
        assert state(52)[0x100]==state(276)[0x100]==0x5600
        assert state(68)[0x100]==0x3600
        if visible:
            for line in (111,134,137,205):assert state(line)[0x100]==0x1200
            for line in (135,206):
                r=state(line);y=line-51
                assert r[0x100]==0x5600
                assert pointer(r,0xe0)==0x10000+y*40
                assert pointer(r,0xe4)==0x10000+20480+((200+y)&255)*40
                assert pointer(r,0xf0)==npc.bitmap+(52+y-npc.start)*40
                assert (r[0x180],r[0x182])==(0x123,0x456)
            assert pointer(state(137),0xe0)==0x50000+86*40
        assert state(211)[0x100]==0x3600 and state(276)[0x18c]==0
        assert state(206)[0x1a2]==(0x9f9 if fast else 0x6ff)
    print('PASS full-width captions: 120 source glyph/border rows; 240 sprite clips;',clipped,'masked rows; bar ramps and Copper plane/palette/pointer restoration')

if __name__=='__main__':main()
