# VVVVVV A500 conversion plan

Reviewed revision: `52ad6ae3`, 27 September 2026. Target confirmed by the user: A500, 68000, OCS/ECS, 1 MB RAM.

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
and cached/uncached movement match extracted source. Moving-platform recovery,
visibility and tower-specific life timing remain outside this comparison. The full desktop
loop is unverified. The A500 compression and checkpoint-route captures pass after
the reset fix; the route remains at 196 PAL lines with clean exit.

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

Preferred small-memory route: obtain suitable source music and create approved Amiga tracker arrangements with a bounded sample bank. Existing tracker music cannot be assumed to be available, four-channel compatible, or small enough. Converting an Ogg recording into a faithful compact MOD is not an automatic format conversion. Reserve a channel for SFX or define/test channel stealing; account for audio quality changes.

Alternative: preconverted PCM or a low-cost compressed stream for hard-drive installs, after measuring decode cost and I/O reliability. At 11,025 Hz, mono 8-bit PCM alone consumes 661,500 bytes per minute. Full tracks cannot simply remain resident alongside the game. Sustained floppy music streaming is not the baseline solution.

The first playable build can use effects only. Full music remains a release requirement to resolve explicitly, not a hidden omission from the campaign port. Benchmark at least one representative song with gameplay before committing to a soundtrack approach.

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
