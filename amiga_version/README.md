# A500 feasibility prototype

This native slice runs original rooms **(100,110)** and **(119,110)** on a PAL A500 with 512 KiB
Chip RAM and 512 KiB slow RAM. It has player movement, gravity flipping, static
tile collision, spikes, checkpoint activation, death and respawn. It starts at
room (100,110)'s ceiling checkpoint, rather than the campaign starting position.

Moving left from (100,110) enters (119,110), preserving movement state; moving
right returns. Checkpoints retain their room, position and gravity for respawn.
Other exits return to the saved checkpoint and show a notice. A separate
**Security Sweep (112,103)** scene now includes its original moving enemy and
floor checkpoint. **Traffic Jam (115,103)** adds three wide moving enemies;
its seven-channel capture now passes the video headroom gate.
**Stop and Reflect (112,106)** adds three moving platforms and a verified
vertical ride replay. **Just Pick Yourself Down (117,109)** adds an original
horizontal platform and two working checkpoints. General scripts, wider campaign progression, keyboard controls and
music remain unimplemented; the separate Seeing Red rescue fixture described
below now runs its bounded script and follower. See [the port plan](../AMIGA_PORT_PLAN.md).

## Build and run

From the repository root on this Mac:

```sh
make -C amiga_version all
make -C amiga_version test
make -C amiga_version capture
make -C amiga_version capture-transitions
make -C amiga_version run
make -C amiga_version enemy-run
make -C amiga_version enemy-capture
make -C amiga_version traffic-run
make -C amiga_version traffic-capture
make -C amiga_version platform-run
make -C amiga_version platform-capture
make -C amiga_version horizontal-capture
make -C amiga_version pick-run
make -C amiga_version pick-capture
make -C amiga_version pick-checkpoints-capture
make -C amiga_version pick-route-capture
```

- `all`: host asset conversion, Bartman 68000 compile, ELF/Hunk output, bootable ADF.
- `test`: compare the C RLE decoder against every extracted campaign tile array,
  validate malformed packets, compare player physics with extracted original C++
  methods, and run UBSan session lifecycle checks.
- `capture`: deterministic Copperline input, screenshot, memory/timing assertions,
  audio capture, and a resumed-state clean-exit check. Runs headlessly.
- `capture-transitions`: builds a separate test-only input replay in
  `build/amiga-transitions`, verifies the world-wrap crossing without death,
  captures the neighboring room, then checks cross-room respawn and clean exit.
- `enemy-run`: interactive Security Sweep scene, built in `build/amiga-enemy`.
- `enemy-capture`: verifies enemy movement, a player hit, death/respawn, both
  visible sprites, timing and return to AmigaDOS.
- `traffic-run`: interactive three-enemy scene in `build/amiga-traffic`.
- `traffic-capture`: checks seven-channel allocation, three visible red enemies,
  movement, checkpoint, timing and clean exit. This replay does not exercise
  enemy hits.
- `platform-run`: interactive Stop and Reflect in `build/amiga-platform`.
- `platform-capture`: separate deterministic input build in
  `build/amiga-platform-replay`; checks platform transport, three visible
  platforms, seven channels, death/respawn, timing and clean exit.
- `horizontal-capture`: builds a labelled synthetic horizontal-platform fixture,
  verifies the host reference trace, then compares the target snapshot with the
  matching reference tick. Output is in `build/amiga-horizontal-replay`.
- `pick-run`: interactive Just Pick Yourself Down in `build/amiga-pick`.
- `pick-capture`: checks initial checkpoint activation, visible platform,
  three sprite channels, timing and clean exit.
- `pick-checkpoints-capture`: separate test build that places the player at the
  second checkpoint, checks deactivation/redraw of the first, then death/respawn
  at the second. This isolates checkpoint behavior; it is not a traversal replay.
- `pick-route-capture`: normal-input traversal and platform ride to the second
  checkpoint, followed by a requested restart. Checks a live movement snapshot
  against desktop code and the post-respawn snapshot against the host scene.
- `run`: interactive Copperline window. Joystick left/right moves;
  fire flips gravity when supported. Right mouse restarts from the checkpoint;
  left mouse exits to AmigaDOS. Keyboard input is not implemented yet.

The default toolchain is discovered under
`~/.vscode/extensions/bartmanabyss.amiga-debug-*`, the emulator is
`/Applications/Copperline.app`, and the ROM is `~/amiga/KICK13.ROM`.
The asset default is the local Steam installation:
`~/Library/Application Support/Steam/steamapps/common/vvvvvv/VVVVVV.app/Contents/Resources/data.zip`.
Override paths with `BARTMAN=...`, `TOOLS=...`, `COPPERLINE=...`, `CTL=...`,
`ROM=...`, and `DATA=...` on the make command. Quote overrides containing spaces.
Host dependencies are Python 3, a C/C++ compiler, and make. The physics reference
currently expects SDL3 under `/opt/homebrew`. PNG decoding uses
the repository's LodePNG code and needs no Python packages.

`build/amiga/` contains all generated assets and output, and is ignored by Git.
The supplied ROM/archive are read only. No Workbench disk image is needed for
this generated AmigaDOS boot disk. Converted proprietary assets must not be
committed or bundled for distribution without the relevant permission.

## What is implemented

- PAL-only 320×240, two bitplanes, double buffering per cached room; stock 68000, OCS,
  512 KiB Chip RAM + 512 KiB slow RAM, no Fast RAM/FPU.
- Native Copper display, hardware sprite 0 for the player, blitter HUD copies,
  palette conversion, and Paula DMA for one short converted effect.
- A 34 ms gameplay tick accumulated from PAL refresh periods. Static player
  physics preserve the original input/contact/velocity/X/Y collision order.
- Integer 8.24 velocities and explicit binary32 rounding, including rounding
  before position truncation. No floating-point runtime is linked on the Amiga.
- Four colours in the playfield: black, a room accent, green checkpoints and
  white text. Low-intensity tile shading is removed; both rooms retain their
  outlines and hazards. The cyan player uses an independent sprite palette.
- The visible player fits source columns 6–21 and uses one 16-pixel sprite.
  Two banks of eight DMA lists publish animation, position and colours with
  the completed screen. The enemy scene also uses a channel for its pink drone.
  Requests allocate channels in priority order, with the player submitted first.
  Multiplexing and a general blitter fallback remain to be implemented.
- Two screen pairs remain cached in Chip RAM; original room backgrounds live
  in slow RAM. Only checkpoint damage needs CPU restoration; HUD copies update only the
  eight-row text bands whose content changed. The earlier repeating-room scroll
  stress harness has been replaced; actual tower streaming remains outstanding.
- Copper waits until line 44 before reading buffer pointers, so publication
  after the VBL interrupt completes before visible display starts at line 52.
  Sprite pointers are published earlier, at line 20, before sprite control DMA.
- Hardware ownership/restoration and a bounded startup allocation; no OS calls
  inside the main hardware takeover loop.
- Offline room pack covering literal tile initializers, including zero-filled
  defaults and conditional variants. The source location is the authoritative
  record identity, **not** a ready-to-use room-coordinate lookup. Room setup
  C++ code, scripts, and tower data are outside this pack's scope. A separate,
  strictly bounded export includes the two slice rooms' literal checkpoint setup
  and rejects unsupported setup statements.

## Measured result, 27 September 2026

The current automated capture uses Kickstart 1.3 and Copperline's stock A500
cycle timing with 512K Chip + 512K slow RAM. At the 16.5-second memory snapshot:

| Measurement | Result |
|---|---:|
| Room arrays, including explicit-size defaults | 422 |
| Raw tile bytes | 1,012,800 |
| Packed tile bytes, including directory | 252,832 |
| Unique packed payloads | 406 |
| Prototype explicit Chip RAM allocation | 81,934 bytes |
| Free Chip RAM after startup allocation | 376,520 bytes |
| Free non-Chip RAM after startup allocation | 416,784 bytes (interactive build) |
| Maximum measured update/draw work | 167 PAL lines / 10.688 ms (transition replay) |
| Maximum room-change redraw | 167 PAL lines / 10.688 ms |
| Missed VBL observations including transitions | 0 |
| VBL periods crossed by room-change work | 0 |
| Flip, checkpoint, spike death and respawn | Passed |
| Captured flip audio signal | Passed |
| World wrap and cross-room respawn | Passed |
| Return to AmigaDOS | Passed |

These are **emulator measurements of this harness**, not real-hardware or
complete-game performance. The RAM totals do not include a resident full room
pack: only two compressed rooms and their decoded tile/background caches are
resident. A cache per room is temporary slice scaffolding, not the full-campaign
storage design. The ordinary capture peaks at 91 lines / 5.824 ms. During a snapshot
the current tick can be one ahead of the completed-render counter.

Reports and evidence:

- `build/amiga/smoke-report.json`: current timing, RAM, input/audio/exit assertions.
- `build/amiga/prototype.png` and `exit.png`: game display and restored AmigaDOS.
- `build/amiga/prototype.wav`: captured audio.
- `build/amiga/size-report.json`: executable sections/symbol sizes.
- `build/amiga/rooms.json`: tile record manifest and source hashes.
- `build/amiga/assets.json`: asset inventory and input fingerprint.
- `build/amiga/transition-test-report.json`: boundary reference coverage/hash.
- `build/amiga-transitions/smoke-report.json` and `neighbor.png`: target replay
  diagnostics and the second-room display.

The physics test compiles original C++ method bodies extracted from the desktop
sources and compares every state field with the integer core: **181 scenarios,
36,746 ticks, zero differences**, plus **53,280 hazard rectangle cases**. The
reference extraction is recorded with a hash in `player-test-report.json`.
This covers isolated static player physics, not the complete desktop game loop,
all entity interactions, or exhaustive possible states. Session timing checks
cover checkpoint activation, 30-tick death delay, respawn control lock and the
explicit slice exit fallback, checkpoint changes across rooms, and the original
room geometry replay. A separate test compares **32,400 normal-world boundary
cases** with code extracted from `Logic.cpp` and `Map.cpp`, including vertical-
before-horizontal ordering, thresholds, world wrap and retained movement state.
It excludes special-room transitions and the full `loadlevel` side effects.
The desktop Release build also succeeds in
`build/desktop`; full-game reference runs are still outstanding.

Room changes now select the cached screen pair and update checkpoint/HUD damage.
The explicit loading pause has been removed: transition time is included in the
same clock and missed-VBL checks as other work. The tested replay meets the
provisional 20% video headroom target, including room changes. This does not
establish worst-case full-game performance or real-hardware behavior.

The previous four-plane build used 161,486 Chip bytes and peaked at 45.312 ms
for room redraw. The new arrangement uses another 38,400 bytes of static slow-RAM
background storage and removes runtime full-screen copies. Only two rooms are
cached; the general campaign cache remains to be designed.

`PLANES=4` retains an experimental colour comparison build. Use a separate
`BUILD=/absolute/path` output directory for it; the automated performance gates
are for the default two-plane build. Prototype compilation is forced so changing
render flags cannot silently reuse an old object.

## Enemy movement foundation

`enemy.c` implements ordinary bounce behaviours 0–3 with integer speeds from
−16 to 16, hitboxes up to 32×32, patrol-bound clamping and static tile/block
collision. It preserves delayed state changes and the original axis order.
Unsupported initialization parameters fail explicitly. Fractional speeds,
gravity, emitters, platforms and special enemy behaviours are outside this API.

The host differential test extracts the original bounce cases, `outside`,
physics and collision methods. **528 scenarios / 126,720 ticks** match every
tracked state field, including negative speeds, different hitbox sizes, actual
source tile arrays and enemy-only safe blocks. The C implementation runs with
UBSan during these comparisons; `enemy-test-report.json` records the scope and
reference hash. Bartman also compiles it for the 68000.

The separate Security Sweep scene runs the core on the 68000 with the original
vertical speed-8 enemy, frames 36–39, and checkpoint setup. Channel 0 displays
the player and channel 1 the drone, using distinct colours in their shared
sprite palette. Both now submit requests to the bounded eight-channel allocator.

Player/enemy collision uses the original rectangle broad phase followed by
32×32 row masks based on **nonzero source red**, matching `Graphics::Hitest`
even where alpha is zero. Separate collision animation preserves the source's
pre-physics frame selection; enemy animation advances before game logic.
**53,868 pixel tests and 20,000 collision-animation ticks** match extracted C++
methods under UBSan. See `build/amiga/pixel-test-report.json` for scope and hash.
These isolated comparisons do not establish full desktop-loop equivalence.

The enemy capture's diagnostics and screenshot are in
`build/amiga-enemy/smoke-report.json` and `prototype.png`. Its explicit Chip
allocation is **43,534 bytes**, with one room's screen pair resident. Peak work
is **137 PAL lines / 8.768 ms**, with zero missed VBL observations. The replay
verifies an enemy hit, death, checkpoint respawn, visible cyan/pink sprites and
clean exit. It does not connect this room to the two-room world slice.

## Sprite allocation

`sprites.c` allocates up to eight channels in submission order. A monochrome
request up to 32 pixels wide uses one or two 16×32 channels atomically: insufficient
capacity leaves the existing DMA lists unchanged. Clipping occurs before reservation.
Even channels use colour index 1 and odd channels index 3, so each object can
have an independent RGB12 colour despite the shared pair palettes. Off-screen
requests consume no channel. Full capacity and invalid inputs return explicit
errors; the current harness exits cleanly on either rather than hiding objects.
Inactive channels get null control words every frame, preventing stale sprites.

The two DMA banks occupy 2,176 Chip bytes, 1,632 more than the previous two-channel
arrangement. `make -C amiga_version test-sprites` runs **30,600 DMA decode cases**
under UBSan, checking every channel, crop, screen clipping, vertical high bits,
palette selection, capacity, reset and memory guards. Another **33,792 cases**
verify wide sprites, clipping and atomic capacity failure. Traffic Jam now
exercises seven channels: one for the player and two for each original enemy.
Whole-halfword sprite encoding avoids variable shifts for aligned enemy crops.
Vertical multiplexing and attached sprites remain unimplemented.

Traffic Jam's capture shows all three original enemies moving, the checkpoint
activated and a clean AmigaDOS exit. Its 22×32 collision boxes remain separate
from the 32×32 source graphics. The room uses **43,534 Chip bytes** and peaks at
**249 PAL lines / 15.936 ms** at tick 2, below the unchanged **250-line gate**.
`build/amiga-traffic/smoke-report.json` records `video_headroom_passed: true`,
zero missed VBL observations and clean exit. This is a bounded replay result,
not a worst-case campaign guarantee. Enemy hit/respawn coverage still comes
from the Security Sweep replay.

## Collision cache and profiling

Each cached room now has a **2,052-byte non-Chip RAM** terrain cache. It stores
solid-tile classifications with a one-tile duplicated border and a flag for
whether directional tiles exist. Collision queries retain the original tile
rules and truncation toward zero; rooms without directional tiles skip that
scan. Rebuild the cache whenever tiles, tileset or `extra_row` change. The
uncached path remains available by setting `V6Room.terrain` to null.

Both paths independently match all **36,746 player ticks** and **126,720 enemy
ticks** against the extracted desktop reference. Another **9,192,768 queries**
check classification, duplicated edges, out-of-range queries and cache rebuilds
under UBSan (`make -C amiga_version test-terrain`).

Profiling identified collision work as the largest part of Traffic Jam's former
328-line peak. The cache, removal of redundant checkpoint mask writes, and
per-text-row HUD invalidation reduce it to 249 lines without additional Chip RAM.
An optional `CPPFLAGS=-DV6_PROFILE` build records six phase durations at the
highest-work update. Use a separate `BUILD` directory, then decode its `slow.bin`
with `python3 tools/amiga/read_profile.py /path/to/slow.bin`. Values are PAL lines;
instrumentation adds overhead, so use ordinary builds for timing-gate results.

## Dynamic block foundation

`V6Room.blocks` and `block_count` supply caller-owned collision rectangles to
player physics. Blocks can move or be disabled without rebuilding the static
terrain cache. Players collide with solid and directional blocks; SAFE blocks
remain enemy-only. A shared query also fixes enemy collisions with zero-sized,
temporarily disabled blocks, which must be ignored.

`blocks.c` preserves the original lifecycle rules: disabling an origin clears
every matching block's dimensions; moving restores only the first match. These
rules matter when multiple entities occupy the same position.

The new reference suite extracts the original block and player methods and
passes **21,600 collision queries**, **16,000 lifecycle operations**, and
**43,200 player ticks** for each of the cached and uncached paths. It covers
floor/ceiling contacts, gravity flips, directional barriers, changing rectangle
positions, disabled blocks and duplicate origins. Results and the reference
hash are in `build/amiga/blocks-test-report.json`; `make test` includes the suite.

The Stop and Reflect scene uses three live platform blocks. The earlier world
and enemy scenes retain empty lists. Full crush/death source-reference coverage
remains outstanding.

## Ordinary platform movement

`platform.c` implements 32×8 bouncing platforms with behaviours 0–3 and integer
speeds from −16 to 16. It disables the old block, runs the shared bounded
movement core with rule-2 collision semantics, and relocates the block. Platforms
collide with map tiles but ignore collision blocks, including other platforms
and directional barriers.

Floor/ceiling contact lookup preserves `checkplatform`/`hplatformat` ordering:
the first overlapping solid block selects the origin, then the first horizontal
platform at that origin supplies its velocity. A first block with no eligible
platform returns the original −1000 sentinel; zero velocity is a valid result.
The lookup does not itself transport the player. Conveyors are outside this API.

**528 scenarios / 126,720 ticks per cached and uncached path** match extracted
rule-2 movement, and **20,000 contact queries** match the original lookup methods.
`build/amiga/platform-test-report.json` records the scope and source hash.
`make test` includes these checks; run them alone with
`python3 tools/amiga/test_enemy.py --platform`. The Stop and Reflect scene calls this module; the linker still discards unused
platform functions in the other scenes. Full carrying/crushing fidelity across
the campaign is not claimed.

## Platform transport stages

Horizontal carrying now follows the original `Logic.cpp` stage, including
floor-before-roof lookup and suppression while `lifeseq >= 8`. It reuses the
player's collision routine with explicit target coordinates. The caller supplies
the retained pending Y position: the source reruns both axes rather than simply
adding platform speed to X. When blocked, collision retries use player velocity,
which can differ from the requested transport distance.

The vertical push/separation helper matches `movingplatformfix`: it probes the
player's existing vertical motion, adopts platform velocity if still overlapping,
and either separates the player or changes the platform's state when blocked.
Pending Y and visual floor/roof contact counters are explicit caller-owned state.
This helper alone does not establish the game's complete crush/death behavior.

**24,000 map-collision cases**, **24,000 horizontal-carry cases**, and **24,000
vertical-push cases** match extracted original code with cached and uncached
terrain, including fractional player velocities and disabled/overlapping blocks.
Run `python3 tools/amiga/test_carry.py`; `make test` also includes it. The report
is `build/amiga/carry-test-report.json`. All four existing native captures pass
after the shared player-collision refactor; they still contain no platforms.

The player API now exposes separate `v6_player_input` and `v6_player_physics`
stages. `V6PlayerMotion` retains the input acceleration and pending Y between
stages and ticks; initialize pending Y from the spawn position. Input preserves
pending Y, and physics consumes acceleration and records the collision routine's
final pending Y even when the move was blocked. The existing one-call player
step remains a wrapper around these stages.

Another **12,000 ordered transport ticks** match extracted input, vertical push,
horizontal carry and physics code on both terrain paths. These use prescribed
platform positions to isolate sequencing. The results are included in
`carry-test-report.json`; the persistent scheduling test below now covers the
combined movement and collision stages.

The post-physics helpers now reproduce platform-overlap block disabling and
stuck-player correction in **12,000 additional reference cases per terrain
path**. Call `v6_platform_disable_overlaps` before `v6_player_unstick`.
Overlaps disable every block at the platform origin, including duplicates;
these stay disabled until later platform updates relocate them. The stuck
probe ignores dynamic and map-derived directional barriers, but retains solid
terrain (including tileset-2 solids). Horizontal retries change velocity without
committing X; an unresolved collision shifts Y three pixels against gravity.
The test compares player state and block dimensions with extracted original
methods, exercising 6,882 corrections, 6,128 velocity changes and 4,950 cases
with block disabling. The Stop and Reflect scene now calls these helpers.

The pre-physics `v6_platform_transport` scheduler now runs both original
reverse-order passes, selecting vertical candidates by zero X velocity and
horizontal candidates by zero Y velocity. Room creation flags control whether
each pass runs; a stationary platform can run in both. Vertical movement
updates its block before pushing the player, and horizontal carrying follows
the complete horizontal pass.

**23,409 persistent ticks per cached/uncached terrain path** match the extracted
desktop scheduling loops and movement methods across 98 scenarios. Each tick
compares player state, every platform's movement state, block origins and
dimensions, pending Y, and visual contact counters. Coverage includes all four
pass-flag combinations, zero-speed platforms, duplicate block origins,
directional barriers, all three tilesets, and the respawn carry threshold.
Run `python3 tools/amiga/test_platform_loop.py` (also part of `make test`);
results are in `build/amiga/platform-loop-test-report.json`.

This establishes the combined ordinary-platform movement/collision sequence,
not the full game loop: damage, death/respawn, scripts, conveyors, supercrewmates
and native rendering are outside this reference harness. The native scene below
uses the verified scheduler.

## Native platform scene

Stop and Reflect uses the original room, checkpoint and three vertical platforms
at (135,75), (185,110) and (235,145), with speed 3 and bounds (100,70)–(320,160).
The exporter rejects changes to this literal room setup. Each 32×8 sprite repeats
source tile 616 four times; it uses two hardware channels. The player takes the
seventh channel. Platform colour is adapted to monochrome pink.

`v6_slice_step_movement` runs the platform movement callback on live ticks,
after respawn input gating and the life-timer decrement. It runs input,
platform transport, player physics, overlap disabling and stuck correction
before the slice checks checkpoints, tile hazards and exits. Platforms pause
during death and retain positions and block state on same-room respawn; player
pending motion is reset. Unsupported exits still use the slice's checkpoint
fallback, so this is a separate scene, not a campaign connection.

The deterministic capture walks left for 50 ticks and flips on tick 50. It
records **60 vertical transport position changes**, one death and respawn,
checkpoint activation, three visible platforms and seven hardware channels.
It passes the unchanged gate at **237 PAL lines / 15.168 ms**, with no missed
VBL observations and successful return to AmigaDOS. Explicit Chip allocation is
**43,534 bytes**, with **436,824 bytes** of non-Chip RAM free in the replay build.
The version-5 diagnostic actor fields hold platform position, update count and
transport count in this scene; the report also provides platform-named counters.

The initial smoke run cost 267 lines. Emitting only the platform's eight sprite
rows reduced its cost; `v6_sprites_add_rect` adds a height parameter while
preserving atomic wide-sprite allocation. **63,744 variable-height cases** check
DMA positions, pixels, terminators, clipping and capacity, alongside the existing
sprite suite. All four earlier native captures still pass.

The replay demonstrates vertical riding and the slice death/respawn path.
The horizontal target fixture below covers ordinary floor carrying. The standalone target
compression/spike-push regression below covers the logic; an integrated visual
replay and full desktop death fidelity remain outstanding.

## Horizontal target fixture

`horizontal-capture` is a synthetic regression test, explicitly labelled on
screen. It uses a single 32×8 platform starting at (144,116), behaviour 3,
speed 3 and bounds (64,64)–(288,184). The player starts on it at (156,93).
All input is zero, isolating platform transport from player acceleration.
It is separate from Stop and Reflect and does not represent another ported room.

The host suite compares this fixture with extracted desktop scheduling and
physics for 240 ticks on both terrain paths. The capture target regenerates
`build/amiga/horizontal-reference-trace.json`, then compares the emulator's
player position, velocity and gravity, platform position, and transport count
with the matching reference tick. This checks the captured tick, not every
target tick or the full lifecycle.

The A500 capture verifies **180 horizontal transport ticks**, with zero player
X velocity, no deaths or exits, a visible platform and three sprite channels.
It peaks at **167 PAL lines / 10.688 ms**, with no missed VBL observations and
successful return to AmigaDOS. Explicit Chip allocation is **43,534 bytes**;
non-Chip free memory is **437,064 bytes**. The original vertical replay also
still passes at 237 lines.

Just Pick Yourself Down is now exported with both checkpoints (see below).
Gantry and Dolly still needs disappearing platforms; other reviewed rooms need
conveyors or additional enemy/script support.

## Multi-checkpoint core

`checkpoints.c` adds caller-owned state for ordinary floor and ceiling
checkpoints. It preserves initial activation by saved ID, collision arming for
the next update, deactivation of other checkpoints, and floor/ceiling respawn
offsets. Activation records the player's direction at update time.

The per-entity update API lets room integration preserve the original order
among other entity updates. A reverse-order convenience pass is also available.
Activating one checkpoint does not erase other pending activations: overlapping
checkpoints can therefore save multiple times in a tick, with the last processed
one supplying the final save record. The return value counts activations so the
caller can handle sound and persistence for each event.

**32,768 ticks across 256 scenarios** match checkpoint creation, update and
collision branches extracted from the desktop source. The comparison includes
16,559 activations, 3,388 ticks with multiple saves, overlapping positions,
duplicate IDs, both orientations, saved direction and room coordinates.
Run `python3 tools/amiga/test_checkpoints.py`; `make test` includes it and
writes `build/amiga/checkpoint-test-report.json`.

Just Pick Yourself Down now uses this module through `v6_slice_step_entities`.
Its callback updates checkpoints after input and platform transport, before
player physics, then arms collisions before stuck prevention. The slice save
helper records position, gravity and direction for respawn. Earlier scenes keep
their single-checkpoint path. Disk persistence, nodeath mode and full campaign
entity/lifecycle ordering remain outside this test.

## Native room with two checkpoints

Just Pick Yourself Down exports all three original room entities: the platform
at (24,80), moving horizontally at speed 6 with default room bounds, and the
ceiling checkpoint at (64,176), ID 445550, plus the floor checkpoint at (212,192),
ID 445551. The strict exporter checks entity order, coordinates and platform
tile 159. The room starts at its ceiling checkpoint. Unsupported exits use the
existing slice checkpoint fallback.

Both checkpoint masks are drawn into the background. Save events repaint both
locations and mark both display buffers dirty, restoring the inactive checkpoint
as well as the active one. The version-5 diagnostic checkpoint field is an active
bitmask in this scene (1 for the first, 2 for the second).

The normal smoke capture peaks at **171 PAL lines / 10.944 ms**. The isolated
checkpoint replay places the player at the second checkpoint on tick 20,
changes direction on its activation tick, and requests a restart on tick 50.
It verifies the first checkpoint is white, the second is green, and respawn
returns to (208,185) with floor gravity. Host lifecycle checks also verify saved
direction. This replay peaks at **191 PAL lines / 12.224 ms**, with no missed
VBL observations and a successful return to AmigaDOS. Explicit Chip allocation
is **43,534 bytes**; non-Chip free memory is **436,136 bytes** in the replay build.

The placement replay isolates checkpoint behavior. The separate normal-input
route below verifies traversal and riding; crushing/death fidelity remains
outside both replays.

## Normal-input room traversal

`tools/amiga/pick_replay.h` records a route from the initial checkpoint to the
second checkpoint using only left/right/flip input. It activates the first save
on tick 2 and the second on **tick 124**, with **15 horizontal transport ticks**,
no deaths and no unsupported exits. It requests a restart on tick 130, then
verifies respawn at the checkpoint reached by the route. There are no player
placement edits in this replay.

`test_pick_route.py` compiles the native scene adapter for the host and checks
240 ticks with UBSan. Its first 129 movement ticks also match the extracted
desktop platform/player methods on both cached and uncached terrain. This
comparison covers movement before the restart; checkpoint branch equivalence
is covered by the separate checkpoint suite. The generated integration trace
includes the restart/respawn period.

The A500 capture independently checks the live state at **tick 126** against the
desktop movement trace and the post-respawn state at **tick 179** against the
host integration trace. Peak work is **196 PAL lines / 12.544 ms**, with no missed
VBL observations and successful AmigaDOS restoration. Explicit Chip allocation
is **43,534 bytes**, with **436,072 bytes** of non-Chip RAM free.

Run `make -C amiga_version pick-route-capture`. Outputs are under
`build/amiga-pick-route`; host traces and reports are under `build/amiga`.
These are two target-state comparisons, not a comparison of every target tick
or an independent full desktop death/respawn loop. Pink-sprite image checks now
exclude this room's pink terrain colour, so terrain cannot mask a missing
platform.

## Compression and spike-push regression

The ordinary vertical-platform code does not directly kill a player when a push
is blocked. `movingplatformfix` schedules the platform's reversal; overlap
disabling and stuck correction follow, then the damage check can start death.
The tests distinguish compression against solid terrain from being pushed into
a spike, rather than adding an unconditional crush death.

`python3 tools/amiga/test_platform_crush.py` exercises **336 synthetic fixtures**
on cached and uncached terrain. They cover upward and downward pushes, both
ordinary tilesets, four platform speeds, three horizontal offsets, a solid wall,
and six spike tiles. **1,308 live movement ticks per terrain path** match the
extracted scheduling, movement, overlap/stuck and map-damage methods.

All **48 solid-wall fixtures** schedule a reversal without damage. All **288
spike-push fixtures** first start outside damage and then trigger it through the
ordered movement/collision stages. Comparison stops at that first damage tick.

A separate host adapter runs the same fixtures through the slice lifecycle.
It checks death timer 30 on damage, frozen player position/velocity and platform/block state during
the death pause, and respawn at the saved position and gravity with zero
velocity and a life timer of 10. This covers **17,280 death-delay ticks** across
both terrain paths. These lifecycle assertions are not an independent extraction
of the desktop's full death/respawn loop.

`make test` includes the suite; detailed fixtures and their damage ticks are in
`build/amiga/crush-test-report.json`.

`make crush-capture` first reruns those source comparisons, then builds an
asset-free standalone Bartman executable and runs it in Copperline's A500 / 68000 /
OCS / 512K Chip + 512K slow profile. All **672 cached/uncached fixture runs**
complete: **19,896 simulation ticks**, including **576 respawns**. A 32-bit digest
of every tick's player, platform, collision-block and lifecycle snapshot matches
the UBSan host run (the digest is recorded in the report). Fields are folded individually, avoiding
host/68000 byte-order and structure-padding differences.

Results are written to `build/amiga-crush/crush-target-report.json`. The runner
captures RAM at 240 emulated seconds while the completed executable keeps its
record allocated. This is a logic regression, not a rendered compression replay,
a gameplay timing measurement, or an independent desktop death/respawn comparison.
Ordinary gameplay code is unchanged.

`python3 tools/amiga/test_death_lifecycle.py` independently extracts unmodified
`Game::deathsequence`, `mapclass::resetplayer(bool)` and the countdown/reset
branch in `Logic.cpp`. Starting from the damage-boundary snapshot, it compares
**576 cached/uncached spike-push cases** through **17,280 death-delay ticks**.
The death timer, life timer, death count and **all player fields** match on every
tick, including the saved-position reset. Synthetic damage-boundary states vary
held-flip, buffered-flip, tap counters and contacts. Desktop room death counts
also match the slice death count.

This exposed a same-room reset mismatch: the slice reinitialized input latches,
contacts and old positions, while `Map::resetplayer` retains them. The reset now
changes only position, velocity/acceleration, gravity and facing. A behavioral
regression holds flip across death and ten recovery ticks: it does not flip until
the button is released and pressed again. Cross-room reset behavior remains
outside this source comparison.

This test compiles the original method bodies with a small host environment.
Audio, textbox and achievement/statistics side effects are stubbed; unsupported
room changes, tower camera and special-mode operations abort. It covers ordinary
same-room deaths through respawn, not the full game loop, subsequent movement,
visibility, scripts or other modes. `make test` includes it; its source
hash and results are in `build/amiga/death-lifecycle-report.json`.
The reference now also extracts Input.cpp's locked-control branch. Flip presses
and releases update the held latch and buffer while movement/flip execution is
locked, including during death. The player reference previously omitted this
branch; it now covers it in the existing 3,000 control-lock ticks. The death
comparison exercises held, released and repeated presses across all 576 cases.
A slice regression releases during death and presses on its last tick: the buffer
survives five recovery ticks and flips on the sixth, when control returns.
The full host suite passes after this change. Traffic Jam's A500 capture still
peaks at **249 PAL lines**, with no missed VBLs and clean exit.

The death path now refreshes floor/ceiling contact counters before decrementing
the death timer, matching Logic.cpp. The reference extracts that counter-update
stage and supplies probes from the original collision methods, including the
frozen platform block and room tiles. Across 17,280 death ticks it checks **6,480
with neither contact, 8,640 with floor contact and 2,160 with ceiling contact**;
all player fields match on cached and uncached terrain. Positions and velocities
stay frozen while contact counters continue to change. Animation/visibility,
post-respawn movement and other modes remain outside this comparison.
After contact refresh, the full host suite and A500 compression regression pass.
The checkpoint-route capture now peaks at **197 PAL lines / 12.608 ms**, with no
missed VBLs, matching reference snapshots and clean AmigaDOS restoration.

After the retention fix, the full host suite, the standalone A500 compression
regression and the checkpoint-route capture pass. The route remains at **196 PAL
lines / 12.544 ms**, with zero missed VBLs and clean AmigaDOS restoration.

## Recovery movement and life timer

`python3 tools/amiga/test_recovery.py` compares **240 synthetic recovery states /
5,760 movement ticks** with extracted desktop input, `Game::lifesequence` and
player physics. Floor/ceiling spawns, held/released/repeated flip, buffered input,
directional input, saved-gravity restoration and both terrain paths are covered.
Each case runs 24 ticks, through the five-tick control lock and normal movement.
All player fields and the life timer match. These are initialized recovery
states in a static room, not a complete campaign death-to-recovery replay.

Ten restart timings during recovery add **120 death/life-timer checks**. They
exposed the slice leaving its life timer unchanged during death; it now decrements
there too and restores saved gravity while the timer is above five, as in the
ordinary desktop room path. Input gating uses the timer before decrementing.
`make test` includes this test; results and the reference source hash are in
`build/amiga/recovery-report.json`. Platforms, scripts, visibility and tower
camera delays are outside its scope. The full host suite passes. After the fix,
A500 Traffic Jam and checkpoint-route captures pass at **249** and **197 PAL
lines** respectively, with no missed VBLs and clean exits.

## Recovery on ordinary moving platforms

`python3 tools/amiga/test_platform_recovery.py` adds **480 synthetic cases /
11,520 ticks** through the slice movement callback. It compares all player and
platform fields, collision blocks, pending Y, visual contact counters and the life
timer with extracted desktop input, `Game::lifesequence`, reverse-order platform
scheduling, physics and overlap/stuck correction.

Cases cover each of the four ordinary directions, speeds 0/1/3/6, floor and
ceiling riders, held/buffered/repeated flip, cached and uncached terrain, plus
four mixed-axis actors sharing an origin. Each runs 24 ticks. A focused check
confirms horizontal carry is suppressed at life timers 9 and 8, then resumes at
7, independently of the five-tick player-control lock.

`make test` includes this UBSan host regression; its report and source hash are
in `build/amiga/platform-recovery-report.json`. Gameplay code is unchanged.
These are initialized recovery states, not complete death-to-recovery or target
replays. Checkpoint entities, rendering, conveyors and full campaign behavior
remain outside the comparison.

## Rendered spike-push replay

`make crush-replay-capture` builds a separate `V6_CRUSH_REPLAY` scene using the
upward spike-push geometry from the compression suite: player (108,70), platform
(104,93) moving upward at 3 pixels/tick, and spike tile 6 across row 8. It is
labelled **SYNTHETIC SPIKE PUSH TEST**, not exported campaign content. No player
placement or restart is injected after initialization.

The first live update triggers damage. A RAM snapshot during death matches the
host slice trace at **tick 17**, with one platform update and its Y frozen at 90.
The main snapshot matches at **tick 180**, after one death and one respawn. Both
captures verify visible player/platform sprites; screenshots are `death.png` and
`prototype.png` in `build/amiga-crush-replay/`. The report is `smoke-report.json`.
The early capture requires a completed render tick, avoiding mixed diagnostic
fields from an update in progress.

Peak work is **139 PAL lines / 8.896 ms**, with no missed VBLs, three hardware
sprite channels, 43,534 explicitly allocated Chip bytes and clean AmigaDOS exit.
The target compares selected snapshots against a 240-tick native host integration
trace, not every target tick against the complete desktop loop. The command first
reruns the source-derived compression suite. Normal gameplay scenes are unchanged.

## Disappearing-platform lifecycle core

`disappearing.c` implements the ordinary six-state platform lifecycle. Collision
arms the platform; its next update starts a 12-tick collapse and emits the sound
event. Animation advances every third tick, then the platform hides and requests
collision-block disabling. Death finishes an in-progress collapse and arms
recharge. Live updates recreate the block and reverse the animation; contact can
retrigger it during recharge, matching the original `onentity` behavior.

`python3 tools/amiga/test_disappearing.py` compares **40,960 updates** against
unmodified Entity.cpp update/collision branches and Logic.cpp death handling.
All six states and the sound/disable/create events are exercised. The UBSan test
is included in `make test`; its report is `build/amiga/disappearing-report.json`.
The module also compiles for the 68000 without runtime helper dependencies.

`v6_disappearing_update` now applies lifecycle and collision-bank changes
together. `v6_blocks_create_solid` reuses the first fully disabled slot or appends,
clearing its previous type/trigger metadata. Collapse disables all blocks at the
platform origin. If recharge cannot allocate a slot, the update returns
`V6_DISAPPEAR_FULL` with platform state and bank unchanged, allowing a retry.
The caller must synchronize `V6Room.block_count` with the bank count.

An additional **30,720 integrated updates** compare platform state, events, bank
count and every slot against the source's solid allocation, slot clearing and
disable branches. Tests cover shared origins, unrelated disabled slots and
appending; separate checks cover full capacity, retry and partly empty rectangles
that must not be reused. The 68000 module references only the native block helpers.

The native replays below connect the core to animation and sound, including
an original campaign room. Collision geometry is 32x10 at Y-1; the solid block
is 32x8. Room tile/cache mutation and supercrewmates are not covered by this
component test.

`v6_disappearing_death_room` adds the campaign exception for room (111,107).
It returns `V6_DISAPPEAR_DEATH_TILE` only when entering the death update in
state 3 and outside custom mode. The caller must set tile (18,9) to 59 and
refresh terrain/render caches. Finishing a state-2 collapse during death does
not request the patch, nor do subsequent death ticks. The source-derived test
checks 1,296 combinations of room coordinates, custom mode, state and life,
plus a repeated death tick for each. The new 68000 function introduces no runtime
helper dependency. This room is not exported yet; the API does not itself
change tiles or apply collision-bank events.

`v6_terrain_set_tile` provides the tile/cache mutation step: it edits a mutable
40x30 tile buffer and rebuilds collision classifications, including duplicated
border cells and the directional-tile flag. It returns 1 for a changed tile
(the caller must redraw), 0 for a no-op and -1 for invalid coordinates/format.
Use the same buffer and format as the room and an already initialized cache.
`make test-tile-edit` checks 64,800 edits across all supported tilesets/heights,
including removal of directional tiles, plus the death-event-to-solid-tile
path and rejected edits. This runs with UBSan and is included in `make test`.
The 68000 object has no undefined runtime helpers. This is a full cache rebuild;
its cost during live Amiga gameplay has not been measured, and the special
room still needs scene integration and a redraw of its background buffers.

`v6_disappearing_update_room` combines the room context with the existing
collision-bank update. It returns the tile request alongside block/sound events,
so callers need not run the death lifecycle twice. Another 1,296 source-derived
checks compare state, events and collision slots, and two capacity tests verify
unchanged state on failure and successful retry. The tile-edit test now follows
the combined path through death, tile-59 collision refresh, repeated death and
live recharge, checking that the platform block returns while the tile remains
solid. These are host component checks, not a native special-room replay.

“Prize for the Reckless” (111,107) also contains a behaviour-15 platform and a
trinket, and its four wide platforms plus player exceed eight sprite channels.
Those mechanics and sprite scheduling must be supported before exporting the
whole room; it is not currently a playable scene.

## Native disappearing-platform replay

`make disappearing-capture` builds a separate `V6_DISAPPEAR_REPLAY` scene. The
player is initialized on a platform at (104,93), above a spike strip. It collapses,
the player falls and dies, and respawn places the player at a safe checkpoint
ledge while the platform recharges. Initial placement is deliberate fixture
setup; no movement input or restart is injected after initialization.

The scene uses the original tiles 2–6, repeated across a 32x8 hardware sprite,
and the original `vanish.wav` resampled for the existing Paula channel.
`jump.wav` and `vanish.wav` now occupy separate sample regions; flips select
jump and collapses select vanish. The channel remains monophonic, with a collapse
cue taking precedence if both events occur in one tick. The capture checks a cue
peak above twice the later background-audio peak; it does not establish exact
audio waveform fidelity.

A 240-tick host trace compiles the native scene adapter and visits all six states.
A500 snapshots match at **tick 9** (collapse), **29** (hidden), **54** (recharge)
and **180** (fully recharged after one death/respawn). Screenshots verify the
platform is visible during collapse/recharge and absent while hidden. Output is
in `build/amiga-disappearing/`, including `collapse.png`, `hidden.png`,
`recharge.png`, `prototype.png`, `prototype.wav` and `smoke-report.json`.
Diagnostic actor fields contain lifecycle state/frame, live updates and collapse
count in this build.

Peak work is **153 PAL lines / 9.792 ms**, with no missed VBLs, at most three
sprite channels, **45,384 explicitly allocated Chip bytes** and clean AmigaDOS
exit. This is an automated synthetic replay, not a playable campaign room or
full desktop-loop comparison. Retriggering during recharge is covered by the
host core tests; the native fixture respawns away so one recharge completes.

The native adapter now keeps separate lifecycle and animation state for each
platform, uses room-provided positions, and updates entities in reverse order.
`tools/amiga/test_disappearing_scene.py` exercises three independent contacts
and 32 simultaneous collapse/death/recharge cycles with UBSan, checking that
restored collision blocks reuse free slots independently of entity indices.
A further 16 recharge retriggers reach walking frame 48. The converter now
exports compact eight-byte tile masks from base tile 2 to the atlas end
(9,584 bytes in ordinary memory for the supplied assets). The renderer expands
each selected mask into a repeated 32x8 sprite; it no longer rejects frames
above four. Out-of-atlas indices draw blank defensively. The native capture
still covers the ordinary five-frame cycle, not a retrigger traversal.
These are host adapter checks with empty terrain, not a three-platform campaign
replay. The existing single-platform Copperline fixture remains the target test.

## What Lies Beneath?

`make -C amiga_version beneath-run` launches the original room (116,110), with
normal joystick controls, flip, restart and exit. The strict exporter accepts
its original checkpoint and all three disappearing platforms, using base tile
707. No synthetic terrain, player placement or forced input is applied.
The room uses seven hardware sprite channels and both jump/vanish cues.

`make -C amiga_version beneath-capture` checks the idle checkpoint spawn at
(60,145), all three visible platforms, no deaths/exits, and clean AmigaDOS
restoration on the minimum A500 profile. Peak work is **206 PAL lines / 13.184 ms**,
with **45,384 allocated Chip bytes** and no missed VBLs. Output is in
`build/amiga-beneath/`, including `prototype.png` and `smoke-report.json`.
Neighbouring rooms are not included.

`make -C amiga_version beneath-route-capture` adds a separate deterministic
normal-input build: move right for 35 ticks and flip on ticks 5, 13 and 27,
then release the controls. The player reaches the first platform from below,
flips down onto the lower platform, then up onto the right platform. Each
collapses; ceiling spikes cause one death, followed by checkpoint respawn.
No forced placement or restart is used. The 240-tick UBSan host trace visits all
six states for each platform, verifies three collapses and three flips, and
checks that recharge restores exactly one solid block at each original position.
It is included in `make test`.

Target snapshots match the host at ticks **17** (collapse), **61** (all hidden),
**85** (all recharging) and **170** (respawned). In this replay only, diagnostic
actor state/frame fields contain three four-bit slots, exposing all platforms
rather than only the first. Phase reports decode these into arrays. Screenshots
check that all pink platforms disappear and return. Peak work is **214 PAL
lines / 13.696 ms**, with no missed frames, seven sprite channels, 45,384 allocated
Chip bytes and clean exit. Artifacts are in `build/amiga-beneath-route/`.
This compares the native adapter across host and 68000, not an independent full
desktop game loop. Campaign recharge retriggers still need traversal coverage; the separate
fixture below covers them on target with deliberate checkpoint placement.

## Recharge-contact fixture

`make -C amiga_version retrigger-capture` builds a separate synthetic scene
with its saved checkpoint directly on the disappearing platform. Following
spike death, respawn contacts the platform during recharge, triggering another
collapse without input or subsequent forced placement. State 5 can become
state 1 in the same live tick because contact follows the recharge update.

The 240-tick host trace runs with UBSan and checks repeated collapses/respawns,
no exits and frames beyond four; it is included in `make test`. Target state
matches the trace at tick **61**, with walking frame **5** visibly rendered,
and tick **160**, with frame **10**, three deaths and three respawns. Peak work
is **131 PAL lines / 8.384 ms**, with no missed frames, 45,384 allocated Chip
bytes, three sprite channels and clean exit. Artifacts, including `extended.png`,
are in `build/amiga-retrigger/`. This tests the native adapter and renderer;
it is not a campaign route or independent desktop-loop comparison.

## Waiting moving-platform behaviours

`platform_gate.c` implements the behaviour-update stage for rules 14 and 15.
An idle platform waits for a hidden disappearing platform at X-32 or X+32,
respectively; Y does not participate. Activation sets its initial velocity;
subsequent updates preserve the source's direction changes and ordered boundary
clamping. Callers supply disappearing states in entity order and run this stage
before movement, including when creating an entity.

`test_platform_gate.py` compares 16,896 cases with the original recursive
Entity.cpp branches and Ent.cpp `outside()`, covering both behaviours, states
0–3, integer speeds -16–16, nearby/exact trigger positions, multiple matches
and boundary crossings. Additional checks cover empty trigger lists and
unsupported behaviours. The core runs with UBSan and compiles for the 68000
without runtime helpers. Creation-time tests cover idle and already-hidden
triggers and rejection of invalid parameters without modifying the platform.

`v6_platform_gate_init` now initializes a waiting platform and applies its
creation-time trigger. `v6_platform_gate_transport` integrates behaviours 14/15
with ordinary platforms: reverse-order passes, map collision, block relocation,
vertical pushing and horizontal carrying. Contact lookup accepts waiting
platforms, including zero-speed contact and the existing life-timer lock.
Movement is shared with ordinary enemies/platforms through `v6_enemy_move`;
behaviour updates remain separate so an idle gate cannot start prematurely.
Supply disappearing states as they stand at this point in the entity loop.

`test_platform_loop.py --waiting` compares **23,520 ordered ticks** with the
desktop source, repeated with cached collision data. It checks player fields,
platform fields, every block, pending Y and visual contacts. Mixed rooms cover
both update passes and positive, negative and zero speeds. Dedicated floor and
ceiling rides remain stationary for 20 ticks then carry on every later tick.
These tests are included in `make test`.

`make -C amiga_version waiting-capture` runs a synthetic A500 fixture using the
integrated API. An external trigger becomes hidden after 20 ticks; it is not a
rendered disappearing entity. Source-derived transport snapshots match at ticks
**11** (waiting), **41** (carrying) and **179** (later ride), with no player input.
Peak work is **179 PAL lines / 11.456 ms**, with no missed frames, three sprite
channels, 43,534 allocated Chip bytes and clean exit. Screenshots and report are
in `build/amiga-waiting/`. This completes bounded movement/carry integration;
it does not yet export the special campaign room or implement its trinket and
sprite scheduling requirements.

## Next implementation step

Prioritize native tower row streaming and scrolling. Music uses the working
Lightspeedplayer/tracker plan; benchmark it when a representative module is ready.
Further campaign expansion still needs trinkets, sprite scheduling and conveyors,
plus full desktop-loop comparisons. Sprite
multiplexing and a blitter fallback remain necessary for rooms that exceed
the eight-channel budget. Expand the strict room-setup export and
add full desktop-loop traces covering entity/update ordering. Target replays combine milestone assertions with selected state comparisons;
they do not yet compare every target state field on every tick.
Tower row streaming and the music storage/playback experiment remain separate
feasibility gates.

The 252,832-byte simple-RLE pack exceeds the plan's provisional 128 KiB combined
content/cache budget before scripts. Evaluate stronger compression and regional
loading; do not assume the entire campaign pack can stay resident unchanged.

The lifecycle checks pass with UBSan. An AddressSanitizer build stalled on this
host and was interrupted; ASan validation is not claimed.

Sprite register encoding follows the [Commodore hardware manual](https://www.ikod.se/wp-content/uploads/2020/08/Amiga_Hardware_Reference_Manual_3rd_Edition.pdf).

## Tower and music feasibility

`make -C amiga_version feasibility-probe` extracts all four literal tower maps,
packs independently decodable rows with duplicate sharing, and validates them
with the actual C room decoder. It also exercises a bounded decoded-row cache
through forward/reverse scrolling, wraps and jumps. Private generated packs and
`tower-feasibility.json` are in `build/amiga-feasibility/`.

| Map | Raw 16-bit tiles | Packed rows and index |
|---|---:|---:|
| Main tower (700 rows) | 56,000 bytes | 18,312 bytes |
| Background (120 rows) | 9,600 bytes | 7,260 bytes |
| Mini-tower 1 | 8,000 bytes | 2,776 bytes |
| Mini-tower 2 | 8,000 bytes | 3,238 bytes |

A 32-row tile cache requires 2,560 bytes. A proposed 320x256 two-plane display
ring would require 20,480 Chip bytes, or 40,960 for two buffers, before HUD,
sprites and other DMA data. These are layout budgets, not implemented scrolling.
The probe's normal camera steps up to 16 pixels need at most two row decodes;
jumps require refilling the visible rows. It does not yet measure 68000 row
rendering, Copper wrap, parallax, camera gameplay or contention with music.

Music assumes **Lightspeedplayer with tracker modules produced by a musician**.
PCM streaming is not the current plan. The optional `probe_feasibility.py --music`
retains an offline PCM comparison for reference; it is not required for tower
work. Player/module memory, worst-case replay time and SFX channel sharing need
measurement once a representative tracker module is supplied. No tracker format
or Lightspeedplayer resource budget has yet been verified.

The native `tower_stream.c` reader now validates V6TR headers and directory spans
and decodes rows on demand through a fixed 32-slot cache. Logical row numbers
select slots; wrapped source rows select data, avoiding cache aliasing when the
visible window crosses a map whose height is not a multiple of 32. Invalid
packets cannot leave a valid cached row. Packed buffers must remain immutable
and resident; this is memory streaming, not disk I/O.

`test_tower_stream.py` compares 1,011,840 C-cache queries with all four original
maps, tests malformed headers/directories/packets, cache hits, signed row limits
and additional map heights. The 68000 object depends only on the existing row
decoder, with no runtime division helper. The cache stores 2,560 tile bytes plus
metadata. Its pointer views are temporary until a colliding logical row replaces
the slot. `make test` includes these checks. It is not yet connected to Copper
scrolling or row drawing; native display timing remains the next feasibility gate.

`tower_draw.c` now provides the planar row-writing stage: 40 atlas tiles become
one 8-pixel-high row in a 320x256 two-plane ring. Each display buffer has its own
logical-row tags, so alternating buffers update their own missing rows. Preparing
31 rows covers a 240-pixel viewport plus fine-scroll coverage. The caller must
write an inactive buffer and publish it only on success; Copper pointer changes
and wrap splitting remain separate. Reset display tags whenever the stream or
atlas changes. Invalid tile IDs are rejected before any part of that row is
written; a failed multi-row preparation may retain earlier completed writes.

`test_tower_draw.py` checks **2,600 alternating-buffer frames / 80,600 rows**
against a distinct-pattern two-plane atlas and the original tower maps. It tests
strides, both planes, forward/reverse/map/cache wrap, unchanged-window zero work,
guard bytes and invalid IDs/coordinates. Initial preparation draws 31 rows;
subsequent one-row-per-frame camera steps need at most two rows per alternating
buffer. Each ring is 20,480 bytes. UBSan tests and the 68000 build pass, with no
new runtime helper dependency. This is not yet a hardware scrolling demo: actual
tower graphics conversion, Copper wrap and DMA-contended timing remain next.

`make -C amiga_version tower-assets` converts colour bank 0 of the user's
`graphics/tiles3.png` into a 480-byte planar atlas and four OCS palette entries.
The source renderer selects tiles as `tile + bank*30`; the converter supports
`--bank` to select another bank. Alpha is composited onto black, with the most
frequent three nonblack OCS colours and nearest-colour mapping. Bank 0 has seven
source OCS colours, so this is a colour reduction rather than exact source art.

The same command validates the actual C row renderer against converted source
pixels: **691,200 pixel checks** at camera positions 0, 1, 7, 8, 249, 255, 256,
5599 and 5600. It uses a separate Python packet decoder for expected tile IDs.
Generated private output includes `tower_assets.h`, `tower_tiles.bin`,
`tower-assets.json` and PNG previews at camera positions 0, 255 and 5599, all in
`build/amiga-feasibility/`. These previews are host-generated, not emulator
captures; no parallax, bank cycling or gameplay is included. The next step is
Copper publication and vertical ring wrap on the A500, followed by timing with
row refill and graphics DMA active.

`tower_copper.c` builds a pointer-only Copper segment for the proposed ring:
it waits at PAL line 44, sets both plane pointers at the selected pixel offset,
and resets them after the last fetched ring scanline when the visible window
crosses the ring end. Resets below line 255 include the Copper vertical-counter
barrier. At offsets 0–16 no reset is needed within the 240-line viewport.
The builder emits at most 24 words (48 bytes), including its end marker.

`make test-tower-copper` checks all 256 offsets at four base addresses,
245,760 modeled visible scanlines, the line-255 boundary, list capacity and
rejected inputs. UBSan and the 68000 build pass with no runtime dependencies.
This is a structural address/wait test, not a cycle-accurate Copper simulation.
The standalone tower probe now installs this segment; room gameplay is unchanged.

Run `make -C amiga_version tower-capture` from the repository root to build and
capture the separate `build/amiga-tower/tower.adf`. `tower-probe` builds only.
The probe moves one pixel per PAL frame between logical camera positions
5344 and 5856, reversing at each endpoint, using two Chip RAM rings and two lists; it prepares the inactive pair and publishes the list pointer at
line 311. Left mouse exits and restores the OS. Original map and converted tile
bytes are generated into ignored build output from the user's assets.

The Copperline A500/512K Chip + 512K slow capture now checks two forward
source-map seam crossings and one reverse crossing in 1,564 PAL frames, with
zero missed frames and at most one row redrawn per update. Peak incremental
work is 136 scanlines (8.70 ms), excluding initial ring preparation; allocated Chip RAM
is 41,216 bytes. The screenshot was visually inspected and the saved-state
exit check returns to AmigaDOS with diagnostics status 2. Reports, screenshots
and logs are in `build/amiga-tower`. These are emulator results, not measurements
on physical hardware. Logical camera coordinates remain continuous through source row 700: the
stream wraps source rows independently of the physical ring slots, avoiding a
full redraw at the map boundary. This bounded route tests the seam in both
directions, not traversal of all 700 rows. Negative camera positions, parallax,
tower gameplay and concurrent tracker playback remain unverified.

`make -C amiga_version tower-pixel-test` additionally builds fixed-camera probes
at 0, 16, 17, 52, 53, 255, 5599 and 5600. All eight native Copperline captures
pass exact RGB comparisons at every logical pixel centre: 614,400 pixels total.
This covers the no-reset/reset boundary, the PAL line-255 wait boundary, the
last ring scanline, and the source-map seam. The reference reads the desktop
map directly and uses the converted atlas; it does not call the C decoder,
cache, renderer or Copper builder. Results are in `build/amiga-tower-pixels`.
The sampler explicitly targets the installed emulator's 716x540 presentation,
checking all 320x240 logical pixels while avoiding resampling blends between
pixels. This verifies fixed-camera display output, not tearing during motion,
all 256 native offsets, or physical Amiga timing.

Tower parallax direction: use OCS dual playfield, following the user's correction.
Two total bitplanes give one plane per layer: foreground COLOR01, background
COLOR09, and COLOR00 where both are transparent. The foreground must use a
one-colour silhouette; its current three-colour shading cannot be retained in
that layout. Three total planes could give a two-plane foreground and one-plane
background; four would give two planes to each. Test the two-plane arrangement
first to preserve the current DMA budget. The Copper builder needs independent
initial pointers and independently ordered wrap resets for the two layers.
The foreground gets priority; the background camera follows the desktop
`mapclass::setbgobjlerp` half-speed position. Native dual-playfield integration
and visual assessment are still pending.

The work started before that correction remains as a software reference:
`tower_masks.bin` contains 240 bytes of foreground opacity (tile zero is skipped,
matching the desktop renderer). Partial-alpha input is explicitly rejected.
`tower_compose.c` combines independently offset two-plane rings using a mask
ring, without changing the running display. `make test-tower-compose` passes
1,228,800 pixel comparisons over 16 camera positions using the desktop maps,
plus source-alpha and invalid-input checks. This full-viewport compositor is
not the planned native parallax path and has not been timed on the Amiga.

Selected tower layout (superseding the two-plane trial): three total bitplanes,
with planes 1/3 for foreground and plane 2 for parallax. Two buffered layer sets
cost 61,440 bytes before lists/sprites. Native integration and timing are pending.

`tower_copper.c::v6_tower_dual_copper` now builds the three-plane pointer segment:
foreground BPL1/BPL3, background BPL2, independently ordered ring-wrap events,
coincident resets, and a single PAL line-255 barrier. It emits at most 34 words
(68 bytes). `make test-tower-dual-copper` checks every one of the 65,536 offset
pairs and 47,185,920 modeled plane addresses under UBSan; the 68000 build passes.
This is a structural test, not a DMA timing simulation. The existing native
probe still uses its two-plane single-playfield renderer. Next is integrating
the background ring, three-plane mode and palettes, then native captures/timing.


The standalone tower probe now runs the selected three-plane dual playfield.
The foreground uses BPL1/BPL3 and its existing three nonzero colours; BPL2
uses a one-bit background ring at half the positive logical camera position.
Foreground palette index zero is transparent, so any opaque source pixels
previously quantized to zero also reveal the background. Background source OCS
channel sums >=3 become its single dark colour (COLOR09=0x223); darker pixels
become transparent. This is an explicit visual reduction, not full source-colour
fidelity. Foreground priority is enabled. Both rings and lists are double buffered.

The native moving test passes with 61,696 bytes allocated in Chip RAM, zero
missed frames, at most two total rows redrawn per update, and a peak of 273 PAL
scanlines (17.47 ms). It records two forward map-seam crossings and one reverse,
and returns to AmigaDOS on mouse exit. Initial fills are excluded from the work
peak. This leaves little room in a PAL frame for additional game work; no player,
sprite DMA, SFX or tracker replay runs in this probe yet.

The eight fixed-camera capture checks now compare the three-plane display,
including foreground priority and visible background pixels, against independently
indexed desktop maps and converted atlases. The moving capture still does not
prove absence of tearing on every frame. Negative-camera semantics, colour
cycling, full tower traversal and physical-hardware timing remain open.

The row-copy loop is now unrolled into eight constant-displacement byte stores
per tile column, shared by the foreground and background renderers. On the same
native moving route, peak work drops from 273 to 134 PAL scanlines (17.47 to
8.58 ms, about 51% lower), with zero missed frames and clean OS restoration.
Chip allocation remains 61,696 bytes; initial fills remain excluded. Host row
checks pass for 2,600 frames / 80,600 rows. The fixed-camera native pixel checks
are repeated for this change. This improves this probe's measured headroom;
it does not establish the combined gameplay/music budget or worst-case cost
for larger camera steps across the entire tower.

`make -C amiga_version tower-step-measure` builds synthetic 4-, 8- and 16-pixel
per-frame routes, captures each, and records overruns rather than asserting
that every stress load fits. Each route reverses between 5344 and 5856 and
crosses the source seam in both directions. Results on the same A500 profile:

| Camera step | Peak work (PAL lines) | Approx. ms | Max rows redrawn | Missed frames |
| --- | ---: | ---: | ---: | ---: |
| 4 | 134 | 8.58 | 2 | 0 |
| 8 | 184 | 11.78 | 3 | 0 |
| 16 | 320 | 20.48 | 6 | 555 |

All three exit-restoration checks passed. Reports are under
`build/amiga-tower-step{4,8,16}` and `build/amiga-tower/step-measurements.json`.
The 16-pixel result is a measured failure of the one-frame budget, not a passing
performance test. Counts apply to these captures, not a universal drop rate.
The desktop Logic.cpp contains 8- and 12-pixel tower camera moves; this synthetic
per-video-frame load is not yet the desktop camera controller or its logic
cadence. Test the actual controller and larger camera changes before considering
the renderer's scheduling complete. Moving-frame pixel integrity is still not
checked by this measurement harness.

Large-step row reuse now copies already-rendered rows from the other buffer
with the blitter, instead of drawing those rows from the atlas a second time.
Source cache tags must match the requested logical row; only the inactive ring
is written. Each blit finishes before the destination tag is set and before CPU
rendering or list publication. Reuse is attempted only when that buffer's camera
has moved more than eight pixels; smaller changes retain direct rendering.
The shared tile atlas and map must remain unchanged for these tags to be valid.

On the same 4/8/16-pixel stress routes, peak work is now 135/166/236 PAL lines
(8.64/10.62/15.10 ms), with zero missed frames and successful restoration in
all three runs. The 16-pixel run reaches 24 forward and 24 reverse map-seam
crossings; it draws at most three rows and copies at most three per update.
Chip allocation stays 61,696 bytes. Diagnostic version 3 adds `max_copied`;
`max_rows` counts atlas-drawn rows only. This resolves the measured 16-pixel
route overrun, not arbitrary jumps or a combined gameplay/music workload.

`make -C amiga_version tower-full-measure` now traverses logical cameras 0..5856
and back at 12 and 16 pixels per video frame. This covers the complete 700-row
source map, its seam, and repeated background wraps. Endpoints clamp safely
when a step does not divide a route's length. Diagnostic version 4 records the
compiled step, route bounds and reached bounds; the runner verifies the step
and requires both endpoints on full-map runs.

The full-map 12-pixel run peaks at 235 PAL lines (15.04 ms); the 16-pixel run
peaks at 242 (15.49 ms). Both have zero missed frames, at most three atlas-drawn
and three copied rows per update, unchanged 61,696-byte Chip allocation and
successful OS restoration. Reports are in `build/amiga-tower-full12`,
`build/amiga-tower-full16` and `build/amiga-tower/full-measurements.json`.
These are timing/route checks, not full-map pixel comparisons. Although 12 pixels
is a desktop camera-move magnitude, the actual camera state machine, 34 ms logic
cadence and interpolation are not reproduced. Gameplay, sprites, colour cycling,
negative positions, recovery jumps and tracker playback remain separate work.

`tower_camera.c` now ports the early camera phase from desktop Logic.cpp:
old-position/spike snapshots, mode-0 startup, two-pixel normal movement,
stopped/damage holds, recovery seek setup and ten-step seek, then main/mini-tower
bounds. It deliberately excludes subsequent death/respawn mode changes and
player-edge corrections. Callers must supply bounded tower coordinates as
specified in the header. It is not wired into the native probe yet.

`make test-tower-camera` compares 72,000 ticks in multi-tick traces against the
corresponding desktop source block compiled as a reference. It covers both
scroll directions, moving targets, missing-player fallback, stop/resume and
main/mini bounds under UBSan. The 68000 object builds without runtime helpers.
Actual 34 ms scheduling, interpolation and integration with player/recovery
remain to be implemented; the native timing tests still use synthetic routes.

The separate `v6_tower_camera_edges` helper now ports the late player-edge and
spike-height phase. In normal play, relative y <=0 or >=208 requests deathseq=30.
Only invincibility enables the 2/8/12-pixel camera corrections and background
redraw request. Spike heights then update from the corrected relative position;
nonzero lifeseq suppresses this phase. This ordering is important: the helper
must run in the desktop's late gameplay phase, not folded into the early camera
tick. Bounds are not reapplied until the next early tick.

`make test-tower-edges` passes 20,480 boundary cases against the extracted desktop
block, including invincibility, missing players, both directions, life-sequence
gating and spike limits. The existing 72,000 early-phase comparisons still pass;
the 68000 object has no runtime dependencies. These helpers are not yet wired
into the native probe. Death/respawn recovery transitions, tick scheduling and
player collision integration remain open.

Camera-side recovery gating is now available through `v6_tower_camera_recover`,
called after the early camera tick. With positive lifeseq, damage mode enters
seek setup and resets the resume delay. The lifecycle callback runs only when
seek frames and the delay permit it; a callback result of zero resumes normal
scrolling. The caller retains ownership of player lifecycle state. Separately,
`v6_tower_camera_death` applies the later death-phase camera freeze and colour
superstate, including overriding a recovery transition in the same tick.

`make test-tower-camera-recovery` passes 5,760 cases against extracted desktop
recovery/death camera blocks, checking callback count, return handling, seek and
delay gates, and ordering. Its lifecycle callback is a controlled stub: this
does not yet test real respawn/player integration. The 72,000 early-camera and
20,480 late-edge checks still pass, and the 68000 object has no runtime helpers.
Native scheduling, player integration and colour rendering remain outstanding.

`make -C amiga_version tower-controller-capture` now runs the actual early-camera
helper in a separate native probe variant. It starts in mode 0, then descends
normally by two pixels per 34 ms logic tick. The PAL accumulator uses the same
19,968-us-per-frame convention as the room prototype; camera positions are held
between ticks (no interpolation yet). The synthetic stress variants remain
available separately.

Diagnostic version 5 adds logic ticks, accounted video frames and remaining
microseconds. The capture checks the exact accumulator identity and expected
camera position. The first run accounts for 1,522 video frames, 893 logic ticks
and 29,296 us remainder, reaching camera 1784. Peak work is 137 PAL lines
(8.77 ms), no frames are missed, and exit restores AmigaDOS. Chip allocation is
unchanged. The standard one-pixel stress capture is also rerun after integration.
This native test does not yet exercise player physics, the late edge phase,
recovery callbacks, interpolation, colour cycling or music, and the frame-time
constant is an accounting convention rather than a wall-clock timer measurement.

`make -C amiga_version tower-recovery-capture` exercises camera death/recovery
natively at the same 34 ms cadence. The scripted fixture requests death for ticks
60..69, starts a five-update lifecycle at tick 70, and supplies a fixed player
y=300 as the seek target. It invokes early camera update, recovery gating and
then the death override in desktop order. The lifecycle callback only decrements
a fixture counter; no player is respawned or drawn.

Diagnostic version 6 adds camera mode and recovery state. The captured final
state is checked against a replay of the extracted desktop early/recovery/death
blocks. At 893 ticks it reaches camera 1798, mode 1, five lifecycle calls and
zero remaining life/delay/seek frames. Peak work is 138 PAL lines (8.83 ms),
with no missed frames, unchanged Chip allocation and successful exit restoration.
This is final-state validation of one scripted recovery, not per-tick native
trace equivalence or integration of player physics, collision, sprites or music.

The recovery-only build now records all ten camera fields plus lifecycle,
resume delay and callback count for its first 128 logic ticks. Each complete
record is published through a count field in a 3,344-byte test-only trace outside
the Chip allocation. The capture compares every recorded field on every tick
against replayed desktop source blocks, then checks the later aggregate state.
All 128 records (1,664 field comparisons) pass, covering startup, death hold,
seek setup/movement, resume delay and all five lifecycle callbacks.

The instrumented run reaches tick 884/camera 1780, peaks at 139 PAL scanlines
(8.90 ms), misses no frames and restores the OS. The controller diagnostic camera
now reports logical position immediately after the tick phase, rather than
waiting for display publication; this avoids comparing a new tick count with
the previous displayed camera. Visited bounds still describe published frames.
The trace is bounded and fixture-specific; player lifecycle remains a stub.

The recovery probe now uses `V6TowerSession`, which owns a real `V6Player`,
checkpoint values, movement state, death/life timers, visibility and camera.
The old decrement-only lifecycle stub is removed. A requested death runs for
30 ticks, then restores the same-tower checkpoint position, saved gravity and
facing, clears velocities/acceleration and pending movement, and starts the
10-step life sequence. Old positions and input/contact state are retained.
Camera seeking/resume delay gates the real lifecycle callback; its visibility
and gravity rules follow `Game::lifesequence` (including no-flashing handling).
The session returns whether the death branch consumed the tick so a caller can
avoid running live movement on the respawn tick.

The native test displaces the player from saved (144,300), requests death at
tick 60, and verifies the actual checkpoint reset and all ten lifecycle calls.
Trace version 2 records 128 ticks of camera/lifecycle and player state (25 fields
per tick; 9,488 bytes outside Chip RAM). Camera and visibility updates are checked
against compiled desktop source blocks; reset position/velocity/facing/gravity,
old-position retention and death/respawn counts are checked against the expected
same-tower checkpoint contract. All 3,200 field comparisons pass. The run records
one respawn, peaks at 140 PAL scanlines (8.96 ms), misses no frames and restores
the OS. Chip allocation remains 61,696 bytes.

This integrates actual player respawn state, but the death request is scripted:
this probe still does not run live player physics, collision or player sprite
rendering. Cross-room checkpoint loads, scripts, statistics, death animation
and full entity-list rebuilding remain outside this same-tower lifecycle.

## Live tower player slice

`make -C amiga_version tower-play-run` builds and runs a separate PAL A500 tower
slice. Use joystick left/right and fire to flip; left mouse exits. It starts
at the main tower's original checkpoint (144,1824), with an ascending camera.
The player uses streamed world-coordinate collision, full-tile tower spike
checks, a hardware sprite and the existing death/checkpoint recovery session.
The standalone synthetic scrolling and scripted recovery probes remain separate.

- `make -C amiga_version test-tower-player`: 25,728 extracted-desktop movement
  ticks and 10,800 spike comparisons over the main and both mini-tower maps.
- `make -C amiga_version tower-play-capture`: normal-input native damage/recovery
  replay; 128 ticks × 25 camera/player fields checked against host integration,
  visible player capture and clean OS restoration.

The replay measures 272 PAL lines (17.408 ms), zero missed frames and 64,128
explicit Chip bytes, including sprites and lists. Initial ring fills are
excluded. It fits the video frame but misses the 20% headroom target. Results
are under `build/amiga-tower-play-replay/capture.json`. The first 128 ticks are
instrumented in both player builds. The replay uses ten deaths/nine respawns;
this is checkpoint-area coverage, not a full tower route or full desktop-loop
comparison. Active checkpoint entities, horizontal gameplay wrapping/exits,
trinkets, scripts, exact animation ordering, interpolation, cycling colours and
audio remain pending. Music/SFX must still be measured with gameplay.

The latest renderer update supersedes the 272-line figure above. The same
player replay now peaks at **242 PAL lines / 15.488 ms**, meeting the unchanged
250-line headroom gate with zero misses and the same Chip allocation. The
capture command now enforces that gate. `capture.json` also splits logic and
rendering work. Completed 31-row cache windows let the renderer and peer-row
copy path inspect only newly exposed rows; a failed prepare clears that window
promise. Reset caches after stream/atlas changes or external ring/tag writes.
Host checks include large/signed-limit jumps and partial failure/retry on both
layer formats; the eight native fixed-camera pixel captures still pass.

The full-map synthetic 12/16-pixel stress routes also pass after this update:
196/204 PAL lines, zero misses, both endpoints and clean exit. They continue
to measure scrolling without player gameplay or audio.

## Tower checkpoints and horizontal boundaries

`make -C amiga_version tower-world-run` builds the checkpoint-enabled main-tower
slice. Joystick left/right moves, fire flips, and left mouse exits. All 18
original checkpoints are present; touching one saves it on the next logic
tick and changes its sprite to green. Death restores the current checkpoint.
The starting ceiling checkpoint at (144,1824) saves (140,1822), gravity 1.

- `test-tower-world`: extracted desktop boundaries, normal-input second
  checkpoint route, recovery and cached masks through 32 checkpoints.
- `tower-world-capture`: native second-checkpoint route and natural recovery;
  first 128 ticks × 37 fields match host integration, and eight later respawns
  use the new save at (220,1641). No forced deaths or route placements.
- `tower-wrap-capture`: ordinary input crosses both horizontal wrap boundaries.
- `test-tower-pairs` and `tower-paired-pixel-test`: paired tile rendering versus
  source maps and native fixed-camera pixel captures.

The checkpoint replay passes the 250-line gate at **244 PAL lines / 15.616 ms**,
zero misses, 64,128 explicit Chip bytes, and clean OS restoration. Its report
is `build/amiga-tower-world-replay/capture.json`. The paired renderer uses
6,304 additional ordinary-memory bytes for offline tile-pair tables/atlases.
It validates the whole immutable map before the measured loop; revalidate
after reopening/changing the map or tables and reset rendering caches.
Optional batched wall probes preserve the desktop's sampled points while
sharing decoded rows. Both batched and fallback paths pass the source tests.

Horizontal wrapping works in the scrolling region.
The wrap replay crosses right/left at ticks 30/36 and passes at 238 PAL lines,
zero misses, nine natural respawns and clean exit.
Outside the scrolling region, boundary
handling transforms coordinates and requests the original adjacent room;
the standalone harness exits on that request. Loading those rooms and
returning from them remains the next integration step. This is still a short
tower slice without other tower entities, scripts, interpolation, palette
cycling or music/SFX. The headroom figure applies to the measured replay,
excluding audio and initial full-map validation/ring fills.

## Connected tower hallways

`make -C amiga_version tower-route-run` builds the tower plus Teleporter Divot
(108,109) and Seeing Red (110,104). Controls remain joystick left/right and
fire; left mouse exits. Hallways load their original terrain/checkpoints and
use ordinary-room collision. Checkpoint saves retain their room, so death can
return from a hallway to the tower or from the tower to a saved hallway.

- `tower-route-capture`: normal-input lower exit/re-entry, 128 × 40 native state
  fields checked, seven natural deaths/respawns, and clean OS restoration.
- `test-tower-route`: source entry/history and hallway movement comparisons,
  checkpoint returns in both directions, same-room bank retention and invalid
  load checks.
- `tower-hallway-pixel-test`: both native hallway terrain views, 153,600 exact
  logical-pixel comparisons. Entities are hidden for these fixed captures.

The route replay peaks at **249 PAL lines / 15.936 ms**, zero misses, and the
same 64,128 explicit Chip bytes. The report is in
`build/amiga-tower-route-replay/capture.json`. Collision tiles are prepared in
resident views before the frame loop (4,800 additional ordinary-memory bytes).
Checked cold display fills publish complete banks and pause logic until both
are ready. Each replay crossing takes 62 PAL fields, about 1.24 seconds; the
old completed image stays visible during loading. This loading work is timed,
and paused fields are excluded from logic-clock accounting.

Seeing Red's crew/dialogue and exits beyond these rooms remain pending. `tower-upper-route-capture` adds native upper entry,
Seeing Red checkpoint activation and tower re-entry through ordinary input,
then a natural spike death at tick 56 tests remote hallway restore. The replay
uses eight right ticks and fifty left ticks, then no input. Crossings are at
ticks 7, 14 and 85, with 5,120 matching host state fields, 212 PAL lines peak
work, zero misses and 96 total loading fields. Host checks also confirm the
death position against source-extracted desktop spike code. Its report is
`build/amiga-tower-upper-replay/capture.json`. Initial placement is beside the
upper exit; a complete tower climb remains pending.
This build still excludes audio, other tower entities and full story logic.
The earlier checkpoint/wrapping work is committed as `88a5293f`; hallway work
is committed as `1db8ce47`.

## Faster staged hallway loading

Cold loads now take 32 PAL fields per transition, about 0.639 seconds instead
of 62 fields / 1.238 seconds. The crossing frame retains a one-row fill per
layer, while subsequent paused frames fill two rows. Both banks are still
completed before gameplay resumes; partial banks are never published. This
uses the same 64,128 explicit Chip bytes. The lower replay expects 64 total
loading fields and the upper recovery replay 96. Both retain the 250-line
A500 gate and full host trace comparisons. Paired-render tests now cover 378
cold-fill frames, including mixed one/two-row schedules. Fresh lower/upper
captures peak at 249/213 PAL lines with zero misses and clean OS restoration;
each matches all 5,120 traced state fields.

## Static hallway tower backdrops

Teleporter Divot and Seeing Red now use the desktop static tower background at
offset 200, with their cyan/green dark base and grey details. The source colour
banks share the existing mono tile pattern; conversion validates all 768 tile
pixels. The existing background plane is filled during staged loading and
stays fixed while the player moves. Chip memory and load duration are unchanged.
Native lower/upper routes pass at 249/232 PAL lines with zero misses and all
5,120 state fields matching. `tower-hallway-pixel-test` checks both complete
hallway compositions, including their static backgrounds and hidden entities.

## Seeing Red crew appearance

The route harness now displays Vermilion's idle sad frame at the source
position (264,185). His room-entry conditions match the desktop setup in 256
host cases. The harness currently supplies normal unrescued campaign defaults;
rescue persistence, dialogue and following are still pending. The source mask
fits one existing sprite channel and adds 128 ordinary-memory bytes, with no
additional Chip RAM. His tint is fixed red until palette animation is added.

`test-hallway-crew` verifies source presence conditions. `tower-crew-pixel-test`
compares the complete fixed Seeing Red composition against source terrain,
background and sprite data: all 76,800 pixels match. This also validates the
corrected sprite horizontal origin and priority over the background. Both
native replays still match 5,120 state fields, peak at 250/246 PAL lines, miss
no frames, and restore the OS cleanly. Loading remains 64/96 fields in total.

Live screenshot checks now reject AmigaDOS startup pixels and capture from
22 seconds; earlier route cyan counts at 15 seconds were not valid gameplay
visibility evidence. The new upper capture contains 614 Vermilion pixels.
Timing samples also retry pending VBlank at the beam wrap to prevent unsigned
phase-clock underflow; phase maxima must fit the overall maximum work.

## Seeing Red rescue trigger handoff

`hallway_trigger` implements the source trigger 36 collision and one-shot
handoff: set flag 8, remove the trigger and retain a `rescuered` request. It
leaves rescue/companion flags for their script commands. Room entry samples
crew presence, so the trigger does not erase an already loaded Vermilion.
`test-hallway-trigger` compares 1,254 cases against source Entity/Game code,
then checks repeat contacts, room reloads and explicit request consumption.

The asset pipeline exports the full `rescuered`/`skipred` command streams,
including six speech boxes, into `hallway-scripts.json` (version 1) and
`hallway_scripts.h` in ignored build output. The script consumer and dialogue
renderer remain pending; this is not a completed rescue cutscene.

`tower-trigger-capture` tests the handoff in a dedicated native fixture. Eight
right inputs enter the strip at tick 4. One pending request and the existing
crew remain for the rest of the replay, without awarding rescue or changing
the checkpoint. All 6,016 state fields match, peak work is 195 PAL lines, no
frames are missed, Chip use remains 64,128 bytes and OS restoration passes.
The interactive route does not enable this handoff until it has a consumer.

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
