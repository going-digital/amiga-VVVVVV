#!/usr/bin/env python3
"""Actual UI file consumers preserve records rejected by checkpoint validation."""
import ctypes as C
from pathlib import Path
import subprocess
from test_player import block
from test_campaign_file import Files,IO
from test_campaign_save import Checkpoint,Story,values
ROOT=Path(__file__).resolve().parents[2]
def main():
    out=ROOT/'build/amiga-campaign-save';out.mkdir(parents=True,exist_ok=True)
    source=(ROOT/'amiga_version/tower_probe.c').read_text()
    parts=[block(source,source.rindex('static int '+name+'(')) for name in ('checkpoint_bank_valid','ui_load_checked','ui_save_checked')]
    fixture='''
#include "campaign_file.h"
#include "tower_route.h"
#include "campaign_route.h"
V6CampaignIO v6_campaign_dos;
static const char *save_name="save",*save_temp="temp",*save_backup="backup";
static V6TowerGameplay world;
static V6HallwayStory hallway_story;
static V6Checkpoint bank={144,1824,20,505147,0,0};
static V6Teleporter teleporter={112,48,0,1,1,0};
static const V6TowerRouteRoom tower_route_rooms[5]={{109,109,0,0,&bank,1,0,0},{0},{0},{0},{111,104,0,0,0,0,0,&teleporter}};
'''+ '\n'.join(parts)+'''
void setup(const V6CampaignIO *io,const V6CheckpointSave *c,const V6HallwayStory *s) {v6_campaign_dos=*io;world.save=*c;hallway_story=*s;}
int valid_four(const V6CheckpointSave *c){return v6_campaign_route_checkpoint_valid(c,tower_route_rooms,4);}
int save(void){return ui_save_checked();}
int load(V6CheckpointSave *c,V6HallwayStory *s){return ui_load_checked(c,s);}
'''
    # Extract complete production functions, leaving platform ownership outside this host fixture.
    (out/'ui-consumer.c').write_text(fixture)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(out/'ui-consumer.c'),str(ROOT/'amiga_version/campaign_save.c'),str(ROOT/'amiga_version/campaign_file.c'),*[str(ROOT/'amiga_version'/name) for name in ('campaign_route.c','teleporter.c','player.c','terrain.c')],'-o',str(out/'ui-consumer.so')],check=True)
    lib=C.CDLL(str(out/'ui-consumer.so'));lib.setup.argtypes=[C.POINTER(IO),C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.load.argtypes=[C.POINTER(Checkpoint),C.POINTER(Story)]
    lib.v6_campaign_encode.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(Checkpoint),C.POINTER(Story)]
    c=Checkpoint(140,1822,1,1,109,109,505147);story=Story(0,0,9,1,1)
    def encoded(cp):
        raw=(C.c_uint8*44)();assert lib.v6_campaign_encode(raw,44,C.byref(cp),C.byref(story));return bytes(raw)
    old=encoded(c);bad=Checkpoint(*values(c));bad.x+=1;bad_record=encoded(bad)
    newer=Checkpoint(*values(c));newer.dir=0
    for image in ({b'save':bad_record,b'backup':old},{b'save':old,b'backup':bad_record},{b'backup':bad_record,b'temp':old}):
        f=Files();f.files=image.copy();lib.setup(C.byref(f.io),C.byref(newer),C.byref(story))
        assert lib.save()==4 and f.files==image
        a=Checkpoint(*([77]*7));b=Story(*([88]*5));before=bytes(a),bytes(b)
        assert lib.load(C.byref(a),C.byref(b))==4 and (bytes(a),bytes(b))==before and f.files==image
        assert not any(call[0] in ('write','rename') for call in f.calls)
    for image in ({},{b'save':old},{b'backup':old,b'temp':bad_record}):
        f=Files();f.files=image.copy();lib.setup(C.byref(f.io),C.byref(newer),C.byref(story));assert lib.save()==0
        assert f.files=={b'save':encoded(newer)}
    f=Files();f.files={b'save':old,b'backup':old};lib.setup(C.byref(f.io),C.byref(bad),C.byref(story))
    assert lib.save()==1 and not f.calls and f.files=={b'save':old,b'backup':old}
    f=Files();f.files={b'temp':old};lib.setup(C.byref(f.io),C.byref(newer),C.byref(story));assert lib.save()==2 and f.files=={b'temp':old}
    # New room's canonical teleporter record passes the real file consumers;
    # CRC-valid wrong centre, gravity, ID or facing must preserve both files.
    tele=Checkpoint(156,92,0,1,111,104,0)
    lib.valid_four.argtypes=[C.POINTER(Checkpoint)]
    assert not lib.valid_four(C.byref(tele))
    tele_blob=encoded(tele)
    f=Files();lib.setup(C.byref(f.io),C.byref(tele),C.byref(story))
    assert lib.save()==0 and f.files[b'save']==tele_blob
    out_cp=Checkpoint();out_story=Story()
    assert lib.load(C.byref(out_cp),C.byref(out_story))==0 and values(out_cp)==values(tele)
    for field,value in (('x',157),('y',93),('gravity',1),('id',1)):
        invalid=Checkpoint(*values(tele));setattr(invalid,field,value);blob=encoded(invalid)
        for final,backup in ((blob,tele_blob),(tele_blob,blob),(None,blob)):
            f.files.clear()
            if final is not None:f.files[b'save']=final
            f.files[b'backup']=backup;before=dict(f.files)
            assert lib.save()==4 and f.files==before
            out_before=bytes(out_cp),bytes(out_story)
            assert lib.load(C.byref(out_cp),C.byref(out_story))==4 and f.files==before
            assert (bytes(out_cp),bytes(out_story))==out_before
    # Compile the same consumers under the dedicated build's capability gate.
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
        '-DV6_TOWER_BUILDING','-I'+str(ROOT/'amiga_version'),str(out/'ui-consumer.c'),
        *[str(ROOT/'amiga_version'/name) for name in ('campaign_save.c','campaign_file.c','campaign_route.c','teleporter.c','player.c','terrain.c')],
        '-o',str(out/'ui-building.so')],check=True)
    dedicated=C.CDLL(str(out/'ui-building.so'))
    dedicated.setup.argtypes=lib.setup.argtypes;dedicated.load.argtypes=lib.load.argtypes
    zero=Story(0,0,0,0,0)
    for image in ({b'save':tele_blob},{b'save':tele_blob,b'backup':tele_blob},{b'backup':tele_blob}):
        f.files=image.copy();dedicated.setup(C.byref(f.io),C.byref(tele),C.byref(zero))
        before=bytes(out_cp),bytes(out_story)
        assert dedicated.load(C.byref(out_cp),C.byref(out_story))==4
        assert f.files==image and (bytes(out_cp),bytes(out_story))==before
        assert dedicated.save()==4 and f.files==image
    story=zero
    clean=encoded(tele)
    f.files={b'save':clean,b'backup':tele_blob}
    dedicated.setup(C.byref(f.io),C.byref(tele),C.byref(zero))
    assert dedicated.load(C.byref(out_cp),C.byref(out_story))==4 and f.files=={b'save':clean,b'backup':tele_blob}
    f.files={b'save':clean}
    assert dedicated.load(C.byref(out_cp),C.byref(out_story))==0 and values(out_cp)==values(tele)
    f.files.clear()
    print('PASS actual UI consumers: malformed final/backup preservation, transactional load rejection, new/replaced/recovered saves and invalid-live-state guard')
if __name__=='__main__':main()
