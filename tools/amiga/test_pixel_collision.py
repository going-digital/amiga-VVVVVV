#!/usr/bin/env python3
"""Original Hitest and humanoid collision-animation reference comparisons."""
import ctypes as C
import hashlib
import json
import random
import subprocess
from pack_rooms import ROOT
from test_player import BUILD, Player, block, original_reference

original_reference()
entity=(ROOT/'desktop_version/src/Entity.cpp').read_text()
graphics=(ROOT/'desktop_version/src/Graphics.cpp').read_text()
anim=block(entity,entity.index('void entityclass::animatehumanoidcollision('))
hit=block(graphics,graphics.index('bool Graphics::Hitest('))
source=(BUILD/'player_reference.cpp').read_text()+'\n#include "animation.h"\n'+anim+r'''
struct MaskSurface { int w=32,h=32; const uint32_t *rows; };
#define SDL_Surface MaskSurface
struct Graphics {
    SDL_Color ReadPixel(MaskSurface *s,int x,int y) {
        /* Zero alpha deliberately ensures reference tests preserve the red-channel bug. */
        SDL_Color c={static_cast<Uint8>((s->rows[y]>>(31-x))&1),0,0,0}; return c;
    }
    bool Hitest(SDL_Surface*,SDL_Point,SDL_Surface*,SDL_Point);
};
'''+hit+r'''
extern "C" int hit_reference(const uint32_t *a,int ax,int ay,const uint32_t *b,int bx,int by) {
    MaskSurface aa,bb; aa.rows=a; bb.rows=b; Graphics g;
    return g.Hitest(&aa,{ax,ay},&bb,{bx,by});
}
extern "C" void animation_reset() { obj.entities.clear(); obj.entities.resize(1); }
extern "C" int animation_step(V6CollisionAnimation *a,const V6Player *p,int ground,int roof,int death) {
    entclass& e=obj.entities[0]; e.type=EntityType_PLAYER; e.dir=p->dir; e.vx=p->vx;
    e.visualonground=ground; e.visualonroof=roof; game.gravitycontrol=p->gravity; game.deathseq=death;
    obj.animatehumanoidcollision(0);
    a->delay=e.collisionframedelay; a->walk=e.collisionwalkingframe;
    return e.collisiondrawframe;
}
'''
path=BUILD/'pixel_reference.cpp';path.write_text(source)
subprocess.run(['c++','-std=c++11','-O2','-shared','-fPIC','-I/opt/homebrew/include',
    '-I'+str(ROOT/'desktop_version/src'),'-I'+str(ROOT/'amiga_version'),'-I'+str(ROOT/'tools/amiga'),
    str(path),'-L/opt/homebrew/lib','-lSDL3','-o',str(BUILD/'pixel_reference.so')],check=True)
subprocess.run(['cc','-std=c99','-O2','-shared','-fPIC','-fsanitize=undefined','-fno-sanitize-recover=all',
    str(ROOT/'amiga_version/pixel_collision.c'),str(ROOT/'amiga_version/animation.c'),
    '-o',str(BUILD/'pixel_core.so')],check=True)
core=C.CDLL(str(BUILD/'pixel_core.so')); ref=C.CDLL(str(BUILD/'pixel_reference.so'))
args=[C.POINTER(C.c_uint32),C.c_int,C.c_int]*2
core.v6_pixel_hit.argtypes=ref.hit_reference.argtypes=args
rng=random.Random(68000); cases=0
for trial in range(12):
    # Include empty masks, single edge pixels, sparse interiors and dense masks.
    a=(C.c_uint32*32)(*[rng.getrandbits(32) if trial>6 else (1<<rng.randrange(32) if trial else 0) for _ in range(32)])
    b=(C.c_uint32*32)(*[rng.getrandbits(32) if trial>6 else 1<<rng.randrange(32) for _ in range(32)])
    for dx in range(-33,34):
        for dy in range(-33,34):
            assert core.v6_pixel_hit(a,-10,7,b,dx-10,dy+7)==ref.hit_reference(a,-10,7,b,dx-10,dy+7),(trial,dx,dy)
            cases+=1
class Animation(C.Structure):
    _fields_=[('delay',C.c_int),('walk',C.c_int)]
args=[C.POINTER(Animation),C.POINTER(Player),C.c_int,C.c_int,C.c_int]
core.v6_collision_frame.argtypes=ref.animation_step.argtypes=args
ref.animation_reset(); a=Animation(); expected=Animation(); p=Player()
for tick in range(20000):
    p.dir=rng.randrange(2);p.gravity=rng.randrange(2);p.vx=rng.choice((-3,0,3))
    ground,roof=rng.randrange(-1,3),rng.randrange(-1,3);death=rng.choice((-1,-1,-1,30,0))
    actual=core.v6_collision_frame(C.byref(a),C.byref(p),ground,roof,death)
    want=ref.animation_step(C.byref(expected),C.byref(p),ground,roof,death)
    assert (actual,a.delay,a.walk)==(want,expected.delay,expected.walk),tick
report=dict(pixel_cases=cases,animation_ticks=20000,reference_sha256=hashlib.sha256(source.encode()).hexdigest(),
    scope='Original red-channel Hitest with zero-alpha pixels and player collision-frame selection; not a full game-loop replay.')
(BUILD/'pixel-test-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',json.dumps(report))
