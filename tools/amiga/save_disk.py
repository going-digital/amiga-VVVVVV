"""Private OFS data disk, seeded once from the generated boot filesystem."""
from pathlib import Path
import struct
import zlib
def create_save_disk(template:Path,target:Path):
    if target.exists():return
    image=bytearray(template.read_bytes());root=(len(image)//512//2)*512
    assert struct.unpack_from('>I',image,root)[0]==2 and struct.unpack_from('>I',image,root+508)[0]==1
    label=b'V6 Saves';image[root+432:root+464]=bytes([len(label)])+label+bytes(31-len(label))
    struct.pack_into('>I',image,root+20,0)
    struct.pack_into('>I',image,root+20,(-sum(struct.unpack_from('>128I',image,root)))&0xffffffff)
    target.write_bytes(image)
def read_record(path:Path,name=b'campaign.v6cs'):
    image=path.read_bytes();headers=[]
    for block in range(0,len(image),512):
        if struct.unpack_from('>I',image,block)[0]!=2 or struct.unpack_from('>I',image,block+508)[0]!=0xfffffffd:continue
        length=image[block+432]
        if image[block+433:block+433+length]==name:headers.append(block)
    assert len(headers)==1,headers
    header=headers[0];assert sum(struct.unpack_from('>128I',image,header))&0xffffffff==0
    block=struct.unpack_from('>I',image,header+16)[0]*512
    assert struct.unpack_from('>I',image,block)[0]==8 and struct.unpack_from('>I',image,block+12)[0]==44
    assert sum(struct.unpack_from('>128I',image,block))&0xffffffff==0
    record=image[block+24:block+68]
    assert zlib.crc32(record[:40])==struct.unpack_from('>I',record,40)[0]
    return record
