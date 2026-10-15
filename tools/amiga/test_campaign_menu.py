#!/usr/bin/env python3
"""V6 metadata vectors, legacy migration and actual transaction faults."""
import ctypes as C,struct,zlib,subprocess
from test_campaign_save import ROOT,Checkpoint,Story,values
from test_campaign_state import Exploration
from test_station_trigger import Story as Yellow
from test_campaign_collection import Collect
from test_campaign_hint import Hints
from test_save_summary import Clock,Summary
from test_campaign_file import Files,IO
from test_campaign_replace import Operations
class Menu(C.Structure):_fields_=[('clock',Clock),('deaths',C.c_uint32),('crew_mask',C.c_uint16),('last',Summary)]
class Record(C.Structure):_fields_=[('checkpoint',Checkpoint),('red',Story),('yellow',Yellow),('explored',Exploration),('collected',Collect),('hints',Hints),('menu',Menu)]
def main():
 out=ROOT/'build/amiga-campaign-menu';out.mkdir(parents=True,exist_ok=True)
 sources=['campaign_save.c','campaign_file.c','campaign_menu.c','campaign_menu_file.c','save_summary.c']
 subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',*[str(ROOT/'amiga_version'/s) for s in sources],'-o',str(out/'menu.so')],check=True)
 lib=C.CDLL(str(out/'menu.so'));rp=C.POINTER(Record)
 lib.v6_campaign_menu_encode.argtypes=[C.c_void_p,C.c_size_t,rp];lib.v6_campaign_menu_decode.argtypes=[rp,C.c_void_p,C.c_size_t]
 for name in ('read','recover','replace'):
  getattr(lib,'v6_campaign_menu_'+name).argtypes=[C.POINTER(IO)]+[C.c_char_p]*(1 if name=='read' else 3)+[rp]
 r=Record();r.checkpoint=Checkpoint(60,73,0,1,112,107,443501);r.yellow=Yellow(0,0,7,1,1)
 r.explored.rooms[19]=1;r.hints.map_hint_seen=1;r.collected.bits[0]=64
 r.menu.clock=Clock(1,2,3,4);r.menu.deaths=17;r.menu.crew_mask=5;r.menu.last=Summary(Clock(1,2,3,4),112,107,1,5,1)
 def encode(record):
  b=(C.c_uint8*144)();assert lib.v6_campaign_menu_encode(b,144,C.byref(record));return bytes(b)
 blob=encode(r)
 flags=120;prefix=struct.pack('>4sHH7iI',b'V6CS',6,144,*values(r.checkpoint),flags)+bytes(r.explored)+bytes(r.collected)+bytes(5)
 meta=struct.pack('>4HIBB4HhhHH2x',1,2,3,4,17,5,1,1,2,3,4,112,107,1,5)
 expected=prefix+meta;expected+=struct.pack('>I',zlib.crc32(expected));assert blob==expected and len(blob)==144
 def decode(data,success):
  a=Record.from_buffer_copy(bytes([0xa5])*C.sizeof(Record));before=bytes(a)
  raw=(C.c_uint8*len(data)).from_buffer_copy(data)
  result=lib.v6_campaign_menu_decode(C.byref(a),raw,len(data));assert bool(result)==success
  if not result:assert bytes(a)==before
  return a
 assert encode(decode(blob,True))==blob
 for bit in range(1152):
  b=bytearray(blob);b[bit//8]^=1<<(bit%8);decode(b,False)
 for n in range(144):decode(blob[:n],False)
 decode(blob+b'x',False)
 for offset in [103,104,105,106,107,138,139,121,120]:
  b=bytearray(blob);b[offset]^=128;b[140:]=struct.pack('>I',zlib.crc32(b[:140]));decode(b,False)
 # Version 5 migration does not invent a previous summary or elapsed time.
 old=bytearray(blob[:108]);old[5]=5;old[7]=112;old+=struct.pack('>I',zlib.crc32(old))
 migrated=decode(old,True);assert bytes(migrated.menu.clock)==bytes(8) and migrated.menu.deaths==0 and migrated.menu.crew_mask==5 and not migrated.menu.last.exists
 # All older layouts migrate from a checkpoint admitted by their source version.
 legacy_cp=Checkpoint(156,92,0,0,111,104,0);legacy_map=bytearray(50);legacy_map[91//8]=1<<(91%8)
 for version in range(1,6):
  size=44 if version==1 else 96 if version<4 else 112
  body=struct.pack('>4sHH7iI',b'V6CS',version,size,*values(legacy_cp),0)
  if version>1:body+=legacy_map
  if version>=4:body+=bytes(18)
  elif version>1:body+=bytes(2)
  old_blob=body+struct.pack('>I',zlib.crc32(body));m=decode(old_blob,True)
  assert m.menu.crew_mask==1 and not m.menu.last.exists and not any(bytes(m.menu.clock))
 # Old readers cannot silently discard new metadata.
 ptrs=[C.POINTER(t) for t in (Checkpoint,Story,Yellow,Exploration,Collect,Hints)]
 lib.v6_campaign_hint_decode.argtypes=ptrs+[C.c_void_p,C.c_size_t]
 outputs=[t.from_buffer_copy(bytes([91])*C.sizeof(t)) for t in (Checkpoint,Story,Yellow,Exploration,Collect,Hints)]
 before=tuple(bytes(o) for o in outputs)
 assert not lib.v6_campaign_hint_decode(*[C.byref(o) for o in outputs],(C.c_uint8*144).from_buffer_copy(blob),144)
 assert tuple(bytes(o) for o in outputs)==before
 # V6 admits only the original north-route checkpoint bank. Legacy V5
 # admission stays unchanged, even when a caller recomputes a valid CRC.
 from tower_gameplay_data import north_route_room
 north_cases=0
 lib.v6_campaign_hint_encode.argtypes=[C.c_void_p,C.c_size_t]+ptrs
 for name in ('reflect','yesmen','gantry','security','linear','filter','traffic'):
  room=north_route_room(name)
  for x,y,tile,identifier in room['checkpoints']:
   for direction in (0,1):
    candidate=Record.from_buffer_copy(bytes(r))
    candidate.checkpoint=Checkpoint(x-4,y-(2 if tile==20 else 7),int(tile==20),direction,room['x'],room['y'],identifier)
    bit=(room['y']-100)*20+room['x']-100;candidate.explored.rooms[bit//8]|=1<<(bit%8)
    encoded=encode(candidate);assert encode(decode(encoded,True))==encoded
    assert struct.unpack_from('>7i',encoded,8)==values(candidate.checkpoint)
    legacy=bytearray(encoded[:108]);legacy[5]=5;legacy[7]=112;legacy+=struct.pack('>I',zlib.crc32(legacy))
    decode(legacy,False)
    unchanged=(C.c_uint8*112)(*([0xa5]*112))
    assert not lib.v6_campaign_hint_encode(unchanged,112,*[C.byref(getattr(candidate,n)) for n in ('checkpoint','red','yellow','explored','collected','hints')])
    assert bytes(unchanged)==bytes([0xa5]*112)
    for field in ('x','y','gravity','id','dir'):
     bad=Record.from_buffer_copy(bytes(candidate));setattr(bad.checkpoint,field,getattr(bad.checkpoint,field)+(2 if field=='dir' else 1))
     outbuf=(C.c_uint8*144)(*([0xa5]*144));assert not lib.v6_campaign_menu_encode(outbuf,144,C.byref(bad))
     assert bytes(outbuf)==bytes([0xa5]*144)
    missing=Record.from_buffer_copy(bytes(candidate));missing.explored.rooms[bit//8]&=~(1<<(bit%8))
    assert not lib.v6_campaign_menu_encode((C.c_uint8*144)(),144,C.byref(missing))
    for offset in (8,12,16,20,32):
     bad=bytearray(encoded);struct.pack_into('>I',bad,offset,struct.unpack_from('>I',bad,offset)[0]+2)
     bad[140:]=struct.pack('>I',zlib.crc32(bad[:140]));decode(bad,False)
    north_cases+=1
 oldrecord=encode(migrated)
 def replace(fs,io=None):return lib.v6_campaign_menu_replace(C.byref(io or fs.io),b'save',b'temp',b'backup',C.byref(r))
 def recover(fs,io=None):
  a=Record.from_buffer_copy(bytes([77])*C.sizeof(Record));before=bytes(a)
  result=lib.v6_campaign_menu_recover(C.byref(io or fs.io),b'save',b'temp',b'backup',C.byref(a))
  if result:assert bytes(a)==before
  else:assert encode(a) in (oldrecord,blob)
  return result
 fs=Files();assert replace(fs)==0 and fs.files=={b'save':blob}
 fs=Files();fs.files[b'save']=bytes(old);ops=Operations(fs);assert replace(fs,ops.io)==0
 snapshots=ops.snapshots;steps=ops.count
 for image in snapshots:
  f=Files();f.files=dict(image);assert recover(f)==0 and f.files[b'save'] in (bytes(old),blob) and set(f.files)=={b'save'}
 for after in (False,True):
  for step in range(1,steps+1):
   f=Files();f.files[b'save']=bytes(old);ops=Operations(f,step,after)
   assert replace(f,ops.io)!=0,(step,after)
   f.fault='';assert recover(f)==0 and f.files[b'save'] in (bytes(old),blob)
 for files in [{b'backup':bytes(old)},{b'backup':bytes(old),b'temp':blob}]:
  f=Files();f.files=files;assert replace(f)==0 and f.files=={b'save':blob}
 print(f'PASS V6 menu save: exact vector, 1152 corruptions, V5 migration, {len(snapshots)} interrupted snapshots, {steps*2} transaction failures and backup promotion')
 print('PASS V6 north checkpoint admission:',north_cases,'source checkpoint/direction pairs; malformed banks and missing exploration rejected; V5 admission unchanged')
if __name__=='__main__':main()
