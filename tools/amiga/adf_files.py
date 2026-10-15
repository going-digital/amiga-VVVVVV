#!/usr/bin/env python3
"""Add bounded root files to a generated private OFS boot image."""
from pathlib import Path
import struct

def get(image,block,index):return struct.unpack_from('>I',image,block*512+index*4)[0]
def put(image,block,index,value):struct.pack_into('>I',image,block*512+index*4,value&0xffffffff)
def checksum(image,block,index):
    put(image,block,index,0)
    put(image,block,index,-sum(struct.unpack_from('>128I',image,block*512)))
def name_hash(name):
    value=len(name)
    for c in name.upper():value=(value*13+c)&0x7ff
    return value%72

def extract(image,name):
    root=len(image)//1024;block=get(image,root,6+name_hash(name))
    while block:
        at=block*512;length=image[at+432]
        if image[at+433:at+433+length].upper()==name.upper():
            size=get(image,block,81);data=get(image,block,4);out=bytearray();seq=1
            while data:
                assert get(image,data,0)==8 and get(image,data,1)==block and get(image,data,2)==seq
                assert sum(struct.unpack_from('>128I',image,data*512))&0xffffffff==0
                n=get(image,data,3);assert 0<n<=488
                out.extend(image[data*512+24:data*512+24+n]);data=get(image,data,4);seq+=1
            assert len(out)==size
            return bytes(out)
        block=get(image,block,124)
    return None

def add(path,files):
    image=bytearray(path.read_bytes());root=len(image)//1024
    assert image[:4]==b'DOS\0' and get(image,root,0)==2 and get(image,root,127)==1
    bitmap=get(image,root,79);assert bitmap and not get(image,root,80)
    def allocate():
        for block in range(2,len(image)//512):
            index=(block-2)//32+1;bit=1<<((block-2)%32)
            value=get(image,bitmap,index)
            if value&bit:put(image,bitmap,index,value&~bit);return block
        raise ValueError('Boot disk is full')
    for source in files:
        name=source.name.encode('ascii');data=source.read_bytes()
        assert 0<len(name)<=30 and data and extract(image,name) is None
        chunks=[data[i:i+488] for i in range(0,len(data),488)];assert len(chunks)<=72
        header=allocate();blocks=[allocate() for _ in chunks];bucket=6+name_hash(name)
        image[header*512:(header+1)*512]=bytes(512)
        for index,value in ((0,2),(1,header),(2,len(blocks)),(4,blocks[0]),(81,len(data)),(124,get(image,root,bucket)),(125,root),(127,0xfffffffd)):
            put(image,header,index,value)
        at=header*512;image[at+432]=len(name);image[at+433:at+433+len(name)]=name
        for i,(block,chunk) in enumerate(zip(blocks,chunks)):
            image[block*512:(block+1)*512]=bytes(512)
            for index,value in ((0,8),(1,header),(2,i+1),(3,len(chunk)),(4,blocks[i+1] if i+1<len(blocks) else 0)):
                put(image,block,index,value)
            image[block*512+24:block*512+24+len(chunk)]=chunk
            put(image,header,77-i,block);checksum(image,block,5)
        checksum(image,header,5);put(image,root,bucket,header)
        assert extract(image,name)==data
    checksum(image,bitmap,0);checksum(image,root,5);path.write_bytes(image)
    print('OFS region files:',', '.join(p.name for p in files))

if __name__=='__main__':
    import sys
    add(Path(sys.argv[1]),[Path(p) for p in sys.argv[2:]])
