"""Native rescue UI/platform readiness model with a separately compiled runner."""
import ctypes as C
from test_companion import Companion,bind as bind_companion,state as companion_state
from test_rescue_script import VM,Signals,programs
class Rescue:
    def __init__(self,core,skip=False):
        self.core=core;self.skip=skip;self.vm=VM();self.vm.control=self.vm.mood=1
        (self.normal,self.alternate),self.keep=programs()
        core.v6_rescue_start.argtypes=[C.POINTER(VM),C.POINTER(type(self.normal)),C.POINTER(type(self.alternate)),C.c_int]
        core.v6_rescue_tick.argtypes=[C.POINTER(VM),C.c_void_p,C.POINTER(Signals)]
        self.bars=self.fade=self.fade_mode=self.fire=0;self.shown=[];self.flips_applied=0
        bind_companion(core);self.crew=Companion();core.v6_companion_init(C.byref(self.crew));core.v6_companion_idle(C.byref(self.crew),1)
    def input(self,tick,buttons,player):
        v=self.vm
        if tick>=8:
            buttons=4 if v.waiting and tick%30==0 else 0
            if not v.active and v.following:
                phase=self.crew.follow_steps%96
                buttons=1 if phase<12 or 36<=phase<48 else 2 if phase<36 else 0
                if player.x>270 and buttons==2:buttons=1
                if player.x<140 and buttons==1:buttons=2
        self.bars=min(361,self.bars+25) if v.bars else max(0,self.bars-25)
        if v.fade!=self.fade_mode:
            self.fade_mode=v.fade;self.fade=416 if v.fade<0 else 0
        elif self.fade_mode>0:self.fade=min(432,self.fade+24)
        elif self.fade_mode<0:self.fade=max(0,self.fade-24)
        self.signals=Signals(self.bars>=360 if v.bars else self.bars==0,
            self.fade>416 if v.fade>0 else self.fade==0,player.roof>0,bool(buttons&4) and not self.fire)
        self.fire=bool(buttons&4)
        if v.active:
            buttons&=~4
            if not v.control:buttons|=8
        if v.flips!=self.flips_applied:
            buttons|=4;self.flips_applied=v.flips
        return buttons
    def crew_step(self,player,room,death):
        self.core.v6_companion_step(C.byref(self.crew),C.byref(player),C.byref(room),death)
    def tick(self,trigger,story):
        v=self.vm
        if trigger.pending and not v.active:
            assert self.core.v6_hallway_trigger_take(C.byref(trigger))==1
            assert self.core.v6_rescue_start(C.byref(v),C.byref(self.normal),C.byref(self.alternate),self.skip)
        serial=v.ui_serial
        self.core.v6_rescue_tick(C.byref(v),C.byref(story),C.byref(self.signals))
        self.crew.mood=v.mood;self.crew.following=v.following
        assert not v.error
        if v.ui_serial!=serial and v.speech:self.shown.append(v.speech.contents.index)
    def state(self,story):
        v=self.vm
        return tuple(n&0xffffffff for n in (v.pc,v.active,v.error,v.delay,v.waiting,v.bars,v.control,
            v.mood,v.following,v.ui_serial,v.cues,v.flips,v.fade,v.speech.contents.index+1 if v.speech else 0,
            story.red_rescued,story.companion,self.bars,self.fade))
