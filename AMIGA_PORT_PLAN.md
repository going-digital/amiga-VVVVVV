# VVVVVV A500 conversion plan

Reviewed revision: `52ad6ae3`, 27 September 2026. Target confirmed by the user: A500, 68000, OCS/ECS, 1 MB RAM.

Latest milestone (7 October 2026): Building Apport's resident route is
committed as `32c57c07`. Teleporter checkpoint records now pass source-bank
validation and a native DF1 save/fresh-boot fixture, including malformed-centre
rejection before takeover. See "Teleporter checkpoint disk persistence" below.
Travel UI and integration into interactive saving remain next.

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
