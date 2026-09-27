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
OBJECTS := $(BUILD)/prototype.o $(BUILD)/room_codec.o $(BUILD)/player.o $(BUILD)/slice.o $(BUILD)/enemy.o $(BUILD)/pixel_collision.o $(BUILD)/animation.o

.PHONY: all test capture run FORCE
all: $(BUILD)/prototype.adf

$(BUILD):
	mkdir -p $@

$(BUILD)/scene.txt: FORCE | $(BUILD)
	python3 -c 'from pathlib import Path; import sys; p=Path(sys.argv[1]); v=sys.argv[2]; p.write_text(v) if not p.exists() or p.read_text()!=v else None' $@ $(SCENE)

$(BUILD)/prototype_room.h: $(BUILD)/scene.txt $(ROOT)/tools/amiga/pack_rooms.py $(addprefix $(ROOT)/desktop_version/src/,Otherlevel.cpp Spacestation2.cpp Labclass.cpp Finalclass.cpp WarpClass.cpp) | $(BUILD)
	python3 $(ROOT)/tools/amiga/pack_rooms.py --out $(BUILD) --scene $(SCENE)

$(BUILD)/prototype_assets.h: FORCE $(BUILD)/prototype_room.h
	python3 $(ROOT)/tools/amiga/convert_assets.py --data "$(DATA)" --out $(BUILD) --scene $(SCENE)

$(BUILD)/prototype.o: prototype.c $(ROOT)/tools/amiga/transition_replay.h $(BUILD)/prototype_room.h $(BUILD)/prototype_assets.h FORCE
	$(CC) $(CPPFLAGS) $(if $(filter enemy,$(SCENE)),-DV6_ENEMY_SCENE,) $(CFLAGS) -Wno-volatile-register-var -fno-delete-null-pointer-checks -c $< -o $@

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

$(BUILD)/prototype.elf: $(OBJECTS)
	$(CC) $(LDFLAGS) $^ -o $@

$(BUILD)/prototype.exe: $(BUILD)/prototype.elf
	$(ELF2HUNK) $< $@
	"$(CTL)" size-report $@ --elf $< --out $(BUILD)/size-report.json

$(BUILD)/prototype.adf: $(BUILD)/prototype.exe
	"$(CTL)" exe2adf $< --boot --out $@

test: $(BUILD)/prototype_room.h
	python3 $(ROOT)/tools/amiga/pack_rooms.py --out $(BUILD) --scene $(SCENE)
	python3 $(ROOT)/tools/amiga/test_rooms.py
	python3 $(ROOT)/tools/amiga/test_player.py
	python3 $(ROOT)/tools/amiga/test_enemy.py
	python3 $(ROOT)/tools/amiga/test_pixel_collision.py
	python3 $(ROOT)/tools/amiga/test_transitions.py
	cc -std=c99 -Wall -Wextra -Werror -fsanitize=undefined -I. -I$(BUILD) player.c slice.c room_codec.c $(ROOT)/tools/amiga/test_slice.c -o $(BUILD)/test_slice
	$(BUILD)/test_slice

FORCE:

capture: all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(BUILD) --capture $(if $(filter enemy,$(SCENE)),--enemy,)

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
