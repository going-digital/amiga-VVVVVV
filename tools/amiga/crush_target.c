/* Test-only runner: identical state digest on host and 68000, no assets. */
#include "player.h"
#include "platform.h"
#ifdef V6_HOST_TEST
#include <stdio.h>
#else
#include <stddef.h>
#include <proto/exec.h>
#include <proto/dos.h>
#include <exec/execbase.h>
struct ExecBase *SysBase;
struct DosLibrary *DOSBase;
/* GCC emits this for the test snapshot structure copies. */
void *memcpy(void *dst,const void *src,size_t count)
{
    unsigned char *d=dst;const unsigned char *s=src;
    while(count--) *d++=*s++;
    return dst;
}
#endif
void crush_session_init(int,int,int,int,int,int);
void crush_session_step(void);
void crush_session_read(V6Player *,V6Platform *,V6Block *,int *);
static volatile struct {
    uint32_t magic,version,complete,cases,ticks,respawns,digest;
} result={0x56364352,1,0,0,0,0,0x12345678};
static void word(uint32_t value)
{
    uint32_t h=result.digest;
    result.digest=((h<<5)|(h>>27))^value;
}
static int step(void)
{
    V6Player p; V6Platform e; V6Block b; int s[6]; unsigned i;
    crush_session_step();crush_session_read(&p,&e,&b,s);
#define P(f) word((uint32_t)p.f)
    P(x);P(y);P(old_x);P(old_y);P(vx);P(vy);P(ay);P(ground);P(roof);
    P(tap_left);P(tap_right);P(held);P(buffer);P(gravity);P(dir);P(flips);
#undef P
#define E(f) word((uint32_t)e.f)
    E(x);E(y);E(old_x);E(old_y);E(vx);E(vy);E(behavior);E(speed);E(state);
    E(onwall);E(x1);E(y1);E(x2);E(y2);E(cx);E(cy);E(w);E(h);
#undef E
    word(b.x);word(b.y);word(b.w);word(b.h);word(b.type);word(b.trigger);
    for(i=0;i<6;++i) word((uint32_t)s[i]);
    ++result.ticks;
    if(s[5]&8) ++result.respawns;
    return s[0];
}
static void run(void)
{
    static const int tiles[]={80,6,7,8,9,49,50},speeds[]={1,2,3,6},xs[]={103,108,115};
    int set,down,t,v,x,cache,n,j;
    for(set=0;set<2;++set) for(down=0;down<2;++down)
    for(t=0;t<7;++t) for(v=0;v<4;++v) for(x=0;x<3;++x)
    for(cache=0;cache<2;++cache) {
        crush_session_init(set,down,tiles[t],speeds[v],xs[x],cache);
        for(n=0;n<16;++n) if(step()==30) {
            for(j=0;j<30;++j) step();
            break;
        }
        ++result.cases;
    }
    result.complete=1;
}
#ifdef V6_HOST_TEST
int main(void)
{
    run();
    printf("{\"cases\":%u,\"ticks\":%u,\"respawns\":%u,\"digest\":%u}\n",
           result.cases,result.ticks,result.respawns,result.digest);
    return 0;
}
#else
int __attribute__((used,section(".text.unlikely"))) _start(void)
{
    __asm volatile ("move.l 4.w,%0" : "=r"(SysBase));
    DOSBase=(struct DosLibrary *)OpenLibrary((CONST_STRPTR)"dos.library",0);
    if(!DOSBase) return 20;
    run();
    /* Keep the diagnostic allocation live for the emulator RAM capture. */
    Delay(50*120);
    CloseLibrary((struct Library *)DOSBase);
    return 0;
}
#endif
