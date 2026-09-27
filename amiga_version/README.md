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
its functional capture works but currently fails the video headroom gate. Scripts, wider campaign progression, keyboard controls and
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
make -C amiga_version traffic-capture  # currently fails the timing gate
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
  movement, checkpoint and clean exit; saves evidence before reporting the
  outstanding timing-gate failure. This replay does not exercise enemy hits.
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
  in slow RAM. Only checkpoint damage needs CPU restoration; HUD copies occur only when
  their content changes. The earlier repeating-room scroll
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
| Free non-Chip RAM after startup allocation | 421,984 bytes (interactive build) |
| Maximum measured update/draw work | 197 PAL lines / 12.608 ms (transition replay) |
| Maximum room-change redraw | 195 PAL lines / 12.480 ms |
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
storage design. The ordinary capture peaks at 155 lines / 9.920 ms. During a snapshot
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
is **204 PAL lines / 13.056 ms**, with zero missed VBL observations. The replay
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
**328 PAL lines / 20.992 ms** at tick 2, above the unchanged **250-line gate**.
`build/amiga-traffic/smoke-report.json` records `video_headroom_passed: false`;
the command returns failure after saving the screenshot and exit evidence.
Zero skipped VBL observations in this replay does not mean work fits one PAL
frame: this peak exceeds a frame. This scene remains a performance experiment.
Enemy hit/respawn coverage still comes from the Security Sweep replay.

## Next implementation step

Profile and reduce Traffic Jam's enemy collision and checkpoint-update costs
until it passes the video headroom gate. Then add platforms, multiplexing and a
blitter fallback. Expand the strict room-setup export and
add full desktop-loop traces covering entity/update ordering. The target replay
currently asserts milestones rather than comparing every target state field.
Tower row streaming and the music storage/playback experiment remain separate
feasibility gates.

The 252,832-byte simple-RLE pack exceeds the plan's provisional 128 KiB combined
content/cache budget before scripts. Evaluate stronger compression and regional
loading; do not assume the entire campaign pack can stay resident unchanged.

The lifecycle checks pass with UBSan. An AddressSanitizer build stalled on this
host and was interrupted; ASan validation is not claimed.

Sprite register encoding follows the [Commodore hardware manual](https://www.ikod.se/wp-content/uploads/2020/08/Amiga_Hardware_Reference_Manual_3rd_Edition.pdf).
