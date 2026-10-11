# VVVVVV A500 conversion plan

Reviewed revision: `52ad6ae3`, 27 September 2026. Target confirmed by the user: A500, 68000, OCS/ECS, 1 MB RAM.

Current direction (11 October 2026): pause automatic music reconstruction while
the user seeks original tracker files from Magnus Palsson. Preserve the editing
assets and return to engine work. The screen-shake core and native register-based teleporter fixture now pass
source, sprite, pixel-capture and A500 timing checks. Shake/SFX coexistence now also passes within the timing budget. Completed arrivals now also pass disk/fresh-boot validation. Next, add
explored-destination admission and enable the validated Energize menu route. See "Native register-based screen shake" below.

Latest milestone (7 October 2026): Building Apport's resident route is
committed as `32c57c07`. Teleporter checkpoint records now pass source-bank
validation and a native DF1 save/fresh-boot fixture, including malformed-centre
rejection before takeover. See "Teleporter checkpoint disk persistence" below.
Interactive Building save/load controls now pass real mouse and fresh-boot
checks, committed as `c6800d55`; see "Building Apport interactive saving" below.
The selector core is committed as `34eed379`. Native menu controls and captions
now pass hardware-input checks, committed as `182d92cd`. Energize collision data
and the source teleport handoff are committed as `2a601eaf`. Its compact native
renderer is committed as `6f2f9491`; the normal arrival state core is committed
as `1a4a817e`. Native arrival motion, control, visibility and grey flash are
committed as `415e6ad9`; departure and host round trips are committed as
`5c5c07d0`; native staged round trips are committed as `420fe2e2`.
Flashing colours are committed as `ec78ab8a`. The overlap mixer and source cue
conversion now pass host checks; see "Teleporter audio overlap core" below.

## Implementation progress — 27 September 2026

The first native hardware harness is now in [`amiga_version/`](amiga_version/README.md), with a
Bartman GCC build, generated boot disk, and repeatable Copperline smoke test.
The user supplied the desktop asset location, and the converter reads that
archive without modifying it. Kickstart 1.3 is available in `~/amiga`.

The current build is a playable static slice of original rooms **(100,110)**
and **(119,110)**, connected by the main world's horizontal wrap. Movement,
flips, tile collision, spikes, animated drawing and checkpoint/death/respawn are
implemented. Checkpoints now retain their room and gravity; respawn reloads the
saved room. Other exits explicitly return to the saved checkpoint. Only these
two rooms' literal checkpoint setup is exported; moving entities and scripts
are still pending.

The desktop Release build succeeds. An isolated reference harness extracts
original C++ methods and compares them with the integer Amiga core: **36,746
matching ticks across 181 scenarios**, plus **53,280 hazard cases**. Integer
8.24 arithmetic preserves binary32 rounding at collision boundaries. This is
not yet a full-game replay equivalence test.

Normal-world boundary behavior passes **32,400 reference comparisons**, including
thresholds, vertical-before-horizontal ordering, world wrap and preserved
movement state. The target replay reaches the neighboring room through normal
inputs without death and verifies a later cross-room respawn. These checks do
not cover full `loadlevel` side effects or special-room transitions.

The renderer now uses **two bitplanes** and hardware sprite 0 for the player.
The player's visible pixels fit one 16-pixel channel. A separate Security Sweep
scene uses a second channel for its drone. A bounded allocator now supports
all eight channels, with independent monochrome colours and explicit overflow. The four playfield colours are
black, one room accent, green checkpoints and white text; the player has an
independent cyan sprite colour. Low-intensity tile shading is omitted.

On Copperline's stock PAL A500, 512K Chip + 512K slow RAM profile, the slice
allocates **81,934 Chip bytes**. Ordinary work peaks at **91 lines / 5.824 ms**;
the transition replay peaks at **167 / 10.688 ms**, with room-change work at
**167 / 10.688 ms**. Both pass the 20% video-headroom gate, zero missed VBL checks,
visible-player checks and clean exit; the ordinary capture also verifies audio.
The previous 45.312 ms full-room redraw and explicit loading pause are gone.

Each of the two cached rooms retains a screen pair in Chip RAM. Backgrounds
occupy **38,400 bytes of slow RAM** and supply small checkpoint restorations.
This is bounded slice scaffolding; screen pairs cannot remain resident for the
whole campaign. Measurements do not establish full-game or real-hardware limits.

The offline codec passes all **422 literal arrays / 1,012,800 raw bytes**, packed
to **252,832 bytes** with simple RLE and deduplication. This exceeds the proposed
128 KiB content budget; stronger compression or regional loading is needed.
The earlier repeating-room scroll probe was replaced by the playable slice.
Actual tower streaming, music feasibility, full desktop-loop traces and general
room setup/transitions remain outstanding, so stages 0–2 are not complete.

A separate enemy movement core now matches **126,720 extracted-reference ticks
across 528 scenarios**. It covers bounce behaviours 0–3, bounded hitboxes and
integer speeds, including patrol boundaries, tile collisions and enemy barriers.
It now runs on the 68000 in the original **Security Sweep (112,103)** room,
with its speed-8 vertical drone, checkpoint, hardware sprite and player-hit
handling. This separate one-room scene allocates **43,534 Chip bytes** and peaks
at **137 PAL lines / 8.768 ms**, with zero missed VBL observations.
Pixel-mask collision matches **53,868 reference cases**, and collision animation
matches **20,000 ticks**, using the original red-channel mask semantics and
pre-physics frame selection. The target replay verifies a hit, death, respawn,
both visible sprites and clean exit. HUD caching and smaller checkpoint damage
restoration reduce rendering work. Existing player and enemy differential tests
also cover the movement optimizations.

The allocator passes **30,600 host DMA decode cases**, including all channels,
clipping, palette selection, capacity and stale-list clearing. Eight-channel
double buffering adds **1,632 Chip bytes**. The separate **Traffic Jam (115,103)** scene now exercises seven channels with
three original enemies. Wide requests reserve two channels atomically and pass
another **33,792 host cases**. Its capture verifies three visible red enemies,
movement, checkpoint activation and clean exit, and now **passes the unchanged
250-line performance gate**: peak **249 lines / 15.936 ms**, down from 328 lines.
Chip allocation remains **43,534 bytes**. A **2,052-byte non-Chip terrain cache
per room**, smaller checkpoint writes and per-text-row HUD invalidation provide
the reduction. Cached and uncached movement both match the full existing player
and enemy reference suites; **9,192,768 cache queries** check tile classification
and borders. Caches must be rebuilt when tile data or room settings change.
These replay measurements do not establish worst-case full-campaign performance.

Sprite multiplexing, blitter fallback, fractional speeds,
conveyors and special behaviours remain outstanding. Full entity-loop fidelity
is not claimed from isolated reference tests and target milestone assertions.

A shared dynamic-block layer now supplies solid/directional rectangles to player
physics while preserving SAFE blocks for enemies only. Disabling all blocks at
an origin and moving only the first match follow the original lifecycle.
**21,600 query cases**, **16,000 lifecycle operations** and **43,200 player ticks
per cached/uncached path** match extracted desktop methods. Empty blocks are
correctly ignored by both player and enemy collision. The original world/enemy scenes use empty dynamic-block lists; Stop and Reflect
now supplies three live platform blocks. An ordinary **32×8 platform movement core** now
matches **126,720 rule-2 reference ticks per cached/uncached path**, plus
**20,000 floor/ceiling contact-velocity queries**. Platforms ignore collision
blocks while still colliding with map tiles; block relocation preserves source
ordering. The Stop and Reflect native scene now calls this module.
Horizontal carrying and vertical `movingplatformfix` now also have isolated
implementations. **24,000 cases each** match their original methods, alongside
**24,000 explicit-target map-collision cases**, with cached and uncached terrain.
The retained pending Y position, respawn suppression and platform reversal when
blocked are preserved. The player API now separates input from physics and retains pending Y in
caller-owned motion state. **12,000 ordered input/push/carry/physics ticks** match
extracted reference code with prescribed platform positions. Post-physics block
disabling and stuck-player correction now match **12,000 additional reference
cases per terrain path**, including duplicate origins and directional-barrier
skipping. The reverse-order platform scheduler now matches **23,409 persistent
ticks per terrain path** across 98 scenarios, together with player input,
transport, physics and post-physics overlap/stuck correction. Tests preserve
blocks between ticks and compare every platform's movement state; zero-speed
platforms can participate in both velocity-selected passes. A separate native **Stop and Reflect (112,106)** scene now connects this
scheduler to the slice lifecycle and renders all three 32×8 platforms using
six hardware channels plus the player. Its deterministic replay records
**60 vertical transport position changes**, one death/respawn and an active
checkpoint, with all three platforms visible. It passes the unchanged gate at
**237 PAL lines / 15.168 ms**, with **43,534 bytes** of explicit Chip allocation
and no missed VBL observations. Same-room respawn preserves platform state.
Height-limited sprite DMA avoids writing 24 unused rows per platform half;
63,744 new host cases validate height, clipping and atomic allocation.
All four earlier captures still pass. A separate, clearly labelled synthetic
horizontal fixture now verifies **180 transport ticks** on target at
**167 PAL lines / 10.688 ms**, using three sprite channels. Its captured player
and platform state matches tick 180 of an extracted desktop reference trace.
The host fixture compares 240 ticks on both terrain paths. Just Pick Yourself Down now supplies an original horizontal-platform room
with multiple checkpoints. Focused host and standalone target compression tests
are described below; full desktop lifecycle comparison remains outstanding.

A caller-owned multi-checkpoint core now matches **32,768 reference ticks**
across 256 scenarios, including 16,559 activations and 3,388 ticks with multiple
saves. It preserves reverse entity order, pending activations, duplicate IDs,
orientation offsets, saved direction and room coordinates. The per-entity API
supports later integration among other entity updates. The native **Just Pick Yourself Down (117,109)** scene now integrates both
checkpoints and its original horizontal platform. Activation runs after input,
records save direction, and redraws both checkpoint locations in both buffers.
The normal capture peaks at **171 PAL lines / 10.944 ms**. A separate test-only
placement replay verifies deactivation of the first checkpoint, activation of
the second and respawn at (208,185), peaking at **191 PAL lines / 12.224 ms**.
It uses **43,534 bytes** of explicit Chip allocation and observes no missed VBLs.
This is isolated checkpoint coverage. A further **normal-input traversal**
now reaches the second checkpoint at **tick 124**, with **15 platform-transport
ticks** and no deaths or unsupported exits, then requests a restart on tick 130.
Its first 129 host movement ticks match extracted desktop methods. Target
snapshots match desktop movement at tick 126 and the host integration trace
after respawn at tick 179. Peak work is **196 PAL lines / 12.544 ms**, with no
missed VBLs. Full desktop death/respawn-loop equivalence is still not claimed.

A new **336-fixture host compression/spike-push suite** matches **1,308 live
ticks per terrain path** against extracted source movement, collision and
damage checks. All 48 solid-wall fixtures reverse the platform without damage;
all 288 spike-push fixtures trigger damage after starting outside it. The source
does not impose unconditional death for a blocked vertical push. Separate slice
checks verify the 30-tick pause, frozen platform state and respawn across 17,280
death-delay ticks. A standalone Bartman/Copperline A500 regression now runs all
672 cached/uncached variants: 19,896 ticks and 576 respawns, with the per-tick
state digest matching the host run. `make -C amiga_version crush-capture`
reproduces this asset-free logic test. An integrated visual compression replay
and independent full desktop-loop comparison remain future work.

A further source-extracted same-room death regression now compares **576 cases /
17,280 ticks** against `Game::deathsequence`, `Map::resetplayer` and the original
Logic.cpp countdown/reset branch. Timers, death counts and all player fields
match through respawn, including synthetic input/contact retention states. This
exposed and fixed the slice clearing input latches, contacts and old positions
on same-room reset. Holding flip across death now requires release/repress for a
new flip, checked through ten recovery ticks. The source comparison begins at the
damage boundary and stops at respawn; subsequent movement, visibility, cross-room
resets and special modes remain outside it. The surrounding desktop loop also
updates flip latches without control and contact counters during death. The
locked-input branch is now extracted and implemented, including held/released/
repeated input during the 576 death cases and 3,000 player control-lock ticks.
A buffered press during death now survives recovery lock and executes when
control returns. Death-time contact refresh is now implemented and checked using
extracted Logic.cpp counter updates and original floor/ceiling collision probes:
6,480 no-contact, 8,640 floor-contact and 2,160 ceiling-contact ticks agree across
cached and uncached terrain. Position/velocity and platform motion stay frozen.
The full host suite and A500 compression regression pass; the updated route
capture peaks at 197 PAL lines / 12.608 ms, with no missed VBLs and clean exit.
A separate static-room recovery comparison now covers 240 states / 5,760
movement ticks plus 120 life-timer checks across ten restart timings. It exposed
and fixed the timer not decrementing during another death; saved gravity is now
restored above life timer five. Input gating, buffered flips, floor/ceiling spawns
and cached/uncached movement match extracted source.
A further host comparison covers recovery on ordinary moving platforms: **480
cases / 11,520 ticks**, all four directions, speeds 0/1/3/6 and mixed-axis actors
sharing an origin. Player/platform state, blocks, pending movement, visual
contacts and the life timer agree; horizontal carry resumes at life timer 7.
No gameplay changes were needed. A complete death-to-recovery replay, visibility,
tower-specific timing and the full desktop loop remain unverified. Current
checkpoint-route peak work is 197 PAL lines with clean exit.

A rendered synthetic upward spike-push replay now passes on the A500 profile:
`make -C amiga_version crush-replay-capture`. It compares the death pause at tick
17 and post-respawn state at tick 180 with the host integration trace, verifies
visible player/platform sprites and clean exit, and peaks at **139 PAL lines /
8.896 ms** with no missed VBLs. This is a labelled fixture, not a campaign room
or complete desktop-loop equivalence. Disappearing platforms and conveyors are
the next entity expansion.

The ordinary disappearing-platform lifecycle core is now implemented and matches
40,960 source-derived updates across all six states and sound/disable/create
events. It compiles for the 68000 without helper-library dependencies. It is not
yet integrated into an original campaign room. Collision-bank integration now matches 30,720 source
updates, including first-disabled-slot reuse, metadata clearing, shared origins
and appends. Fixed-capacity exhaustion leaves both state and bank unchanged;
separate tests cover failure and retry. A synthetic native replay now connects animation and the original vanish cue:
`make -C amiga_version disappearing-capture`. Collapse, hidden and recharge
snapshots (ticks 9/29/54) and the final state (tick 180) match the host scene
trace. Peak work is 153 PAL lines / 9.792 ms, using 45,384 explicit Chip bytes,
with no missed VBLs and clean exit. It is an automated fixture, not an original
campaign room. Original-room export and conveyors are described below; the
(111,107) tile exception now has a context-aware death event API, compared against
1,296 source cases plus repeated death ticks. A tile-edit API now updates the mutable room buffer and rebuilds collision
classification; 64,800 edits plus the tile-59 death-patch path pass UBSan checks.
The context-aware collision-bank update now reports the tile request alongside
normal block events, with another 1,296 source comparisons and failure/retry
checks. A host test applies the edit and verifies the solid tile persists through
platform recharge. Special-room scene integration, background redraw and target
timing remain pending: this room also needs a behaviour-15 platform, trinket
handling and more than eight sprite channels for its four wide platforms/player. The native adapter now supports independent states and
room-provided positions for multiple disappearing platforms. Host checks cover
three independent contacts and 32 shared-bank collapse/death/recharge cycles,
including reverse-order block restoration. “What Lies Beneath?” (116,110) is the
next original-room candidate (one checkpoint, three platforms, seven sprite
channels). Separate flip/vanish samples are now resident and selected by event.
Compact tile masks (9,584 ordinary-memory bytes) replace the five-frame renderer
limit; host adapter checks reach frame 48 through repeated recharge contacts.
“What Lies Beneath?” now has a separate interactive build (`beneath-run`), with
its original tiles, checkpoint, three disappearing platforms and tile-707 masks.
The `beneath-capture` idle smoke verifies all three visible platforms, seven
sprite channels, checkpoint spawn and clean exit. Peak work is 206 PAL lines /
13.184 ms, with 45,384 allocated Chip bytes and no missed VBLs. A separate `beneath-route-capture` now visits all three platforms using
normal right/flip inputs, with no placement or restart injection. Three
collapses lead to one ceiling-spike death and checkpoint respawn. It matches
the native host trace at collapse/hidden/recharge ticks 17/61/85 and final tick
170, exposing all three states and frames in packed diagnostic fields. Peak
work is 214 lines / 13.696 ms with no missed frames and clean exit. The 240-tick
UBSan host trace visits all six states per platform and verifies restoration
of all three solid blocks. A separate synthetic `retrigger-capture` fixture now respawns directly on a
recharging platform, automatically retriggering it. Target snapshots match the
host at tick 61 (visible frame 5) and tick 160 (frame 10, three deaths/respawns).
Peak work is 131 lines / 8.384 ms with no missed frames and clean exit. This
covers extended rendering on target but does not establish a campaign retrigger
route or independent desktop-loop equivalence.

A separate behaviour-stage helper now covers waiting platform rules 14/15,
including hidden-platform activation and boundary/direction updates. It matches
16,896 extracted-source cases and compiles without 68000 runtime helpers.
Creation, movement, block relocation and player carrying are now integrated
through the gated-platform transport API, sharing the ordinary movement core.
A further 23,520 ordered source comparisons run with both cached and uncached
collision data, including mixed passes, signed speeds and floor/ceiling rides.
The synthetic native waiting/carry fixture matches at ticks 11/41/179, peaks at
179 lines / 11.456 ms, uses 43,534 Chip bytes and misses no frames. Its trigger
state is externally staged; a full mixed-room lifecycle is not claimed. The
special campaign room still needs trinkets and sprite scheduling. Tower/music
feasibility are the recommended next focus.

Tower inventory now includes the actual 700-row main map, 120-row background
and both 100-row mini-towers. Independent-row RLE with duplicate-row sharing
packs them into 18,312 / 7,260 / 2,776 / 3,238 bytes respectively, including
row directories. A 32-row decoded tile cache needs 2,560 bytes. The host probe
checks every packed row with the native C decoder and exercises wrap, reverse
scrolling and jumps; normal synthetic camera steps up to 16 pixels refill at
most two rows. This is storage/decoder evidence, not a native scrolling timing
result. The native C directory reader and bounded row cache are now implemented and
pass 1,011,840 source-map queries plus signed-limit and malformed-data tests.
The 68000 object has no runtime helper dependencies beyond the row decoder.
The planar row writer and per-buffer display tags now prepare 31 visible rows
in a 320x256 two-plane ring. Tests cover 2,600 alternating-buffer frames and
80,600 rows with a patterned atlas and original maps; initial fill is 31 rows,
then at most two dirty rows per buffer for one-row camera steps. The 68000 object
adds no runtime helpers. The actual `tiles3.png` colour-bank converter now produces a 480-byte atlas;
691,200 pixel comparisons pass through the C renderer at fine-scroll, ring-wrap
and map-wrap positions. Alpha is baked onto black and colours are reduced to
four; previews are host-generated. A pointer-segment builder now emits initial plane addresses and the ring-wrap
reset, including the PAL line-255 barrier, in at most 48 bytes. Structural tests
cover all 256 offsets and 245,760 modeled scanlines; the 68000 object has no
runtime dependencies. A standalone native tower probe now installs alternating
Copper lists and two rings, publishing completed lists at PAL blank. On
Copperline A500/512K Chip + 512K slow, it reached camera 555 (crossing two
256-line ring seams), with zero missed frames and peak incremental work of
135 scanlines (8.64 ms), excluding initial ring fill. Its Chip allocation is
41,216 bytes. The screenshot looks intact and mouse exit restores AmigaDOS.
The subsequent bounded camera route (5344..5856 pixels, forward and reverse)
keeps logical coordinates continuous across source row 700 instead of resetting
the camera and invalidating ring tags. It passed two forward source-map seam
crossings and one reverse crossing in 1,564 PAL frames, with no missed frames,
at most one row drawn per update, and peak work of 136 scanlines (8.70 ms).
Exit restoration also passed. Fixed-camera native capture comparisons now pass
at cameras 0, 16, 17, 52, 53, 255, 5599 and 5600: 614,400 exact RGB comparisons
at logical pixel centres against the desktop map and converted atlas, independent
of the native decoder/renderer. These include the ring-reset and PAL line-255
boundaries and source-map seam. Moving-frame tearing, traversal of the entire
tower, negative camera coordinates, parallax, gameplay and music running
together remain open; physical Amiga timing is not established by these tests.

Music now assumes Lightspeedplayer and a musician-produced tracker soundtrack,
per the user's direction. PCM streaming is no longer the working path. Measure
tracker playback together with gameplay once a representative module is ready.

The detailed review below remains the roadmap; original static-review figures
and provisional budgets are retained for context. Current commands, scope and
evidence are in [`amiga_version/README.md`](amiga_version/README.md).

## Recommendation

Build a native Amiga implementation around the desktop game's existing rules and campaign. Retain and progressively adapt the C++ game logic; replace its presentation, audio, platform services, and runtime content representation. Do not attempt to bring the SDL3/FAudio desktop stack onto a 1 MB A500, or rewrite all gameplay from scratch.

Assume the restrictive memory configuration: **512 KiB Chip RAM + 512 KiB expansion RAM**, without an accelerator or FPU. Expansion RAM is not available to custom-chip DMA and must not be assumed to provide Fast RAM performance. Start with PAL, the original 320×240 logical playfield, keyboard and one-button joystick. PAL, English-only presentation, and an AmigaDOS executable are proposed initial scope decisions, not additional user requirements. NTSC and floppy distribution need separate validation.

Feasibility is promising for the visuals and room-based gameplay, but **not yet demonstrated** for the complete campaign, code size, scrolling effects, or soundtrack within this memory limit. The first milestones explicitly test these constraints.

## What is in this checkout

| Area | Evidence | Port treatment |
|---|---|---|
| Maintained engine | `desktop_version/src`, approximately 86,712 lines across C/C++ source and headers | Use this as the behavioral reference. |
| Build | `desktop_version/CMakeLists.txt` specifies C++98, no exceptions/RTTI, SDL3, FAudio, PhysicsFS, TinyXML2, LodePNG, C-HashMap, SheenBidi | Create a separate Amiga target. The desktop README still describes SDL2; follow the actual build and source. |
| Old mobile engine | `mobile_version/readme.MD`: unmaintained Adobe AIR/ActionScript | Useful historical reference, not the port base. |
| Geometry | `Constants.h`: 40×30 tiles, each 8×8 pixels | Preserve coordinates, tile size, and collision geometry. |
| Game rules | `Entity.cpp`, `Ent.cpp`, `Logic.cpp`, `Game.cpp`, `Map.cpp`, `Input.cpp` | Preserve behavior; remove desktop dependencies incrementally. |
| Update sequencing | `main.cpp`, `RenderFixed.cpp` | Preserve the ordering of scripts, fixed animation, input, and logic. Rendering is not currently a cleanly isolated backend. |
| Campaign | `Otherlevel.cpp`, `Spacestation2.cpp`, `Labclass.cpp`, `WarpClass.cpp`, `Finalclass.cpp`, `Tower.cpp` | Convert tile payloads offline; retain room setup behavior, including entity creation and conditional changes. |
| Scripting | `Script.cpp`, `Scripts.cpp`, `TerminalScripts.cpp` | Keep command semantics and dialogue; reduce string parsing/storage after behavioral tests exist. |
| Drawing | `Graphics.cpp`, `GraphicsResources.cpp`, `Render.cpp`, `Screen.cpp`, `Font.cpp` | Replace textures and RGB operations with planar drawing and palette operations. |
| Audio | `Music.cpp`, `Music.h`, `BinaryBlob.cpp` | Preserve music IDs, cues, fades, and SFX semantics; replace FAudio and runtime Vorbis decoding. |
| Files and saves | `FileSystemUtils.cpp`, `Game.cpp`, `XMLUtils.cpp` | Native file access, indexed data pack, compact versioned saves. |
| Optional desktop features | Editor, custom levels, localization maintenance, IME, networking, store integrations | Exclude from the initial campaign build. Preserve useful gameplay/accessibility settings where practical. |

### Measured constraints

- A scan of the `static const short contents[]` initializers in the five ordinary campaign level files found **417 arrays, 500,400 tile values, or 1,000,800 bytes at two bytes per tile**. This is a source-data measurement, not a linked binary measurement or a count of unique playable rooms. It excludes other array forms and tower data. These arrays alone nearly exhaust 1 MiB; leaving the campaign linked as raw data is untenable.
- `Tower.h` holds 40×700 main tiles, 40×120 background tiles, and 40×100 minitower tiles: **73,600 bytes** with 16-bit shorts, before any duplicate initialization data.
- One 320×240 32-bit image costs **307,200 bytes**. The desktop creates multiple render targets. Four planar bitplanes cost **38,400 bytes per screen**, five cost **48,000 bytes**; double buffering costs 76,800 or 96,000 bytes before padding.
- `Ent.h` uses floating-point acceleration, velocity, and prospective position. `Entity.cpp` collision resolution converts these values to integer coordinates and adjusts velocity in steps. Rounding is part of gameplay behavior.
- `Game::get_timestep()` normally returns **34 ms**, with 41/55/83 ms slowdown cases. This checkout is nominally “30 fps” but its default interval is not exactly 1/30 second.
- No desktop `data.zip` or soundtrack files were found. Some fonts, icons, and legacy mobile images are present; this is not a complete desktop asset set. Actual palette counts, converted graphics sizes, and music feasibility remain unmeasured.

## Architecture and implementation decisions

### 1. Preserve behavior before optimizing it

Keep a runnable desktop reference at this revision. Add deterministic input recording and state traces at logical tick boundaries: player position/velocity, gravity, room, entity state/order, collision results, script position/delay, flags, checkpoints, and RNG state. Control initial state and random seeds; audit visual RNG consumption before removing effects.

Extract a small platform boundary for input, elapsed time, files, sound commands, and rendering operations. Replace incidental SDL types such as rectangles/colors with small local types where needed. A temporary helper shim for memory/string operations is acceptable; implementing a general SDL texture compatibility layer is not the intended architecture.

Keep C++98 where useful. Measure the linked runtime and STL footprint before deciding which containers to replace. Bound entity/block storage using instrumented campaign maxima, with explicit overflow diagnostics. Preserve vector index behavior and creation/deletion order; arbitrary entity caps or swap-removal can change gameplay.

Separate fixed state updates from drawing carefully: `gamerenderfixed()` calls collision queries and entity animation. Retain these updates even when a video frame is skipped. Preserve the source loop's phase ordering rather than substituting a generic input/update/draw loop without comparison.

### 2. Timing and arithmetic

Use elapsed-time accounting independent of vertical blank. Preserve the 34 ms simulation interval initially, including slowdown/death behavior. On PAL, present completed buffers at 50 Hz; repeated images and a mixture of one/two-refresh intervals are expected. Do not simply run the original logic at 25 or 50 Hz. Interpolation is optional polish after profiling.

The desktop accumulator uses modulo when advancing, so overload behavior is not a standard unlimited catch-up loop. Document and test the port's bounded catch-up policy, input edge handling, pause/resume, and disk-loading time exclusion. Do not let audio interrupts or room loading accidentally advance game time.

Start with the original arithmetic in the host comparison build. Audit constants and ranges, then migrate hot movement paths to fixed point (16.16 is a candidate, not a proven choice). Explicitly reproduce truncation toward zero, especially for negative coordinates: an arithmetic shift is not generally equivalent. Use adequate intermediate widths, test overflow, and avoid changing collision order. Compare per-tick results around platforms, spikes, gravity lines, room wraps, and moving hazards before accepting the conversion.

### 3. Native graphics

Use the measured **two-bitplane, four-color playfield with hardware sprites** as the baseline. Retain the four-plane build for visual comparison; expand depth only if essential campaign colours cannot be represented. Allocate colors by gameplay role and room; reserve readable UI and distinct crew/hazard colors. Quantize RGB to the OCS color range offline and translate fades/glows into palette changes where possible. Validate actual assets before committing to a palette design.

Use native planar tiles, masked blitter objects, and a bitmap font. Draw the room background on entry and restore damaged regions for moving objects. Each back buffer needs its own damage history. Merge overlapping regions and fall back to larger redraws when cheaper. Avoid converting an entire chunky framebuffer to planar every frame.

Hardware sprite 0 now renders the player. Allocate the remaining seven channels to moving objects where width, palette sharing and overlap allow; reuse channels across separated vertical bands only after timing tests. The blitter path must cover general entities. Preserve clipping, flipped graphics, text boxes, gravity lines, and layer order.

Treat the tower and animated backgrounds as an early dedicated prototype: use scrolling planar buffers and redraw incoming tile rows where suitable, with guard rows and explicit wrap handling. Benchmark with full display DMA, sound, and moving hazards enabled. Stationary-room performance is not evidence that the tower will work.

Use PAL 320×240 first, checking borders and aspect on real displays. Do not crop the game to 320×200 for NTSC: that discards gameplay space. NTSC requires a tested display strategy and remains a separate milestone.

### 4. Offline content pipeline

Build host tools that consume the source campaign and user-supplied desktop assets and produce a versioned, endian-explicit Amiga data pack:

1. Extract tile payloads into indexed room records; measure simple RLE versus a lightweight LZ codec and deduplicate identical content. Preserve tile IDs above 255, or use validated room-local remapping.
2. Preserve executable room setup separately. These functions also spawn entities/blocks and inspect state; a tiles-only export is insufficient. Initially replace array storage while keeping those setup routines. Convert setup commands to data later only if code size requires it.
3. Store compressed world tiles resident if they fit; otherwise use regional packs with adjacent-room caching. Decompress to bounded buffers. Keep respawn and common room transitions free of disk access wherever possible.
4. Handle tower data as compressed sections or a compact resident map, selected after measuring scrolling access and RAM. Never require per-frame floppy reads.
5. Convert graphics to planar images/masks, font glyphs, and palette metadata. Avoid storing every tint/shift variant unless measured savings justify the memory.
6. Initially keep script interpretation compatible. If necessary, compile built-in scripts to compact opcodes/string tables with a host validator and behavior comparisons; this is a separate change from rendering.
7. Emit manifests with sizes, offsets, counts, checksums, and bounds. Test every room against the original tile data and setup behavior, including conditional variants.

Do PNG, ZIP, XML content processing and audio conversion on the development machine. Do not serialize native C++ structures: define integer widths, byte order, alignment, and format versions explicitly for the 68000.

### 5. Audio is an early feasibility decision

Use Paula-native signed 8-bit sample playback for effects, with priorities and an explicit music/SFX channel policy. Preserve the 28 enumerated effect meanings and 16 base music IDs. Test fades, interruptions, reversed music cues, looping, death, and room changes.

**Working decision:** use Lightspeedplayer for music. The user will work with a
musician to port the soundtrack to tracker modules. Treat this as the music
architecture assumption; do not continue developing PCM streaming as the default.

Once a representative module and player integration are available, measure
player code/workspace, module and sample Chip RAM, worst-case replay CPU cost
alongside tower rendering, and the music/SFX channel policy. Confirm cue changes,
loops, fades and interruptions against the game. No particular tracker format,
channel count or Lightspeedplayer resource usage has been verified yet.

The initial PCM storage experiment remains exploratory evidence, not a release
path: a full 219.43-second song required 1.76–3.07 MB at 8–14 kHz mono 8-bit.
Tower scrolling is now the immediate feasibility priority. Full soundtrack
integration remains a release requirement; musician-produced modules will supply
the representative assets for its acceptance tests.

### 6. Platform, storage, and build

Use a 68000 C/C++ cross toolchain and separate Amiga build configuration. Verify compiler/runtime support with a minimal executable before selecting optimization flags. Generate a linker map and report code, constants, BSS, heap, stack, and Chip RAM allocations on every build. Enable section removal only after verifying static initialization and retained entry points.

Start with an AmigaDOS executable and indexed data files for straightforward development, loading, and saves. Plan controlled ownership of display, blitter, audio, interrupts, and input with restoration on exit. Define an OS-safe loading phase; do not invoke DOS while the OS is disabled. Reuse preallocated DMA buffers and keep interrupt work bounded.

Support joystick left/right/fire for movement/flip, keyboard equivalents, and explicit map/pause/restart controls. Provide edge-triggered presses, pause behavior, and an alternative interaction mapping where needed. Avoid requiring a second joystick button.

Write small versioned saves containing the original checkpoint/progression semantics, options, and records. Validate lengths and checksums and use a recoverable replacement scheme. Desktop XML import/export can be a host utility. Preserve immediate in-memory checkpoint respawn independently of disk persistence.

Add floppy images only after measuring packed content and disk access. Disk count is unknown until music is settled. Treat boot-floppy and WHDLoad packaging as later delivery work, with their own memory and save requirements; neither should silently require more RAM than the base target.

## Provisional memory envelope

These are **allocation targets, not measurements**. Figures are KiB, rounded upward. Test both allocation peaks and largest free blocks on the minimum configuration.

| Chip RAM allocation | Target KiB |
|---|---:|
| Two two-plane 320×240 screens | 38 |
| Background restoration cache / scroll storage | 48 |
| Current planar tiles, object masks, font | 80 |
| Music samples / SFX / audio DMA buffers | 96 |
| Copper lists, sprites, disk/DMA scratch | 24 |
| Subtotal | **286** |
| Remaining from 512 KiB: OS use, alignment, temporary peaks, contingency | **226** |

| Expansion RAM allocation | Target KiB |
|---|---:|
| Code, runtime, permanent constants | 192 |
| Compressed room data/cache and scripts | 128 |
| Current room/tower state, entities, progression | 48 |
| Stack, bounded heap, conversion scratch | 48 |
| Subtotal | **416** |
| Remaining from 512 KiB: OS use and contingency | **96** |

The OS reserve is not measured and must be verified at boot. A larger soundtrack, code image, full tower arrays, or shifted graphics bank may exceed this envelope. Fix that through packing, allocation lifetime changes, and measured code reductions; do not quietly raise the hardware requirement. If the envelope fails, stop and revise the architecture or agree a scope change.

## Staged delivery and acceptance gates

| Stage | Deliverable | Exit condition |
|---|---|---|
| 0. Reference and inventory | Desktop reference build, asset inventory, repeatable inputs/state traces, baseline memory/content report | Reference runs with supplied assets; timing and test-room states reproducible. |
| 1. A500 feasibility prototype | Cross-built executable, planar room, controllable player, tower scroll stress test, SFX and one music experiment | Runs on a 7 MHz-class 68000 with 512K Chip + 512K expansion; measured RAM and frame cost leave headroom. No unrestricted emulator CPU settings. |
| 2. Playable vertical slice | Exact movement/collision, flip, hazards, checkpoint, death, room transition, minimal UI | Replays match reference gameplay states for selected difficult rooms; frame skips do not alter updates. |
| 3. Campaign data and scripts | Packed rooms, room setup, tower, warps, crew rescues, trinkets, terminals, dialogue | Every room validates against reference data; all major mechanics and campaign paths exercised. |
| 4. Complete game | Menus, map, teleporters, saves, ending/credits, agreed soundtrack, core settings | Full campaign completable; save/reload and long-session tests pass within memory budget. |
| 5. Release hardening | Disk/install packaging, documentation, real hardware testing, optional NTSC | Minimum-hardware regression runs, disk error recovery, stable audio, clean exit, verified distribution assets. |

At stages 1–2, record worst-case logic time, blitter time, audio interrupt cost, room-load latency, Chip/expansion RAM high-water marks, and stack depth. Measure integrated workloads with DMA contention. A 34 ms game tick and 20 ms PAL video refresh are distinct deadlines; average emulator FPS is not an acceptance metric. Set a headroom target (initially 20%) and revise from measured worst cases.

Regression scenes should include moving/disappearing platforms, conveyors, gravity lines, wrapping rooms, spike edges, rapid death/respawn, tower scrolling, companion behavior, final-level transitions, and the Gravitron. Test all campaign room setup variants, RNG-dependent behavior, script waits, and save flags. Run long play sessions for fragmentation/leaks and test interrupted or failed saves. Confirm critical performance and video behavior on a real A500 as well as a suitably configured emulator.

## Scope and open decisions

- First release objective: main campaign, its core mechanics, dialogue, map, checkpoints/saves, and an agreed music solution. Custom-level browser/editor, broad localization, online integrations, and desktop display features are deferred. Extra game modes follow the campaign unless effectively free to retain.
- The highest risks are code/data fitting simultaneously, fixed-point collision fidelity, tower DMA cost, and acceptable music under the storage/RAM budget.
- The user-supplied desktop asset set is now available locally. Full desktop reference runs are still needed before stage 0 completes. Needed before release scope is frozen: music approach, distribution media, and PAL-only versus NTSC support.
- Do not estimate a release date from static inspection. Estimate after the feasibility prototype and measured asset conversion; a playable room is substantially less work than a faithful complete campaign.

## Distribution and references

The checked-in `LICENSE.md` and `License exceptions.md` distinguish source permission from proprietary asset redistribution. Plan a converter accepting the user's own assets. Bundling campaign assets needs the relevant permission; the Make and Play exception requires its define and excludes the original campaign, so it does not automatically cover this port. Recheck the applicable terms before publishing.

Hardware design references: Commodore's [memory-system description](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0005.html), [bitplanes and colors](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0066.html), [color table](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0067.html), and [blitter chapter](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0118.html). These document why DMA allocation and bitplane count are architectural constraints.

The initial review used static source inspection and a tile-initializer size scan. Subsequent implementation evidence is recorded in the progress section above and `amiga_version/README.md`. The full-game memory table and unimplemented architectural choices remain proposals to validate.

## Tower parallax implementation decision

Use OCS dual playfield for independent hardware scrolling, following the user's
correction. Start with two total bitplanes (one per layer): one foreground
colour, one background colour, and the shared backdrop. This reduces foreground
shading compared with the current four-colour single playfield. If visual
assessment warrants it, evaluate three planes (two foreground, one background)
or four (two each) against the A500 budget. See the hardware manual's
[dual-playfield layout](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0078.html)
and [colour mapping](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node007A.html).

Next native work: separate layer rings, independent pointer-wrap events in the
Copper list, foreground priority, half-speed background, and native pixel and
frame-budget checks. Desktop `Map.cpp::setbgobjlerp` sets background position to
`ypos / 2` and scroll delta to `(ypos - oldypos) / 2`; interpolation and negative
coordinates still need explicit treatment. The newly tested software compositor
is a host reference only (1,228,800 pixel checks), not the selected runtime path.

The user selected **three total bitplanes** for the tower: planes 1 and 3 form
its two-plane foreground, plane 2 is the independently scrolling one-plane
background. This supersedes the two-total-plane trial above. Preserve three
opaque foreground colours, use foreground priority, and measure the additional
DMA cost. Two buffered 320x256 layer sets require 61,440 bytes of Chip RAM before
Copper lists and sprites. Native implementation and timing remain pending.

Three-plane Copper groundwork is implemented: independent foreground/background
initial pointers and sorted wrap resets, including coincident events and the
PAL line-255 barrier. Exhaustive host checks pass for 65,536 offset pairs
(47,185,920 modeled plane addresses), and the 68000 build passes. The segment
needs at most 68 bytes. This is not yet connected to the native probe; background
asset reduction, separate ring allocation, mode/palette setup and DMA validation
remain necessary before claiming hardware parallax works.


Native three-plane integration is now implemented in the standalone tower probe:
two-plane foreground plus half-speed one-plane background, foreground priority,
independent ring resets, double buffering and dark one-colour backdrop conversion.
The moving A500/512K Chip + 512K slow test passes with zero missed frames,
61,696 Chip bytes, at most two row refills per update, and peak work 273 PAL
scanlines (17.47 ms), excluding initial fills. Two forward source-map seam
crossings, one reverse and OS restoration pass. There is limited remaining frame
headroom: gameplay, sprites and music are not present in this experiment.
Foreground index zero is transparent, including any opaque source pixels reduced
to that index. Background intensity is thresholded to one colour. Native
fixed-camera RGB checks cover the composed display; moving-frame tearing,
negative camera positions, colour cycling and full-game timing remain unverified.

Tower rendering optimisation: fixed eight-scanline tile copies now use explicit
constant-displacement byte stores instead of an inner row loop. Peak incremental
work on the same three-plane Copperline route falls from 273 to 134 scanlines
(17.47 to 8.58 ms), with no missed frames, unchanged 61,696-byte Chip allocation
and clean restoration. Host checks pass for 2,600 frames / 80,600 tile rows;
fixed-camera native pixel regressions are also rerun. Initial fill, larger camera
steps, full tower traversal and combined gameplay/music still need separate
measurement before closing tower feasibility.

Synthetic larger-step native measurements now expose a scheduling limit:
4 pixels/update peaks at 134 PAL lines, 8 at 184, and 16 at 320. The first two
have no missed frames; the 16-pixel capture records 555 misses. Maximum row
refills are respectively 2, 3 and 6; all restore AmigaDOS. The route still tests
only the region around the map seam, without gameplay or music. Desktop tower
logic includes 8- and 12-pixel camera moves, but its controller/cadence is not
integrated here. Next scheduling work must handle larger changes or reproduce
the actual camera cadence; do not treat the 16-pixel result as passing the PAL
frame budget. Run `make -C amiga_version tower-step-measure` to reproduce.

The measured large-step overrun is now addressed by blitter reuse of matching
rows from the other display buffer. The active ring is read-only, the inactive
ring receives copies, and each transfer completes before its tag is published.
Small buffer advances (<=8 pixels) bypass reuse to avoid extra scan overhead.
The repeated 4/8/16-pixel captures peak at 135/166/236 PAL lines, respectively,
all without missed frames and with clean OS restoration. The 16-pixel workload
now takes 15.10 ms instead of 20.48 ms, with unchanged Chip allocation. It still
excludes gameplay/music, arbitrary camera jumps and complete tower traversal.

Full source-map timing coverage is now measured: synthetic 12- and 16-pixel
per-video-frame routes reach both 0 and 5856 and return, traversing all 700 source
rows, foreground map seams and background wraps. Peaks are 235 and 242 PAL lines
(15.04 and 15.49 ms), respectively, without missed frames; both restore the OS.
The diagnostics validate the compiled step and reached endpoints. This expands
the earlier seam-region measurements but does not establish full-map pixel
correctness or the combined game budget. The desktop camera controller and
34 ms logic/interpolation cadence, colour cycling, recovery jumps and gameplay
integration remain outstanding. Use `make -C amiga_version tower-full-measure`.

Camera-controller groundwork: `tower_camera.c` implements the early desktop
camera update through bounds, including recovery seeking and old-value snapshots.
72,000 multi-tick comparisons pass against an extracted, unmodified desktop
source block under UBSan; the 68000 object has no runtime dependencies. This is
not yet the whole controller: later death/respawn transitions, player-edge
corrections, 34 ms tick scheduling, interpolation and native integration remain
outstanding. Existing native performance reports still describe synthetic routes.

Late tower camera rules are now ported separately: ordinary play requests death
at the screen edges, while invincibility alone permits 2/8/12-pixel corrections.
Spike heights update after those corrections, and lifeseq gates the phase.
20,480 source-reference boundary cases pass, alongside the existing 72,000 early
camera ticks. This corrects the earlier implication that 12-pixel corrections
represent normal tower play; those performance tests remain useful synthetic
stress loads. Recovery/lifecycle transitions, native scheduling and integration
with actual tower player physics are still outstanding.

Camera-side lifecycle transitions are now implemented as explicit ordered
helpers: recovery gating after the early camera tick, and the death camera
freeze at the later death-processing phase. The recovery callback invokes the
caller's lifecycle logic only when seeking and resume delay allow it. 5,760
cases match extracted desktop blocks, including a subsequent death override;
earlier camera/edge regressions still pass. This tests camera transitions with
a stub lifecycle callback, not actual tower respawn. Native cadence, player
integration and colour-state rendering remain to be connected.

Native camera cadence now has a dedicated probe variant: the early desktop
camera helper runs from a 34 ms accumulator, using the room prototype's 19,968 us
PAL-frame accounting. Normal descending startup/movement is validated through
893 ticks and camera 1784, including the exact tick/remainder identity. Peak
work is 137 PAL lines (8.77 ms), with no missed frames and clean restoration.
Positions are held between logic ticks. Actual player/recovery integration,
late-edge processing, interpolation, colour cycling and music remain outstanding;
this does not replace the synthetic full-map stress tests.

Native camera recovery fixture now passes: scripted death on ticks 60..69,
life-sequence start on tick 70, fixed seek target and a five-call stub lifecycle.
The final native state at tick 893 matches replayed desktop source blocks
(camera 1798, normal mode, five callbacks, no pending recovery counters).
Peak work is 138 PAL lines (8.83 ms), with zero missed frames and clean OS
restoration. This validates camera-side native ordering and callback gating;
actual player respawn, per-tick native trace validation, interpolation and full
tower gameplay remain outstanding. Reproduce with `tower-recovery-capture`.

Recovery validation now includes a bounded native tick trace: 128 ticks x 13
fields match desktop-source replay (all camera fields plus lifecycle/delay/call
count), in addition to final-state checks. The trace covers the full scripted
recovery and occupies 3,344 non-Chip bytes in that test variant only. Instrumented
peak work is 139 PAL lines, with no misses and clean restoration. Controller
camera diagnostics now track logical state at the tick phase, independently of
later display publication. This strengthens camera verification without claiming
actual player respawn or unbounded native trace coverage.

Actual same-tower player respawn state is now integrated through `V6TowerSession`:
real player and saved checkpoint, 30-tick death countdown, checkpoint reset,
10-step lifecycle/visibility, and camera-gated recovery. The former stub is gone.
The native fixture verifies one respawn and ten lifecycle callbacks, with 128
traced ticks x 25 camera/player fields passing. Peak instrumented work is 140
PAL lines (8.96 ms), no missed frames, unchanged Chip allocation and clean exit.
Camera/life-sequence rules use extracted desktop references; checkpoint reset
fields are checked against the same-tower contract. The trigger remains scripted;
live physics/collision, sprite display, cross-room respawn and campaign scripts
are not yet integrated into this tower probe.

## Playable tower slice — 6 October 2026

The tower probe now has a separate live-input build (`make -C amiga_version
 tower-play-run`): joystick left/right and fire to flip, left mouse to exit.
It starts at the original main-tower checkpoint (144,1824), using saved player
position (140,1817), upward camera motion and the existing 34 ms cadence.
Streamed tile reads preserve Tower::at vertical wrapping and horizontal edge
replication. Tower solids are IDs 12..27; invincibility also makes IDs 6..11
solid. Damage follows the desktop's full-tile tower-spike probes rather than
ordinary-room spike rectangles. The player is drawn with a double-buffered
hardware sprite, including lifecycle visibility and death frames.

`test-tower-player` compares 25,728 movement ticks and 10,800 spike cases with
extracted desktop methods across the main and both mini maps, including signed
positions and invincibility. Existing ordinary-room player and camera suites
still pass. A native normal-input replay (`tower-play-capture`) triggers damage
without death/placement injection, records ten deaths and nine respawns over
856 logic ticks, and matches all 3,200 fields of its first 128 ticks against the
host integration. Its screenshot verifies 516 visible cyan player pixels;
exit restores AmigaDOS. This host integration comparison is supported by the
isolated source tests, not independent full desktop-loop replay equivalence.

Peak work is 272 PAL lines / 17.408 ms, with zero missed frames and 64,128 bytes
of explicit Chip allocation. Initial ring fills are excluded. Extending the
exact quarter-pixel arithmetic fast path to bounded tower coordinates and
avoiding the general row-decoder call on collision cache hits reduced workload.
The measured route fits a frame but **does not meet the 20% headroom target**.
This is a short checkpoint-area slice, not a playable full-tower traversal:
checkpoint activation, horizontal gameplay wrapping/exits, other entities,
scripts, interpolation, palette cycling and audio are still absent. Sprite
animation selection is simplified and is not a full entity-animation replay.

Next: profile and reduce combined recovery/rendering work to meet the headroom
gate, then add tower checkpoint activation and boundary transitions with a
longer normal-input traversal. Measure Lightspeedplayer/SFX alongside that
workload before declaring A500 feasibility complete.

## Tower renderer headroom — 6 October 2026

The live-player replay now **passes the unchanged 250-line headroom gate**:
peak 242 PAL lines / 15.488 ms, zero missed frames, unchanged 64,128 explicit
Chip bytes and clean OS restoration. Native camera/player state still matches
all 3,200 fields of the first 128 ticks. `tower-play-capture` now enforces the
headroom gate; `--measure` remains available for explicitly measured overruns.

A separate non-Chip profile splits logic and rendering. Before optimization,
the worst frame was 48 lines of logic plus 225 rendering (273 with profiling).
The renderer now remembers each buffer's last fully populated 31-row window
and scans only newly exposed rows. A failed prepare invalidates the window
promise; retries fall back to tag checks. Peer blitter copies inspect the same
new-row span and preserve the overlap. Remaining scans rotate a bit mask rather
than rebuilding a variable-shift mask for every row. Stream/atlas changes or
external ring/tag edits still require a reset. The additional cache metadata
costs 16 ordinary-memory bytes across the four foreground/background buffers.

Host drawing checks cover 2,636 alternating-buffer frames and 81,716 rows,
including nonoverlapping jumps, both signed row limits, and partial-failure
recovery/reset on one- and two-plane rings. Eight native fixed-camera captures
still match all 614,400 logical pixels. These are fixed-camera pixel checks,
not proof of tear-free moving output or arbitrary recovery-jump timing.

The repeated full-map synthetic 12- and 16-pixel routes now peak at 196 and
204 PAL lines (12.544 / 13.056 ms), down from 235 / 242, with zero missed
frames, both route endpoints reached and clean OS restoration. These routes
exclude player gameplay and audio.

Next gameplay work remains tower checkpoint activation and horizontal boundary
handling, followed by a longer normal-input traversal. The measured headroom
applies to this existing checkpoint-area replay without music/SFX; combined
Lightspeedplayer audio and broader tower routes still need their own gates.

## Tower checkpoints and boundaries — 6 October 2026

The new `tower-world-run` slice exports all 18 main-tower checkpoints in their
original entity order. Contact arms a checkpoint; the next entity update saves
it, deactivates the previous checkpoint, and updates the session's respawn
position, gravity and facing. Visible checkpoint sprites change from grey to
green. The original checkpoint at (144,1824) is a **ceiling** checkpoint (tile
20); this build starts at its literal save position (140,1822), gravity 1.
The earlier player-only fixture (140,1817), gravity 0, remains a separate test.

A 72-tick normal-input route activates checkpoint 505147 at tick 2 and
checkpoint 505167 at tick 72, saving (220,1641), gravity 0, facing right.
Native replay checks all 4,736 fields of its first 128 camera/player/checkpoint
ticks against host integration and verifies eight subsequent respawns at the
new checkpoint. The captured display contains both the cyan player and green
active checkpoint. Exit restores AmigaDOS.

This combined workload peaks at **244 PAL lines / 15.616 ms**, with zero missed
frames and unchanged 64,128 explicit Chip bytes. The worst measured frame is
81 logic lines plus 163 rendering lines. Initial ring fills and full-map
validation occur before the measured loop. The gate still requires at most
250 lines. Results are in `build/amiga-tower-world-replay/capture.json`.

Adding checkpoint entities initially exceeded a frame. The converter now
prepares deduplicated pairs of adjacent tile columns; the renderer writes
aligned words and validates every immutable source row before hardware
takeover. Pair tables/atlases add 6,304 ordinary-memory bytes, not Chip RAM.
Changing streams, tables or atlas limits requires validation again and cache
reset. Collision shares decoded rows across the exact desktop wall samples;
the tile-reader fallback remains available. Cached checkpoint masks avoid
rebuilding sprite/trace state on every tick and support at most 32 entities.

Verification covers 51,456 extracted-desktop movement ticks and 21,600 tower
spike cases with both collision paths, all main/mini maps and invincibility;
600 extracted main-tower boundary cases; 8,448 session checkpoint-mask ticks
against extracted desktop checkpoint code, including bit 31 and duplicate
IDs; and the existing 32,768 checkpoint update/collision cases. Ordinary-room
player regressions still pass. Paired rendering matches 66,092 source-map rows
over 2,132 alternating-buffer frames, including signed limits and failures.
Eight native fixed-camera captures match all 614,400 logical pixels.

Main-tower horizontal boundaries now wrap the player in the scrolling region
and report the desktop coordinate transforms/destination rooms outside it.
The normal-input native `tower-wrap-capture` crosses right at tick 30 and left
at tick 36, checks another 4,736 trace fields, and records nine natural
respawns. It peaks at 238 lines / 15.232 ms with zero misses and clean exit.
Adjacent room loading remains caller-owned: the standalone slice exits cleanly
on a room-load request rather than continuing with tower terrain. This is
checkpoint-area coverage, not a complete tower traversal or full desktop-loop
replay. The earlier player-only replay also passes at 236 lines; the scripted
recovery regression passes at 122 lines, both with zero misses and clean exit.

Next: load the adjacent rooms for tower exits and checkpoint returns, extend
normal-input traversal beyond this area, then measure Lightspeedplayer music
and SFX with gameplay. Other tower entities, scripts, interpolation and palette
cycling remain pending. These emulator timing results exclude audio and do
not establish physical A500 validation.

## Tower hallway loading — 6 October 2026

The previous milestone is committed as `88a5293f`. The new `tower-route-run`
build connects the main tower to Teleporter Divot (108,109) and Seeing Red
(110,104). It loads their literal 40x30 terrain and checkpoint banks, uses
ordinary-room tileset-2 collision/spike geometry there, and preserves the
global save's room identity while traversing. Returning through the lower
entrance adds 5368 to player Y and starts the camera at 5368; the upper entrance
keeps local Y and starts the camera at zero. Physics history is reset after
that entrance transform, while velocity is retained.

Hallway death can load the saved tower checkpoint and snap its camera to the
saved player; a hallway checkpoint can also be restored after death in the
tower. A same-hallway respawn retains the checkpoint bank instead of rebuilding
it. The current room and saved room are now separate inputs to checkpoint
updates. Unknown exits and malformed room loads are explicit failures, with
the live collision/checkpoint state retained on failed load.

Native `tower-route-capture` starts at the original lower tower checkpoint
(44,5449), exits left into Teleporter Divot at tick 11, and returns right at
tick 18 using ordinary inputs. It checks 5,120 fields of the first 128 ticks
against host integration, records seven natural deaths/respawns over 669 logic
ticks, and restores AmigaDOS. Peak work is **249 PAL lines / 15.936 ms**, zero
missed frames, and unchanged 64,128 explicit Chip bytes. The worst frame is
88 logic lines plus 161 rendering lines. Results are under
`build/amiga-tower-route-replay/capture.json`.

Room display changes use checked, resumable cold fills: at most one foreground
and one background row per frame, and a bank is published only once its full
window is ready. The previous completed image stays visible until then. Both
banks are prepared before logic resumes; this pauses gameplay for 62 PAL
fields (about 1.24 seconds) per crossing in this replay, 124 fields total.
Paused fields do not advance the 34 ms logic clock. Transition work is included
in the timing gate. This is a bounded loading policy, not seamless desktop
transition timing.

Whole-room collision decoding initially exceeded the frame budget. Resident
immutable hallway tile views now add 4,800 ordinary-memory bytes and remove
that decode from the frame loop; the packed fallback remains validated and
tested. All resident display sources are fully validated before takeover,
then rebound only to those identical immutable bytes. Pair tables remain
6,304 bytes: the two extra hallway pairs reuse existing pixel patterns. The
interactive build's Hunk footprint is 86,684 bytes, excluding explicit Chip
allocation, stack and OS memory. The fallback loader uses a 2,400-byte temporary
buffer so malformed packets cannot corrupt the live room.

Host checks include 60 entry/history cases compiled from desktop Map.cpp,
3,840 extracted desktop movement/spike ticks on the actual hallway maps,
both directions of remote checkpoint restore, same-room bank retention,
resident/packed views, and failed-load state retention. Paired drawing checks
now cover six maps, 71,238 rows, 2,298 alternating-buffer frames and 186 cold
fill steps. Two native hallway captures match all 153,600 terrain pixels;
the eight fixed tower views also remain a separate regression gate. The earlier
second-checkpoint native replay still passes, now at 243 lines with zero misses.

Seeing Red's crew entity and dialogue trigger, other story scripts, exits
beyond these hallways, other tower
entities, interpolation, palette cycling and music/SFX remain outside this
slice. Native upper coverage proves ordinary Seeing Red checkpoint activation,
tower re-entry, a natural spike death at logic tick 56, and restore to the saved
hallway at tick 85. The inputs are eight right ticks and fifty left ticks,
then no input; no mid-replay position or damage injections are used. The
initial placement remains a bounded upper-exit fixture, not a full tower climb.
Crossings occur at ticks 7, 14 and 85; all 5,120 traced fields match the host
route. Host checks confirm the exact death position (96,193) against the
source-extracted desktop tower spike code. The A500 replay peaks at 212 PAL
lines, with zero misses, 96 loading fields and unchanged 64,128 Chip bytes.
Run `tower-upper-route-capture`. This supersedes the earlier scripted-death
upper recovery fixture.

The next increment reduces cold loading to 32 PAL fields per transition,
about 0.639 seconds (48.4% shorter). The crossing frame fills one row per
layer; later paused frames fill two, while continuing to publish only complete
banks and warm both banks before resuming logic. An unconditional two-row fill
reached 284 lines on a crossing and was rejected by the unchanged 250-line
gate. No extra Chip allocation is needed. Host paired-render coverage now
includes 378 cold-fill frames across one-row, two-row and mixed schedules.
Fresh native lower/upper captures pass at 249/213 PAL lines, zero misses,
64/96 total loading fields and 5,120 matching traced fields each. Both restore
the OS cleanly.

Next: expand natural traversal and story coverage, and measure
Lightspeedplayer audio with the combined workload.

The following increment restores the static hallway tower backgrounds. Desktop
background modes 7/8 sample the tower backdrop at offset 200 with colour banks
15/10. Both banks share the existing mono pattern: a cyan/green dark base and
grey detail. Offline conversion checks all 768 source tile pixels before using
those Copper colours, so no new atlas or Chip memory is needed. Static views
fill during the same staged load and remain fixed during ordinary movement.
The lower/upper native routes still pass at 249/232 PAL lines, zero misses,
64/96 loading fields and 5,120 matching state fields each. Seeing Red's story
entity and trigger remain the next bounded room-content gap. Both fixed
hallway captures match all 153,600 terrain/background pixels.

The next bounded Seeing Red increment adds Vermilion's stand-still sad pose at
(264,185), source frame 147, with a fixed red OCS tint. The native harness uses
normal unrescued campaign defaults; the room-presence function accepts time
trial, translator exploration, companion, flag 8 and red rescue state. All
256 combinations/room cases match the literal Finalclass.cpp setup. Dialogue,
rescue-state persistence, follow-player AI and tint cycling remain pending.
One existing sprite channel holds every visible source pixel (crop 6), with
128 ordinary-memory bytes for the mask and no additional Chip allocation.
A fixed native composition matches all 76,800 terrain/background/crew pixels.
Run `test-hallway-crew` and `tower-crew-pixel-test`.

That composition also exposed existing sprite alignment and priority errors:
DMA X was one pixel right of the playfields, and nonzero backdrop pixels could
hide sprites. Sprite X now uses the calibrated display origin; BPLCON2=0x24
puts both playfields behind all sprite pairs while retaining foreground over
background. The priority encoding follows the [Commodore hardware manual](https://www.theflatnet.de/pub/cbm/amiga/AmigaDevDocs/hard_7.html).
30,600 sprite and 33,792 wide-sprite host DMA cases pass after recalibration.

Earlier route “live” screenshots taken at 15 seconds could still show AmigaDOS;
their reported cyan pixel counts are withdrawn as player-visibility evidence.
Capture verification now rejects startup terrain, uses bounded fresh captures
from 22 seconds, and confirms actual player/crew pixels. State and timing trace
comparisons were unaffected. A pending VBlank IRQ could also make a phase clock
sample move backwards; the clock now retries that window, and phase maxima
must be bounded by total maximum work. Fresh lower/upper captures pass at
250/246 PAL lines, zero misses, unchanged 64/96 loading fields, 5,120 matching
state fields each and clean OS restoration. The upper gameplay capture shows
614 red crew pixels. Next: the Seeing Red trigger and `rescuered` script flow.

The next increment implements the source Seeing Red trigger handoff. The strip
(208,0,32,240) intersects the player's source collision rectangle, then Game
state 36 sets flag 8, removes the trigger and requests `rescuered` once. Rescue
status and companion state are untouched until the script consumer runs their
commands. A retained one-slot request survives contacts and room reloads, and
can be taken explicitly by a consumer. Presence is sampled at room entry in
the native fixture, so setting flag 8 does not erase the crew already loaded.
1,254 source-extracted Entity::checktrigger/Game state 36 cases, 128 repeat
contacts and reload/consumption checks pass. Run `test-hallway-trigger`.

The offline pipeline exports all 51 `rescuered` lines and five `skipred` lines
into a versioned JSON manifest and a C string table. It validates known command
names, text payload lengths, all six dialogue boxes, and the required rescue,
companion and follow-player commands. The script data is not yet executed or
presented by the renderer. The handoff is exercised only in the dedicated
`tower-trigger-capture` integration fixture; ordinary interactive gameplay
awaits the script consumer and dialogue renderer.

The A500 fixture enters the strip through ordinary input at tick 4, retains
exactly one pending request, and keeps Vermilion visible for 728 logic ticks.
All 6,016 camera/player/checkpoint/route/trigger fields match the host. Peak
work is 195 PAL lines, with zero missed frames, unchanged 64,128 Chip bytes,
no checkpoint mutation and clean OS restoration. The initial placement is
in the lower Seeing Red corridor, not a full tower traversal. Next: consume
the request through the rescue script and add dialogue presentation/advance.

## Seeing Red rescue script and captions

The trigger handoff now has an opt-in native consumer. `rescue_script` executes
bounded opcode programs compiled from the actual `rescuered` and `skipred`
source lines. Normal playback waits for the bar/fade backend, changes
Vermilion to his happy pose, awards the red rescue state, presents all six
speeches, and sets companion 9 plus a follow-player request. Fire-button
press edges advance speech while player control is suspended. The skip path
awards the same state without opening dialogue. `tofloor` queues a player
flip; cue requests are recorded but do not yet play sound.

The first renderer uses an opaque full-width caption strip at Y=16..63, with
the source bitmap font and red/cyan speaker colours. It switches Copper
planes around the strip and restores both independently wrapped terrain
pointers and palette afterwards. Six immutable captions are prepared before
OS takeover, adding 23,040 Chip bytes; larger inactive Copper lists bring
explicit Chip use to 87,424 bytes. The bounded readiness backend uses source
bar/fade durations, a placeholder black strip and uniform palette fading.
Desktop-positioned boxes and animated bar/fade geometry remain pending.

Run `make -C amiga_version tower-rescue-run` for an interactive fixture starting
in the lower Seeing Red corridor: move right to trigger rescue and release/
press fire to advance each speech. This fixture is separate from the ordinary
tower route. `tower-rescue-capture` and `tower-rescue-skip-capture` exercise
normal and skip execution on a 512K Chip/512K Slow OCS A500 configuration.
Each compares 8,320 initial state fields plus final state against the host,
checks rescue completion, retains the saved checkpoint, and restores the OS.
Normal/skip playback peaks at 231/220 PAL lines with zero missed frames.

`test-rescue-script` checks 48 actual Script.cpp handler cases, both complete
programs, bounded failures, caption write guards and all 65,536 foreground/
background offset pairs (maximum caption segment: 74 words). Run
`tower-caption-pixel-test` to compare all six native captions and resumed
hallway terrain against the source font/text: 460,800 logical RGB pixels
match. Caption pixels are excluded from live player/crew visibility checks.

Next: implement Vermilion's follow-player movement and room transitions;
then connect cue playback and campaign-state persistence. Exact source
textbox positioning, fade/bar geometry and crew tint cycling are still open.

## Vermilion follow movement and room entry

`companion` now executes Vermilion's bounded follow-player AI with source
five-pixel facing and 45-pixel acceleration thresholds, downward floor physics,
terrain collision and humanoid collision animation. It runs before Viridian's
physics, matching the reverse entity update order. The rescue consumer changes
the existing actor to follow after the script finishes. Interactive joystick
movement in `tower-rescue-run` now draws the moving companion. Normal and skip
replays add bounded left/right inputs after rescue to exercise both characters.

On room changes, companion 9 follows the source spawn rule: retain the player's
velocity/facing, use Y=185, and spawn at X=100 when entering room column 110 with
player X<20. No companion is spawned in tower mode. `tower-companion-route-capture`
starts with an explicitly pre-rescued companion and reuses the upper route:
hallway entry at tick 7, tower return at tick 14, ordinary spike death at tick
56 and remote hallway checkpoint return at tick 85. The two hallway spawns,
tower absence, all 6,912 initial state fields and final state match the host.
It peaks at 249 PAL lines, misses no frames, retains 96 loading fields and
restores the OS. Its visible hallway capture contains 576 red crew pixels.

The extra actor initially exceeded the frame budget. The bounded position
calculation now reproduces binary32 rounding with a 32-bit split sum, retaining
the general fallback. Both resident hallways have prebuilt collision caches
(4,104 ordinary RAM bytes). For cached tileset-2 terrain, directional tiles are
also solid: after edge probes, only an unsampled interior directional block
needs an additional check. Player/companion/probe builds use `-O2`, traces cache
their destination pointer, and blank sprite channels do not need palette writes.
Explicit Chip use remains 87,424 bytes.

`test-companion` passes 3,840 source AI/physics/animation ticks plus the same
3,840 cached ticks, 72 extracted Map spawn cases, 100,198 independent binary32
position checks and 20,000 source collision queries against both cached and
uncached paths. Existing player tests still match 36,746 ticks and 53,280
hazard cases; tower physics matches another 51,456 ticks and 21,600 hazard
cases. Normal and skip rescue captures now compare 10,112 initial state fields
plus final state, including moving crew. They peak at 232/224 PAL lines with
zero missed frames. Screenshot retries require visible
crew as well as terrain/player so a still-loading tower phase cannot be mistaken
for a hallway composition.

Scope remains the two resident hallways and their tower entrances. The AI 1
special restraint in room (110,105), other companion types, gravity lines and
unsupported campaign rooms are excluded. Next: connect the recorded sound cues
to native playback, then campaign-state persistence. Desktop textbox placement,
fade/bar geometry and crew tint cycling remain pending.

## Native rescue speech cues

The follower implementation is committed as `35774efa`. The rescue and skip
fixtures now play the source `crew6.wav` (Vermilion) and `crew1.wav` (Viridian)
cues through Paula channels 0 and 1. Offline conversion uses a 63-tap low-pass
filter and signed eight-bit samples at PAL period 161 (about 22.03 kHz), with
no normalization. Private source audio, converted samples and capture WAVs
remain ignored build assets. The two samples and dedicated silent word add
4,886 Chip bytes, bringing these rescue fixtures to 92,310 bytes.

The portable audio module emits ordered register writes. Requests mute and
stop DMA, wait a complete PAL field before restarting, then queue a silent
word after the first block interrupt. The next interrupt stops DMA and mutes
both channels. Interrupt status is polled each display field; no audio CPU
interrupt handler is added. A new request replaces any pending or active cue.
Exit stops audio before freeing Chip memory or restoring the OS. The fixture
requires idle audio DMA and disabled channel 0/1 interrupts before takeover,
because another client's write-only audio pointers cannot be restored.

`make -C amiga_version test-audio` checks invalid sample guards, ordered start/
drain/stop plans, replacement in all active states, conversion and the actual
Script.cpp speaker-to-sound mapping. `tower-rescue-capture` and
`tower-rescue-skip-capture` now record isolated Paula output, excluding emulator
floppy-drive sounds. Their six/one cues complete without replacement or error;
waveform correlations are 0.95–0.98, stereo channels match, unused channels
remain silent and the recording ends in silence. Both captures retain their
10,112-field source comparison and clean OS restoration. They peak at 233/229
PAL lines, with zero missed frames. The interactive `tower-rescue-run` disk
includes the same playback. The companion route keeps its existing audio-free
249-line gate.

This is bounded rescue speech playback with exclusive hardware ownership.
Music, general gameplay effects and audio.device integration remain pending.
Next: campaign-state persistence, followed by broader room coverage. Desktop
textbox placement, fade/bar geometry and crew tint cycling are still open.

## Campaign save format foundation

Native rescue audio is committed as `6746812e`. `campaign_save` now defines a
44-byte version-1 bounded-route record: `V6CS`, big-endian version and length,
seven explicit 32-bit checkpoint fields, story flags and IEEE CRC32. It maps
the desktop save's `savex`, `savey`, `savegc`, `savedir`, `saverx`, `savery`,
`savepoint`, companion and red rescue/trigger state. It does not serialize
native structure layouts or transient actors, scripts, camera and audio state.

Encoding and decoding validate the four resident route destinations, coarse
coordinate bounds, gravity/facing, supported companion and consistent rescue
flags. Triggered-but-unrescued state is rejected: reloading it without an active
script would consume the one-shot trigger permanently. Time trial/translator
modes, unsupported companions and rooms are rejected. Decode is transactional:
invalid records leave both output structures unchanged. The caller must finish
scripts before saving and validate checkpoint identity against loaded content;
this codec does not prove that an arbitrary coordinate is a safe spawn.

`make -C amiga_version test-campaign-save` compiles the freestanding 68000
object and runs host UBSan checks. An independent Python big-endian/CRC vector
matches; 1,152 boundary/state round trips, every one of 352 single-bit
corruptions, 45 length guards, and 16 checksum-valid malformed payloads pass.
Header and encode guards also pass. The native object has no unresolved runtime
symbols. This is the persistence format foundation, not disk saving or a native
load/restart gate. Next: OS-safe AmigaDOS file loading/writing, checkpoint-bank
validation and a native rescue/save/restart replay. Full campaign saves still
require additional crew, flags, trinkets and room coverage.

## AmigaDOS new-file save and cold-boot restart

The save codec is committed as `c00a46ce`. `campaign_file` now stages a new
record in a distinct temporary file, checks the write and close results,
rereads and compares the complete record, then renames it to the final path.
Existing final or temporary files are refused. Failed writes/readback/renames
clean up the owned temporary file; failed cleanup retains it and a retry refuses
to overwrite it. The caller must exclusively own both paths. `campaign_dos`
implements the operations using Kickstart 1.3 AmigaDOS services. All file calls
run with the OS enabled, outside the display/audio takeover.

Loading checks exact file length, read/close results and the version/CRC/field
rules before committing decoded output. The fixture stages decoded fields and
then selects the saved room's resident checkpoint bank. A restart additionally
requires a matching checkpoint ID and the source checkpoint-derived position,
gravity and facing. Invalid saves fail before opening graphics or taking over
hardware. Initial ID -1 saves are not accepted as checkpoint restarts.

Run `make -C amiga_version tower-persistence-capture`. It creates a private
writable ADF copy in `build/amiga-tower-persistence`, boots to complete the normal
Seeing Red rescue and 64 follow steps, restores the OS and writes
`DF0:campaign.v6cs`. A second, fresh emulator boot reads the floppy record and
restarts the renderer at checkpoint 505147: (140,1822), gravity 1, facing 1.
Companion 9 and both rescue flags survive; the companion is absent in tower
mode, its following state is retained, the saved checkpoint is active, and no
rescue request or speech is repeated. The first boot's 10,112 initial trace
fields and final state still match the source-derived host replay. Both runs
restore the OS, use 92,310 Chip bytes, and miss no frames, peaking at 234/236 PAL
lines. The harness independently checks the actual 44-byte record in the OFS
image. Two more fresh boots reject bad CRC and checksum-valid bad checkpoint
position records before takeover, without rewriting either image.

`test-campaign-file` exercises existing-file preservation, 11 injected I/O
faults, failed-cleanup/retry handling, seven transactional read failures, all
40 source checkpoint/facing combinations and 200 invalid spawn variants. The
68000 file/DOS objects compile; all save codec tests pass. Normal/skip rescue
and recorded audio captures still pass at 233/229 PAL lines with zero misses.

This is a bounded new-save/cold-boot fixture, not a general in-game save menu.
Existing-file replacement, recovery from interrupted replacement, full campaign
fields and unsupported rooms remain open. Next: safe replacement of an existing
save with recovery, then connect save/load actions to the interactive slice.

## Save replacement and interrupted-operation recovery

New-file AmigaDOS saves and cold-boot restart are committed as `b8cc0303`.
`v6_campaign_replace` now writes and verifies a temporary record, renames the
validated old final to `campaign.bak`, promotes the temporary file to the final
name, rereads it and removes the backup. Startup recovery accepts a valid final,
or restores a valid backup when the final is absent, then removes owned stale
transaction files. An uncommitted temporary record is never promoted. Corrupt
final or backup records are retained and reported. A temporary file without a
committed final/backup also remains intact. Recovery failures leave decoded
outputs unchanged; a later retry can resume cleanup.

The native caller validates checkpoint-bank semantics for both existing final
and backup records before recovery can remove either. All operations remain
outside hardware takeover. Paths must be reserved, distinct and exclusively
owned; ASCII case aliases are rejected. A reported I/O error can occur after
promotion, so callers recover before retrying instead of assuming the old record
is still final. These guarantees cover complete logical file operations, not
arbitrary filesystem damage or physical power-loss durability.

`test-campaign-replace` verifies all 24 operation snapshots, 48 replacement
failures and 92 recovery failures, including failures reported after a mutation,
cleanup retries, idempotence and corrupt-record preservation. Every interrupted
replacement retains a complete old or new record. Existing file fault, source
checkpoint and codec tests continue to pass.

Run `make -C amiga_version tower-save-replacement-capture` for three private
writable ADF variants. The successful replacement changes only the fixture's
saved facing from 1 to 0. The two interruption fixtures construct the same file
states as the rename boundaries: old backup plus uncommitted new temp, or new
final plus old backup. Each is followed by a fresh emulator boot. Recovery
restores facing 1 in the first case and retains facing 0 in the second. All six
boots retain checkpoint 505147, rescue and following flags, active checkpoint
state and clean OS restoration. Cold boots repeat neither rescue nor speech;
all first-boot source traces still match. Every pair peaks at 234/236 PAL lines,
with zero missed frames and unchanged 92,310-byte Chip allocation. The harness
follows the named OFS file header to verify the actual final record, excluding
freed backup blocks. The ordinary persistence target also passes both malformed
save rejection gates before takeover.

Next: connect explicit save/load actions to the interactive slice, with OS-safe
pause and resume. Full campaign fields and unsupported rooms remain pending.

## Interactive checkpoint save/load

Run `make -C amiga_version tower-interactive-save-run`. Right mouse saves;
holding fire while pressing right mouse loads; left mouse exits. The launcher
uses keyboard joystick mode. Load consumes fire until release so the gesture
cannot also flip gravity. There is no automatic startup load.

The boot disk in DF0 is write protected. DF1 uses
`build/amiga-tower-interactive-save/save-disk.adf`, labelled `V6 Saves`, which
ordinary rebuilds retain. Capture tests use a separate disposable image. Saves
retain the source checkpoint and supported rescue/following flags, rather than
live actor positions. Actions are blocked during dialogue, active audio, death
or room loading. Five immutable caption buffers provide help and saved, loaded,
failed and busy messages; they add 19,200 bytes, bringing Chip allocation to
111,510 bytes.

Eligible actions restore the OS before AmigaDOS access, validate checkpoint-bank
semantics before backup cleanup, and flush DF1 before taking the display back.
The Kickstart 1.3 implementation sends an
[AmigaDOS ACTION_FLUSH packet](https://wiki.amigaos.net/wiki/AmigaDOS_Packets)
through a private reply port. Native OFS acknowledges completion with both result
and error fields zero. The flush matters: closing and renaming alone left writes
buffered while the game disabled OS interrupts. Failed flush or lost audio
ownership leaves the OS running and exits safely. Audio ownership is checked
again atomically at takeover and resume.

Successful loads rebuild both resident display banks and reset actors, camera
history and supported story state to the saved checkpoint. Saves and failed
loads preserve gameplay. File access advances no gameplay ticks; the private
clock retains its phase and excludes time spent in the OS. Each tested action
uses two private warm-up fields on resume.

`make -C amiga_version test-interactive-save` checks the actual production
consumer with CRC-valid but source-invalid final and backup records, preserving
file bytes and output state on rejection. It also covers replacement, backup
recovery, invalid live checkpoints and retained temp-only files. Control tests
cover 600 held-button fields and all 16 gameplay input masks; the existing
replacement/recovery fault tests remain dependencies.

`make -C amiga_version tower-interactive-save-capture` passes the scripted
missing-save, busy, save and load sequence, matching 10,112 desktop-source trace
fields before loading. It peaks at 236 PAL lines. Real mouse/fire actions peak
at 232 lines; the actual DF1 record is verified while the first game session is
still running. A fresh boot loads that record, exits normally and peaks at 243
lines. All three have zero missed frames, preserve the boot disk bytes and stay
within the 250-line budget. The status caption was also visually checked.

Next: broader resident room coverage and campaign state. Source-exact textbox
and fade geometry, crew tint cycling and general audio ownership remain pending.

## Ordinary resident-room boundaries

The route's ordinary-room branch now loads vertical destinations instead of
rejecting every top/bottom exit. It follows the desktop `Logic.cpp` thresholds:
y >= 238 subtracts 240 and enters the room below; y < -2 adds 240 and enters the
room above. Horizontal checks then use the newly loaded room coordinates. A
corner crossing therefore loads vertical first, then horizontal, resetting
physics history through each normal room load. Entering a tower suppresses the
ordinary horizontal phase. Velocity, facing, gravity and the saved checkpoint
survive these transitions.

Missing or malformed destinations latch the route error while retaining the
coordinates and state at the failed edge. If a diagonal crossing has already
loaded its vertical destination, that successful load remains committed when
the horizontal destination fails. Existing unsupported exits remain explicit
failures.

`make -C amiga_version test-room-boundaries` compiles the actual desktop vertical,
horizontal and room-entry history blocks. It compares 480 edge/threshold/corner
cases on a synthetic nine-room resident grid, checks eight missing/malformed
edges plus a partial diagonal failure, and exercises five crossings through the
production gameplay loop. These tests establish transition behavior; they do
not claim nine newly playable campaign rooms. Existing route tests also pass
3,840 source hallway movement ticks, 60 entrance transformations, natural spike
death and remote checkpoint returns.

`make -C amiga_version tower-route-capture tower-upper-route-capture` passes both
native regressions, comparing 5,120 trace fields each. The lower/upper variants
peak at 245/244 PAL lines, miss zero frames and retain their 64,128-byte Chip
allocation. Vertical crossings themselves currently have host verification;
the existing native fixtures exercise horizontal tower/hallway routes.

Next: implement the teleporter needed by Building Apport (111,104), then admit
its complete room setup into the resident route. Its literal terrain alone is
insufficient: the desktop creates a teleporter entity there. General campaign
coverage and additional saved progression fields remain pending.

## Teleporter activation core

`teleporter.c` ports desktop type-14 creation, rule-3 collision and entity update.
Building Apport (111,104) creates this entity at (112,48), with default identity
0. Its 96-by-96 collision rectangle arms state 1; activation occurs at the next
entity update, even if the player has moved away. Activation changes tile 1 to
2, disables further contact activation, enables the 160-by-160 interaction
region at (x-32,y-32), and writes the centre checkpoint at (x+44,y+44), normal
gravity and the player's facing. Ordinary checkpoints become inactive without
clearing their pending updates, matching desktop ordering.

The caller receives saved-sound and message requests. Time-trial and no-death
modes suppress the message request, while the sound and checkpoint still occur.
State 2 silently initializes an arriving teleporter with flashing tile 6 and an
active interaction region; it leaves the checkpoint and ordinary checkpoint
bank unchanged. Repeated active contact produces no further save request.
Canonical checkpoint validation checks the teleporter identity, centre,
gravity and facing after the caller selects the bank by room identity.

`make -C amiga_version test-teleporter` compiles the core with the 68000 toolchain
and compares its behavior with extracted desktop creation/update/collision
branches under host undefined-behavior checking. It passes 288 activation cases,
1,375 collision edge cases, a full deferred-contact sequence, 120 subsequent
idle updates, repeat suppression and invalid checkpoint guards. The fixture
also checks Building Apport's literal entity call and the source default-ID
overload. Room-boundary and campaign-codec regressions pass unchanged.

This core is not yet connected to the native frame loop. Next: add teleporter
bitmap/animation rendering and room integration, then interaction/travel UI,
arrival flow and disk-save support. The current campaign codec and checkpoint
consumer continue to accept only the existing tower/hallway banks; Building
Apport is not yet admitted as playable terrain without its complete setup.

## Teleporter graphics and native composition

The private asset converter now exports all ten 96-by-96 teleporter alpha
masks. Desktop `GraphicsResources.cpp` loads this image as `TEX_WHITE`, so RGB
is discarded while alpha is preserved. The supplied source alpha is binary.
Frame zero supplies the dark base; the selected frame supplies the tint,
overriding base pixels where both are opaque. The static fixture applies the
desktop frame clamp (below 1 becomes 1; above 9 becomes 8).

`teleporter_draw.c` builds six 16-by-96 unattached hardware sprites. Palette
index 1 is the dark base, index 2 the tint, and zero remains transparent. The
caller owns six consecutive channels and their shared pair palettes; the core
does not touch registers. It clips against x=0..319 and the gameplay strip
y=16..215, emits terminating DMA words, and rejects invalid coordinates before
writing. Native Chip storage holds one immutable DMA bank in the fixed fixture.
Dynamic gameplay will need inactive banks and a channel budget shared with the
player and companion.

`make -C amiga_version test-teleporter-draw` checks every generated mask against
source PNG alpha, reconstructs all emitted DMA pixels in 1,080 frame/position
cases, and checks guard words, clipping, termination and invalid-input
preservation under host undefined-behavior checking.

`make -C amiga_version tower-teleporter-capture` renders Building Apport's
literal terrain and its teleporter at (112,48), with the static hallway
background at offset 200. It compares every 320-by-240 logical pixel for frame
1, frame 6 and out-of-range frame 10 (clamped to 8): 230,400 checks. Frozen OCS
tints are 0x444 and 0xaaf; these fixtures do not reproduce random tint cycling.
All three captures pass, with zero missed frames, a 15-line steady-state peak
and 64,564 bytes of Chip RAM. The native sprite image was visually inspected.
The static harness reserves 192 Copper words per list for the extra sprite
pointers and pair palettes; its former 64-word allocation was insufficient.

Building Apport is exported as a visual fixture, not added to the live route.
Its terrain pairs are included in the verified paired atlas. Activation and
ordinary-room boundary host regressions also pass. The existing lower native
route still matches 5,120 trace fields, peaks at 245 lines and misses zero
frames. Next: source animation,
live activation and renderer integration, then interaction/travel UI and
teleporter checkpoint disk-save support. Static timing is not a moving-gameplay
performance result.

## Moving teleporter activation and animation

`teleporter_animation.c` ports the desktop type-14 animation branch. Active
tile 2 uses a one-tick delay; arriving tile 6 uses two ticks. Random choices 4
or 5 select frame 1 and a four-tick pause in both modes. No-flashing mode uses
the current tile directly while retaining delay/walking state. The caller
supplies a choice in 0..5 when updating; invalid choices preserve state. The
native fixture uses a repeatable choice sequence, not the desktop global RNG.

`make -C amiga_version test-teleporter-animation` compares 1,200 state cases and
1,200 consecutive ticks against the extracted desktop animation branch,
including inactive/active/arrival transitions and no-flashing behavior.

`make -C amiga_version tower-teleporter-live-capture` runs a scripted moving
Building Apport fixture. A real player steps against its literal ordinary-room
terrain. The player moves right for 40 ticks, left for 40 and then idles.
Teleporter update precedes player movement and collision; collision arms the
next update. Animation updates once per 34 ms gameplay tick. Six hardware
channels display the teleporter and the remaining two display the player.
Each render writes only the inactive DMA bank. Tints remain frozen; saved-sound
and message requests are counted rather than played or displayed.

The renderer prepares nine teleporter DMA frames before hardware takeover,
then copies a frame only when the inactive bank needs a different one. Copying
in groups of eight words keeps the measured peak within the 250-line budget.
Templates use 23,520 bytes outside Chip RAM; the complete fixture allocates
69,088 bytes of Chip RAM. DMA mask rebuilding during gameplay exceeded the
budget, so it is excluded from the frame loop.

The first 256 native ticks match 3,072 fields against desktop teleporter
activation/animation and host player physics. Contact saves exactly once on
tick 5, producing (156,92), normal gravity, facing right, room (111,104), ID 0.
Injected arrival state on tick 181 silently switches to tile 6 without changing
the saved checkpoint. The private PAL/gameplay clock identity also passes.
The capture peaks at 239 PAL lines, misses zero frames, and its player and
teleporter image was visually inspected. All 230,400 fixed-frame pixel checks
still pass; the existing lower route matches 5,120 trace fields at 245 lines
with zero missed frames.

This is a moving room fixture, not campaign travel. Next: integrate Building
Apport into the resident route with a complete teleporter/checkpoint bank,
then interaction/travel UI, saved-message/audio handling and teleporter disk
save validation. Crew coexistence and source random tint cycling remain open.

## Building Apport resident route

Run `make -C amiga_version tower-building-route-run` for the dedicated playable
five-room build. It starts beside the right-hand Seeing Red exit. Use the
keyboard joystick to enter Building Apport (111,104), move and flip; left mouse
exits. Existing campaign builds retain their four-room set. The new build
supports normal-mode movement and in-memory checkpoint respawn; travel
selection, saved-message/audio handling and teleporter disk saves are pending.

Resident route descriptors can now own a source type-14 teleporter alongside
ordinary checkpoint banks. Room entry recreates its inactive entity and clears
the active interaction region. The ordinary-room step updates the teleporter
before physics, arms it through collision afterward, and copies successful
centre saves into session respawn state. Same-room death retains the entity;
a remote return recreates it before restoring the saved centre. Teleporter
sound/message requests are exposed to the caller as per-step events.

Building Apport's packed and predecoded terrain, display stream and teleporter
setup are emitted from the literal desktop room. Its display pairs are
validated before takeover. The renderer uses a cached ordinary collision map,
prepared teleporter DMA templates, six teleporter channels and two player
channels. Inactive banks are updated independently. Frozen inactive/active
tints are 0x444/0xaaf. The dedicated build excludes rescue/following rendering
because shared channels with a companion have not been implemented.

Building Apport uses one foreground and one background tile row per paused
loading field, leaving room for the final teleporter DMA copy. Logic remains
paused until both resident display banks are publishable. Copper lists reserve
192 words each; total Chip allocation is 69,088 bytes. Other room transitions
retain their existing fill budgets.

`make -C amiga_version test-building-route` verifies natural Seeing Red entry,
a single centre-checkpoint activation, same-room death, remote tower death
return and malformed room rejection without changing actors or save state.
`make -C amiga_version tower-building-route-capture` matches 1,536 native fields
against host route integration: entrance on tick 7, deferred activation on tick
41, checkpoint (156,92), normal gravity, room (111,104), ID 0. It peaks at 195
PAL lines, misses zero frames and preserves the private gameplay clock identity.
The active teleporter and player capture was visually checked; the interactive
build compiles with replay input removed.

Existing route and ordinary-boundary host tests still pass, as do actual
interactive file-consumer and replacement/recovery fault tests. The original
lower native route also passes its 5,120-field comparison within budget.

Next: teleporter interaction/travel UI and destination admission, then source
bank validation and disk codec support for teleporter checkpoints. General
campaign traversal, companion sharing and random tint cycling remain pending.

## Teleporter checkpoint disk persistence

The existing 44-byte version-1 codec now accepts Building Apport's room bounds.
The format and checksum remain unchanged. `campaign_route.c` selects the saved
room's actual resident descriptor, then validates either a source ordinary
checkpoint or a teleporter centre. Building Apport's canonical record is
(156,92), normal gravity, facing 0 or 1, room (111,104), ID 0. A CRC-valid record
with another centre, gravity or ID is rejected. Consumers built with the
original four-room table still reject this unsupported room.

The production file consumers now use this shared route validator before
replacement/recovery can remove final or backup records. Host tests cover
teleporter creation and reading, malformed final/backup combinations, preserved
file bytes and transactional output rejection. The codec now passes 1,440 round
trips; its 352 bit-corruption, 45 length and 16 semantic guards still pass, along
with the existing file/replacement/recovery fault tests.

`make -C amiga_version tower-building-save-capture` runs a private native DF1
fixture. Its first boot reaches the room and activates the teleporter normally,
returns to the OS after 128 gameplay ticks, writes and flushes the checkpoint.
The second boot validates and recovers the source record before takeover and
restores the centre position. This fixture accepts Building Apport with zero
story flags; it refuses progression that its dedicated renderer cannot retain.
The capture data disk is disposable and separate from interactive user saves;
DF0 stays write protected.

Actual OFS file bytes verify checkpoint (156,92), normal gravity, facing left,
room (111,104), ID 0 and zero flags. A fresh boot starts at (156,92), retains the
record unchanged and exits normally. The first/cold boots peak at 196/205 PAL
lines, miss zero frames and retain the 69,088-byte Chip allocation. The harness
then changes the centre to x=157 while recomputing both record CRC and OFS block
checksum. The native consumer rejects it before display takeover and leaves
the entire data disk unchanged. This verifies source validation beyond CRC.
The original tower persistence regression still passes its fresh-boot and
malformed-record checks at 234/236 lines with zero misses; the first boot
retains its 10,112-field source comparison.

This completes backend teleporter checkpoint persistence and a native startup
fixture. The playable Building Apport launcher still uses in-memory checkpoints.
Next: travel/interaction UI and connect teleporter saving to the interactive
save controls, with progression and companion rendering supported consistently.

## Building Apport interactive saving — 7 October 2026

The dedicated five-room Building route now exposes the existing right-mouse
save and fire + right-mouse load controls, with help/result captions and a
persistent separate DF1 disk. Run `make -C amiga_version tower-building-interactive-save-run`.
The build has no rescue follower or audio; shared save controls no longer depend
on either subsystem. Load consumes fire until release, including in this build.

Source-bank validation runs before recovery can remove a backup. This bounded
build also rejects final or backup records containing rescue/companion progress,
preserving disk contents and the current game rather than dropping that progress.
Host tests exercise both production consumer configurations and transactional
rejection. Real emulated mouse controls save the activated teleporter checkpoint
(156,92), then load it during play and on a separate boot. Both native captures
have zero errors/missed fields, peaks of 201/197 PAL lines, and 88,288 bytes of
Chip RAM. DOS time does not advance the private gameplay clock; the read-only
boot disk and persisted checkpoint remain intact. The loaded caption/teleporter
capture was visually checked. Capture movement uses the established Building
input fixture; the playable launcher uses the keyboard joystick.

Next: implement the bounded normal-mode teleporter travel UI and destination
selection. Rescue sprite sharing and wider campaign progression remain separate
work; disk records still use the existing 44-byte format.

## Teleporter selector core — 7 October 2026

Added `teleporter_menu.c/.h`, a platform-independent normal-mode selector based
on desktop `Logic.cpp` readiness and `Input.cpp` TELEPORTERMODE controls. Readiness
rises by 25 inside the active teleporter region, decays by 50 outside or without
control, and saturates at 255. Opening requires readiness above 20 and source
integer velocity limits. The menu starts on the current room, wraps left/right
through the caller's explored resident destinations, and requires release of all
buttons between actions. Confirming the current room or cancelling closes it;
confirming another destination emits a request without mutating player, region,
checkpoint or route data. Invalid/duplicate destination lists retain menu state.

`make -C amiga_version test-teleporter-menu` compiles the core for the 68000 and
runs 5,260 host readiness/velocity cases plus selection, input-latch, single-room,
cancel, output-isolation and malformed-list checks under undefined-behaviour
sanitization. Existing teleporter activation/collision and Building route tests
also pass. Multiple destinations in the selector test are synthetic; Building
Apport remains the only resident teleporter. No new destination is unlocked by
this increment, and no on-screen menu or travel sequence is wired yet.

Next: connect this state to the native Building controls/caption renderer, pause
player logic while selecting, and verify opening/current-room cancellation in
a native capture before adding another resident destination and arrival effects.
The destination list must remain stable for an open menu. Explored-destination
persistence and cross-room travel remain pending; the save format is unchanged.

## Native Building teleporter menu — 7 October 2026

The Building interactive save build now connects the selector core to joystick
controls and a resident caption. Down + fire opens the menu after activation,
region readiness and stationary checks; left/right selects, fire confirms, and
down + fire cancels. Building Apport is the sole resident destination, so
confirmation returns to play. The normal playable launcher remains
`make -C amiga_version tower-building-interactive-save-run`.

An open menu pauses player/session, checkpoint, route, and teleporter animation
updates while retaining the PAL accumulator and rendering. Save/load reports
busy without pausing for DOS or touching disk contents. Caption priority keeps
the menu visible through that refusal. Fire is consumed until release on opening,
confirmation and cancellation; holding confirmation and subsequently pressing
down cannot reopen the menu or introduce an unintended gravity flip. Loading a
checkpoint resets selector state. The extra immutable caption costs 3,840 bytes
of Chip RAM; this build now uses 92,128 bytes.

`make -C amiga_version tower-building-menu-capture` uses fixture movement with
real emulated joystick/mouse input. It verifies three opens, left/right selection,
current-room confirmation, explicit cancellation, held-confirmation suppression,
118 paused logical ticks, matching gameplay hashes throughout selection, one
busy save, unchanged disks, and unchanged player flip count. The final native
capture has zero errors/missed fields and peaks at 204 PAL lines. The on-screen
menu capture was visually checked. Existing physical disk save/load and separate
fresh-boot load captures also pass with the extra caption (209/210 peak lines,
zero errors/missed fields); the rescue/audio interactive build still compiles.

Next: add a second source-backed resident teleporter destination and a validated
arrival path. Only then offer cross-room travel and its source arrival effects.
The menu currently offers no remote destination and no new exploration or
travel progress is serialized; the 44-byte checkpoint format is unchanged.

## Energize collision data and teleport handoff — 7 October 2026

Selected source **Energize (110,105)** for the second normal-mode teleporter.
`Spacestation2.cpp` translates it to literal room (48,41), with teleporter
(36,68), ID 0, checkpoint centre (80,112), and no normal-mode moving entities.
Its trial-only barrier is excluded. `Map.cpp` selects **tileset 0** here; it must
not inherit Building's tileset 2. The converter now exports its exact 1,200-tile
collision view, compressed room and source metadata. Native display integration
is deliberately pending: its tile IDs reach 805 and require a different graphics
bank from the existing tower atlas.

Resident route descriptors now carry the explicit ordinary-room tileset. Updated
all generated descriptors and host ABI fixtures; existing rooms retain their
original collision classification. Added `v6_tower_route_teleport`, the bounded
normal `Script.cpp::teleport` room-change/save stage. It validates a different
resident ordinary destination, teleporter geometry/ID, collision decode and
checkpoint bank before changing state. It seeds source position (150,110),
gravity 0, interpolation history, silent teleporter state 2, and the destination
centre checkpoint while retaining source direction/velocities. The source
(117,117) position exception is also covered. Caller-owned exploration/menu
gates, paused control, sounds/flashes and subsequent arrival states remain
outside this helper.

`test-teleporter-travel` passes nine handoffs against the extracted source prefix
(including both facings, packed/decoded views, both directions and the special
entry), silent state-2 activation, failed-load preservation, and 480 real Energize
collision ticks against desktop player methods. The codec accepts its checkpoint
without changing the 44-byte format (1,728 round trips); source-bank guards reject
wrong centres/gravity/ID/room. The current five-room UI consumers reject and
preserve Energize final/backup records because their renderer lacks that room.
Existing Building, boundary, file/recovery and native menu regressions pass;
native menu still uses 92,128 Chip bytes, peaks at 204 PAL lines, and misses no
fields. Energize is resident in the six-room **host fixture only** and is not yet
listed in the playable menu.

Next: prepare Energize's private graphics bank and native room renderer, then
implement the source arrival sequence and add a native round-trip capture. Offer
it through the selector only after the renderer/arrival path is complete, with
an explicit explored-destination policy. Wider exploration persistence remains
pending.

## Native Energize graphics — 8 October 2026

Disk space is available again and the interrupted renderer increment is validated.
The private converter reads `graphics/tiles.png`, remaps Energize's 16 source tile
IDs to a compact display-only bank, and emits 28 paired-column patterns plus a
frozen four-colour palette. Original 1,200-tile collision IDs remain intact in
tileset 0. `test-energize-graphics` compares all 79,360 pixels in the 31-row ring
against the original PNG and chosen palette, including the wrapped coverage row.

The opt-in `V6_TOWER_ENERGIZE` six-room build binds this foreground bank and
cached terrain, reuses the two-bank six-channel teleporter DMA allocation, and
prepares its masks at the source (36,68) position. Both foreground banks use the
matching pair table/palette; switching scenes resets frame caches and cold fills.
This fixture retains the frozen tower backdrop and omits source arrival effects.
It does not add Energize to the playable menu or change the standard five-room
save build's supported-room list.

`make -C amiga_version tower-energize-capture` starts through the validated
teleport handoff, exercises silent state-2 entity initialization, and checks
1,536 native trace fields against host route/animation state. It holds after 128
verified logic ticks for the screenshot. The native capture is visually checked,
uses 69,088 Chip bytes, peaks at 188 PAL lines, and has zero errors/missed fields.
The Building menu regression still passes at 204 peak lines with zero errors or
missed fields. An initial finite fixture also returned to the AmigaDOS prompt.

Next: implement and source-validate the normal arrival states 4010–4019, then
connect them to native rendering/control and validate a round trip before making
Energize a selectable destination. Departure effects, exploration policy, and
wider campaign progression remain pending.

## Default teleporter arrival core — 8 October 2026

Added `teleporter_arrival.c/.h` for normal, unlocked `Game.cpp` states 4010–4019,
the default arrival used by Building Apport and Energize. It reproduces source
15/5/15 delays, flash/shake requests, flash/teleport cue requests, centre placement
and interpolation history, visible cyan-facing-right launch motion, the successive
10/10/8/6/3/1 horizontal offsets, and final control/text/region restoration. It
emits the final save request once without writing files or changing the already
selected checkpoint. Direction saved by the handoff remains separate from the
arrival's facing-right player pose.

The caller must run input with prior control permission, apply this phase before
physics so scripted acceleration survives input clearing, and separately handle
entity state-2 update, animation, effect decay/rendering, and OS-safe persistence.
Departure, other rooms' special arrivals, state locking and trial/no-death modes
remain outside this bounded helper. Active starts and invalid state/geometry are
rejected without changing outputs. Inactive ticks clear pending request bits.

`make -C amiga_version test-teleporter-arrival` compiles the core for 68000 and
compares 400 state/delay/facing/visibility cases against the actual extracted
source switch. Seventy sequential phase ticks reproduce the complete 42-tick
state sequence, including one-shot requests and silent completed ticks. Invalid
state/delay/geometry preservation and active restart refusal pass under undefined
behaviour sanitization. Existing handoff and selector tests also pass.

Next: connect the arrival phase to native player/control ordering and effects,
then verify both source motion and cold scene-bank transitions in a native round
trip. Energize remains absent from the playable menu until this integration and
its explored-destination policy are complete. Disk serialization is unchanged.

## Native default arrival integration — 8 October 2026

The ordinary-room route now offers a script phase after player input and before
checkpoint/teleporter updates and physics. Existing route callers retain their
behavior. The phase is excluded from dead-player and streamed-tower updates;
failures latch a route error before physics. The opt-in Energize arrival fixture
runs the committed state core at this boundary, locks input with prior control
permission, hides the player until tick 17, and restores control on tick 42.
The arrival's final save event remains a request; this fixture performs no DOS
write and retains the handoff's centre checkpoint and saved direction.

Flash and shake counters decay once per fixed logic tick. Copper palette writes
implement Graphics::flashlight's complete RGB 0xBB fill without extra Chip memory.
Screen shake displacement and flash/teleport audio requests are not yet rendered
or played. The fixture starts after the validated room handoff and assumed hidden
departure pose; it does not implement departure or offer Energize in the menu.

`test-arrival-route` couples the extracted Game.cpp states to the extracted
Input.cpp/Entity.cpp/Map.cpp physics for 168 matching ticks, varying retained
velocity and saved facing while holding direction/flip through the control lock.
It also verifies dead/tower phase exclusion and failure handling.
`tower-energize-arrival-capture` compares 3,328 native trace fields over 128 ticks:
state/delays/effects/events, visibility, full launch velocities and history,
teleporter animation, checkpoint and control. The A500 uses 69,088 Chip bytes,
peaks at 207 PAL work lines, and reports zero errors/missed fields. A separate
one-tick hold verifies the captured flash viewport is uniformly RGB (187,187,187).
Route/handoff regressions pass. The native Building menu still passes its physical
input and gameplay-isolation checks, with zero errors/missed fields, 92,128 Chip
bytes and 205 peak PAL work lines; its disks remain unchanged.

Next: integrate departure, audio and screen shake, then exercise a native
Building/Energize round trip and final OS-safe save before enabling explored
Energize destinations in the playable selector. The frozen tower backdrop and
existing five-room playable save build remain the current supported scope.

## Short teleporter departure core — 8 October 2026

Added `teleporter_departure.c/.h` for the normal remote selector confirmation
and Game.cpp states 4000–4003. Start disables player control and the active
teleporter region and selects flashing tile 6. Departure requests flash on tick
1 and teleport audio on tick 11, hides the player and selects inactive tile 1
on tick 12, then unlocks state and emits the travel request on tick 22. The
source's manual state increments work even while state is locked. Control stays
disabled until arrival completes. The pending travel flag survives inactive
ticks and is cleared by the caller only after a successful room handoff.

The core owns no player motion, entity colour, rendering, audio, room load,
checkpoint mutation or disk access. Native integration must supply the flashing
player colour and its cyan restoration at state 4002, run locked input before
the script phase and physics afterward, and handle the effect requests. Active,
locked or unconsumed starts are refused; invalid state, delay, geometry and null
arguments retain all outputs.

`test-teleporter-departure` compiles for 68000 and compares the extracted remote
Input.cpp selection and 160 Game.cpp phase cases, including locked states,
delays and visibility. Forty sequential ticks verify the complete 22-tick
departure, one-shot cues/travel and persistent pending request under undefined
behaviour sanitization.

`test-departure-route` exercises two host Building → Energize → Building round
trips: 256 coupled source departure/arrival/input/physics ticks and four extracted
Script.cpp handoffs. It checks unchanged departure checkpoints, exact destination
centre saves, held-input locking and retained pending requests on rejected loads.
Selections are staged; this is not a native scene-bank, exploration/readiness,
audio, screen-shake or disk-save test. Arrival core/physics and travel regressions
also pass.

Next: connect departure to native Building/Energize scene-bank transitions and
arrival, then integrate effect audio, screen shake and the final OS-safe save.
Energize remains excluded from the playable selector until the native round trip
and explored-destination policy are validated.

## Native teleporter round trip — 8 October 2026

The opt-in round-trip fixture now runs short departure, the validated Script
handoff and default arrival on the native A500 in both directions. It starts
with an activated Building teleporter, requests Energize travel on tick 22,
restores arrival control on tick 64, starts a staged return on tick 65, requests
Building travel on tick 86, and completes arrival on tick 128. Input remains
locked through both sequences, and visibility and effect counters follow the
source cores. Departure and arrival events are recorded once per logic tick.

Each handoff rebinds collision terrain, compact foreground/palette and teleporter
DMA templates, invalidates both display banks, and pauses fixed logic during
cold rebuilding. The round trip uses 124 loading fields (62 per destination),
then resumes the source-derived 34,000/19,968 logic accumulator without advancing
scripts or effects during those pauses. The destination checkpoint is selected
at the handoff, and the pending departure request is consumed only on success.

`make -C amiga_version tower-teleporter-roundtrip-capture` checks 4,352 native
trace fields over the full 128 ticks and another 2,176 fields in a separate
64-tick outbound hold. Both captures pass with zero errors/missed fields,
69,088 Chip bytes and a 211 PAL-line peak. The captured Energize and returned
Building scenes are visually checked. Boot disks remain unchanged. The existing
arrival/flash captures and physical Building-menu regression also pass; the menu
build remains at 92,128 Chip bytes, 205 peak lines and zero errors/missed fields.

This is staged travel, not a newly selectable menu destination. The renderer
still uses the frozen tower backdrop and existing teleporter palette, and the
player's flashing departure colour remains to be integrated. Flash fills are
rendered, but effect audio and screen-shake displacement remain pending. Final
arrival save events do not yet invoke OS-safe disk persistence in this fixture.

Next: implement the remaining departure/effect visuals and audio, then connect
arrival save requests to a six-room persistence build and validate a fresh
boot. Enable Energize in the playable selector only after its explored
selection policy and this save path are verified.

## Native teleporter flashing colour — 8 October 2026

Added `teleporter_colour.c/.h` for Graphics::getcol(102), preserving its red,
green, blue and lavender branches and their channel calculations. Four uniform
16-bit samples stand in for fRandom(); each source RGB channel is truncated
before its high nibble becomes the OCS channel. The core uses integer arithmetic
and returns the source's fixed (196,196,223), OCS 0xccd, for noflashing or NULL
samples. It does not own randomness or effect timing.

The native staged round trip now samples flashing teleporter tile 6 and the
visible departure player once per fixed logic tick, with separate colour RNG
state so validated teleporter animation choices are unchanged. Colours remain
latched through cold scene-bank rebuilding and capture holds. State 4002 restores
the player's cyan colour as it hides the player; visible arrival uses the existing
0x6ff cyan. Active/inactive teleporter colours retain their previous mapping.
Full-screen flash still overrides every palette entry with 0xbbb. This reproduces
the source colour formulas at OCS precision, not its exact random sequence or
render-frame sampling frequency. Global noflashing UI/mode behavior is not added.

`test-teleporter-colour` compiles for 68000 and passes 337,680 comparisons against
the extracted Graphics.cpp case, covering all branch/channel sample thresholds,
mixed samples and fixed noflashing/NULL output under undefined behaviour checks.
`tower-teleporter-colour-capture` holds tick 6 after the first flash has decayed,
checks 216 native fields, and verifies the PNG contains the distinct expected
teleporter and player RGB colours. The capture is visually checked.

The full round trip now compares 4,608 fields (including per-tick colours), and
outbound checks 2,304. All three captures use 69,088 Chip bytes, peak at 220 PAL
work lines, and report zero errors/missed fields. Boot disks remain unchanged.
Arrival/flash and physical Building-menu regressions also pass. No new colour
sampling occurs during the 124 fixed-logic-paused destination-loading fields.

Next: integrate flash/teleport audio requests and screen-shake displacement, then
arrival disk saving and fresh-boot validation. Energize remains excluded from the
playable menu while explored-destination policy and persistence are unfinished.

## Teleporter audio overlap core — 8 October 2026

Source enum/load-order lookup maps Sound_FLASH to preteleport.wav (0.38449 s)
and Sound_TELEPORT to teleport.wav (1.50930 s). These effects overlap, including
three simultaneous cues during the staged return. The existing rescue one-shot
player remains in use for rescue speech. Travel audio needs overlapping voices.

Added `sfx_mixer.c/.h`: four caller-owned signed 8-bit one-shot voices at a common
sample period, allocated in lowest-free-slot order. It mixes with constant 1/4
gain to reserve four-voice headroom, truncates toward zero, advances every voice
through silent samples, clears completed slots and emits silence after tails.
Busy requests preserve playing voices and increment a dropped counter; invalid
arguments/state preserve outputs. Chunk boundaries do not change the waveform.
Completed counts rendered source tails, not drained Paula buffers.

`convert_teleporter_audio.py` derives filenames from the desktop enums and sound
load order, then reuses the private 9 kHz low-pass/signed 8-bit converter at PAL
period 161. Generated source/PCM hashes, headers and manifest remain in ignored
build output. The cues contain 8,474 and 33,254 bytes, including silent/aligned
tails. Tower asset generation now exports them separately; existing rescue PCM
and header hashes remain unchanged.

`test-sfx-mixer` compiles for 68000, checks all 16 occupancy masks against the
extracted desktop slot-allocation prefix (bounded to four voices), verifies
2,401 signed sum/headroom cases with an independent fractional oracle, and tests
uneven render chunks, silence and invalid-state preservation under undefined
behaviour sanitization. A field-quantized host round-trip schedule, including
62 PAL loading fields per destination, renders all eight source cues with three
peak voices and zero drops. Output matches the independent overlapping-waveform
oracle through its final silent tail. Existing one-shot audio tests and full
asset generation also pass.

This core is not yet connected to native playback and does not claim desktop
mixing-volume equivalence: the fixed quarter gain is deliberate headroom. No
new Chip allocation or native hardware behavior is introduced by this increment.
Next: evaluate hardware-panned Paula voices and mono software mixing, including
CPU/video headroom and the channel budget for eventual music. Choose the playback
backend from those measurements before connecting events and validating captured
waveforms and tail draining. Screen shake and final arrival saving follow.

## Audio output constraint — 8 October 2026

User guidance: mono or hardware-panned stereo is acceptable for the A500 port.
Centred stereo duplication is not a requirement. Paula has four independent
channels with fixed left/right routing, so channel allocation must account for
both sound effects and eventual music. See the Commodore Hardware Reference
Manual's [channel routing](https://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node00D9.html).

Prioritize direct DMA voices with hardware panning for the next native audio
experiment. Measure simultaneous-cue playback and reserve/channel-stealing policy
with future music in mind. Retain the tested mono software mixer as an alternative
for preserving overlaps, but measure its 68000 CPU cost before selecting it.
Duplicating an identical mono stream on a left/right pair is an optional output
arrangement and consumes two channels; arbitrary software stereo is not planned.
The current rescue stereo fixture remains a regression fixture, not a required
shipping audio layout. Source cue conversion and overlap tests remain useful for
either backend. No playback backend or final music/SFX channel split is fixed yet.

## Native hardware-panned teleporter audio — 8 October 2026

`make -C amiga_version tower-teleporter-audio-capture` now runs the staged
Building/Energize round trip with direct Paula DMA voices. The channel adapter
reuses the one-shot tail-draining engine and confines register, DMA and IRQ writes
to its selected channel. Requests select the lowest idle channel; playback keeps
advancing during the 124 paused room-loading fields. This experiment reserves no
music channels and does not establish the shipping music/SFX allocation.

The A500 capture completes all eight flash/teleport requests, with three peak
voices, zero drops and 16 completion IRQs. All 4,608 gameplay/render trace fields
still match the source oracle. Captured channel waveforms correlate with the
converted cues at 0.927–0.993; durations and sustained final silence pass. The
aggregate recording confirms channels 0/3 on the left and 1/2 on the right, with
routing correlations 0.793/0.829 after emulator filtering. Channel 3 stays silent.
The fixture uses **110,818 Chip bytes**, including 41,730 audio bytes, and peaks
at **233 PAL lines**, with zero missed fields or diagnostic errors. Sprite banks
are placed before the audio allocation to prevent overlap.

`test-paula-voice` checks four concurrent voices, isolated register plans,
selective DMA/IRQ masks, draining and transactional rejection under undefined
behaviour sanitization. The existing native rescue-audio regression also passes
(all six cues complete and the OS display is restored). The software mixer remains an alternative; its native
CPU cost has not been measured. Next: decide music/SFX channel reservation and
priority/stealing policy before extending this experimental playback to normal
gameplay. Screen shake and final arrival saving remain pending.

## Configurable Paula allocation policy — 8 October 2026

`audio_policy.c` provides a pure four-channel allocation decision. A caller-owned
mask protects channels reserved for music. Idle channels are chosen first, in
hardware order. When all permitted channels are busy (including cooldown and
silence draining), only a strictly higher incoming priority may replace a voice:
lowest priority first, then oldest elapsed age, then lowest channel. Equal-priority
requests are rejected rather than restarting existing cues. Allocation itself
mutates no voice or register state; sample validation and channel-local playback
remain the caller's responsibility. No shipping cue priorities or music channel
count have been selected, and the native fixture still uses its original pool.

`make -C amiga_version test-audio-policy` compiles for 68000 and checks 62,208
mask/occupancy/priority combinations against an independent ordered oracle,
24 age permutations including unsigned wrap-derived ages, invalid inputs, and
12 replacements across cooldown, playback and draining. Replacement plans touch
only the selected voice's DMA/IRQ bits; all three reserved voice states remain
unchanged. Checks run with undefined behaviour sanitization.

When the prior native capture is available, its eight recorded request times
also drive an optional budget simulation using the converted cue durations,
two cooldown fields and a final polling field. With experimental teleport-above-
flash priority, one SFX channel accepts six requests, drops two and interrupts
one cue; two channels accept eight but interrupt one cue; three or four channels
accept all eight without interruptions. This is not a music playback measurement.
Results are in `build/amiga-audio/audio-policy-budgets.json`. Next: connect the
policy to a native reserved-channel stress fixture and verify replacement audio
and reserved DMA/IRQ isolation before choosing the shipping music/SFX budget.

## Native reserved-channel replacement capture — 8 October 2026

The staged teleporter audio fixture now uses `v6_audio_choose` with a configurable
`V6_TRAVEL_SFX_MASK` (default 15). Experimental priority assigns teleport above
flash; accepted requests update caller-owned priority/start time only after
sample validation. Cooldown, playback and drain all count as occupied. Tick and
stop operations visit permitted channels only. The capture's register-plan
adapter records and blocks any attempted sample-register, DMA or IRQ write to a
reserved channel; the policy diagnostic exposes the mask and replacement count.

`make -C amiga_version tower-teleporter-reserved-audio-capture` uses mask 3:
channels 0/1 for SFX, 2/3 reserved and idle. All eight requests start with no drops
and two peak voices. The tick-65 flash is interrupted by the tick-75 teleport on
channel 1, producing seven fully drained cues, one replacement and 15 completion
IRQs. The isolated recording confirms the shortened flash (0.313 seconds), the
replacement teleport waveform, expected complete-cue durations, sustained final
silence and hardware panning. Reserved-channel stems remain silent, with zero
attempted forbidden writes. This checks SFX isolation with idle reservations;
concurrent music playback has not yet been implemented or measured.

All 4,608 round-trip source/render fields still match. The A500 fixture uses
110,818 Chip bytes, peaks at 229 PAL lines, and reports no errors or missed
fields. Artifacts are in `build/amiga-teleporter-reserved/`. The four-channel
fixture also passes with the allocator integrated: eight complete cues, zero
replacements or policy violations, unchanged channel order, all 4,608 trace
fields matching, and a peak of 233 PAL lines. Host policy and isolated voice
regressions pass. The shipping
music/SFX budget and cue priorities remain open. Next: assess the music asset
format and Paula channel requirements before selecting the allocation; screen
shake and final arrival saving also remain pending.

## Source music catalogue and tracker intake — 8 October 2026

The existing architecture decision remains Lightspeedplayer with a musician-
produced tracker soundtrack. `make -C amiga_version music-intake` now exports an
ignored `build/amiga-music/music-intake.json` catalogue from `Music.h`,
`BinaryBlob.h` and `Music.cpp`: 16 base IDs and source filenames, the 400-entry
music area map, source hashes, suggested `00.mod` through `15.mod` names, and
source loop policy. PATHCOMPLETE (0) and PLENARY (7) are one-shot tracks;
POSITIVEFORCEREVERSED (9) retains its own soundtrack identity. This does not
replace it with runtime reversal of another module. Alternate/custom soundtrack
IDs, fade/control implementation and module playback are not included yet.

For an actual module, run:

```
python3 tools/amiga/audit_music.py --module /path/to/02.mod --reserved-mask 0xc
```

The intake accepts 31-instrument four-channel ProTracker M.K./M!K! containers.
It checks header/order/sample bounds, tuning, volumes, instrument references and
sample loops, and reports stored pattern bytes, sample bytes, hashes, used
instruments, effect commands and ordered-pattern channel activity. Effects-only
commands count as activity. Proposed reserved-channel conflicts are reported;
zero conflicts do not establish replay safety. This is static inspection, not
complete tracker effect emulation, LSP conversion or converted-bank measurement.
`test-music-intake` verifies source IDs/loop policy, independent two-pattern MOD
fixtures, effects-only conflicts, unplayed patterns and 14 malformed inputs.

Upstream [standard LSP source](https://github.com/arnaud-carre/LSPlayer/blob/main/LightSpeedPlayer.asm)
exposes all four Paula register banks and patches DMA restart bits. Its sample
bank belongs in Chip memory and replay must run at the music rate. Therefore the
SFX reservation mask alone cannot protect SFX from a tracker player. A module
and player adapter must agree on channel ownership, including DMA restarts,
volume/fade writes and sample reloads. Music scheduling must remain independent
of 34 ms gameplay steps and paused destination loading. No upstream player code
has been vendored or connected in this increment.

No MOD/lsmusic/lsbank assets were found in the project/build output; the local
original soundtrack is a desktop `vvvvvvmusic.vvv` blob. Converted tracker-bank
memory, combined playback CPU cost and the shipping channel split remain open.
Next: implement source-validated music control/fade semantics independently of
the replay adapter; audit and measure a representative module when available.

## Portable source music transitions and fades — 8 October 2026

`music_control.c/h` now implement the base soundtrack control layer independently
of tracker replay. Caller-owned state tracks current/halted/queued IDs, pause,
backend presence, successful-start availability, source control gain (0..128),
quick/slow fade selection and the shared integer fade envelope. Commands emit
ordered start, pause-clock, resume-clock and gain operations for an adapter.
Gain is source control volume, not a Paula channel volume; user gain and tracker
instrument-volume scaling remain adapter responsibilities.

The core preserves the source's 3000 ms fade-in, 500/2000 ms fade-out, fade-out
duration proportional to current gain, evaluate-before-advance integer rounding,
zero-duration completion, same-track no-restart and queued niceplay ordering.
Fade completion pauses rather than destroys playback; resume restores the halted
song. Explicit halt cancels queued changes, whereas fade completion preserves
one for the same tick. Tracks 0/7 start once at full gain; other base tracks loop.
The source's safe-processing gate and unsuccessful backend-start state changes
are retained. IDs are restricted to -1/0..15 for play and 0..15 for niceplay;
alternate/custom soundtrack remapping is excluded. Duration and elapsed timestep
limits (60000/1000 ms) keep all products in bounded signed 32-bit arithmetic.

`make -C amiga_version test-music-control` compiles the core for 68000 and compares
30,167 state snapshots against extracted `Music.cpp` method bodies with minimal
backend stubs. Tests cover every base ID, complete fade envelopes, repeated and
queued requests, interruptions by one-shot tracks, pause/halt/resume, zero and
partial durations, unavailable starts and deterministic mixed sequences. The
fade-completion adapter order is explicitly checked as gain-zero, pause, start,
gain-zero. Invalid commands, limits, NULL arguments and corrupt states preserve
state/output transactionally. Host builds run with undefined behaviour
sanitization. Music intake regressions also pass.

No player code is linked into the native executable, and this increment adds no
Chip allocation or native timing claim. Control ticks consume game elapsed ms;
tracker replay must continue on its independent music clock during gameplay
pauses. Next: connect source room music selection to this controller and validate
its area-map/special-case behavior before native replay integration. A musician-
produced representative module is still needed for music/SFX memory and timing.

## Source room music selection — 8 October 2026

`music_area.c/h` now implement main-map `Music.cpp::changemusicarea` selection,
and `v6_music_change_area` connects it to the portable transition controller's
niceplay command. Inputs are normalized main-map coordinates 0..19: source
`Map.cpp` wraps ordinary room coordinates to 100..119 before subtracting 100.
The API validates each coordinate separately, avoiding overflow and flattened
index aliases, and requires boolean script/flip/time-trial flags.

The 400-byte signed music map is generated from source through
`export_music_area.py`, with Make dependencies on the source catalogue inputs.
The table contains no music samples and is immutable ordinary-memory data.
Script ownership and map value -1 suppress changes without disturbing current,
halted or queued IDs, fade envelope or processing flags. Tower entries (-2)
select Positive Force (2) normally and its reversed track (9) in flip mode.
The Space Station 2 entry (-3) selects Pushing Onwards (1) in time trials and
Passion for Exploring (4) otherwise. Other entries pass their base ID to niceplay;
selection queues transitions without directly starting the replay driver.

`make -C amiga_version test-music-area` cross-compiles both modules and checks
3,200 exhaustive room/flag selections and 22,400 controller snapshots against
extracted desktop area-map, changemusicarea, niceplay and fade method bodies.
Stateful route sweeps cover pending fades and repeated requests, including script
ownership while a transition is queued. Invalid coordinates/flags, NULL inputs
and corrupt controller state preserve state/output transactionally, even on
no-change paths. All host comparisons run with undefined behaviour sanitization;
the existing 30,167 transition/fade comparisons still pass.

These functions are not yet called by the native game loop and make no native
music timing or Chip-allocation claim. Custom/final-level rooms outside the main
map remain outside this selector. Next: cover source room-entry music dispatch
for final-level special cases and connect main-map selection at native route
handoffs using a trace fixture. Tracker playback still awaits a representative
musician-produced module and a player adapter with coordinated Paula ownership.

## Room-entry music dispatch and native controller trace — 8 October 2026

`v6_music_entry_track` and `v6_music_enter_room` now cover the music portion of
source `Map.cpp` room-entry dispatch. Normal coordinates wrap independently to
100/119 before main-map selection. Final mode takes precedence over custom mode;
only final time-trial room (46,54) requests Predestined Fate Remix (15), including
when a script is running. Other final rooms and custom-mode entries leave music
unchanged. Flags and controller state are validated transactionally. Custom
soundtrack playback and full final-level gameplay are not implemented here.
`test-music-entry` matches 14,270 snapshots against extracted Map.cpp dispatch
and Music.cpp controller methods, including extreme coordinates, mode precedence,
final-trigger neighbors and stateful transitions. Area, control and intake
regressions remain green.

`make -C amiga_version tower-teleporter-music-capture` adds an opt-in trace-only
controller to the native staged Building/Energize round trip. A virtual successful
backend is seeded with track 4, then source dispatch selects each room at startup
and route handoff. End-of-logic control ticks use 34 ms; the 124 cold scene-bank
loading fields do not advance this logic-clock envelope. Music emits ordered
adapter operations into the trace, with no tracker replay or Paula music writes.
This fixture uses normal mode, no running script, no flip mode and no time trial.

All 4,096 controller/operation/entry trace fields match the host oracle, with
controller snapshots checked against extracted desktop methods. The fixture
enters three rooms and requests looping tracks 2, 1 and 2 on ticks 1, 35 and 119;
final control gain is 11. All 4,608 gameplay/render fields still match. On the
A500 profile it uses 69,088 Chip bytes, peaks at 240 PAL lines and has zero errors
or missed fields. The trace itself occupies 16,384 ordinary RAM bytes plus its
header; these instrumentation costs are not a tracker replay timing estimate.
Artifacts are in `build/amiga-teleporter-music/`.

Native linkage exposed compiler runtime calls for 32-bit fade arithmetic and
aggregate clearing. Bounded products/quotients now use 68000 MULU/DIVU and
volatile byte clearing for trace plans, keeping the freestanding executable
free of those runtime dependencies. All 30,167 source controller comparisons
still pass, and the emitted arithmetic instructions are checked in the object.
The reserved-audio report also now retains its accurate idle-reservation scope.

Next: implement the adapter's user/control/instrument gain scaling and channel
ownership rules, then measure combined playback using a representative converted
tracker module. Native source music selection/fades are traced, but no music is
yet audible and the shipping music/SFX split remains open.

## Music gain plans and volume ownership — 10 October 2026

`music_gain.c/h` add the portable adapter's volume stage. The source first
truncates control gain (0..128) times user gain (0..256) divided by 256. Each
tracker instrument volume (0..64) then scales by that result divided by 128,
truncating at Paula resolution. This two-stage rule retains source user-gain
rounding; the second stage is the chosen hardware quantization. Global/music
mute select zero without changing the caller's stored instrument volumes, so
unmuting can restore the current tracker envelope.

A gain plan accepts disjoint music/SFX masks and writes only the music-owned
AUDnVOL words, in hardware channel order. It emits no DMA or IRQ operations and
leaves SFX/unassigned registers untouched. Empty music masks emit empty plans.
Invalid masks, overlapping ownership, invalid gain/instrument values, nonboolean
mute flags and NULL inputs preserve the output transactionally. This enforces
ownership for gain writes only; raw tracker sample/period/DMA writes still need
a coordinated driver boundary. No shipping channel split is selected.

`make -C amiga_version test-music-gain` checks 2,254,404 source/fraction gain
comparisons and 324 valid partition/mute plans. The reference extracts both
source set_music_volume and updatemutestate bodies. Tests cover all source
control/user pairs and instrument levels, effects ownership, mute restoration,
register isolation and invalid-input preservation under undefined behaviour
sanitization. The 68000 object uses native MULU with power-of-two shifts, and an
entry-point link check verifies there are no freestanding runtime dependencies.

The gain stage is not yet connected to tracker replay or native gain writes;
no new Chip allocation, audible music or playback timing is claimed. Next:
implement the driver boundary for decoded tracker register plans, including
reserved-channel sample/period writes and DMA restarts, then connect it to an
actual representative module for combined playback measurements.

## Decoded tracker register ownership boundary — 10 October 2026

`music_registers.c/h` add a transactional filter for decoded word-register plans.
Disjoint music/SFX masks select ownership; SFX and unassigned AUDn location,
length, period and volume writes are removed. Audio DMA/IRQ masks are reduced to
music-owned bits, preserving set/clear direction and operation order; operations
with no remaining channel bits are omitted. Exact in-place filtering is supported.
The full input (including suppressed channels) is validated before output changes.
Unsupported registers, global DMA/interrupt bits, invalid volumes, oversized
word values and plans above 16 writes are rejected. Global DMA master ownership
and interrupt enables remain the platform takeover layer's responsibility.

This boundary assumes volume words have already passed through gain scaling. It
does not validate Chip pointer accessibility, sample lifetimes or complete tracker
commands. Raw LSP byte/long writes must be decoded by an adapter first; running
upstream replay directly against Paula would bypass these guarantees. Larger
tracker ticks require planned batching; this API is bounded to 16 writes per plan.
No shipping channel allocation or native tracker integration is selected here.

`make -C amiga_version test-music-registers` checks 41,472 partition/DMA/IRQ plans
and exact in-place results under undefined behaviour sanitization. Independent
register models begin with all channels enabled and all audio IRQs pending,
confirming that reserved sample/period registers, DMA bits and IRQ bits survive.
Tests also cover every supported channel register, full-capacity plans, mixed
valid/malformed streams, forbidden global bits, suppressed-channel errors, NULL
inputs and transactional rejection. The object cross-compiles and links as a
freestanding 68000 entry point with no runtime library dependencies.

No new native playback, Chip allocation or timing claim is introduced. Next:
compose gain plans and guarded sample/restart plans in a native synthetic
music/SFX coexistence fixture, then connect an actual converted representative
tracker module to measure the replay adapter and combined frame budget.

## Native synthetic music/SFX coexistence — 10 October 2026

`make -C amiga_version tower-coexist-audio-capture` now combines synthetic
looping replay on channels 2/3 with the two-channel teleporter SFX pool on 0/1.
A generated 64-byte triangle sample is shared by the looping voices, with
instrument volumes 48/32. Decoded plans intentionally contain writes for all
four channels: the register boundary removes SFX-owned locations, lengths,
periods, DMA and IRQ bits before application. Music IRQ acknowledgement runs
before SFX IRQ polling, exercising isolation with the hardware voices active.
A separate native application check records forbidden-write attempts.

Seven hardware-field stages cover start (field 1), half gain (80), music mute
(120), half-gain restoration (160), full gain (200), changed periods (240) and
stop (280). Gain plans are also passed through the register boundary. Synthetic
playback continues during cold scene-bank loading independently of logic ticks;
this is fixed synthetic replay, not tracker tempo scheduling or a MOD player.
The stop uses a raw all-channel DMA-clear plan, testing preservation of active
SFX channels through filtering. Exit cleanup also stops music-owned DMA.

Captured isolated stems verify half-gain ratios of approximately 0.500 on both
voices, exact silent mute windows, restored gains and final sustained silence.
Hann-windowed spectral scans find fundamentals 344/221 Hz on channel 2 and
230/306 Hz on channel 3 before/after period changes. Spectral analysis avoids
false extra zero crossings from emulator filter ringing. Aggregate stereo
correlations confirm hardware panning (0.915/0.965). All eight SFX requests start;
seven cues drain completely and one flash is replaced by a teleport, as in the
existing two-channel policy fixture. SFX waveforms, durations, replacement and
silence remain valid with the synthetic voices active. Both ownership diagnostics
report zero violations; all 4,608 gameplay/render trace fields still match.

On the A500 profile the combined fixture uses 110,882 Chip bytes (64 more than
the reserved-SFX fixture), peaks at 234 PAL lines, and reports zero errors or
missed fields. Artifacts are in `build/amiga-coexist-audio/`. Gain and register
boundary host tests and freestanding link checks also pass. The original private
cue assets remain in ignored build output; the synthetic sample is generated
at startup and introduces no licensed music asset.

This validates the adapter primitives during native overlapping playback;
it does not measure Lightspeedplayer, tracker conversion, actual module memory
or soundtrack quality. The fixture holds its scene for capture, so full OS-exit
restoration has not been capture-validated here. Next: adapt actual tracker
replay to emit decoded ownership-safe plans and measure a representative module
alongside gameplay/SFX before selecting the shipping music channel budget.

### Audio-to-tracker recognition experiment

`tools/amiga/transcribe_tracker.py` now makes a bounded pitch sketch from a
recording using Basic Pitch 0.4.0 with ONNX. This is an experimental route from
original game audio to a tracker approximation, not recovery of the original
score. It exports detected MIDI/JSON, four-channel and two-channel ProTracker
MODs, and a structural report. Each row selects lowest bass/highest melody,
then strongest inner notes for the remaining voices. Triangle loops replace
source instruments; percussion/effects are not reconstructed, octave folding
keeps periods in range, and changing chord ranks can retrigger voices.

Reproduce in an isolated Python 3.9 environment (all assets under ignored
`build/`; do not commit original recordings or derived music):

```sh
python3.9 -m venv build/amiga-transcription-env
build/amiga-transcription-env/bin/python -m pip install -r tools/amiga/transcription-requirements.txt
build/amiga-transcription-env/bin/python -m pip install --no-deps basic-pitch==0.4.0
build/amiga-transcription-env/bin/python tools/amiga/transcribe_tracker.py PATH_TO_POSITIVE_FORCE_RECORDING --duration 24 --out build/amiga-transcription/prototype
python3 tools/amiga/test_transcribe_tracker.py
```

Supply a locally extracted `data/music/2positiveforce.ogg` from the installed
music blob, or a WAV excerpt. `--bpm` overrides the uncertain automatic estimate.
The prototype input was a mono 22,050 Hz first-24-second WAV, made with ffmpeg;
its report records the input digest. Basic Pitch found 351 notes; beat tracking
estimated 92.285 BPM, rounded to 92. Neither recognition nor beat accuracy has
been confirmed by listening. The four-voice reduction omitted 81 note-rows;
the two-voice reduction omitted 512, so this arrangement is intentionally lossy.

Independent Lightspeedplayer converter 1.33 (`arnaud-carre/LSPlayer`, built with
CMake in ignored `build/amiga-lsp-tools`) accepted both modules and rendered
non-silent, 48 kHz hard-panned stereo previews using `-amigapreview`. Both last
24.043 seconds and use 1,572-byte LSP sample banks; score sizes are 3,631 and
2,535 bytes respectively. MOD source sample storage is 96 bytes. The reduced
module contains events only on channels 2/3, leaving 0/1 empty; this static fact
does not prove the replay driver avoids writing reserved channels. Playback at
92 BPM requires variable-rate scheduling/CIA or converter `-fixed50hz` handling.
This has not yet been integrated into native gameplay or measured on the A500.

Private audition artifacts: `build/amiga-transcription/prototype/`, including
`excerpt.wav`, `four-channel_amiga.wav`, `two-channel_amiga.wav`, both MODs,
detected MIDI, notes and report. Structural tests check reserved-channel
silence, pitch error, note release, loop placement and duration/tempo bounds.
Next: listen against the source, correct beat/subdivision and stable voice
assignment, separate bass/lead/percussion, and improve timbres before native
replay integration. Current output is a reviewable recognition baseline, not
shipping soundtrack quality.

### Eight-channel working arrangement and revised reduction target

User audition: the four-voice pitch sketch is recognisable but needs substantial
refinement; the two-voice sketch is not recognisable. Two music voices are no
longer the intended soundtrack budget. Plan for three or four music channels;
SFX allocation must be reconsidered after the arrangement is convincing.
Existing two-channel coexistence fixtures remain useful adapter tests, not a
shipping channel-budget decision.

The transcription exporter now writes `eight-channel.mod` (8CHN editing master)
and the four-channel baseline by default. The rejected two-channel baseline is
available only with `--legacy-two-channel`. The master retains held events on
stable lanes, allocates new events to free lanes and uses different triangle
loop lengths to preserve detected pitch without octave folding. This is event
continuity, not identification of instruments or musical parts. It still uses
the existing uncorrected 92 BPM grid and recognition results.

For the Positive Force excerpt, the editing master retains all 351 detected
note starts with zero omitted note-rows, uses 496 sample bytes, and occupies
11,820 bytes. Private output: `build/amiga-transcription/eight-master/`. Tests
cover stable held lanes when a lower note enters, low/high pitch preservation,
eight-channel pattern storage, plus prior four-channel checks. The eight-channel
file has not yet been auditioned or independently player-validated; the LSP
converter and four-channel hardware intake are not its playback path.

Next sequence:

1. Correct the eight-channel master against the recording: beat/grid and note
   errors first, then stable melody, bass, harmony and percussion parts, timbre
   and envelopes. Additional channels preserve room for these parts; they do
   not improve recognition automatically.
2. Once the master is musically convincing, compare three- and four-channel
   reductions. Keep lead/bass articulation; consider pre-rendered chord samples
   or layered attacks for simultaneous inner voices. Chord sample transposition
   shifts every component together, so use a suitable sample per chord shape
   and retain independent parts when their timing/envelopes differ. Measure
   converted Chip bank size and audible seams; do not assume tiny loop samples
   suffice for every chord or instrument.
3. Decide SFX policy from those arrangements (reserved voice, temporary voice
   stealing or further measured mixing), then validate ownership-safe native
   replay, timing and memory alongside gameplay. No shipping allocation is
   selected by the eight-channel editing format.

### Independent eight-channel playback and finer timing grid

`tools/amiga/render_tracker.py` independently loads and renders MOD files using
an explicitly supplied local libxmp shared library. It bounds playback at 120
seconds, stops at the first loop, exports stereo 48 kHz WAV and records module
and library digests. The final buffer may include up to 100 ms of silence;
player tick rounding can also affect rendered duration. This is host tracker
playback, not an Amiga hardware capture. No third-party library or music is
committed. Tested libxmp revision: `5d4f6aa2c7dcdf8e9cd8129fe579d45b36a302da`.

Independent playback identified a reference tuning mismatch: the sample-period
calculation passed structural checks, but libxmp's multichannel MOD playback
rendered test notes approximately 17 cents flat. The editing master's samples
now use MOD finetune +1. Five independently rendered pitches spanning MIDI
24, 48, 55, 72 and 84 measure roughly 5.2–5.9 cents flat. The optional integration
check also verifies audible note starts, sustained silence after release, first
loop completion and rejection of a truncated pattern stream. This validates
those test pitches through this player; it does not establish all-player or
native Paula tuning. Four-channel legacy exports are unchanged.

Master note starts/releases now round to the nearest row, with at least one row
for short detections, rather than always delaying a start to the next row.
`--master-bpm` permits a finer editing grid independently of the four-channel
baseline's tempo. For the unchanged 351 Positive Force detections:

- 92 BPM: 23.51 ms RMS onset displacement, at most 40.66 ms.
- 184 BPM: 12.56 ms RMS onset displacement, at most 20.27 ms.

Both masters retain all 351 starts with no omitted note-rows. This comparison
shows grid precision relative to recognition timestamps; it is not a source
beat/tempo or transcription accuracy score. Doubling BPM changes the editing
subdivision and pattern placement. The 184 BPM option is an audition candidate,
not a confirmed musical tempo. Private tuned previews and modules are in
`build/amiga-transcription/refined-grid/master-{92,184}.{wav,mod}`. Independent
playback accepts both and completes their first loop; bounded WAV files last
24.2 seconds including player rounding/final padding. The 184 BPM MOD occupies
22,060 bytes versus 11,820 bytes for 92 BPM; sample storage remains 496 bytes.

Reproduction (original/derived audio remains ignored):

```sh
git clone https://github.com/libxmp/libxmp.git build/amiga-libxmp
cmake -S build/amiga-libxmp -B build/amiga-libxmp/build -DBUILD_SHARED=ON
cmake --build build/amiga-libxmp/build -j 4
build/amiga-transcription-env/bin/python tools/amiga/transcribe_tracker.py PATH_TO_POSITIVE_FORCE_RECORDING --master-bpm 184 --out build/amiga-transcription/refined
python3 tools/amiga/render_tracker.py build/amiga-transcription/refined/eight-channel.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/refined/eight-channel.wav
build/amiga-transcription-env/bin/python tools/amiga/test_tracker_render.py --library build/amiga-libxmp/build/libxmp.dylib
```

The shared-library filename above is for macOS; pass the corresponding library
path on another supported little-endian host. Next: compare the audition
candidates to the source, correct recognition errors and identify musical parts
before separating percussion/improving timbres or baking chord samples. No
musical part identification or subjective quality improvement is claimed yet.

### Audition decision: retain original grid; defer vibrato repair

User comparison finds the original 92 BPM editing grid sounds just as good as
the finer 184 BPM candidate. Keep 92 BPM as the working baseline; retain the
finer candidate for comparison without making it the preferred arrangement.
This is an audition choice, not confirmation of the recording's musical tempo.

The user hears vibrato in the recording that the reconstruction misses and
suspects it contributes to dropped notes. That causal explanation remains to
be checked against pitch contours; retaining every detected note does not mean
the recognizer detected every source note. Defer vibrato reconstruction and
related note-gap repair until later, as requested. When revisiting it, inspect
pitch contours and distinguish modulation within a sustained note from a new
attack before merging fragments or adding tracker vibrato/pitch effects.

Next priority remains identifying melody, bass, harmony and percussion and
improving timbres on the eight-channel master. Keep three/four-channel reduction
and chord-sample baking downstream of that work.

### Provisional musical roles, distinct timbres and percussion audition

`tools/amiga/arrange_tracker.py` builds an editable eight-channel audition from
cached detected notes and the source excerpt, keeping the chosen 92 BPM grid.
Pitch-range guesses assign MIDI below 48 to bass, 67 and above to lead, and the
remainder to harmony. These are provisional labels, not recovered instruments
or a corrected score. Boundaries are CLI options; `arrangement.json` records a
role per input note, role levels, transient samples and hit events. Reusing an
edited arrangement checks the detected-note file digest and does not rerun note
recognition or transient extraction. Vibrato and note-gap repair remain deferred.

The master exporter accepts optional roles, prefers bass channels 0/1, lead 2/3
and harmony 4/5/6, and spills into other free pitched channels during overlaps.
Held notes retain their lanes. Channel 7 is reserved for percussion. Distinct
loop banks use a round bass wave, a bright seven-harmonic pulse-like lead and
softer harmony. Default level multipliers are bass 1, lead 1.2, harmony 0.5;
these are editable audition choices, not measured source instrument matches.
The original all-triangle working master remains available unchanged in mode.

Percussion extraction uses a conservative HPSS percussive component, onset
detection and spectral-centroid low/mid/high transient categories. It chooses
one energetic source excerpt per category, converts it to a short 11,025 Hz
signed 8-bit one-shot and reuses it for that category's detected hits. Attack and
release fades reduce clip-edge clicks. Transient labels deliberately do not
claim kick/snare/hat recognition. Melodic attacks can leak into samples and hit
candidates; onset timestamps, selection, playback rate and repeatability require
listening review. Same-row hits retain the stronger candidate; a subsequent hit
can truncate the preceding one-shot on the single percussion lane.

For Positive Force's first 24 seconds: 53 bass, 103 lead and 195 harmony guesses;
all 351 note starts are played. Reserving percussion causes one omitted pitched
note-row (the affected event starts later); 14 starts spill outside preferred
role channels. 165 candidate transients produce 157 tracker hit rows after eight
same-row collisions. Three 1,764-byte transient samples plus pitched banks use
6,780 MOD sample bytes; the complete editing MOD occupies 18,104 bytes. These
are MOD storage figures, not converted hardware bank measurements.

Private mix, four isolated stems, MODs and editable arrangement are in
`build/amiga-transcription/role-arrangement/`. Independent libxmp playback accepts
all five modules, reaches their first loop and produces non-silent previews
without clipping. They last 24.2 seconds including replay rounding/padding.
Structural tests cover role-to-bank/channel assignments, percussion reservation,
non-looping sample headers and invalid role counts; existing pitch/release/loop
playback tests and music intake checks also pass. No subjective improvement or
successful instrument separation is claimed before audition.

```sh
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/eight-master/notes.json --out build/amiga-transcription/role-arrangement
python3 tools/amiga/render_tracker.py build/amiga-transcription/role-arrangement/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/role-arrangement/arranged-eight.wav
```

To re-export corrections, add `--arrangement PATH_TO_EDITED_ARRANGEMENT_JSON`.
The remaining `bass`, `lead`, `harmony` and `percussion` MOD stems can be rendered
with the same command. Original and derived licensed assets remain ignored.
Next: audition stems to correct role guesses and transient contamination, then
improve instrument matching/envelopes. Three/four-channel reduction and chord
sample baking remain downstream of the eight-channel arrangement.

### Role-arrangement audition: melody close; percussion needs identification

User audition finds the role-based mix close and the melody close. Retain that
arrangement and the original timing grid as the next comparison baseline.
Percussion, especially the drum sample, is not being recognised adequately.
The present low/mid/high transient exemplars are not identified drum instruments;
this feedback establishes percussion identification and timbre matching as the
next priority, ahead of general melodic timbre changes or channel reduction.

Next: inspect candidate source hits and isolated percussion, distinguish actual
drum attacks from melodic leakage, and match representative drum sounds and
hit timing. Preserve the accepted melodic baseline during that comparison.
Vibrato and associated missing-note repair remain deferred. This audition does
not confirm every melodic note or validate the current percussion transcription.

### Repeated-hit drum candidates with preserved low-frequency attacks

`tools/amiga/recognize_percussion.py` replaces the broad low/mid/high transient
exemplars with a new percussion-only audition. It keeps the accepted 92 BPM
arrangement's pitched channels, role levels, instrument headers and sample bank
byte-for-byte identical. Vibrato and melody recognition remain untouched.

The detector combines a gentler HPSS mask with low-frequency spectral novelty,
so tonal low-frequency attacks are not automatically removed with harmonic
content. Independent low/mid/high-band onset detection catches quieter high-band
hits beneath stronger attacks. Nearby energy rise refines timestamps on both
sides of centered spectral frames; an energy-growth check and 60 ms deduplication
reduce repeated detections inside decaying drum tails. Those choices can still
miss fast rolls or simultaneous hits.

Short spectral-band and decay profiles form three recurring-hit clusters.
Brightness ordering gives provisional kick/snare/hat labels; a representative
cluster member above the quietest detections supplies each exemplar, replacing
the previous maximum-energy selection. Category filters, resampling to 11,025 Hz
and short edge fades produce 240 ms signed 8-bit one-shots. This is unsupervised
candidate classification, not confirmed identification of the game's drums.
Pitched attacks can still contaminate clusters, and brightness ordering can
mislabel a class. Single-lane playback still truncates overlapping sample tails;
simultaneous layers need later inspection/composite samples or a different budget.

A controlled test beneath sustained bass/lead tones initially exposed missed
hats and retriggers in decaying drum bodies. After fixes it detects and labels
all nine separated synthetic kick/snare/hat hits within 60 ms, checks MOD sample
layout, and emits no hits for silence or the sustained-tone-only input. This
establishes controlled behavior; it does not prove real-song detection accuracy.
The test requires the isolated audio environment's NumPy/SciPy/librosa and
scikit-learn dependencies (scikit-learn 1.6.1 is now pinned explicitly).

Positive Force yields 166 candidate attacks: 42 kick, 82 snare, 42 hat guesses.
Representative source times are 21.213, 11.350 and 20.370 seconds respectively.
The unchanged grid emits all 166 as distinct hit rows. The resulting MOD is
20,750 bytes with 9,426 sample bytes, not converted Amiga bank measurements.
Independent libxmp playback accepts the mix and percussion stem, completes the
first loop and produces non-clipping previews (mix peak 0.560, percussion 0.308).
All 320 stored rows' seven pitched-channel cells, their headers and the 1,488-byte
pitched bank match the accepted baseline exactly. All 351 melodic note starts
remain, with the same one-row overlap delay as before.

Private outputs in `build/amiga-transcription/drum-refinement/` include the mix,
percussion stem, individual `sample-{1,2,3}.wav` candidates, cleaned source stem,
editable arrangement/hit profiles and provenance reports. Next: audition the
candidate kick/snare/hat sounds and percussion sequence against the recording,
correct wrong classes/exemplars and timing, and inspect simultaneous hits before
any channel reduction. No subjective improvement is claimed before audition.

```sh
build/amiga-transcription-env/bin/python tools/amiga/test_percussion_recognition.py
build/amiga-transcription-env/bin/python tools/amiga/recognize_percussion.py build/amiga-transcription/positive-force-excerpt.wav --arrangement build/amiga-transcription/role-arrangement/arrangement.json --out build/amiga-transcription/drum-refinement
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/eight-master/notes.json --arrangement build/amiga-transcription/drum-refinement/arrangement.json --out build/amiga-transcription/drum-refinement
python3 tools/amiga/render_tracker.py build/amiga-transcription/drum-refinement/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/drum-refinement/arranged-eight.wav
```

Use the same renderer for `percussion.mod`. Original and derived recordings,
exemplars and modules remain ignored and uncommitted.

### Drum-candidate audition: reject melodic contamination

User audition of the repeated-hit candidates finds melodic content remaining:

- Sample 1 (kick candidate) contains higher-pitched melodic material that should
  not be in the drum sample. It is contaminated and not accepted as a kick.
- Sample 2 (snare candidate) sounds like a chord rather than percussion and is
  not recognised. Reject it as a percussion exemplar.
- Sample 3 (hat candidate) sounds close to an instrument in the track. Retain it
  only as a possible instrument/timbre reference, not as a confirmed hi-hat.

The controlled synthetic test did not establish separation or drum identification
in the mixed game recording. The real-song brightness clusters are still able
to select pitched attacks/chords. Neither the candidate labels nor their 166
hit assignments are accepted as a drum transcription. Existing private outputs
remain available as comparison artifacts, not approved musical assets.

Next change the recognition criterion before another sample-selection pass:
inspect harmonicity, pitch stability/sweep, broadband noise and amplitude decay
in source hits to distinguish pitched attacks from percussion. Then seek clean
representative hits or reconstruct drum sounds from measured noise/decay/sweep
parameters if isolated samples remain contaminated. Avoid promoting source
chops to drum samples on spectral brightness alone. Preserve the accepted
melody/grid, keep sample 3 separately available for instrument comparison, and
leave vibrato repair deferred.

### Percussion reconstruction instead of contaminated source chops

`tools/amiga/reconstruct_drums.py` starts from the previous candidate timestamps
but evaluates nearby original-audio attacks independently of their rejected
brightness labels. It checks active-band spectral flatness, narrow-peak energy
concentration, decay, low-frequency dominant-peak movement and high-band energy.
A kick hypothesis requires a low-frequency downward sweep; a noise-drum
hypothesis requires a sufficiently broadband, decaying attack. Other events are
retained as rejected/ambiguous observations. Candidate provenance must match
the supplied recording; analysis skips short end-of-excerpt clips.

Accepted groups provide median sweep/decay parameters. Their samples contain
no copied source waveform: kick is one exponentially swept sine oscillator;
snare/hat paths use reproducible seeded filtered noise with decaying envelopes.
Low-band residual decay estimates the kick envelope; noise envelopes use the
measured decay, with bounded fallback/clamping where mixed-source estimates
are weak. Filters and oscillator/noise models are deliberately simple timbre
approximations, not confirmed matches to source instruments. This removes the
previous direct route by which melodic notes/chords entered sample audio, but
it does not establish that all retained timestamps are actual drum hits.

Controlled checks recognize isolated sweep/noise drum fixtures, reject strongly
attacked and decaying sine/chord fixtures, verify sample determinism and decay,
check that reconstructed kick energy above 600 Hz is below 1%, and produce no
drums from silent input. Those fixtures do not prove separation or classification
accuracy when real drums and instruments overlap in the source recording.

For Positive Force, 13 kick and 37 snare hypotheses remain, 115 attacks are
rejected, and one short final clip is skipped. No hat passes the conservative
criteria; do not invent a hat sequence or reuse sample 3 as a confirmed hat.
The estimated kick sweep is approximately 151 to 86 Hz with a 62 ms amplitude
constant. The simple snare noise envelope is clamped to 100 ms. The editable
arrangement records all measurements/rejection reasons. Reconstructed samples
and pitched banks total 9,990 MOD sample bytes; the MOD is 21,314 bytes. These
are editing-file figures, not converted Amiga bank measurements.

The seven pitched-channel cells across all 320 stored rows, their instrument
headers and the 1,488-byte pitched bank remain byte-for-byte equal to the
accepted role arrangement. The original 92 BPM grid, 351 pitched note starts,
role levels and prior overlap delay remain unchanged. Vibrato repair is deferred.
Independent libxmp playback accepts the new mix/percussion modules, completes
the first loop and produces non-clipping previews (mix peak 0.486; percussion
0.292). Both bounded previews last 24.2 seconds with rounding/padding.

Private outputs: `build/amiga-transcription/reconstructed-drums/`, with mix,
percussion stem, standalone `kick.wav`/`snare.wav`, editable measurements and
arrangement. A copy of the old sample 3 is retained separately as
`instrument-reference-3.wav` for instrument comparison; it is not played as a
drum in this arrangement. No licensed audio/modules are committed.

```sh
build/amiga-transcription-env/bin/python tools/amiga/test_drum_reconstruction.py
build/amiga-transcription-env/bin/python tools/amiga/reconstruct_drums.py build/amiga-transcription/positive-force-excerpt.wav --candidates build/amiga-transcription/drum-refinement/arrangement.json --arrangement build/amiga-transcription/role-arrangement/arrangement.json --out build/amiga-transcription/reconstructed-drums
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/eight-master/notes.json --arrangement build/amiga-transcription/reconstructed-drums/arrangement.json --out build/amiga-transcription/reconstructed-drums
python3 tools/amiga/render_tracker.py build/amiga-transcription/reconstructed-drums/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/reconstructed-drums/arranged-eight.wav
```

Next: audition these reconstructed drum timbres and the reduced candidate hit
sequence against the source; correct missing/wrong hits and envelope/timbre
estimates. No subjective drum match is claimed before that review. Simultaneous
percussion and three/four-channel reduction remain later work.

### Percussion audition accepted sounds; bias placement towards repeated bars

User audition accepts the reconstructed kick/snare sounds but rejects their
placement. Percussion keeps the track's rhythm, so recurring positions across
bars are now preferred over independent local attack decisions. Preserve the
accepted drum waveform bytes and the melody while changing hit placement.

`tools/amiga/regularize_percussion.py` estimates a repeating period from
normalized low/high-band onset-envelope autocorrelation. The earliest strong
1..4-second repeat within 95% of the best peak becomes the candidate bar length,
with local peak interpolation. This interprets repetition as a four-beat bar
and assumes initial downbeat phase zero; neither meter nor phase is confirmed.
Manual `--bar-seconds`/`--phase` overrides remain available.

Distinct bars vote once per sample/16th-note position. A configurable backbeat
prior (default weight four independent-bar votes) favors kick beats 1/3 and
snare 2/4. The two strongest positions per instrument form a repeating template,
repairing missed occurrences and suppressing isolated/off-template detections.
Only instruments with existing hit evidence participate. This is a deliberate
regularization hypothesis, not a recovered exact score: it can erase genuine
syncopation, fills, rests and section changes. `--prior-weight 0` reduces the
prior's influence; templates/evidence remain editable in the arrangement JSON.

For Positive Force the candidate repeat is 1.714025 seconds (correlation 0.520),
equivalent to 140.021 quarter-note BPM under the four-beat assumption. This is
independent of the retained 92 BPM editing clock; the melody remains unchanged.
The proposed template is kick on beats 1 and 3, snare on beats 2 and 4. Detected
support for those positions spans 5/1 kick bars and 2/5 snare bars respectively,
so the weaker positions are materially influenced by the prior. The template
fills the excerpt with a steady backbeat and still requires source audition.

The master exporter now optionally quantizes percussion to ticks (not whole
rows), writing ED0/ED1/ED2 note delays at speed 3. At 92 BPM a tick is 27.174 ms;
placed-hit rounding is at most 12.83 ms here instead of a half-row up to 40.76 ms.
Delayed notes use per-instrument median template gain because one MOD cell
cannot encode both EDx and Cxx. Sample waveforms are unchanged. The final
percussion cell carries B00: one candidate at the excerpt boundary is skipped
rather than overwriting its delay. Reports distinguish boundary skips from
actual same-row collisions.

There are 56 placed hits with no collisions, plus that one boundary skip.
All seven pitched-channel cells, their headers and every waveform byte equal
the preceding accepted arrangement. The MOD remains 21,314 bytes with 9,990
sample bytes. Independent libxmp playback accepts the mix/stem, completes their
first loop and produces non-clipping previews (mix peak 0.583; percussion 0.244).
Artifacts: `build/amiga-transcription/regular-drums/{arranged-eight,percussion}.wav`
and the corresponding modules, editable bar template and evidence report.

Tests cover filling a missing bar, repeated positions, preventing a one-bar
roll from dominating consensus, phase, no-hit input, ED2 encoding and explicit
boundary skips. An independent waveform test verifies ED2 delays audible onset
instead of playing at row start. Existing master structure, pitch/release/loop
playback and four-channel intake checks also pass. This has not yet been
validated through LSP/native gameplay. Vibrato remains deferred.

```sh
python3 tools/amiga/test_percussion_rhythm.py
build/amiga-transcription-env/bin/python tools/amiga/regularize_percussion.py build/amiga-transcription/positive-force-excerpt.wav --arrangement build/amiga-transcription/reconstructed-drums/arrangement.json --out build/amiga-transcription/regular-drums
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/eight-master/notes.json --arrangement build/amiga-transcription/regular-drums/arrangement.json --out build/amiga-transcription/regular-drums
python3 tools/amiga/render_tracker.py build/amiga-transcription/regular-drums/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/regular-drums/arranged-eight.wav
```

Next: audition bar phase and template positions against the source, adjusting
syncopation/fills where necessary while preserving accepted timbres. Original
and derived licensed audio remain ignored and uncommitted.

### Preserve promising groove; add sparse observed syncopation/pickups

User audition finds the regularized bar phase promising and the result starting
to sound musical. Keep that phase, steady groove and accepted drum timbres as
the working baseline; this feedback does not confirm an exact rhythm score.

`tools/amiga/vary_percussion.py` adds conservative variations to that accepted
regular arrangement. The original unregularized observations must align within
30% of a 16th-note slot (32.14 ms here), and an extra position must recur in at
least three distinct bars. Multiple detections/roll hits in one bar count once.
Even-slot offbeat kick positions may be restored in observed bars. Late-bar
snare pickups may be restored only where observed at an assumed four-bar phrase
end. At most one extra is allowed per bar, with a supported phrase-end pickup
preferred there. Anchor positions and existing hits are never removed or moved.

The bar length/phase are taken directly from the promising arrangement rather
than re-estimated. Samples, instrument-header levels and EDx timing are retained.
Variation support counts, original detection timestamps, alignment exclusions
and chosen additions remain editable in the output JSON. Re-export is idempotent
and retains the original base-groove hit list. This does not establish correct
source drum identities, phrase length, rests or fills; the prior detector's
labels can still be wrong. It is an audition of sparse evidence-backed additions.

For Positive Force, four offbeat kicks at approximately 12.641, 16.069, 17.783
and 22.925 seconds restore slot 6 (the eighth-note upbeat following beat 2),
supported in four observed bars. One snare at 20.461 seconds restores slot 15
(the last sixteenth before the next downbeat) at a phrase end; that slot has
observations in five bars. Three observed slot-14 snare bars also qualify as
candidates but are not selected under the one-extra/phrase-priority rules.
Four original observations fail the alignment tolerance. Other isolated or
non-qualifying positions remain suppressed; no fills are invented for missing
observations or unobserved phrase boundaries.

There are 61 placed drum hits (five more than the baseline), no row collisions
and the same single excerpt-boundary skip. The original nonempty percussion
cells, all pitched-channel cells, the full MOD header and every sample byte
match the baseline. The module remains 21,314 bytes with 9,990 sample bytes.
Independent libxmp playback accepts the mix/stem and reaches their first loop;
24.2-second previews do not clip (mix peak 0.583; percussion 0.244). Artifacts:
`build/amiga-transcription/varied-drums/{arranged-eight,percussion}.{mod,wav}`
and the editable arrangement/variation report. Licensed outputs remain ignored.

Tests cover anchor/sample/phase preservation, distinct-bar support, rejection of
a one-bar roll and off-grid detections, observed phrase-end priority, one-extra
per bar, non-mutation of input and idempotent regeneration. Existing bar-template
and tracker-structure checks also pass.

```sh
python3 tools/amiga/test_percussion_variations.py
python3 tools/amiga/vary_percussion.py --arrangement build/amiga-transcription/regular-drums/arrangement.json --out build/amiga-transcription/varied-drums
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/eight-master/notes.json --arrangement build/amiga-transcription/varied-drums/arrangement.json --out build/amiga-transcription/varied-drums
python3 tools/amiga/render_tracker.py build/amiga-transcription/varied-drums/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/varied-drums/arranged-eight.wav
```

Next: compare the sparse additions to the steady baseline and source, retaining
only musically justified variations. Vibrato repair, simultaneous percussion
and three/four-channel reduction remain deferred.

### Recover short-note candidates without changing the accepted drums

User audition finds the sparse drum variations an improvement, with dropped
notes, percussion changes and missing percussion still needing refinement.
This increment targets omitted short attacks; the accepted drum arrangement
and all 351 accepted note events/roles are retained.

`tools/amiga/recover_short_notes.py` reruns Basic Pitch at a 60 ms minimum
instead of the original approximately 128 ms minimum. Of 570 candidates,
483 overlap an accepted/previously added pitch. Additions require confidence
at least 0.4, onset probability at least 0.5, duration 50–128 ms and mean CQT
pitch strength at least 1.25 times either neighboring semitone. Overlapping
adjacent pitches remain excluded as possible vibrato ambiguity. Quantized
occupancy must leave room among seven pitched voices; percussion retains its
own channel. Source and accepted-note hashes are checked before processing.

Eighteen short-note candidates pass; 54 fail note/attack evidence, 14 fail
isolated pitch support and one has adjacent-pitch ambiguity. This is an
editable audition candidate, not confirmation that every added note is right.
No vibrato effects, sustained-gap merging or section-specific drum repair are
implemented here. Original notes are preserved exactly as the output prefix.

The exported eight-channel module starts all 369 notes, retaining the existing
single omitted-note row and 61 drum hits. Drum cells, complete header and sample
bytes match the accepted variation mix exactly. Independent libxmp rendering
produces 24.2-second mix and bass/lead/harmony previews without clipping (mix
peak 0.583). Module size remains 21,314 bytes; this is an editing master, not
four-channel hardware replay input. Outputs are ignored licensed derivatives:
`build/amiga-transcription/note-recovery/{arranged-eight,bass,lead,harmony}.{mod,wav}`,
`notes.json`, editable `arrangement.json` and `recovery-report.json` with every
candidate's evidence/decision. Model output and candidate notes are also saved.

Regression checks cover duplicate suppression, input preservation, ambiguous
and weak attacks, and voice capacity after tracker-row rounding. Existing
tracker, percussion rhythm and variation checks pass. Integrated comparison
checks preserve accepted notes/roles and every drum cell/sample byte.

```sh
python3 tools/amiga/test_short_note_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_short_notes.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/eight-master/notes.json --arrangement build/amiga-transcription/varied-drums/arrangement.json --out build/amiga-transcription/note-recovery
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/note-recovery/notes.json --arrangement build/amiga-transcription/note-recovery/arrangement.json --out build/amiga-transcription/note-recovery
python3 tools/amiga/render_tracker.py build/amiga-transcription/note-recovery/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/note-recovery/arranged-eight.wav
```

Next: audition the short-note additions against the accepted mix/source, then
investigate percussion changes by section and missed hits/instruments. Vibrato
repair and three/four-channel reduction remain subsequent work.

### Restore a recurring percussion position within the later section

User audition confirms the 18 short-note additions are an improvement. Keep
that 369-note arrangement as the working baseline. The next percussion pass
preserves those notes, the accepted groove, sparse pickups, phase and samples.

`tools/amiga/section_percussion.py` examines the existing source observations
for positions recurring in at least four distinct bars with at least 75%
coverage between the first and last observed bars. Alignment must be within
30% of a sixteenth-note slot. It restores only observed hits, adds at most one
per bar and preserves every existing event. Late-bar material stays under the
prior phrase/pickup rules. Saved base hits make regeneration idempotent.

For Positive Force, one position qualifies: snare slot 9, observed in all six
bars 8–13. Restore it at 14.676, 16.390, 18.104, 19.818, 21.532 and 23.246
seconds. Source observations differ from these grid times by at most 3.82 ms.
This is the sixteenth immediately after beat 3, producing a repeating later
section change rather than assuming the same pattern throughout the excerpt.
The source detector's snare identity remains uncertain; audition this addition
before treating the rhythm as confirmed. No hats/new instruments, unsupported
hits, missing-bar interpolation or late-bar fills are introduced.

The new module contains 67 placed drum hits, zero collisions and the existing
single excerpt-boundary skip. All pitched-channel cells, every existing drum
cell, the entire MOD header and all sample bytes match the improved baseline.
Only six previously empty percussion cells change. All 369 note starts remain;
file/sample sizes stay 21,314/9,990 bytes. Independent libxmp mix and percussion
renders reach the first loop and produce 24.2-second previews without clipping
(peaks 0.583/0.244). This remains an eight-channel editing master.

Artifacts: `build/amiga-transcription/section-drums/{arranged-eight,percussion}.{mod,wav}`
and editable `arrangement.json` containing support, section bounds and added-hit
metadata. Original/derived licensed audio remain ignored and uncommitted.
Tests cover preservation, idempotence, distinct-bar support, sparse/roll rejection,
absence of interpolation, late-fill exclusion and existing-event collisions.
Existing tracker, rhythm, variation and short-note checks also pass.

```sh
python3 tools/amiga/test_section_percussion.py
python3 tools/amiga/section_percussion.py --arrangement build/amiga-transcription/note-recovery/arrangement.json --out build/amiga-transcription/section-drums
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/note-recovery/notes.json --arrangement build/amiga-transcription/section-drums/arrangement.json --out build/amiga-transcription/section-drums
python3 tools/amiga/render_tracker.py build/amiga-transcription/section-drums/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/section-drums/arranged-eight.wav
```

Next: audition the recurring offbeat snare, then improve source percussion
recognition for missing hits/instruments rather than filling unsupported gaps.
Vibrato and three/four-channel reduction remain later work.

### Recover masked percussion attacks at established positions

User audition finds the section-specific version more accurate, with missing
percussion and dropped notes still present. Keep it as the working baseline.
This increment revisits the existing 166 source attack candidates, addressing
classification misses rather than changing the melody or inventing new onsets.

`tools/amiga/recover_percussion.py` classifies the transient signal after the
existing HPSS/low-frequency-novelty suppression. That signal extraction is now
a shared helper in `recognize_percussion.py`; the original detector behavior
is retained. Noise-like residuals alone are unsafe: a sustained pure tone can
become a false snare after masking. A full-mix spectral peak-concentration veto
(>=0.6) in `classify_masked` excludes that case. Disagreement with a positive
full-mix drum classification also prevents restoration.

Restoration requires the same accepted instrument and grid position in at
least four distinct accepted bars, agreement within 30% of a sixteenth-note
slot, an empty position and at most one recovered hit per bar. Only observed
attacks are restored; no missing-bar interpolation or new samples are added.
Input recording hashes must match both the arrangement and candidate file.
Review metadata retains raw/residual metrics, classifications and decisions;
saved base hits make regeneration idempotent.

Four attacks qualify: offbeat kicks at 7.499 and 9.213 seconds (slot 6, bars
4–5) and snares at 11.248 and 12.962 seconds (slot 9, bars 6–7). These extend
positions already supported in the accepted later rhythm. The full-mix tonal
concentration veto retains all four. Their musical identity still needs
subjective audition; residual classification is evidence, not ground truth.

The export places 71 drum hits with zero collisions and the existing single
boundary skip. All 369 note starts remain. Every pitched cell, existing drum
cell, full MOD header and sample byte matches the accepted section version;
only four previously empty percussion cells change. Sizes remain 21,314 bytes
for the MOD and 9,990 sample bytes. Independent libxmp mix/percussion playback
reaches its first loop and produces 24.2-second previews without clipping
(peaks 0.583/0.244). Outputs remain ignored licensed derivatives at
`build/amiga-transcription/recovered-drums/{arranged-eight,percussion}.{mod,wav}`
and the editable `arrangement.json`.

Regression tests cover preservation, idempotence, distinct accepted-bar support,
existing-event collisions, new-position/instrument rejection, classification
conflicts and off-grid rejection. Acoustic tests now check rejection of pure
tone/chord attacks after masking as well as in the full mix. Existing synthetic
kick/snare/hat recognition, reconstruction, tracker, rhythm, section, variation
and short-note checks pass.

```sh
python3 tools/amiga/test_percussion_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/test_drum_reconstruction.py
build/amiga-transcription-env/bin/python tools/amiga/recover_percussion.py build/amiga-transcription/positive-force-excerpt.wav --arrangement build/amiga-transcription/section-drums/arrangement.json --candidates build/amiga-transcription/drum-refinement/arrangement.json --out build/amiga-transcription/recovered-drums
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/note-recovery/notes.json --arrangement build/amiga-transcription/recovered-drums/arrangement.json --out build/amiga-transcription/recovered-drums
python3 tools/amiga/render_tracker.py build/amiga-transcription/recovered-drums/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/recovered-drums/arranged-eight.wav
```

Next: audition these restored attacks, inspect sustained/vibrato-related note
gaps, and investigate percussion events absent from the candidate timestamps.
New percussion identities and three/four-channel reduction remain later work.

### Audition supported short same-pitch release gaps

Continue from the accepted section improvements and latest masked-percussion
candidate. Remaining dropped-note feedback motivates checking gaps between
same-pitch notes, while retaining every recognized attack and the drum pattern.

`tools/amiga/recover_note_gaps.py` compares adjacent same-pitch events with
fresh Basic Pitch frame/onset/contour evidence and source CQT strength. A gap
must be 20–200 ms, with mean/minimum note probabilities >=0.2/0.12, mean/minimum
contour probabilities >=0.18/0.14 within one third of a semitone, and mean source
pitch strength >=1.4 times either neighboring semitone. An internal onset >=0.5
blocks extension; 25 ms around each edge is excluded from that onset check so
the preserved following attack does not count as an internal attack. Extensions
must change at least one tracker row and leave room among seven pitched voices.

Five of 22 gaps pass; 15 fail continuous model evidence and two fail isolated
source pitch evidence. Their original release times are 7.016, 10.525, 10.908,
17.483 and 17.937 seconds, with extensions of approximately 197, 186, 128, 93
and 58 ms. The previous note is extended to the next same-pitch attack; that
following event remains separate and is retriggered normally. All start times,
pitches, strengths, roles and event ordering are retained. This is an audition
of release extensions, not confirmation of intended legato articulation or a
transcription of vibrato effects. There are no newly inferred pitches/attacks.

The MOD retains all 369 note starts, the original single omitted-note row and
71 percussion hits. Every pitched attack cell remains on its original tracker
row (lanes may change); every percussion cell, header and sample byte matches
the latest percussion baseline. Sizes remain 21,314/9,990 bytes. Independent
libxmp mix and bass/lead/harmony renders reach the first loop, last 24.2 seconds
and do not clip (mix peak 0.583). Ignored licensed audition artifacts:
`build/amiga-transcription/note-gaps/{arranged-eight,bass,lead,harmony}.{mod,wav}`,
`notes.json`, model output and `arrangement.json` with gap evidence/review.

Tests cover attack/input preservation, conservative release changes, silence,
pitch changes, internal attacks, tracker quantization and voice capacity.
Existing tracker, short-note, section and percussion-recovery checks pass.

```sh
python3 tools/amiga/test_note_gap_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_note_gaps.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/note-recovery/notes.json --arrangement build/amiga-transcription/recovered-drums/arrangement.json --out build/amiga-transcription/note-gaps
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/note-gaps/notes.json --arrangement build/amiga-transcription/note-gaps/arrangement.json --out build/amiga-transcription/note-gaps
python3 tools/amiga/render_tracker.py build/amiga-transcription/note-gaps/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/note-gaps/arranged-eight.wav
```

Next: audition articulation around the five extensions, then investigate fully
missing pitch events and percussion onsets absent from the existing candidates.
Actual vibrato effects and three/four-channel reduction remain later work.

### Sensitive fast-note recheck with accepted-run support

User audition confirms fewer dropped notes after release-gap recovery, while
vibrato, arpeggios and accurate percussion remain missing. Keep the note-gap
version as the accepted baseline. This increment checks for omitted fast pitched
attacks without changing its note lengths or percussion.

`tools/amiga/recover_fast_notes.py` reruns recognition with a 35 ms minimum,
onset threshold 0.4 and frame threshold 0.25 (previous short-note pass used
60 ms and the default 0.5/0.3 thresholds). Of 852 events, 189 do not overlap
an accepted same-pitch event. Additions require duration 35–128 ms, confidence
>=0.3, attack probability >=0.45, mean contour support >=0.18 and source CQT
pitch strength >=1.4 times either adjacent semitone. Adjacent-pitch overlap is
excluded as ambiguous. Quantized occupancy must preserve seven pitched voices.

Fast-run context must come from two accepted attacks bracketing the candidate,
with distinct pitches 2–12 semitones away, attack spacing 25–220 ms, durations
35–250 ms, overlap <=25 ms and combined span <=320 ms. New candidates cannot
provide support for each other; a simultaneous chord cannot establish a run.
All accepted notes, lengths, roles and percussion are retained.

Only one candidate passes: MIDI 73 (C#5) at 12.872–12.976 seconds. This is a
small audition candidate, not recovery of the full missing arpeggio. Decisions
for the remaining candidates: 57 weak isolated source pitches, 96 weak pitched
attacks, 23 outside fast-note duration scope, two adjacent-pitch ambiguities and
ten lacking accepted surrounding fast-run support. The remaining 663 events
are already covered by an accepted pitch. All measurements/decisions are saved
in `arrangement.json`; more sensitive inference alone is insufficient evidence
to add the remaining events.

The MOD starts all 370 notes with the same single omitted-note row and 71 drum
hits. Original 369 events/roles, every drum cell, the MOD header and all sample
bytes are preserved. Sizes remain 21,314/9,990 bytes. Independent libxmp mix
and lead playback reaches the first loop and produces 24.2-second previews
without clipping (peaks 0.583/0.338). Artifacts remain ignored licensed outputs:
`build/amiga-transcription/fast-notes/{arranged-eight,lead}.{mod,wav}`,
`notes.json`, model output and editable `arrangement.json`.

Tests cover accepted-context/input preservation, duplicate suppression, rejection
of chords and self-supporting candidate runs, weak pitch/attack evidence,
adjacent-pitch ambiguity and voice capacity. Existing tracker, short-note and
gap-recovery checks pass. Original 92 BPM tracker-row timing is retained; this
pass does not recover sub-row arpeggio timing or MOD 0xy/4xy effects.

```sh
python3 tools/amiga/test_fast_note_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_fast_notes.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/note-gaps/notes.json --arrangement build/amiga-transcription/note-gaps/arrangement.json --out build/amiga-transcription/fast-notes
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/fast-notes/notes.json --arrangement build/amiga-transcription/fast-notes/arrangement.json --out build/amiga-transcription/fast-notes
python3 tools/amiga/render_tracker.py build/amiga-transcription/fast-notes/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/fast-notes/arranged-eight.wav
```

Next: audition the single added attack; investigate pitch contours for vibrato
and source-supported rapid pitch changes that event recognition still misses.
Accurate percussion and three/four-channel reduction remain pending.

### First coherent source-vibrato audition, with calibrated MOD effects

Continue from the accepted note-gap improvement and the single fast-note
candidate. Inspect sustained source notes for sinusoidal pitch modulation.
`tools/amiga/detect_vibrato.py` fits interpolated spectral peak pitch within
+/-60 cents of each expected fundamental and its second harmonic. Use 2048-point
STFT windows at 22,050 Hz, 128-sample hops, and exclude 45 ms at both note edges.
Fit constant/drift plus 3–10 Hz sine/cosine components to notes >=400 ms and
MIDI >=60. Periodic score is measured against a linear-drift baseline.

Both harmonics must score >=0.75, agree within 0.3 Hz and 0.4 radians, have
compatible depths (ratio 0.6–1.6), fundamental depth 5–35 cents, drift <=30
cents/second and at least 2.5 observed cycles. This rejects pitch drift and many
polyphonic/interference fits. Two notes qualify: C#5 at 9.096 seconds and E5
at 11.349 seconds. Their estimated source rates are 7.8/7.85 Hz and depths
7.67/9.72 cents. A third initially promising note lacks sufficient final evidence.

Standard MOD vibrato on the old 92 BPM/speed-3 tick clock cannot reach the
source rate: independent playback measures approximately 5.8 Hz at maximum
speed 15. The exporter now optionally doubles transport tempo and speed to
184 BPM/speed 6. Row duration and original 92 BPM editing grid remain exactly
the same. Accepted drum EDx delay values are doubled, preserving their original
rounded onset times rather than re-quantizing the percussion. Default export
behavior remains at the original clock when this option is absent.

The detector independently renders candidate effects using local libxmp and
chooses speed/depth against measured playback. Each source candidate becomes
482 (speed 8, depth 2): measured rate 7.65 Hz, depths 10.41/12.29 cents, periodic
scores >0.97. Calibration must score >=0.6, stay within 0.5 Hz and have depth
ratio 0.5–1.5 relative to source. Source fits, calibration WAV/MOD/render reports,
chosen effects and calibration-library SHA remain reviewable under ignored build
outputs. Depth is coarse and the spectral window attenuates modulation; phase
is not source-aligned. Effects start on held rows after the original attack,
so onset volume commands and every attack remain intact. Note releases stop
modulation normally. This is a two-note audition, not complete vibrato recovery.

`working_module` accepts per-note vibrato metadata and the optional doubled
clock; `arrange_tracker.py` retains these effects in pitched stems. The module
adds 482 to eight previously empty held-note cells. Original notes/roles, all
370 attacks, 71 drum hits, header and sample data are retained; only transport
commands and EDx delay values change alongside vibrato effects. File/sample
sizes remain 21,314/9,990 bytes. Independent mix/lead/percussion playback reaches
the first loop, lasts 24.2 seconds and does not clip (mix peak 0.625). Player
waveforms may differ with the finer tick clock; a controlled impulse test
confirms old ED2/new ED4 onsets agree within one sample (both 54.4375 ms here).

Artifacts: `build/amiga-transcription/vibrato/{arranged-eight,lead,percussion}.{mod,wav}`
and editable `arrangement.json`. Licensed assets remain ignored. Tests cover
periodic harmonic agreement, drift/rate mismatch rejection, preservation of
attacks/releases/sample bytes, effect/clock validation and doubled-delay timing.
Existing tracker, rhythm and independent pitch/delay/loop checks pass.

```sh
build/amiga-transcription-env/bin/python tools/amiga/test_vibrato.py
build/amiga-transcription-env/bin/python tools/amiga/test_tracker_render.py --library build/amiga-libxmp/build/libxmp.dylib
build/amiga-transcription-env/bin/python tools/amiga/detect_vibrato.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/fast-notes/notes.json --arrangement build/amiga-transcription/fast-notes/arrangement.json --out build/amiga-transcription/vibrato --library build/amiga-libxmp/build/libxmp.dylib
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/fast-notes/notes.json --arrangement build/amiga-transcription/vibrato/arrangement.json --out build/amiga-transcription/vibrato
python3 tools/amiga/render_tracker.py build/amiga-transcription/vibrato/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/vibrato/arranged-eight.wav
```

Next: audition modulation phase/depth at the two notes, then refine contour
tracking for shorter notes and fast arpeggios. Percussion accuracy and native
three/four-channel replay integration remain pending.

### Trace export losses and recover phrase-supported omitted notes

User still hears dropped notes after the initial vibrato pass. Distinguish
recognition omissions from tracker allocation losses before changing timing.
`working_module` now reports `unstarted_note_indices` and `delayed_attacks`
with event indices and planned/actual rows. Tests distinguish a completely
lost short note under overload from a held note that receives a late attack.

The current baseline starts every recognized event. Its existing one-row
omission is a delayed MIDI-68 attack at source time 22.282 seconds: eight
pitched events briefly overlap, while percussion reserves channel 7. Event 24
starts on row 274 instead of row 273. This is an actual eight-pitch overlap in
the source event list, not merely an artifact of rounding. It remains unchanged;
removing that overload requires a separate voice-sharing/chord-sample decision.

The sensitive recognition pass had excluded useful candidates because they
lacked accepted fast-run neighbors. `recover_fast_notes.py` now also supports
`--context recurring-phrase`: same source attack/contour/CQT gates, accepted
same-pitch repetitions at an assumed two-bar interval, alignment within 35 ms,
and at least two distinct accepted repetition cycles (up to six cycles away).
Accepted supporting notes must have confidence >=0.3. Duration scope is
35–350 ms; duplicate/adjacent-pitch/capacity protections remain. New candidates
cannot support one another. Phrase matching is additional evidence, not an
instruction to fill all repeated positions. Only actual observed attacks are
added; phrase length and candidate identity still need audition.

Five candidates pass: E4 at 8.562 and 12.454 seconds, D4 at 17.042, F#4 at
22.166 and F#3 at 23.780. The earlier fast-note addition remains intact. Saved
vibrato metadata is extended with empty entries for new notes, retaining the
two existing effects and doubled tick clock. Previous fast-note provenance is
retained; the new review is stored separately as `phrase_note_recovery`.

The module starts all 375 notes with no unstarted events, the same single late
attack, eight vibrato rows and 71 drum hits. Original 370 events/roles/effects,
every original pitched attack cell on its original row, all drum cells, header
and sample bytes are preserved. File/sample sizes remain 21,314/9,990 bytes.
Independent libxmp mix and bass/lead/harmony playback reaches the first loop,
lasts 24.2 seconds and does not clip (mix peak 0.625). Licensed outputs remain
ignored at `build/amiga-transcription/recurring-notes/{arranged-eight,bass,lead,harmony}.{mod,wav}`,
with `notes.json`, source model outputs and editable `arrangement.json`.

Tests cover distinct accepted phrase support, duplicate-cycle rejection and
phase mismatch, alongside existing fast-note safeguards. New export audit tests
cover complete losses versus late attacks; tracker, gap, vibrato and percussion
recovery tests pass. This does not establish complete source-note coverage.

```sh
python3 tools/amiga/test_note_export_audit.py
python3 tools/amiga/test_fast_note_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_fast_notes.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/fast-notes/notes.json --arrangement build/amiga-transcription/vibrato/arrangement.json --out build/amiga-transcription/recurring-notes --context recurring-phrase
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/recurring-notes/notes.json --arrangement build/amiga-transcription/recurring-notes/arrangement.json --out build/amiga-transcription/recurring-notes
python3 tools/amiga/render_tracker.py build/amiga-transcription/recurring-notes/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/recurring-notes/arranged-eight.wav
```

Next: audition the five recovered attacks; localize remaining recognition gaps,
then refine rapid pitch changes, vibrato coverage and percussion. The known
eight-pitch overlap and native three/four-channel reduction remain pending.

### Restore same-pitch attacks hidden inside held recognition events

Continue investigating remaining dropped attacks. Earlier recovery stages
reject any candidate overlapping an accepted same pitch; that protection also
hides genuine repeated attacks inside notes the first recognizer merged.

`tools/amiga/retrigger_notes.py` examines model onset peaks within accepted
held events. Peaks must have prominence >=0.15, onset probability >=0.7 and
note probability >=0.3. Source CQT strength must rise at least 2x at the
fundamental and 1.5x at the second harmonic, comparing 45–10 ms before the
candidate with 0–40 ms afterward. Fundamental strength after the attack must
also exceed either adjacent semitone by 1.3x. These source gates reject many
model-only peaks and isolated harmonic/noise changes.

Require at least 70 ms from the event edges and between restored attacks,
distinct interior tracker rows and no existing same-pitch attack within 40 ms.
Already annotated vibrato notes are excluded to preserve their articulation.
Split qualifying held events into contiguous same-pitch segments, keeping the
original attack, final release, pitch, gain and role. Additional tail segments
inherit their parent's role and receive no new vibrato. Quantized per-pitch
coverage and simultaneous voice occupancy remain exactly unchanged; this pass
adds retriggers rather than new concurrent voices or new pitches.

Twenty-five attacks qualify. Of 185 reviewed internal peaks, 121 fail model
attack evidence, 38 fail isolated harmonic rises and one is excluded to preserve
vibrato. The exported module starts all 400 events, retaining the same single
late attack at row 273/274, eight vibrato-effect rows and 71 drum hits. Every
original pitched attack cell remains on its original row. Complete drum cells,
MOD header and all sample bytes match the previous version; final per-pitch
coverage matches at every quantized row. File/sample sizes remain 21,314/9,990
bytes. Independent libxmp mix and bass/lead/harmony renders reach the first loop,
last 24.2 seconds and do not clip (mix peak 0.625). The mix waveform changes
(RMS difference 0.0198), confirming the retriggers affect playback. Their
musical articulation still needs audition; these gates do not establish exact
source note identity or intended envelopes.

Ignored licensed artifacts:
`build/amiga-transcription/retriggered-notes/{arranged-eight,bass,lead,harmony}.{mod,wav}`,
`notes.json`, model outputs and editable `arrangement.json` with peak decisions
and tail-to-parent event indices. Tests cover original attack/pitch/gain/release
and input preservation, exact quantized coverage, complete playback allocation,
weak/model-only/single-harmonic attacks, vibrato exclusion, duplicate rows,
close/edge attacks and repeated-selection stability. Existing tracker, vibrato
and note-export audit tests pass.

```sh
python3 tools/amiga/test_note_retriggers.py
build/amiga-transcription-env/bin/python tools/amiga/retrigger_notes.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/recurring-notes/notes.json --arrangement build/amiga-transcription/recurring-notes/arrangement.json --out build/amiga-transcription/retriggered-notes
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/retriggered-notes/notes.json --arrangement build/amiga-transcription/retriggered-notes/arrangement.json --out build/amiga-transcription/retriggered-notes
python3 tools/amiga/render_tracker.py build/amiga-transcription/retriggered-notes/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/retriggered-notes/arranged-eight.wav
```

Next: audition repeated-note articulation, then investigate residual missing
pitches, more vibrato coverage and inaccurate/missing percussion. The known
eight-pitch overlap and native three/four-channel reduction remain pending.

### Recover quieter missing notes using independent source harmonic attacks

User audition finds the repeated-note recovery good, with some notes still
missing. Continue from that 400-event baseline, preserving articulation,
vibrato and percussion. Earlier context rules excluded isolated attacks and
the confidence cutoff excluded quieter candidates despite strong source rises.

`recover_fast_notes.py --context source-harmonics` requires onset probability
>=0.7, mean contour support >=0.18 and source pitch strength >=1.4 times either
adjacent semitone. A 128-sample-hop CQT independently measures rises at the
fundamental and second harmonic: >=2x/1.5x between 45–10 ms before the candidate
and 0–40 ms afterward. With those source gates, mean recognition confidence
may be >=0.22 rather than >=0.3. Durations stay within 35–350 ms; accepted-pitch
coverage, adjacent-pitch ambiguity and seven-pitched-voice capacity guards remain.
No run/phrase is inferred or used to fabricate an unobserved attack.

Reject candidate pitches 12, 19 or 24 semitones above an accepted lower attack
starting within 40 ms. This flags possible second/third/fourth harmonics that
otherwise satisfy the same source-rise checks; it does not establish that every
such candidate is an overtone. Three otherwise qualifying candidates are
excluded on that ambiguity, including proposed octave notes at 1.718/2.672 s.

Seven candidates pass: A3 at 4.066, G#3 at 6.854, D#4 at 7.492, B3 at 9.212,
F#4 at 10.177, C#4 at 12.964 and F#4 at 17.042 seconds. Four are below the
previous 0.3 confidence cutoff; three lacked accepted fast-run/phrase support.
All have observed model attacks and source harmonic rises. Existing provenance
is retained, with the new evidence and decisions in `source_note_recovery`.
These are additions to audition, not confirmation of complete note coverage.

The export starts all 407 events, with no unstarted notes and exactly the same
single delayed attack at row 273/274. All original 400 events/roles/vibrato
annotations remain; every prior pitched attack cell stays on its original row.
Drum cells, full MOD header and sample bytes match the baseline exactly. Eight
vibrato rows and 71 drum hits remain. Sizes stay 21,314/9,990 bytes. Independent
libxmp mix and bass/lead/harmony renders reach the first loop, last 24.2 seconds
and do not clip (mix peak 0.625). Licensed assets remain ignored at
`build/amiga-transcription/source-supported-notes/{arranged-eight,bass,lead,harmony}.{mod,wav}`,
with `notes.json`, model output and editable `arrangement.json`.

Tests cover quiet-source support without phrase context, rejection of weak
onsets/single-harmonic rises and simultaneous lower-note overtone ambiguity,
alongside existing duplicate/neighbor/capacity guards. Tracker, retrigger,
vibrato, note-export audit and percussion-recovery tests also pass.

```sh
python3 tools/amiga/test_fast_note_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_fast_notes.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/retriggered-notes/notes.json --arrangement build/amiga-transcription/retriggered-notes/arrangement.json --out build/amiga-transcription/source-supported-notes --context source-harmonics
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/source-supported-notes/notes.json --arrangement build/amiga-transcription/source-supported-notes/arrangement.json --out build/amiga-transcription/source-supported-notes
python3 tools/amiga/render_tracker.py build/amiga-transcription/source-supported-notes/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/source-supported-notes/arranged-eight.wav
```

Next: audition these quieter/isolated attacks, then localize remaining missing
pitch evidence and refine vibrato/arpeggio coverage and percussion accuracy.
The known eight-pitch overlap and three/four-channel reduction remain pending.

### Lower-frame sensitivity check; prevent quantized same-pitch doubling

Continue from the 407-event candidate. Check whether the frame threshold still
prevents quiet notes from appearing at all. `recover_fast_notes.py` now exposes
`--frame-threshold` (default 0.25) and records inference thresholds in the review.
Source attack/contour/harmonic gates remain unchanged when sensitivity changes.

A 0.20 frame threshold produces 991 candidates rather than 852. It yields no
justified distinct addition under the source gates. A particularly strong MIDI
54 fragment at approximately 10.072–10.119 seconds precedes an accepted MIDI
54 note starting at 10.119. Both attacks round onto the same row of the current
editing grid. Adding the fragment as an independent voice would double that
pitch rather than restore a separately timed attack. Other source-rising high
candidates coincide with possible harmonics of accepted lower attacks.

Both fast-note and short-note selection now reject a same-pitch collision after
tracker quantization, even where the original continuous-time intervals do not
overlap. This complements the existing source-time duplicate check and avoids
minimum-one-row fragments consuming an extra voice/doubling the same pitch.
The accepted 407-event baseline itself has no quantized same-pitch overlaps.

Lower-threshold review decisions: 685 already covered, seven quantized pitch
collisions, 32 weak isolated pitches, 250 weak attack/contour/confidence cases,
four outside duration scope, six weak harmonic attacks, six possible lower-note
overtone ambiguities and one adjacent-pitch ambiguity. `notes.json` remains
identical to the baseline, and re-exported MOD bytes match the independently
verified baseline exactly. No new audio preview replaces it. Diagnostic model
output and editable review are ignored licensed derivatives at
`build/amiga-transcription/lower-frame-recheck/`.

Regression tests cover source-disjoint fragments that collide after rounding
in both selection paths. Existing fast/short-note, tracker and export-audit
checks pass. This increment improves rejection/audit rather than claiming
additional recovered notes. Remaining omissions need independent source pitch
tracking/localized comparison; lowering this threshold alone is insufficient.
The user subsequently identified lead omissions near 3, 5, 9, 10, 12 and
18 seconds; those locations now guide the next source comparison.

```sh
python3 tools/amiga/test_fast_note_recovery.py
python3 tools/amiga/test_short_note_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_fast_notes.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/source-supported-notes/notes.json --arrangement build/amiga-transcription/source-supported-notes/arrangement.json --out build/amiga-transcription/lower-frame-recheck --context source-harmonics --frame-threshold .2
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/lower-frame-recheck/notes.json --arrangement build/amiga-transcription/lower-frame-recheck/arrangement.json --out build/amiga-transcription/lower-frame-recheck
```

Next: compare specific source phrases and spectral pitch trajectories for
missing attacks/pitches; preserve the last audible improvement as the baseline.
Vibrato coverage, percussion accuracy, the brief overload and native voice
reduction remain unresolved.


### Finer-row timing audition and localized lead-gap review

Keep the 407-event arrangement as the accepted baseline. Export a separate
comparison at editing BPM 184, speed 3, rather than BPM 92, speed 6.
`compare_tracker_timing.py` preserves the baseline drum tick times and
independently recalibrates existing vibrato for this replay clock. The note list,
roles, instrument samples and accepted percussion hits remain the same.
Vibrato calibration now renders both neighboring depth choices and selects the
closest measured depth, instead of assuming depth scales linearly.

The comparison starts all 407 events and places all 71 accepted drum hits,
with no drum row collisions and one excerpt-boundary skip. Quantization onset
RMS improves from 22.831 ms to 12.591 ms. Including actual allocation delays,
the comparison measures 12.818 ms RMS and 49.218 ms maximum onset error.
One attack still waits a row near 22.28 seconds: the finer row is 40.761 ms,
rather than 81.522 ms. This does not eliminate the underlying voice overload.
Both existing vibrato annotations calibrate to effect 4A2; measured rate is
7.65 Hz and depths are 12.895 and 10.947 cents. Source vibrato phase remains
approximate. Independent libxmp rendering reaches the first loop in 24.2 s,
with peak 0.57309 and no clipping. MOD SHA-256:
`e52f2538f1dd1c46ceb006f67c5c6aae91fc2f2e9b9261edf013387349e76488`.

Tests cover preserved drum tick placement under the finer row clock, unchanged
input arrangement, invalid clock assumptions, and onset metrics that include
allocation delays. Independent replay checks verify equivalent delayed drum
attacks to within one sample. Recognition, export, vibrato and replay tests pass.
The comparison is an audition candidate, not a replacement for the accepted
original timing grid, and does not recover any additional notes.

The user reports missing lead notes near 3, 5, 9, 10, 12 and 18 seconds.
Localized lower-threshold review finds potential upper-pitch attacks near
4.914 s (MIDI 78), 10.281 s (78), 11.895 s (78), and 18.204 s (71).
These remain unaccepted: confidence, harmonic attack evidence or simultaneous
lower-note overtone ambiguity fails the current gates. At 9 s the narrow
window contains no uncovered strong lead candidate. Simply lowering model
thresholds is insufficient. No channel omission explains these reported gaps.
Further work should trace the lead instrument through these windows, including
possible lower-register lead notes, rather than assume every high harmonic is
a separate note.

Private 1.2-second source, baseline, finer mix and finer lead clips centered on
all six reported times are in `build/amiga-transcription/lead-gap-comparison/`.
The full comparison is `build/amiga-transcription/finer-timing/arranged-eight.wav`.
These licensed derivatives remain ignored and uncommitted.

```sh
build/amiga-transcription-env/bin/python tools/amiga/compare_tracker_timing.py --arrangement build/amiga-transcription/source-supported-notes/arrangement.json --out build/amiga-transcription/finer-timing --library build/amiga-libxmp/build/libxmp.dylib
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/source-supported-notes/notes.json --arrangement build/amiga-transcription/finer-timing/arrangement.json --out build/amiga-transcription/finer-timing --bpm 184
python3 tools/amiga/render_tracker.py build/amiga-transcription/finer-timing/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/finer-timing/arranged-eight.wav
python3 tools/amiga/test_tracker_timing_comparison.py
```


### Localized lead attack recovery at reported gaps

Continue from the 407-event baseline using the user's reported lead omissions
near 3, 5, 9, 10, 12 and 18 seconds. `recover_local_lead.py` reads the existing
lower-frame candidate review, checks its source/baseline hashes, and limits
source analysis to candidate attacks within 0.6 seconds of those locations.
Timestamps select review windows, not invented pitches or onset positions.

The earlier one-bin-per-semitone CQT can smear a short attack into neighboring
pitches and weaken its harmonic evidence. The local pass uses three bins per
semitone with a +/- one-bin band and tests the second and third harmonics.
Each accepted attack requires model confidence >=0.3, onset >=0.5, contour
>=0.18, fundamental attack rise/isolation >=2, and at least one upper harmonic
with rise/isolation >=2. Interpolated STFT pitch traces must remain within
40 cents for 90% of frames, span no more than 40 cents, and agree between
fundamental/upper harmonic median pitch within 20 cents. These stable-pitch
checks help reject adjacent-pitch leakage and slides. They do not establish
instrument identity or detect new vibrato.

Three source-supported changes form an audition candidate:

- Advance existing MIDI 76 event 294 from 3.252078 to 3.205638 seconds by
  joining its immediately preceding same-pitch candidate fragment. Its end,
  confidence, role and effects stay intact. The fragment fundamental rise is
  2.883, isolation 4.716; third harmonic rise 2.137, isolation 2.274. This moves
  an existing attack rather than allocating a second same-pitch voice.
- Add MIDI 75 at 4.495629-4.542069 seconds (confidence 0.347). Fundamental
  rise/isolation 9.542/6.242 and second harmonic 19.053/5.352 support this short
  attack. Coarse isolation had previously rejected it.
- Add MIDI 74 at 9.583367-9.641417 seconds (confidence 0.401). Fundamental
  rise/isolation 2.248/5.069 and third harmonic 3.815/4.479 support this short
  transition. The earlier second-harmonic-only check was insufficient.

For new pitches, retain the simultaneous lower-note overtone veto, same-pitch
source/quantized duplicate guards, adjacent-pitch ambiguity check, and seven
pitched-voice capacity limit. A contiguous fragment may advance an already
accepted pitch despite a coincident lower attack, because it adds no upper
voice and must independently satisfy the stable fundamental/harmonic gates.
The new test suite covers that distinction, unstable/weak harmonic evidence,
new overtone rejection, voice capacity, duplicates and input preservation.

No accepted notes are removed. The result has 409 events, all started. The
known delayed attack near 22.28 seconds remains the only allocation delay;
there is no added overload. Use the original 92 editing grid (replay BPM 184,
speed 6), leaving the finer-grid experiment separate. All 71 drum placements,
instrument samples, existing roles and eight vibrato-effect rows are unchanged.
The one excerpt-boundary percussion skip remains. Independent libxmp mix and
lead rendering reach the first loop in 24.2 seconds; peaks are 0.62454 and
0.40106, respectively, with no clipping. MOD is 21,314 bytes / 9,990 sample
bytes, SHA-256
`a7dcf5ab03bcbd36251df458f6143dab274577cb4d646f87525c86bc7618cb98`.

The 18.204-second MIDI 71 candidate has two matching accepted phrase
repetitions near 14.788 and 21.654 seconds. It still fails model confidence /
contour and coincides with an accepted lower MIDI 59 attack; recurrence alone
does not remove that ambiguity. Likewise upper MIDI 78 candidates around 5,
10 and 12 seconds are not accepted by this pass. The reported six gaps are
not all resolved, and the three edits need audition for instrument/articulation
accuracy before becoming an accepted baseline.

Ignored licensed derivatives are in
`build/amiga-transcription/local-lead-notes/{arranged-eight,lead}.{mod,wav}`,
with notes and editable arrangement containing per-candidate decisions and
high-resolution source evidence. Matching 1.2-second localized mix/lead clips
are in `build/amiga-transcription/lead-gap-comparison/`. No music assets are
committed. Local recovery, fast/short recovery, tracker and allocation-audit
tests pass, as do metadata preservation and independent replay checks.

```sh
python3 tools/amiga/test_local_lead_recovery.py
build/amiga-transcription-env/bin/python tools/amiga/recover_local_lead.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/source-supported-notes/notes.json --arrangement build/amiga-transcription/source-supported-notes/arrangement.json --candidate-arrangement build/amiga-transcription/lower-frame-recheck/arrangement.json --times 3 5 9 10 12 18 --out build/amiga-transcription/local-lead-notes
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/local-lead-notes/notes.json --arrangement build/amiga-transcription/local-lead-notes/arrangement.json --out build/amiga-transcription/local-lead-notes
python3 tools/amiga/render_tracker.py build/amiga-transcription/local-lead-notes/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/local-lead-notes/arranged-eight.wav
```

Next: audition these localized changes, then distinguish independent lead
energy from simultaneous accompaniment overtones in the unresolved windows.
Do not substitute lowered thresholds or phrase recurrence for that distinction.


### Lower-register lead-role audition; test timbre-induced apparent omissions

Continue from the 409-event localized lead candidate. The remaining upper
candidates frequently coincide with lower notes already present: MIDI 78 is
an octave above 66, MIDI 76 an octave above 64, and MIDI 71 an octave above 59.
At 11.895 s the MIDI 78 candidate instead matches the third harmonic of 59.
Upper/lower frequency traces alone do not establish independent voices.

A different hypothesis deserves audition: the pitch-only role threshold sends
all MIDI pitches below 67 to the soft harmony bank. That bank's synthesized
waveform has a fundamental plus weak third/fifth harmonics and no second
harmonic. It cannot reproduce prominent upper energy in these source windows.
The existing lead pulse bank has a second harmonic. A lower-register note can
therefore be present in the event list while its missing upper harmonics make
it sound unlike the foreground source instrument. This is a role/timbre
hypothesis, not proof that the source contains no independent upper note.

`audition_lead_roles.py` makes a separate comparison by selecting existing
notes with explicit onset/pitch requests, requiring exactly one harmony event
within 35 ms. It rejects duplicate/ambiguous requests, invalid lower-register
pitches, and notes with existing calibrated vibrato (a different instrument
requires fresh calibration). It changes only six supplied roles, copies the
note file byte-for-byte, and records instrument/volume changes and provenance.
The normal lead gain also applies, so this tests both brighter timbre and
foreground level rather than claiming a timbre-only comparison.

Selected events: 391 / MIDI 66 at 4.913588 s; 263 / MIDI 64 at 5.145788 s;
200 / MIDI 66 at 10.292859 s; 179 / MIDI 59 at 11.895036 s; and 90 / MIDI 59
plus 88 / MIDI 66 at 18.204390 s. Tracker attack volumes change respectively
13->30, 13->31, 12->28, 15->36, 11->27 and 16->39. These are existing pitches;
no uncertain octave candidate is added to the score.

`compare_lead_role_harmonics.py` binds its diagnostic to the source, baseline
arrangement, identical note files, independent replay module/library metadata,
and rendered audio hashes. It measures first/second/third CQT harmonic
magnitudes with three bins per semitone and normalizes each profile to its
fundamental. Windows run from source onset +20 ms to the earlier of end -10 ms
or onset +130 ms. Shared harmonics, interference, leakage and quantization can
contaminate these mixed-source ratios; they are not instrument recognition.

Measured second-harmonic ratios (fundamental normalized to 1):

| Source event | Original role | Source | Role audition |
| --- | ---: | ---: | ---: |
| 4.914 s / MIDI 66 | 0.283 | 1.265 | 0.781 |
| 5.146 s / MIDI 64 | 0.014 | 0.731 | 0.511 |
| 10.293 s / MIDI 66 | 0.003 | 0.791 | 0.503 |
| 11.895 s / MIDI 59 | 0.084 | 0.459 | 0.473 |
| 18.204 s / MIDI 59 | 0.022 | 0.441 | 0.507 |
| 18.204 s / MIDI 66 | 0.095 | 0.523 | 0.622 |

Both second- and third-harmonic absolute ratio errors decrease at all six
probes. At 18.204 s / MIDI 59, the third-harmonic ratio improves from 0.113 to
0.734 versus source 0.940 when both MIDI 59 and 66 use the lead bank. This
illustrates shared harmonic energy: the third harmonic of 59 nearly coincides
with the second harmonic of 66. It still does not identify a missing voice.

Verification: all 409 events start, with only the previous delayed attack near
22.28 s. Encoded pitched attack row/period/sample-cycle multisets match the
409-event baseline exactly; sample payload and every percussion channel cell
match. Existing effects, event confidences/timings, all 71 drums and original
92 editing grid (replay 184 / speed 6) stay intact. Independent libxmp mix/lead
renders reach the first loop in 24.2 s, peaks 0.62454 / 0.40106, no clipping.
MOD remains 21,314 bytes with 9,990 sample bytes; SHA-256
`a33b4a621c82ec50bb54dab6d49c48b77fb7675d3ae68b68b5ebd9d413a7196e`.
Tests cover exact role/input preservation, volume audit, explicit-request
ambiguity/vibrato guards, and encoded pitch preservation through export.
Tracker and allocation-audit tests pass. Channel choices may change with the
role assignment; native mono/hard-panned reduction remains later work.

Private preview, lead stem, editable arrangement, identical notes and measured
profiles are ignored under `build/amiga-transcription/lead-role-audition/`.
Localized source/comparison clips remain in `lead-gap-comparison/`. No music
assets are committed. Keep this comparison separate until auditioned; no
claim that the six reported gaps are resolved or that roles are recognized.

```sh
python3 tools/amiga/test_lead_role_audition.py
python3 tools/amiga/audition_lead_roles.py --notes build/amiga-transcription/local-lead-notes/notes.json --arrangement build/amiga-transcription/local-lead-notes/arrangement.json --lead-note 4.914:66 --lead-note 5.146:64 --lead-note 10.293:66 --lead-note 11.895:59 --lead-note 18.204:59 --lead-note 18.204:66 --out build/amiga-transcription/lead-role-audition
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/lead-role-audition/notes.json --arrangement build/amiga-transcription/lead-role-audition/arrangement.json --out build/amiga-transcription/lead-role-audition
python3 tools/amiga/render_tracker.py build/amiga-transcription/lead-role-audition/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/lead-role-audition/arranged-eight.wav
build/amiga-transcription-env/bin/python tools/amiga/compare_lead_role_harmonics.py build/amiga-transcription/positive-force-excerpt.wav --baseline build/amiga-transcription/local-lead-notes --audition build/amiga-transcription/lead-role-audition
```

Next: audition the foreground role comparison at the reported gaps. If it
helps, learn/source-check a consistent instrument assignment across repeated
phrases rather than assuming pitch range determines the role. Continue source
pitch/arpeggio, vibrato, percussion and native reduction work afterward.


### Accepted editing baseline and protected manual-edit handoff

The user considers the latest reconstruction close enough for manual correction.
Treat `lead-role-audition` (409 events, six lower-register role adjustments) as
the working editing baseline and stop automatic recognition refinement for this
excerpt. It is still an approximation, with vibrato/arpeggios, percussion and
individual note corrections remaining. Acceptance for editing is not approval
of native playback or a complete soundtrack conversion.

`prepare_tracker_edit.py` creates a protected handoff under the ignored
`build/amiga-transcription/manual-edit-v1/` directory:

- `positive-force-edit.mod`: the editable eight-channel MOD, with a descriptive
  title and pitched instrument names explaining their reference tuning.
- `baseline.mod`: byte-identical accepted unedited module.
- `preview.wav`: independent replay of the named editing copy; verified
  byte-for-byte identical to the accepted preview.
- `reference.wav`: original first-24-second mono excerpt.
- `README.txt`: playback-clock, instrument, effect, location and save guidance.
- `event-map.json`: all 409 source events matched to actual decoded tracker
  order/pattern/row/channel/instrument/period/volume, including the delayed
  attack and existing vibrato annotations.
- `manifest.json`, `notes.json`, `arrangement.json`: initial provenance, source
  recognition history and editing/reduction diagnostics.

The editable MOD changes display-name bytes only. Pattern cells, sample
metadata and sample PCM remain unchanged; initial editable SHA-256 is
`30ae0d84894d2a8345973029cf0066b1cf67738fbeee9a292447a377d6383030`.
It plays identically to baseline
`a33b4a621c82ec50bb54dab6d49c48b77fb7675d3ae68b68b5ebd9d413a7196e`.
The tool validates source/notes/module/replay-library provenance and the
expected sample-bank format before preparing the copy. It refuses an existing
output directory, preventing regeneration over later tracker edits. After
manual changes, the edited MOD is authoritative; original JSON and event map
are historical and must not be used to regenerate over those changes.

Important editing details: enter replay BPM 184 / speed 6, preserving F06 and
FB8, not the separate analysis-grid BPM 92. Rows are 81.522 ms. The source
1.714-second bar does not align with the 64-row editing pattern boundary.
Pitched sample banks contain five cycle lengths (16, 32, 64, 128, 256 samples)
for each of bass, lead and harmony, rather than five different instruments.
Names indicate approximate sounding C octave at period 428 (conventional
tracker C-2); tracker octave labels can differ. Pitched finetune remains +1.
Drum samples are decimal 16 / hex 10 kick and decimal 17 / hex 11 snare.
Channels 1-7 carry pitched events with role spillover; channel 8 carries drums.
The handoff is an eight-channel editing asset, not LSP/four-channel replay input.

Correction markers map the user's reported times approximately as follows
(order/pattern decimal, row hex): 3 s -> 0/0/25; 5 s -> 0/0/3D;
9 s -> 1/1/2E; 10 s -> 1/1/3B; 12 s -> 2/2/13; 18 s -> 3/3/1D.
The existing overloaded MIDI 68 attack near 22.28 s waits from order/pattern
4 row 11 to row 12. No accepted event is completely lost by allocation.

A decoded held-lane capacity audit starts the next three/four-channel planning
step without silently dropping notes. Across 295 played rows, peak pitched
activity is seven voices, and peak provisional foreground (lead/bass) activity
is five. Reserving one music voice for percussion, 190 rows exceed a four-voice
budget and 269 exceed a three-voice budget. On 54 rows, more than two foreground
voices remain, so merely baking all harmony into one voice cannot guarantee
four-voice playback. Roles remain guesses, not independent instrument tracks;
manual part identification and selective foreground/composite sample decisions
are necessary before choosing SFX ownership and native reduction. These row
counts are a capacity diagnostic, not a duration-weighted musical quality score
or a shipping voice-allocation decision.

Four handoff tests cover display-only renaming/sample integrity and tuning
labels, actual delayed/lost-event mapping, held-lane capacity/release counting,
and refusal to overwrite an existing edit directory. Tracker and allocation
audit tests pass. Full preparation independently replays the copy identically
to the accepted audio. Original and derived music assets remain ignored and
uncommitted; only tooling, tests and implementation records are committed.

```sh
python3 tools/amiga/test_tracker_edit_handoff.py
python3 tools/amiga/prepare_tracker_edit.py --baseline build/amiga-transcription/lead-role-audition --reference build/amiga-transcription/positive-force-excerpt.wav --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/manual-edit-v1
```

The preparation command intentionally fails if that handoff already exists;
choose a new version directory for an independent fresh handoff. Keep manual
edits in a separately named MOD. This remains only the first 24 seconds; full
Positive Force and other soundtrack tracks are not yet transcribed. Next:
work from the manually corrected master for three/four-channel comparisons,
selectively bake simultaneous parts where appropriate, then measure Chip bank
size, mono/hard-panned balance, SFX policy and native replay alongside gameplay.


### Source waveform correction and reduced adjustment export

The user identifies bass as triangle, lead as 25% pulse and harmony as 50%
pulse/square, and reports excessive repeated notes with volume adjustments.
The full original reference is
`build/amiga-transcription/positive-force-source.ogg` (168.001 s, stereo 44.1 kHz);
`positive-force-excerpt.wav` is the mono first-24-second reference used for the
editing MOD. These files remain private/ignored.

The initial sketch bass was sine plus a weak second harmonic, and harmony was
fundamental plus weak third/fifth harmonics. The lead was already a softened
25% pulse approximation. `working_module` now has an opt-in `pulse-triangle`
profile: triangle bass, existing seven-harmonic quarter-pulse lead, and a
seven-harmonic band-limited 50% pulse harmony. The default sketch remains
byte-identical to the accepted 409-event baseline; both original manual-edit
copies and any subsequent user edits remain untouched.

Recognition confidence had been incorrectly used as an onset volume estimate.
That score is not measured source loudness. New opt-in fixed-volume export uses
base volume 32 with existing role gains: bass 32, lead 38, harmony 16. Instrument
headers carry these levels; pitched attacks need no Cxx adjustment because an
explicit instrument restores its header volume after a prior C00 cut. Required
C00 releases, two existing vibrato annotations and delayed percussion commands
remain. `arrange_tracker.py` passes the profile and fixed level consistently to
the full mix and all stems. Drum PCM, headers/placements and level policy remain
unchanged. This constant-level prototype does not claim to recover real source
dynamics; intentional dynamics can be restored manually.

`simplify_tracker_notes.py` forms a separate audition from the accepted score.
It considers adjacent same-pitch/same-role fragments with at most 25 ms source
gaps, protecting any calibrated vibrato note. Source/model evidence at the
following boundary must have onset probability <0.65 and rises <1.5 at all of
the fundamental, second and third harmonic. Stronger repeated attacks remain.
A merge is also rejected if it would fill any additional tracker row. Chains
join with original pitch/initial confidence and extend the retained note's end;
no occupied pitch/role rows disappear or get added. The original arrangement
history is preserved byte-for-byte in a separate sidecar, while retained role,
effect and active vibrato calibration indices are updated for the simplified
score. The tool refuses an existing output directory.

For this excerpt, 36 weak same-pitch boundaries merge, reducing 409 events to
373. Of 182 reviewed boundaries, 146 stronger attack cases remain. The full
quantized pitch/role coverage multiset is exactly identical to the input.
Every one of the 373 retained events starts; the sole original late attack near
22.28 s persists (now event 23). Existing eight vibrato rows and all 71 drums
remain; no new voice overload or percussion collision occurs.

Positive pitched Cxx commands fall from 409 to zero. There are still 157 C00
release commands (previously 153), because channel allocation and note cuts
remain necessary; these are not confidence-driven volume automation. New MOD
SHA-256 `acb994e664703ccd5e569fb9bd1fac16f31b3bdfab21d3170c1b489167c99e08`,
21,314 bytes with 9,990 sample bytes. Independent libxmp playback reaches the
first loop in 24.2 s, peak 0.62061 with no clipping. The edited palette and fewer
attacks need audition and are not claimed to resolve every recognition error.

Private assets are under `build/amiga-transcription/simplified-waveforms/`.
A new protected manual handoff is `build/amiga-transcription/manual-edit-v2/`,
including `positive-force-edit.mod`, baseline/reference/preview, guide and
373-event decoded map. Display-only renamed MOD SHA-256 is
`5186d433b4891465d581309f62bc923ec5627c16b46e19dcf31895b809bc6dce`;
its independently rendered preview matches the simplified baseline exactly.
Version 1 remains available unchanged. This is still only the first 24 seconds,
not the full 168-second track or a native four-channel asset.

Tests cover weak fragment chains, protection of attacks/roles/vibrato, refusal
to fill a rounded-row gap, triangle/pulse/square harmonic signatures, fixed
header levels and absence of volume commands on attacks. Independent replay
checks all three timbres restore equal levels after a C00 cut despite differing
recognition confidences, and confirms silence between notes. Existing pitch,
EDx timing, malformed-module, tracker/handoff and allocation checks pass.
Metadata/effect reindexing, quantized coverage and unchanged default export
bytes are verified. Licensed source/derived assets remain uncommitted.

```sh
python3 tools/amiga/test_tracker_simplification.py
build/amiga-transcription-env/bin/python tools/amiga/test_tracker_render.py --library build/amiga-libxmp/build/libxmp.dylib
build/amiga-transcription-env/bin/python tools/amiga/simplify_tracker_notes.py build/amiga-transcription/positive-force-excerpt.wav --baseline build/amiga-transcription/lead-role-audition --candidate-dir build/amiga-transcription/lower-frame-recheck --out build/amiga-transcription/simplified-waveforms
build/amiga-transcription-env/bin/python tools/amiga/arrange_tracker.py build/amiga-transcription/positive-force-excerpt.wav --notes build/amiga-transcription/simplified-waveforms/notes.json --arrangement build/amiga-transcription/simplified-waveforms/arrangement.json --out build/amiga-transcription/simplified-waveforms
python3 tools/amiga/render_tracker.py build/amiga-transcription/simplified-waveforms/arranged-eight.mod --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/simplified-waveforms/arranged-eight.wav
python3 tools/amiga/prepare_tracker_edit.py --baseline build/amiga-transcription/simplified-waveforms --reference build/amiga-transcription/positive-force-excerpt.wav --library build/amiga-libxmp/build/libxmp.dylib --out build/amiga-transcription/manual-edit-v2
```

Choose fresh output directories for new auditions; do not regenerate over manual
edits. Next: compare the simpler waveform/level version against the original,
continue manual musical corrections, then proceed with three/four-channel
composite-sample and native replay work.


## Screen-shake viewport core — 11 October 2026

Music reconstruction is parked at the user's request after contacting Magnus
Palsson for original tracker files. Existing MODs and manual edit copies remain
available. Continue engine work with screen shake, which teleporter
departure/arrival states already request and decay but the native renderer has
not yet displaced.

Added `screen_shake.c/.h`. `v6_screen_shake_pre` matches the actual
`Graphics::updatescreenshake` calculation using two caller-owned uniform 16-bit
samples representing fRandom() in [0,1). The integer expression truncates toward
zero, preserving the asymmetric source range -4 through +2, including the -4
endpoint at zero. A positive shake timer refreshes the offsets; inactive timers
retain them. Sampling is separate from visible effect suppression, matching
`renderfixedpre` sampling even when noflashing mode prevents drawing the shake.
The caller still owns RNG progression and existing timer decay.

`v6_screen_shake_plan` produces a clipped 320x240 source/destination rectangle
and physical displacement. Inactive/noflashing plans cover the complete viewport
without displacement. Flipped mode negates physical Y displacement, equivalent
to translating before the desktop's final vertical texture flip. Invalid calls
preserve output; reset restores zero offsets. This is a rendering plan, not a
pixel copy: the native caller must explicitly produce black exposed edges,
translate hardware sprites/text with the playfield, and keep the screenshot
border fixed after translation.

`make -C amiga_version test-screen-shake` compiles the core with the existing
68000 toolchain and runs undefined-behaviour-sanitized host tests. The reference
extracts `Graphics::updatescreenshake` from the desktop source, testing all
65,536 values paired with complementary Y inputs plus 10,000 mixed pairs:
75,536 matching calculations. Every -4..+2 X/Y combination, active/inactive,
noflashing and flip choice drives a per-pixel unique-source-ID oracle: 30,105,600
pixel checks verify clipping, simulated black exposed edges, and translation
before final vertical flipping. Inactive retention, reset, NULL inputs and
transactional invalid-state handling also pass.

This increment adds no Chip allocation and does not change the native frame
loop or claim visible native screen shake. It is the source-matched foundation
for that integration. The new target is included in `make test`. Next: connect
sampling to the teleporter fixed/render phases, move the complete scene in the
native renderer, preserve black edges through simultaneous flashes, then verify
captured offsets and CPU/video headroom on the A500. Final teleporter arrival
saving/fresh-boot validation and enabling Energize in the playable menu remain
subsequent engine work; soundtrack asset conversion stays parked.


## Native register-based screen shake — 11 October 2026

The staged Building Apport/Energize teleporter fixture now samples shake before
fixed-tick counter decay and latches each physical offset through paused fields.
It changes DIWSTRT/DIWSTOP, DDFSTRT and BPLCON1 rather than copying the viewport
with the blitter. Positive X uses the normal twenty-word fetch; negative X
starts one word earlier and uses twenty-one fetches with modulo -2. Copper
pointer resets account for clipped vertical rows and both circular rings.
Hardware sprites move by the same offset; pristine teleporter position headers
are restored before the next translation. The isolated fixture bounds-checks
its teleporter positions so those static six-channel strips never need pixel
clipping. The general sprite helper also supports clipping, checked separately.

An immutable 9,602-byte constant plane makes the dual-playfield backdrop opaque
inside DIW, leaving COLOR00 black outside it. This preserves the original dark
backdrop inside the translated scene and keeps exposed edges black during a
simultaneous grey flash. Flash frames display only that constant plane. No
viewport-copy blit or per-frame mask generation is needed. Noflashing suppresses
the visible translation/flash while shake sampling retains source semantics.

Validation: source sampling/viewport tests remain valid; 16,128 ring/register
plans and 3,000 sprite pixel translations pass, including both Y directions and
invalid-input preservation. Native captures compare every viewport pixel
against identical unshifted fixtures at ticks 1, 6 and 7: grey flash (-3,-1),
rightward scene (+1,0), and left/down scene (-1,+1), 230,400 pixels total. The
128-tick staged round trip retains all 4,608 gameplay/render oracle fields and
has zero missed fields/errors, using 78,690 Chip bytes. The no-audio fixture
reaches the 250-line headroom limit; combined shake/SFX has not yet been admitted.

Run `make -C amiga_version tower-teleporter-shake-capture`. Artifacts are in
`build/amiga-teleporter-shake/` and `build/amiga-shake-pixels-*`. This is a bounded
staged teleporter fixture, not yet the interactive menu/caption renderer. Native
final vertical flip and captions still need integration. Music reconstruction
remains parked while awaiting original tracker files.


## Screen-shake/audio headroom — 11 October 2026

Flash frames now skip sprite drawing and teleporter animation-sample copies.
The source replaces the entire scene with a solid grey rectangle before shake;
the translated opaque mask already supplies all visible pixels. The inactive
sprite heads are terminated for these fields. Existing teleporter cache tags
and translated-head restoration state are retained, so the first non-flash
field restores the current animation normally. Other renderers keep their
existing sprite path.

The no-audio roundtrip peak falls from 250 to 225 PAL lines. The combined
register-shake and two-channel reserved-SFX fixture peaks at 235 lines, using
120,420 Chip bytes, with zero missed fields, errors or channel-policy violations.
All 4,608 gameplay/render fields still match. Shake records are additionally
cross-checked against the source-validated departure/arrival timers before
counter decay. All eight SFX requests start: seven drain, one flash is replaced
by teleport, two voices overlap, and reserved channels 2/3 remain idle. Captured
waveform, duration, replacement, final silence and hard-panning checks pass.

The three native shifted/unshifted pixel capture pairs remain exact, including
the flash and first non-flash field. Run
`make -C amiga_version tower-shake-audio-capture`; combined reports, RAM dump,
screenshot and audio stems are in `build/amiga-shake-audio/`. This admits the
bounded shake/SFX combination, not tracker music or interactive captions/flip.
Next: final teleporter arrival checkpoint disk/fresh-boot validation, then
explored-destination menu admission. Music reconstruction remains parked.


## Completed arrival disk persistence — 11 October 2026

The staged teleporter/save fixture now admits a DF1 write only after the final
source arrival SAVE event, with the arrival script inactive, control restored,
departure inactive and the expected travel leg completed. A valid in-memory
centre set at the handoff is insufficient. DOS replacement/flush runs after
normal native display/interrupt/DMA restoration; this fixture ends gameplay
rather than adding a live autosave pause/resume path.

Two native cases complete the outbound Energize arrival (64 ticks) and the
return Building Apport arrival (128 ticks), write the existing 44-byte campaign
record, then boot a new emulator process against the same private DF1 disk.
Cold boot selects the saved foreground/collision bank, restores the source
centre, gravity and direction with zero velocity, and starts with inactive
travel states. Fresh-boot interpolation history is explicitly initialised to
that centre. Both subsequent cold-room replays match the host route/physics,
teleporter, checkpoint and animation model. Main-record bytes remain unchanged.

All 9,216 warm/cold trace fields match across the two cases. Completed-arrival
runs peak at 226 PAL work lines; cold runs peak at 223/220, with zero missed
fields/errors and 78,690 Chip bytes. CRC-valid records shifted one pixel from
each teleporter centre are rejected before display takeover without changing
the disk. A separate native stop at tick 23 proves that the valid Energize
handoff centre cannot be committed while state 4011 still owns control: the
save is refused and both private DF1 and boot image remain byte-identical.
The original resident Building Apport disk/fresh-boot/rejection fixture still
passes. Campaign encoding, replacement fault/recovery and coupled travel host
checks also pass.

Run `make -C amiga_version tower-arrival-save-capture`. Reports, private disks,
RAM dumps and screenshots are in `build/amiga-arrival-save-{64,128,early}/`, with
summary `build/amiga-arrival-save-capture.json`. The fixture accepts its selected
terminal teleporter and zero story flags only. Automatic in-game DOS pause/
resume, broader story saves, explored-destination admission and live Energize
menu travel remain pending. Music reconstruction remains parked.

## Explored-destination admission core — 11 October 2026

Added a 400-room session exploration bitset and a destination filter that
preserves the original 17-teleporter order. A destination must be explored and
present in the caller's validated resident route list. Exploration alone cannot
unlock an unsupported room. Invalid room coordinates, duplicate or non-source
residents, and insufficient output capacity leave existing state/output intact.
The exploration map is not yet persisted in the 44-byte campaign record.

`make -C amiga_version test-teleporter-admission` passes all 131,072 subsets of
the original teleporters against the desktop source order, all 400 room indices,
resident exclusion, and invalid/capacity cases. The core compiles with the native
68000 toolchain. Native menu integration remains pending: mark entered rooms,
refresh available destinations, connect confirmation to departure/arrival, and
queue DOS autosave only after the final arrival SAVE event. Verify physical menu
input, unexplored exclusion and save pause/resume before admitting live travel.
Music reconstruction remains parked.

## Native explored menu travel and arrival autosave — 11 October 2026

The Building/Energize interactive slice now records room entry in the session
exploration map, filters menu destinations through validated residents, and
uses source ordering. Menu confirmation starts normal departure, latches the
selected destination, loads its resident scene and runs arrival. The final
arrival SAVE event queues DOS replacement/flush through the existing live
pause/resume path; locked-script save/load requests report busy. Loading resets
travel state/effects and marks the loaded room explored.

Physical native captures cover admitted outbound travel, unvisited Energize
exclusion, and a fresh unseeded process loading the actual outbound record and
travelling back. Both journeys compare all 64 ticks, 4,608 model fields total;
checkpoint records are Energize (80,112) and Building (156,92), with source saved
direction/gravity. Menu input causes no extra flip, menu-paused hashes retain
state, and each DOS pause preserves logic ticks/state and excludes disk wall
time from the accumulator. Saving during departure and arrival is rejected
before the final event. The unvisited case changes neither disk. The original
Building-only physical menu regression passes.

Run `make -C amiga_version tower-menu-travel-capture`; reports/RAM/screenshots
are in `build/amiga-menu-travel/` and `build/amiga-menu-unexplored/`. All three
cases use 95,968 Chip bytes, peak at 236 PAL work lines and have zero errors or
missed fields. `tower-menu-travel-run` provides the live controls with separate
retained DF1 storage. The visited-room seed, source movement replay and stable
600-tick RAM-capture hold are absent from that live executable.

Session exploration remains outside the 44-byte campaign disk format. Next:
combine the independently verified register shake/Paula cues with interactive
captions and DOS pauses, then persist exploration with compatible record
validation/recovery. Broader story progress and unsupported teleporters remain
outside this slice. Music reconstruction remains parked.

## Interactive shake/captions/audio and queued autosave — 11 October 2026

The explored-menu slice now supports register-based shake together with its
caption strip, translated sprites and two reserved Paula cue voices. The new
caption Copper path shares DIW/DDF clipping, BPLCON1 and vertical translation,
then restores foreground/background ring pointers at the correct source rows.
Flash covers the caption too. Caption Chip addresses include the shake mask;
inactive Copper lists have capacity for the combined sequence.

Arrival SAVE queues persistence until the final cue drains, preserving playback
and releasing all cue voices before DOS restores the OS display/interrupt/DMA
state. Normal gameplay continues during this short wait. Save/load reports
busy during scripts/cues, and pending autosave blocks reopening the selector.
A quit during the tail is latched until the cue and save complete. DOS itself
still contributes no gameplay time and preserves paused state/ticks. Loading
clears shake and travel state without replaying arrival effects.

`make -C amiga_version tower-menu-effects-capture` validates outbound,
fresh-process load/return and queued-save exit. The three journeys match 6,912
model fields, independently verify shake RNG/timers, complete all four source
cues each, and pass captured PCM/duration/silence/hard-panning checks. Only
channels 0/1 are used; channels 2/3 remain idle and policy violations are zero.
OFS campaign bytes verify the original centre/direction/gravity for both rooms.
The paired native caption/scene fixture compares 76,800 shifted pixels exactly
and retains its disks, with another 2,304 model fields compared.

Host checks cover 16,128 caption/scene DMA plans, 16,128 plain-scene plans,
3,000 general sprite pixel cases, and 252 six-strip header shifts/restorations.
The bounded teleporter fast path avoids repeated generic sprite validation;
resident-first exploration lookup and conditional menu hashes reduce crossing
and gameplay work. Combined fixtures use 147,556 Chip bytes, peak at 233 PAL
lines for interactive travel and 242 for the shifted-caption fixture, and
report zero errors/missed fields. The standalone staged shake/audio regression
also passes at 223 lines. Artifacts are under
`build/amiga-menu-effects{,-return}/` and `build/amiga-menu-pixels-*`.
`tower-menu-effects-run` launches real controls with a retained private DF1 disk;
seeding, movement replay, deterministic render RNG and capture holds remain
confined to test builds.

Next: persist the explored-room map with compatible campaign validation and
recovery, then expand resident routes/story support. The existing 44-byte
record still saves only the checkpoint/story fields. Music work remains parked.

## Explored-room save codec — 11 October 2026

The campaign codec now offers a 96-byte version 2 record containing the
checkpoint/story fields and all 400 explored-room bits in a single CRC-covered
payload. Two reserved bytes must be zero, and the saved checkpoint room must
be visited. Decode publishes checkpoint, story and map together only after
validation. It also reads existing 44-byte version 1 saves, marking only their
checkpoint room as visited. The legacy APIs retain their exact version 1
contract and reject version 2 instead of silently discarding exploration.

`make -C amiga_version test-campaign-state` checks independent big-endian/CRC
vectors, every map bit, 768 single-bit corruptions, 97 length guards, semantic
and reserved-byte corruption with recomputed CRCs, transactional rejection,
and migration from all six supported room banks. Existing codec, file and
replacement/recovery fault tests remain passing.

This is the format foundation; the live DOS file adapter still writes version
1. Next: carry the map through transactional file replacement/recovery, then
restore it on menu load and verify destination admission after a fresh boot.
Music work remains parked.

## Explored-room disk persistence — 11 October 2026

The interactive menu-travel builds now save the 400-room exploration map with
the checkpoint and story in one 96-byte version 2 campaign record. Full-state
file APIs share the existing verified temporary-write, backup promotion and
recovery sequence. Reads accept versions 1 and 2; replacing an old save upgrades
it. Legacy checkpoint-only APIs still reject version 2, preventing map loss.
Both final and backup records undergo source-bank/story validation before
cleanup. Invalid live checkpoint/story/map state is rejected before disk work.
Loading replaces session exploration with the saved map, then marks the loaded
room and rebuilds resident admission. A legacy save seeds only its saved room.

`test-campaign-state-file` checks 48 interruption snapshots and 228 operation
faults across full-state replacement, legacy upgrades and recovery. Checkpoint
and map always remain paired; failed reads/recovery retain all caller outputs.
Checksum-valid altered readback is rejected before promotion. Existing version
1 codec/file/recovery checks and the actual UI consumer tests also pass,
including malformed source centres in either final or backup and legacy map
replacement. Explicit bounded byte copies avoid libc dependencies on the
freestanding 68000 target.

`tower-menu-effects-capture` checks outbound arrival/autosave, quit during the
cue tail, fresh-process full-state load/return and a legacy-load fixture. The
legacy fixture downgrades only a disposable capture disk and verifies that
previously visited but unsaved Building Apport is excluded after loading an
Energize checkpoint. Full-state OFS bytes retain Seeing Red, Building Apport
and Energize visits. The source save and boot disk stay unchanged during cold
loads. Existing shake, caption pixels and reserved Paula cue checks remain in
this target.

Final captures retain the 147,556-byte Chip allocation, peak at 233 PAL work
lines outbound/queued exit and 243 for fresh-process full/legacy loads, and
report zero errors/missed fields. The paired 76,800-pixel caption translation
check also passes within the 250-line gate. The live `tower-menu-effects` build
compiles without warnings.

Next: expand validated resident rooms and story support. Music reconstruction
remains parked pending original tracker assets.
