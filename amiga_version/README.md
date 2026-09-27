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
horizontal platform and two working checkpoints. Scripts, wider campaign progression, keyboard controls and
music remain unimplemented. See [the port plan](../AMIGA_PORT_PLAN.md).

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

## Next implementation step

Expand room-entity support to disappearing platforms and conveyors. Sprite
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
