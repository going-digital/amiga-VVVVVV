#!/usr/bin/env python3
"""Eight-channel DMA scheduling under original Yes Men actor pressure."""
import ctypes as C,subprocess
from test_player import ROOT,BUILD,Room
from test_north_route import Bank
from tower_gameplay_data import north_route_room
class Actor(C.Structure):
 _fields_=[('rows',C.POINTER(C.c_uint32)),('x',C.c_int16),('y',C.c_int16),*[(n,C.c_uint16) for n in ('crop','width','height','colour')]]
class Span(C.Structure):
 _fields_=[('actor',C.c_uint8),('channel',C.c_uint8)]+[(n,C.c_uint16) for n in ('first','last','left','start','stop','words','clip')]
class Plan(C.Structure):_fields_=[('spans',Span*14),('count',C.c_uint16),('used',C.c_uint16*8)]
def main():
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-shared','-fPIC',str(ROOT/'amiga_version/sprite_mux.c'),'-o',str(BUILD/'sprite_mux.so')],check=True)
 mux=C.CDLL(str(BUILD/'sprite_mux.so'));core=C.CDLL(str(BUILD/'north_route.so'))
 mux.v6_sprite_mux_plan.argtypes=[C.POINTER(Plan),C.POINTER(Actor),C.c_uint]
 mux.v6_sprite_mux_update.argtypes=mux.v6_sprite_mux_plan.argtypes
 mux.v6_sprite_mux_pressure.argtypes=[C.POINTER(Actor),C.c_uint,C.POINTER(Actor)]
 mux.v6_sprite_mux_owned_plan.argtypes=mux.v6_sprite_mux_plan.argtypes
 mux.v6_sprite_mux_owned_replan.argtypes=mux.v6_sprite_mux_plan.argtypes
 wp=C.POINTER(C.c_uint16);mux.v6_sprite_mux_dma.argtypes=[C.POINTER(wp),C.POINTER(Plan),C.POINTER(Actor)]
 mux.v6_sprite_mux_copper.argtypes=[wp,wp,C.c_uint,C.POINTER(Plan),C.POINTER(Actor)]
 mux.v6_sprite_mux_rendered_copper.argtypes=mux.v6_sprite_mux_copper.argtypes
 mux.v6_sprite_mux_append_palette.argtypes=[wp,C.c_uint,C.POINTER(Plan),C.POINTER(Actor)]
 core.v6_north_init.argtypes=[C.POINTER(Bank),C.POINTER(Room),C.c_int,C.c_int,C.c_int]
 core.v6_north_entities.argtypes=[C.POINTER(Bank),C.POINTER(Room),C.c_int]
 d=north_route_room('yesmen');tiles=(C.c_uint16*1200)(*d['tiles']);room=Room(tiles,0,0);bank=Bank()
 assert core.v6_north_init(C.byref(bank),C.byref(room),112,105,0)
 rows=(C.c_uint32*32)(*[0xa5a5f00f^(i*0x01010101) for i in range(32)])
 actors=(Actor*14)();plan=Plan();dma=(C.c_uint16*(8*196))();cases=0
 pointers=(wp*8)(*[C.cast(C.byref(dma,i*196*2),wp) for i in range(8)])
 incremental=[Plan() for _ in range(17)];replanned=[Plan() for _ in range(17)];updates=0
 for tick in range(4096):
  core.v6_north_entities(C.byref(bank),C.byref(room),0)
  for player_y in range(-16,241,16):
   actors[0]=Actor(rows,140,player_y,6,16,32,0x6ff);n=1
   for enemy in bank.enemies:
    for crop,width in ((0,16),(16,4)):
     actors[n]=Actor(rows,enemy.x,enemy.y,crop,width,20,0xff4);n+=1
   for y in (80,136):actors[n]=Actor(rows,64,y,0,16,16,0x888);n+=1
   assert mux.v6_sprite_mux_plan(C.byref(plan),actors,n),(tick,player_y,[e.y for e in bank.enemies])
   owned=Plan();assert mux.v6_sprite_mux_owned_plan(C.byref(owned),actors,n) and owned.count==plan.count and bytes(owned.spans)[:plan.count*C.sizeof(Span)]==bytes(plan.spans)[:plan.count*C.sizeof(Span)] and list(owned.used)==list(plan.used)
   rp=replanned[(player_y+16)//16]
   assert mux.v6_sprite_mux_owned_replan(C.byref(rp),actors,n)
   assert rp.count==plan.count and bytes(rp.spans)[:plan.count*C.sizeof(Span)]==bytes(plan.spans)[:plan.count*C.sizeof(Span)] and list(rp.used)==list(plan.used)
   inc=incremental[(player_y+16)//16]
   before=bytes(inc)
   if mux.v6_sprite_mux_update(C.byref(inc),actors,n):updates+=1
   else:
    assert bytes(inc)==before
    assert mux.v6_sprite_mux_plan(C.byref(inc),actors,n)
   assert inc.count==plan.count
   wanted={s.actor:(s.first,s.last,s.left,s.start,s.stop,s.clip) for s in plan.spans[:plan.count]}
   assert {s.actor:(s.first,s.last,s.left,s.start,s.stop,s.clip) for s in inc.spans[:inc.count]}==wanted
   ends=[0]*8
   for span in inc.spans[:inc.count]:
    assert ends[span.channel]<=span.start and inc.used[span.channel]+2<=196
    ends[span.channel]=span.stop+2
   assert plan.count==sum(a.y<216 and a.y+a.height>16 for a in actors[:n])
   ends=[0]*8
   for span in plan.spans[:plan.count]:
    assert ends[span.channel]<=span.start and plan.used[span.channel]+2<=196
    ends[span.channel]=span.stop+2
   if tick%64==0:
    for cy in (0,16,73,86,134,180,204,216):
     optional=Actor(rows,80,cy,6,16,32,0xff4)
     start=max(16,cy);stop=min(216,cy+32)
     expected=any(sum(max(16,a.y)<=y<min(216,a.y+a.height)+2 for a in actors[:n] if a.y<216 and a.y+a.height>16)>=8 for y in range(start,stop+2)) if start<stop else False
     assert bool(mux.v6_sprite_mux_pressure(actors,n,C.byref(optional)))==expected,('rectangle pressure',tick,player_y,cy)
    mux.v6_sprite_mux_dma(pointers,C.byref(plan),actors)
    for span in plan.spans[:plan.count]:
     a=actors[span.actor];at=span.channel*196+span.words
     assert dma[at]==((span.start&255)<<8)|(span.left>>1)
     assert dma[at+1]==((span.stop&255)<<8)|((span.start&256)>>6)|((span.stop&256)>>7)|(span.left&1)
     for i,row in enumerate(range(span.first,span.last)):
      bits=(rows[row]>>(16-a.crop))&span.clip
      assert dma[at+2+i*2]==bits and dma[at+3+i*2]==(bits if span.channel&1 else 0)
    for channel in range(8):assert dma[channel*196+plan.used[channel]:channel*196+plan.used[channel]+2]==[0,0]
    from test_menu_slide import events
    game=(C.c_uint16*14)(0x2c01,0xfffe,0x0100,0x3600,0x6bdf,0xfffe,0x00e4,0,0xffdf,0xfffe,0x0bdf,0xfffe,0xffff,0xfffe)
    copper=(C.c_uint16*512)();words=mux.v6_sprite_mux_copper(copper,game,14,C.byref(plan),actors);assert words
    rendered=(C.c_uint16*512)();assert mux.v6_sprite_mux_rendered_copper(rendered,game,14,C.byref(plan),actors)==words and bytes(rendered)==bytes(copper)
    # Native static lists retain their early register prefix and merge only
    # the late ring-wrap tail. It must match a complete chronological merge.
    split=(C.c_uint16*512)();split[:4]=game[:4]
    tail_words=mux.v6_sprite_mux_rendered_copper(C.cast(C.byref(split,8),wp),C.cast(C.byref(game,8),wp),10,C.byref(plan),actors)
    assert tail_words+4==words and bytes(split)==bytes(copper),('retained prefix / ring-wrap merge',tick)
    static=(C.c_uint16*6)(0x2c01,0xfffe,0x100,0x3600,0xffff,0xfffe)
    expected=(C.c_uint16*512)();nw=mux.v6_sprite_mux_copper(expected,static,6,C.byref(plan),actors)
    direct=(C.c_uint16*512)();direct[:6]=static[:]
    assert mux.v6_sprite_mux_append_palette(direct,6,C.byref(plan),actors)==nw and bytes(direct)==bytes(expected)
    trace=events(list(copper[:words]));colours=[(line,reg,val) for line,reg,val in trace if 0x1a2<=reg<=0x1be]
    assert colours==[(s.start-1,0x180+2*(17+s.channel//2*4+(s.channel&1)*2),actors[s.actor].colour) for s in plan.spans[:plan.count]]
    assert (107,0xe4,0) in trace,trace
   cases+=1
 for i in range(9):actors[i]=Actor(rows,0,64,0,16,32,0xfff)
 before=bytes(plan);assert not mux.v6_sprite_mux_plan(C.byref(plan),actors,9) and bytes(plan)==before
 actors[0].height=33;assert not mux.v6_sprite_mux_plan(C.byref(plan),actors,1) and bytes(plan)==before
 print('PASS sprite multiplexing:',cases,'states and',updates,'retained channel assignments;','original enemy/player-height states; full DMA pixels/controls/terminators; channel exhaustion preserves output')
if __name__=='__main__':main()
