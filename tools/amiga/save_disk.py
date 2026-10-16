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
    size=struct.unpack_from('>I',image,block+12)[0]
    assert struct.unpack_from('>I',image,block)[0]==8 and size in (44,96,112,144)
    assert sum(struct.unpack_from('>128I',image,block))&0xffffffff==0
    record=image[block+24:block+24+size]
    magic,version,length=struct.unpack_from('>4sHH',record)
    assert magic==b'V6CS' and length==size and version in ((1,) if size==44 else (6,7,8) if size==144 else (4,5) if size==112 else (2,3))
    assert zlib.crc32(record[:-4])==struct.unpack_from('>I',record,size-4)[0]
    if size==96:assert record[90:92]==b'\0\0'
    if size>=112:assert record[102]&0xf0==0 and record[103:108]==bytes(5)
    if size==144:assert (record[138:140]==bytes(2) if version==6 else struct.unpack_from('>H',record,138)[0]&~(7 if version==8 else 1)==0)
    return record
def legacy_record_fixture(path:Path,name=b'campaign.v6cs'):
    """Downgrade a disposable capture disk to a valid v1 checkpoint-only record."""
    record=read_record(path,name);assert len(record)==96 and record[5]==2
    legacy=bytearray(record[:40]);struct.pack_into('>HH',legacy,4,1,44)
    legacy+=struct.pack('>I',zlib.crc32(legacy))
    image=bytearray(path.read_bytes())
    for header in range(0,len(image),512):
        if struct.unpack_from('>I',image,header)[0]!=2 or struct.unpack_from('>I',image,header+508)[0]!=0xfffffffd:continue
        n=image[header+432]
        if image[header+433:header+433+n]!=name:continue
        block=struct.unpack_from('>I',image,header+16)[0]*512
        struct.pack_into('>I',image,header+324,44)
        struct.pack_into('>I',image,block+12,44)
        image[block+24:block+120]=legacy+bytes(52)
        for offset in (header,block):
            struct.pack_into('>I',image,offset+20,0)
            struct.pack_into('>I',image,offset+20,(-sum(struct.unpack_from('>128I',image,offset)))&0xffffffff)
        path.write_bytes(image);assert read_record(path,name)==legacy;return
    raise AssertionError('Missing capture record')

def replace_record_fixture(path:Path,record:bytes,name=b'campaign.v6cs'):
    """Replace a single-block record on a disposable OFS capture disk."""
    previous=read_record(path,name)
    magic,version,length=struct.unpack_from('>4sHH',record)
    assert magic==b'V6CS' and length==len(record) and (version,length) in ((1,44),(2,96),(3,96),(4,112),(5,112),(6,144),(7,144),(8,144))
    assert zlib.crc32(record[:-4])==struct.unpack_from('>I',record,length-4)[0]
    image=bytearray(path.read_bytes())
    for header in range(0,len(image),512):
        if struct.unpack_from('>I',image,header)[0]!=2 or struct.unpack_from('>I',image,header+508)[0]!=0xfffffffd:continue
        n=image[header+432]
        if image[header+433:header+433+n]!=name:continue
        block=struct.unpack_from('>I',image,header+16)[0]*512
        struct.pack_into('>I',image,header+324,length)
        struct.pack_into('>I',image,block+12,length)
        padded=max(length,len(previous))
        image[block+24:block+24+padded]=record+bytes(padded-length)
        for offset in (header,block):
            struct.pack_into('>I',image,offset+20,0)
            struct.pack_into('>I',image,offset+20,(-sum(struct.unpack_from('>128I',image,offset)))&0xffffffff)
        path.write_bytes(image);assert read_record(path,name)==record;return
    raise AssertionError('Missing capture record')
