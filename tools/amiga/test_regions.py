#!/usr/bin/env python3
"""Regional cache source equivalence, eviction, failed-load isolation and route admission."""
import ctypes as C
from pathlib import Path
import struct
import subprocess
import zlib
from test_player import ROOT
from test_map_draw import arrays
from tower_gameplay_data import north_route_room
from adf_files import extract,add,put,checksum,name_hash


def main():
    out=ROOT/'build/amiga-region-test';out.mkdir(exist_ok=True)
    (out/'shim.c').write_text('''#include "region_cache.h"
static V6RegionCache cache;
void reset(void){v6_region_init(&cache);}
const V6RegionRoom *request(unsigned r,unsigned id,V6RegionRead reader){return v6_region_get(&cache,r,id,reader,0);}
unsigned counter(unsigned n){switch(n){case 0:return cache.active;case 1:return cache.hits;case 2:return cache.reads;case 3:return cache.errors;default:return sizeof(cache);}}
''')
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',
        '-I'+str(ROOT/'amiga_version'),str(out/'shim.c'),*[str(ROOT/'amiga_version'/f) for f in ('region_cache.c','tower_draw.c','tower_stream.c','room_codec.c')],'-o',str(out/'regions.so')],check=True)
    lib=C.CDLL(str(out/'regions.so'))
    class Room(C.Structure):
        _fields_=[(n,C.c_uint16) for n in ('id','x','y','tileset','tile_count','pair_words','display_bytes')]+[(n,C.POINTER(C.c_uint16)) for n in ('tiles','palette','offsets','pairs')]+[('display',C.POINTER(C.c_uint8))]
    Reader=C.CFUNCTYPE(C.c_int,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.POINTER(C.c_uint))
    lib.request.argtypes=[C.c_uint,C.c_uint,Reader];lib.request.restype=C.POINTER(Room)
    assets=ROOT/'build/amiga-feasibility';good={i:(assets/f'north{i}.v6rg').read_bytes() for i in range(6)};files=dict(good);calls=[]
    @Reader
    def reader(context,region,data,capacity,size):
        calls.append(region)
        value=files.get(region)
        if value is None:return 0
        size[0]=len(value)
        if len(value)>capacity:return 0
        C.memmove(data,value,len(value));return 1
    def request(region,room):return lib.request(region,room,reader)
    lib.reset()
    for ident,name in enumerate(('reflect','yesmen','gantry','security','linear','filter','traffic','leap','solitude','conundrum','welcome'),10):
        room=request((ident-10)//2,ident).contents;source=north_route_room(name)
        assert (room.id,room.x,room.y,room.tileset)==(ident,source['x'],source['y'],source['tileset'])
        assert list(room.tiles[:1200])==source['tiles']
        path=assets/(name+'_assets.h')
        for field,size,symbol in (('palette',4,'palette'),('offsets',room.tile_count*32,'pair_offsets'),('pairs',room.pair_words,'pairs')):
            assert list(getattr(room,field)[:size])==arrays(path,name+'_'+symbol)
        assert bytes(room.display[:room.display_bytes])==bytes(arrays(path,name+'_display'))
    assert calls==[0,1,2,3,4,5] and lib.counter(1)==5,calls
    assert request(0,10) and request(1,12) and calls==[0,1,2,3,4,5,0,1],calls
    variants=[]
    def mutation(offset,fmt,value):
        data=bytearray(good[1]);struct.pack_into(fmt,data,offset,value);data[-4:]=struct.pack('>I',zlib.crc32(data[:-4]));variants.append(bytes(data))
    for offset,fmt,value in ((4,'>H',2),(6,'>H',0),(8,'>H',3),(10,'>H',1),(12,'>I',999),
        (16+8,'>H',33),(16+10,'>H',0),(16+14,'>H',0),(16+16,'>I',81),(16+20,'>I',999),
        (16+24,'>I',1),(48,'>H',12),(16+4,'>H',99),(80+2400,'>H',0xffff)):
        mutation(offset,fmt,value)
    # Packet corruption with a fresh container CRC must fail semantic validation.
    data=bytearray(good[1]);offset=struct.unpack_from('>I',data,32)[0]
    tile_count,pair_words=struct.unpack_from('>HH',data,24)
    data[offset+2408+tile_count*64+pair_words*2]=0
    data[-4:]=struct.pack('>I',zlib.crc32(data[:-4]));variants.append(bytes(data))
    display_at=offset+2408+tile_count*64+pair_words*2
    for change in ('packet','span','pair'):
        data=bytearray(good[1])
        if change=='packet':
            row_offset=struct.unpack_from('>I',data,display_at+10)[0]
            struct.pack_into('>H',data,display_at+190+row_offset,0)
        elif change=='span':struct.pack_into('>H',data,display_at+14,0)
        else:data[offset+2408:offset+2408+tile_count*64]=bytes([255])*(tile_count*64)
        data[-4:]=struct.pack('>I',zlib.crc32(data[:-4]));variants.append(bytes(data))
    variants += [good[1][:n] for n in (0,19,79,len(good[1])-1)]+[good[1]+b'X',bytes(12289),None]
    for bad in variants:
        lib.reset();files=dict(good);calls.clear();pinned=request(0,10);before=list(pinned.contents.tiles[:1200]);active=lib.counter(0)
        files[1]=bad;assert not request(1,12)
        assert lib.counter(0)==active and list(pinned.contents.tiles[:1200])==before
        assert request(0,11) and calls==[0,1] and lib.counter(3)==1
    lib.reset();files=dict(good);assert request(0,10);pinned=lib.counter(0)
    assert not request(1,99) and lib.counter(0)==pinned
    assert request(2,14) and request(0,10) and lib.counter(2)==3
    # Repeated eviction must remain bounded and preserve every room's source tiles.
    lib.reset();files=dict(good)
    for i in range(100):
        ident=10+(i*7)%11;name=('reflect','yesmen','gantry','security','linear','filter','traffic','leap','solitude','conundrum','welcome')[ident-10]
        assert list(request((ident-10)//2,ident).contents.tiles[:1200])==north_route_room(name)['tiles']
    # Build an independent minimal OFS fixture: no previous native capture is required.
    disk=bytearray(901120);disk[:4]=b'DOS\0';root=880;bitmap=881
    for index,value in ((0,2),(3,72),(78,0xffffffff),(79,bitmap),(127,1)):put(disk,root,index,value)
    for block in range(2,1760):
        if block in (root,bitmap):continue
        index=(block-2)//32+1;bit=1<<((block-2)%32)
        current=struct.unpack_from('>I',disk,bitmap*512+index*4)[0];put(disk,bitmap,index,current|bit)
    checksum(disk,bitmap,0);checksum(disk,root,5)
    image=out/'pack-files.adf';image.write_bytes(disk)
    collision=next(f'data{i}.v6rg' for i in range(10000) if name_hash(f'data{i}.v6rg'.encode())==name_hash(b'north0.v6rg'))
    extra=out/collision;extra.write_bytes(bytes(range(256))*5)
    add(image,[*[assets/f'north{i}.v6rg' for i in range(6)],extra])
    disk=image.read_bytes()
    for region,data in good.items():assert extract(disk,f'north{region}.v6rg'.encode())==data
    assert extract(disk,collision.encode())==extra.read_bytes()
    # Generic route materialization rejection must retain player/world and route.
    from test_tower_player import libraries
    from test_tower_route import route_setup,Route
    core,_=libraries();route,session,world,keep=route_setup(core)
    Callback=C.CFUNCTYPE(C.c_int,C.POINTER(Route),C.c_uint,C.c_void_p);entries=[]
    @Callback
    def reject(r,index,context):entries.append(index);return 0
    route.materialize=C.cast(reject,C.c_void_p).value
    snapshots=(bytes(route),bytes(session),bytes(world))
    assert not core.v6_tower_route_load(C.byref(route),108,109,0)
    assert entries==[2] and snapshots==(bytes(route),bytes(session),bytes(world))
    route.materialize=None
    assert core.v6_tower_route_load(C.byref(route),108,109,0)
    print('PASS regional cache: all eleven source collision/graphics banks; two bounded slots;',len(variants),'failed candidates preserve pinned room; 100 evictions; OFS files; atomic route admission')

if __name__=='__main__':main()
