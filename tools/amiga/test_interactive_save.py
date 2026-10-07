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
V6CampaignIO v6_campaign_dos;
static const char *save_name="save",*save_temp="temp",*save_backup="backup";
static V6TowerGameplay world;
static V6HallwayStory hallway_story;
static V6Checkpoint bank={144,1824,20,505147,0,0};
static const V6TowerRouteRoom tower_route_rooms[4]={{109,109,0,0,&bank,1,0},{0},{0},{0}};
'''+ '\n'.join(parts)+'''
void setup(const V6CampaignIO *io,const V6CheckpointSave *c,const V6HallwayStory *s) {v6_campaign_dos=*io;world.save=*c;hallway_story=*s;}
int save(void){return ui_save_checked();}
int load(V6CheckpointSave *c,V6HallwayStory *s){return ui_load_checked(c,s);}
'''
    # Extract complete production functions, leaving platform ownership outside this host fixture.
    (out/'ui-consumer.c').write_text(fixture)
    subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-I'+str(ROOT/'amiga_version'),str(out/'ui-consumer.c'),str(ROOT/'amiga_version/campaign_save.c'),str(ROOT/'amiga_version/campaign_file.c'),'-o',str(out/'ui-consumer.so')],check=True)
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
    print('PASS actual UI consumers: malformed final/backup preservation, transactional load rejection, new/replaced/recovered saves and invalid-live-state guard')
if __name__=='__main__':main()
