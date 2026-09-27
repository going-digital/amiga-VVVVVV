/* Host-only environment for unmodified source-method extraction.
 * No Amiga movement implementation is called by the reference. */
#include <SDL3/SDL.h>
#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>
#include "Ent.h"
#include "player.h"

#define INBOUNDS_VEC(i, v) ((i) >= 0 && static_cast<size_t>(i) < (v).size())
#define TILE_IDX(x, y) ((x) + (y) * 40)
#define vlog_error(...) std::abort()
enum { BLOCK, DAMAGE, DIRECTIONAL, SAFE };
enum { Sound_FLIP, Sound_UNFLIP };
struct blockclass {
    int type, trigger; SDL_Rect rect;
    int xp, yp, wp, hp;
    void rectset(int x,int y,int w,int h) { rect={x,y,w,h}; }
};
struct Game {
    float inertia;
    int lifeseq;
    int deathseq, gravitycontrol, tapleft, tapright, jumppressed, totalflips;
    bool press_left, press_right, press_action, jumpheld;
} game;
struct Music { void playef(int) {} } music;
struct Utility {
    bool intersects(SDL_Rect a, SDL_Rect b) { return SDL_HasRectIntersection(&a, &b); }
} help;
struct mapclass {
    bool invincibility, towermode;
    int tileset, extrarow, contents[1200];
    struct Tower { int at(int, int, int) { std::abort(); } } tower;
    bool collide(int, int, bool);
} map;
struct entityclass {
    int getplayer() { return 0; }
    std::vector<entclass> entities;
    std::vector<blockclass> blocks;
    void disableblock(int);
    void disableblockat(int,int);
    void stuckprevention(int);
    void platformcollision(int,int);
    void moveblockto(int,int,int,int,int,int);
    bool entitycollide(int,int);
    void movingplatformfix(int,int);
    bool checkplatform(const SDL_Rect&,int*,int*);
    float hplatformat(int,int);
    float entitycollideplatformfloor(int);
    float entitycollideplatformroof(int);
    bool checkblocks(const SDL_Rect&, float, float, int, bool);
    bool checkwall(bool, const SDL_Rect&, float, float, int, bool, bool);
    bool checkwall(bool, const SDL_Rect&);
    bool entitycollidefloor(int);
    bool entitycollideroof(int);
    bool testwallsx(int, int, int, bool);
    bool testwallsy(int, int, int);
    void applyfriction(int, float, float);
    void animatehumanoidcollision(int);
    bool updateentities(int);
    void updateentitylogic(int);
    void entitymapcollision(int);
    bool checkdamage(bool scm = false);
} obj;

/* Only initialization is supplied here; behavior is extracted from the checkout. */
entclass::entclass() { std::memset(this, 0, sizeof(*this)); }
bool entclass::ishumanoid() { return type == EntityType_PLAYER; }

extern "C" void reference_init(const V6Player *p, const uint16_t *tiles, int tileset, int extra)
{
    std::memset(&game, 0, sizeof(game));
    game.inertia = 1.1f;
    game.gravitycontrol = p->gravity;
    game.tapleft = p->tap_left; game.tapright = p->tap_right;
    game.jumpheld = p->held; game.jumppressed = p->buffer; game.totalflips = p->flips;
    obj.entities.clear(); obj.entities.resize(1); obj.blocks.clear();
    entclass& e = obj.entities[0];
    e.type = EntityType_PLAYER; e.gravity = true; e.rule = 0;
    e.cx = 6; e.cy = 2; e.w = 12; e.h = 21; e.dir = p->dir;
    e.xp = e.oldxp = p->x; e.yp = e.oldyp = p->y;
    e.vx = p->vx / float(V6_ONE); e.vy = p->vy / float(V6_ONE); e.ay = p->ay / float(V6_ONE);
    e.onground = p->ground; e.onroof = p->roof;
    map.tileset = tileset; map.extrarow = extra;
    for (int i = 0; i < 1200; ++i) {
        map.contents[i] = tiles[i];
        if (tiles[i] >= 14 && tiles[i] <= 17 && i / 40 < 29 + extra) {
            blockclass b = {DIRECTIONAL, tiles[i] - 14, {(i % 40)*8, (i / 40)*8, 8, 8}};
            obj.blocks.push_back(b);
        }
    }
}

extern "C" void reference_read(V6Player *p)
{
    const entclass& e = obj.entities[0];
    p->x = e.xp; p->y = e.yp; p->old_x = e.oldxp; p->old_y = e.oldyp;
    p->vx = std::lround(e.vx * double(V6_ONE)); p->vy = std::lround(e.vy * double(V6_ONE));
    p->ay = std::lround(e.ay * double(V6_ONE));
    p->ground = e.onground; p->roof = e.onroof; p->dir = e.dir;
    p->tap_left = game.tapleft; p->tap_right = game.tapright;
    p->held = game.jumpheld; p->buffer = game.jumppressed;
    p->gravity = game.gravitycontrol; p->flips = game.totalflips;
}
