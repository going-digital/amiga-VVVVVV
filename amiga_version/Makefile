# Invoked from any directory: make -C amiga_version [all|test|capture|run]
ROOT := $(abspath ..)
BUILD := $(ROOT)/build/amiga
BARTMAN ?= $(lastword $(sort $(wildcard $(HOME)/.vscode/extensions/bartmanabyss.amiga-debug-*)))
TOOLS ?= $(BARTMAN)/bin/darwin
CC := $(TOOLS)/opt/bin/m68k-amiga-elf-gcc
ELF2HUNK := $(TOOLS)/elf2hunk
COPPERLINE ?= /Applications/Copperline.app/Contents/MacOS/copperline
CTL ?= /Applications/Copperline.app/Contents/MacOS/copperline-ctl
ROM ?= $(HOME)/amiga/KICK13.ROM
DATA ?= $(HOME)/Library/Application Support/Steam/steamapps/common/vvvvvv/VVVVVV.app/Contents/Resources/data.zip
PLANES ?= 2
SCENE ?= world
CFLAGS := -DV6_PLANES=$(PLANES) -std=c99 -m68000 -Os -g -nostdlib -ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns -fomit-frame-pointer -Wall -Wextra -Werror -ffunction-sections -fdata-sections -MMD -MP -I$(BUILD)
LDFLAGS := -nostdlib -m68000 -Wl,--emit-relocs,--gc-sections,-Ttext=0,-Map=$(BUILD)/prototype.map
OBJECTS := $(BUILD)/prototype.o $(BUILD)/room_codec.o $(BUILD)/player.o $(BUILD)/slice.o $(BUILD)/enemy.o $(BUILD)/pixel_collision.o $(BUILD)/animation.o $(BUILD)/sprites.o $(BUILD)/terrain.o $(BUILD)/blocks.o $(BUILD)/platform.o $(BUILD)/checkpoints.o $(BUILD)/disappearing.o

.PHONY: all test capture run FORCE
all: $(BUILD)/prototype.adf

$(BUILD):
	mkdir -p $@

$(BUILD)/scene.txt: FORCE | $(BUILD)
	python3 -c 'from pathlib import Path; import sys; p=Path(sys.argv[1]); v=sys.argv[2]; p.write_text(v) if not p.exists() or p.read_text()!=v else None' $@ $(SCENE)

$(BUILD)/prototype_room.h: $(BUILD)/scene.txt $(ROOT)/tools/amiga/pack_rooms.py $(addprefix $(ROOT)/desktop_version/src/,Otherlevel.cpp Spacestation2.cpp Labclass.cpp Finalclass.cpp WarpClass.cpp) | $(BUILD)
	python3 $(ROOT)/tools/amiga/pack_rooms.py --out $(BUILD) --scene $(SCENE)

$(BUILD)/prototype_assets.h: FORCE $(BUILD)/prototype_room.h
	python3 $(ROOT)/tools/amiga/convert_assets.py --data "$(DATA)" --out $(BUILD) --scene $(SCENE) $(if $(findstring V6_DISAPPEAR_REPLAY,$(CPPFLAGS)),--disappearing,)

$(BUILD)/prototype.o: prototype.c $(ROOT)/tools/amiga/transition_replay.h $(BUILD)/prototype_room.h $(BUILD)/prototype_assets.h FORCE
	$(CC) $(CPPFLAGS) $(if $(filter enemy traffic,$(SCENE)),-DV6_ENEMY_SCENE,) $(if $(filter platform pick beneath,$(SCENE)),-DV6_PLATFORM_SCENE,) $(if $(filter beneath,$(SCENE)),-DV6_DISAPPEAR_SCENE,) $(CFLAGS) -Wno-volatile-register-var -fno-delete-null-pointer-checks -c $< -o $@

$(BUILD)/room_codec.o: room_codec.c room_codec.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/player.o: player.c player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/slice.o: slice.c slice.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/enemy.o: enemy.c enemy.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/pixel_collision.o: pixel_collision.c pixel_collision.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/animation.o: animation.c animation.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/sprites.o: sprites.c sprites.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/terrain.o: terrain.c terrain.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/blocks.o: blocks.c blocks.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/platform.o: platform.c platform.h enemy.h blocks.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/checkpoints.o: checkpoints.c checkpoints.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/prototype.elf: $(OBJECTS)
	$(CC) $(LDFLAGS) $^ -o $@

$(BUILD)/prototype.exe: $(BUILD)/prototype.elf
	$(ELF2HUNK) $< $@
	"$(CTL)" size-report $@ --elf $< --out $(BUILD)/size-report.json

$(BUILD)/prototype.adf: $(BUILD)/prototype.exe
	"$(CTL)" exe2adf $< --boot --out $@

test-sprites: | $(BUILD)
	cc -std=c99 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -I. sprites.c $(ROOT)/tools/amiga/test_sprites.c -o $(BUILD)/test_sprites
	$(BUILD)/test_sprites

.PHONY: test-sprites
test-terrain: | $(BUILD)
	cc -std=c99 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -I. terrain.c $(ROOT)/tools/amiga/test_terrain.c -o $(BUILD)/test_terrain
	$(BUILD)/test_terrain

.PHONY: test-terrain
test: test-sprites test-terrain $(BUILD)/prototype_room.h
	python3 $(ROOT)/tools/amiga/pack_rooms.py --out $(BUILD) --scene $(SCENE)
	python3 $(ROOT)/tools/amiga/test_rooms.py
	python3 $(ROOT)/tools/amiga/test_player.py
	python3 $(ROOT)/tools/amiga/test_enemy.py
	python3 $(ROOT)/tools/amiga/test_enemy.py --platform
	python3 $(ROOT)/tools/amiga/test_blocks.py
	python3 $(ROOT)/tools/amiga/test_carry.py
	python3 $(ROOT)/tools/amiga/test_platform_crush.py
	python3 $(ROOT)/tools/amiga/test_death_lifecycle.py
	python3 $(ROOT)/tools/amiga/test_recovery.py
	python3 $(ROOT)/tools/amiga/test_platform_recovery.py
	python3 $(ROOT)/tools/amiga/test_disappearing.py
	python3 $(ROOT)/tools/amiga/test_disappearing_scene.py
	python3 $(ROOT)/tools/amiga/beneath_replay_trace.py
	python3 $(ROOT)/tools/amiga/disappearing_replay_trace.py --retrigger
	python3 $(ROOT)/tools/amiga/test_checkpoints.py
	python3 $(ROOT)/tools/amiga/test_pick_route.py
	python3 $(ROOT)/tools/amiga/test_pixel_collision.py
	python3 $(ROOT)/tools/amiga/test_transitions.py
	cc -std=c99 -Wall -Wextra -Werror -fsanitize=undefined -I. -I$(BUILD) player.c slice.c checkpoints.c room_codec.c $(ROOT)/tools/amiga/test_slice.c -o $(BUILD)/test_slice
	$(BUILD)/test_slice

FORCE:

capture: all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(BUILD) --capture $(if $(filter traffic,$(SCENE)),--traffic,$(if $(filter enemy,$(SCENE)),--enemy,))

run: all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(BUILD)

-include $(OBJECTS:.o=.d)

.PHONY: capture-transitions
capture-transitions:
	$(MAKE) BUILD=$(ROOT)/build/amiga-transitions CPPFLAGS=-DV6_TRANSITION_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-transitions --capture --transitions

.PHONY: enemy-run enemy-capture
enemy-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-enemy SCENE=enemy all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-enemy
enemy-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-enemy SCENE=enemy all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-enemy --capture --enemy

.PHONY: traffic-run traffic-capture
traffic-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-traffic SCENE=traffic all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-traffic
traffic-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-traffic SCENE=traffic all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-traffic --capture --traffic

.PHONY: platform-run platform-capture
platform-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-platform SCENE=platform all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-platform
platform-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-platform-replay SCENE=platform CPPFLAGS=-DV6_PLATFORM_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-platform-replay --capture --platform

.PHONY: horizontal-capture
horizontal-capture:
	python3 $(ROOT)/tools/amiga/test_platform_loop.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-horizontal-replay SCENE=platform CPPFLAGS=-DV6_HORIZONTAL_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-horizontal-replay --capture --horizontal

.PHONY: pick-run pick-capture
pick-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-pick SCENE=pick all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-pick
pick-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-pick SCENE=pick all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-pick --capture --pick

.PHONY: pick-checkpoints-capture
pick-checkpoints-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-pick-checkpoints SCENE=pick CPPFLAGS=-DV6_CHECKPOINT_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-pick-checkpoints --capture --pick-checkpoints

.PHONY: pick-route-capture
pick-route-capture:
	python3 $(ROOT)/tools/amiga/test_pick_route.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-pick-route SCENE=pick CPPFLAGS=-DV6_PICK_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-pick-route --capture --pick-route

# Standalone test executable; no game assets, graphics takeover or runtime changes.
.PHONY: crush-capture crush-target
crush-capture:
	python3 $(ROOT)/tools/amiga/test_platform_crush.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-crush crush-target
	python3 $(ROOT)/tools/amiga/run_crush_target.py --build $(ROOT)/build/amiga-crush --rom "$(ROM)" --emulator "$(COPPERLINE)"

crush-target: $(BUILD)/crush.adf
$(BUILD)/crush_target.o: $(ROOT)/tools/amiga/crush_target.c | $(BUILD)
	$(CC) $(if $(filter beneath,$(SCENE)),-DV6_DISAPPEAR_SCENE,) $(CFLAGS) -Wno-volatile-register-var -fno-delete-null-pointer-checks -I. -c $< -o $@
$(BUILD)/crush_session.o: $(ROOT)/tools/amiga/crush_session.c | $(BUILD)
	$(CC) $(CFLAGS) -I. -c $< -o $@
$(BUILD)/crush.elf: $(BUILD)/crush_target.o $(BUILD)/crush_session.o $(addprefix $(BUILD)/,player.o platform.o enemy.o blocks.o terrain.o slice.o animation.o)
	$(CC) $(LDFLAGS) $^ -o $@
$(BUILD)/crush.exe: $(BUILD)/crush.elf
	$(ELF2HUNK) $< $@
$(BUILD)/crush.adf: $(BUILD)/crush.exe
	"$(CTL)" exe2adf $< --boot --out $@

-include $(BUILD)/crush_target.d $(BUILD)/crush_session.d

.PHONY: crush-replay-capture
crush-replay-capture:
	python3 $(ROOT)/tools/amiga/test_platform_crush.py
	python3 $(ROOT)/tools/amiga/crush_replay_trace.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-crush-replay SCENE=platform CPPFLAGS=-DV6_CRUSH_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-crush-replay --capture --crush

$(BUILD)/disappearing.o: disappearing.c disappearing.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: disappearing-capture
disappearing-capture:
	python3 $(ROOT)/tools/amiga/test_disappearing.py
	python3 $(ROOT)/tools/amiga/test_disappearing_scene.py
	python3 $(ROOT)/tools/amiga/disappearing_replay_trace.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-disappearing SCENE=platform CPPFLAGS=-DV6_DISAPPEAR_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-disappearing --capture --disappearing

.PHONY: beneath-run beneath-capture
beneath-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-beneath SCENE=beneath all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-beneath

beneath-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-beneath SCENE=beneath all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-beneath --capture --beneath

.PHONY: beneath-route-capture
beneath-route-capture:
	python3 $(ROOT)/tools/amiga/beneath_replay_trace.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-beneath-route SCENE=beneath CPPFLAGS=-DV6_BENEATH_REPLAY all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-beneath-route --capture --beneath-route

.PHONY: retrigger-capture
retrigger-capture:
	python3 $(ROOT)/tools/amiga/disappearing_replay_trace.py --retrigger
	$(MAKE) BUILD=$(ROOT)/build/amiga-retrigger SCENE=platform CPPFLAGS="-DV6_DISAPPEAR_REPLAY -DV6_RETRIGGER_REPLAY" all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-retrigger --capture --retrigger
