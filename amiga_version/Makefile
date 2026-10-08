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
CFLAGS := -DV6_PLANES=$(PLANES) -std=c99 -m68000 -Os -g -nostdlib -ffreestanding -fno-builtin -fno-tree-loop-distribute-patterns -fomit-frame-pointer -Wall -Wextra -Werror -ffunction-sections -fdata-sections -MMD -MP -I. -I$(BUILD)
LDFLAGS := -nostdlib -m68000 -Wl,--emit-relocs,--gc-sections,-Ttext=0,-Map=$(BUILD)/prototype.map
OBJECTS := $(BUILD)/prototype.o $(BUILD)/room_codec.o $(BUILD)/player.o $(BUILD)/slice.o $(BUILD)/enemy.o $(BUILD)/pixel_collision.o $(BUILD)/animation.o $(BUILD)/sprites.o $(BUILD)/terrain.o $(BUILD)/blocks.o $(BUILD)/platform.o $(BUILD)/checkpoints.o $(BUILD)/disappearing.o $(BUILD)/platform_gate.o $(BUILD)/tower_stream.o $(BUILD)/tower_draw.o $(BUILD)/tower_copper.o

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
	$(CC) $(CFLAGS) -O2 -c $< -o $@

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
	$(CC) $(CFLAGS) -O2 -c $< -o $@

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
test: test-sprites test-terrain test-tile-edit test-tower-copper $(BUILD)/prototype_room.h
	python3 $(ROOT)/tools/amiga/pack_rooms.py --out $(BUILD) --scene $(SCENE)
	python3 $(ROOT)/tools/amiga/test_rooms.py
	python3 $(ROOT)/tools/amiga/test_tower_stream.py
	python3 $(ROOT)/tools/amiga/test_tower_draw.py
	python3 $(ROOT)/tools/amiga/test_player.py
	python3 $(ROOT)/tools/amiga/test_enemy.py
	python3 $(ROOT)/tools/amiga/test_enemy.py --platform
	python3 $(ROOT)/tools/amiga/test_blocks.py
	python3 $(ROOT)/tools/amiga/test_carry.py
	python3 $(ROOT)/tools/amiga/test_platform_crush.py
	python3 $(ROOT)/tools/amiga/test_death_lifecycle.py
	python3 $(ROOT)/tools/amiga/test_recovery.py
	python3 $(ROOT)/tools/amiga/test_platform_recovery.py
	python3 $(ROOT)/tools/amiga/test_platform_gate.py
	python3 $(ROOT)/tools/amiga/test_platform_loop.py --waiting
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

.PHONY: test-tile-edit
test-tile-edit: | $(BUILD)
	cc -std=c99 -O2 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -I. $(ROOT)/tools/amiga/test_tile_edit.c terrain.c disappearing.c blocks.c -o $(BUILD)/test_tile_edit
	$(BUILD)/test_tile_edit

$(BUILD)/platform_gate.o: platform_gate.c platform_gate.h platform.h disappearing.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: waiting-capture
waiting-capture:
	python3 $(ROOT)/tools/amiga/test_platform_loop.py --waiting
	$(MAKE) BUILD=$(ROOT)/build/amiga-waiting SCENE=platform CPPFLAGS="-DV6_HORIZONTAL_REPLAY -DV6_WAITING_REPLAY" all
	python3 $(ROOT)/tools/amiga/run_copperline.py --build $(ROOT)/build/amiga-waiting --rom "$(ROM)" --emulator "$(COPPERLINE)" --capture --waiting

.PHONY: feasibility-probe
feasibility-probe:
	python3 $(ROOT)/tools/amiga/probe_feasibility.py --data "$(DATA)"

$(BUILD)/tower_stream.o: tower_stream.c tower_stream.h room_codec.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/tower_draw.o: tower_draw.c tower_draw.h tower_stream.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: tower-assets
tower-assets:
	python3 $(ROOT)/tools/amiga/convert_tower_assets.py --data "$(DATA)"

$(BUILD)/tower_copper.o: tower_copper.c tower_copper.h tower_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: test-tower-copper
test-tower-copper: | $(BUILD)
	cc -std=c99 -O2 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -I. $(ROOT)/tools/amiga/test_tower_copper.c tower_copper.c -o $(BUILD)/test_tower_copper
	$(BUILD)/test_tower_copper

# Isolated tower display; generated source assets stay in ignored build output.
.PHONY: tower-probe
tower-probe: tower-assets
	python3 -c 'from pathlib import Path; p=Path("$(ROOT)/build/amiga-feasibility"); b=(p/"loadmap.v6tr").read_bytes(); (p/"tower_map.h").write_text("static const unsigned char tower_map[]={"+",".join(map(str,b))+"};\n")'
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower $(ROOT)/build/amiga-tower/tower.adf

$(BUILD)/tower_probe.o: tower_probe.c $(ROOT)/build/amiga-feasibility/tower_assets.h $(ROOT)/build/amiga-feasibility/tower_map.h FORCE | $(BUILD)
	$(CC) $(CPPFLAGS) $(CFLAGS) -O2 -Wno-volatile-register-var -I$(ROOT)/build/amiga-feasibility -fno-delete-null-pointer-checks -c $< -o $@

$(BUILD)/tower.elf: $(BUILD)/audio_policy.o $(BUILD)/paula_voice.o $(BUILD)/teleporter_colour.o $(BUILD)/teleporter_departure.o $(BUILD)/teleporter_arrival.o $(BUILD)/teleporter_menu.o $(BUILD)/campaign_route.o $(BUILD)/teleporter.o $(BUILD)/teleporter_animation.o $(BUILD)/teleporter_draw.o $(BUILD)/save_controls.o $(BUILD)/campaign_save.o $(BUILD)/campaign_file.o $(BUILD)/campaign_dos.o $(BUILD)/audio.o $(BUILD)/terrain.o $(BUILD)/companion.o $(BUILD)/dialogue.o $(BUILD)/rescue_script.o $(BUILD)/hallway_trigger.o $(BUILD)/hallway_crew.o $(BUILD)/tower_route.o $(BUILD)/checkpoints.o $(BUILD)/tower_gameplay.o $(BUILD)/blocks.o $(BUILD)/sprites.o $(BUILD)/animation.o $(BUILD)/tower_session.o $(BUILD)/player.o $(BUILD)/tower_camera.o $(BUILD)/tower_probe.o $(BUILD)/tower_draw.o $(BUILD)/tower_stream.o $(BUILD)/tower_copper.o $(BUILD)/room_codec.o
	$(CC) $(LDFLAGS) $^ -o $@

$(BUILD)/tower.exe: $(BUILD)/tower.elf
	$(ELF2HUNK) $< $@

$(BUILD)/tower.adf: $(BUILD)/tower.exe
	"$(CTL)" exe2adf $< --boot --out $@

-include $(BUILD)/tower_probe.d

.PHONY: tower-capture
tower-capture: tower-probe
	python3 $(ROOT)/tools/amiga/run_tower_probe.py

.PHONY: tower-pixel-test
tower-pixel-test: tower-probe
	python3 $(ROOT)/tools/amiga/test_tower_capture.py

$(BUILD)/tower_compose.o: tower_compose.c tower_compose.h tower_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: test-tower-compose
test-tower-compose: $(BUILD)/tower_compose.o
	python3 $(ROOT)/tools/amiga/test_tower_compose.py

test: test-tower-compose

.PHONY: test-tower-dual-copper
test-tower-dual-copper: $(BUILD)/tower_copper.o
	cc -std=c99 -O2 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -I. $(ROOT)/tools/amiga/test_tower_dual_copper.c tower_copper.c -o $(BUILD)/test_tower_dual_copper
	$(BUILD)/test_tower_dual_copper

test: test-tower-dual-copper

.PHONY: tower-step-measure
tower-step-measure: tower-probe
	python3 $(ROOT)/tools/amiga/measure_tower_steps.py

.PHONY: tower-full-measure
tower-full-measure: tower-probe
	python3 $(ROOT)/tools/amiga/measure_tower_steps.py --full

$(BUILD)/tower_camera.o: tower_camera.c tower_camera.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: test-tower-camera
test-tower-camera: $(BUILD)/tower_camera.o
	python3 $(ROOT)/tools/amiga/test_tower_camera.py

test: test-tower-camera

.PHONY: test-tower-edges
test-tower-edges: $(BUILD)/tower_camera.o
	python3 $(ROOT)/tools/amiga/test_tower_edges.py

test: test-tower-edges

.PHONY: test-tower-camera-recovery
test-tower-camera-recovery: $(BUILD)/tower_camera.o
	python3 $(ROOT)/tools/amiga/test_tower_camera_recovery.py

test: test-tower-camera-recovery

.PHONY: tower-controller-capture
tower-controller-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-controller CPPFLAGS=-DV6_TOWER_CONTROLLER $(ROOT)/build/amiga-tower-controller/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-controller --controller

.PHONY: tower-recovery-capture
tower-recovery-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-recovery CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY" $(ROOT)/build/amiga-tower-recovery/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-recovery --recovery

$(BUILD)/tower_session.o: tower_session.c tower_session.h tower_camera.h player.h tower_gameplay.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-tower-player tower-play tower-play-capture
test-tower-player:
	python3 $(ROOT)/tools/amiga/test_tower_player.py

tower-play: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-play CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY" $(ROOT)/build/amiga-tower-play/tower.adf

tower-play-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-play-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_PLAY_REPLAY" $(ROOT)/build/amiga-tower-play-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-play-replay --play

.PHONY: tower-play-run
tower-play-run: tower-play
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-play --interactive

test: test-tower-player

$(BUILD)/tower_gameplay.o: tower_gameplay.c tower_gameplay.h checkpoints.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/tower_route.o: tower_route.c tower_route.h tower_session.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

-include $(BUILD)/tower_session.d $(BUILD)/tower_gameplay.d

.PHONY: test-tower-world test-tower-pairs tower-paired-pixel-test
test-tower-world:
	python3 $(ROOT)/tools/amiga/test_tower_world.py
test-tower-pairs: tower-probe
	python3 $(ROOT)/tools/amiga/test_tower_pairs.py
tower-paired-pixel-test: tower-probe
	python3 $(ROOT)/tools/amiga/test_tower_capture.py --paired

test: test-tower-world test-tower-pairs

.PHONY: tower-world tower-world-run tower-world-capture
tower-world: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-world CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD" $(ROOT)/build/amiga-tower-world/tower.adf

tower-world-run: tower-world
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-world --interactive

tower-world-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-world-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_PLAY_REPLAY" $(ROOT)/build/amiga-tower-world-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-world-replay --world

.PHONY: tower-wrap-capture
tower-wrap-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-wrap-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_WRAP_REPLAY" $(ROOT)/build/amiga-tower-wrap-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-wrap-replay --wrap

.PHONY: tower-route tower-route-run tower-route-capture test-tower-route
tower-route: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-route CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE" $(ROOT)/build/amiga-tower-route/tower.adf
tower-route-run: tower-route
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-route --interactive
tower-route-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-route-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_ROUTE_REPLAY" $(ROOT)/build/amiga-tower-route-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-route-replay --route
test-tower-route:
	python3 $(ROOT)/tools/amiga/test_tower_route.py
.PHONY: tower-hallway-pixel-test
tower-hallway-pixel-test: tower-probe
	python3 $(ROOT)/tools/amiga/test_tower_capture.py --hallways
test: test-tower-route
-include $(BUILD)/tower_route.d

.PHONY: tower-upper-route-capture
tower-upper-route-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-upper-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_UPPER_REPLAY" $(ROOT)/build/amiga-tower-upper-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-upper-replay --upper-route

$(BUILD)/hallway_crew.o: hallway_crew.c hallway_crew.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
.PHONY: test-hallway-crew
test-hallway-crew:
	python3 $(ROOT)/tools/amiga/test_hallway_crew.py
test: test-hallway-crew

.PHONY: tower-crew-pixel-test
tower-crew-pixel-test: tower-probe
	python3 $(ROOT)/tools/amiga/test_tower_capture.py --crew

$(BUILD)/hallway_trigger.o: hallway_trigger.c hallway_trigger.h hallway_crew.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
.PHONY: test-hallway-trigger
test-hallway-trigger:
	python3 $(ROOT)/tools/amiga/test_hallway_trigger.py
test: test-hallway-trigger

.PHONY: tower-trigger-capture
tower-trigger-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-trigger-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY" $(ROOT)/build/amiga-tower-trigger-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-trigger-replay --trigger-route

$(BUILD)/rescue_script.o: rescue_script.c rescue_script.h hallway_crew.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD)/dialogue.o: dialogue.c dialogue.h rescue_script.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
.PHONY: test-rescue-script
test-rescue-script:
	python3 $(ROOT)/tools/amiga/test_rescue_script.py
test: test-rescue-script

.PHONY: tower-rescue-capture tower-rescue-skip-capture tower-rescue tower-rescue-run
tower-rescue-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-rescue-replay CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO" $(ROOT)/build/amiga-tower-rescue-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-rescue-replay --rescue-route --audio
tower-rescue-skip-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-rescue-skip CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_RESCUE_SKIP -DV6_TOWER_AUDIO" $(ROOT)/build/amiga-tower-rescue-skip/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-rescue-skip --skip-rescue --audio
tower-rescue: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-rescue CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO" $(ROOT)/build/amiga-tower-rescue/tower.adf
tower-rescue-run: tower-rescue
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-rescue --interactive

.PHONY: tower-caption-pixel-test
tower-caption-pixel-test: tower-probe
	python3 $(ROOT)/tools/amiga/test_tower_capture.py --captions

$(BUILD)/companion.o: companion.c companion.h player.h animation.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-companion
test-companion:
	python3 $(ROOT)/tools/amiga/test_companion.py
test: test-companion

.PHONY: tower-companion-route-capture
tower-companion-route-capture: tower-probe
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-companion-route CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_UPPER_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_COMPANION_ROUTE" $(ROOT)/build/amiga-tower-companion-route/tower.adf
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-tower-companion-route --companion-route

$(BUILD)/audio.o: audio.c audio.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-audio
test-audio:
	python3 $(ROOT)/tools/amiga/test_audio.py
test: test-audio

$(BUILD)/campaign_save.o: campaign_save.c campaign_save.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-campaign-save
test-campaign-save: $(BUILD)/campaign_save.o
	python3 $(ROOT)/tools/amiga/test_campaign_save.py
test: test-campaign-save

$(BUILD)/campaign_file.o: campaign_file.c campaign_file.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
$(BUILD)/campaign_dos.o: campaign_dos.c campaign_dos.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -Wno-volatile-register-var -c $< -o $@
.PHONY: test-campaign-file
test-campaign-file: $(BUILD)/campaign_dos.o $(BUILD)/campaign_file.o
	python3 $(ROOT)/tools/amiga/test_campaign_file.py
test: test-campaign-file

.PHONY: tower-persistence-capture
tower-persistence-capture: tower-probe test-campaign-file
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-persistence CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO -DV6_TOWER_PERSIST" $(ROOT)/build/amiga-tower-persistence/tower.adf
	python3 $(ROOT)/tools/amiga/run_campaign_persistence.py

.PHONY: test-campaign-replace
test-campaign-replace: test-campaign-file
	python3 $(ROOT)/tools/amiga/test_campaign_replace.py
test: test-campaign-replace

.PHONY: tower-save-replacement-capture
tower-save-replacement-capture: tower-probe test-campaign-replace
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-replace-1 CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO -DV6_TOWER_PERSIST -DV6_TOWER_REPLACE_TEST=1" $(ROOT)/build/amiga-tower-replace-1/tower.adf
	python3 $(ROOT)/tools/amiga/run_campaign_persistence.py --build $(ROOT)/build/amiga-tower-replace-1 --replace-mode 1
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-replace-2 CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO -DV6_TOWER_PERSIST -DV6_TOWER_REPLACE_TEST=2" $(ROOT)/build/amiga-tower-replace-2/tower.adf
	python3 $(ROOT)/tools/amiga/run_campaign_persistence.py --build $(ROOT)/build/amiga-tower-replace-2 --replace-mode 2
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-replace-3 CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO -DV6_TOWER_PERSIST -DV6_TOWER_REPLACE_TEST=3" $(ROOT)/build/amiga-tower-replace-3/tower.adf
	python3 $(ROOT)/tools/amiga/run_campaign_persistence.py --build $(ROOT)/build/amiga-tower-replace-3 --replace-mode 3

$(BUILD)/save_controls.o: save_controls.c save_controls.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-save-controls tower-interactive-save tower-interactive-save-run tower-interactive-save-capture
test-save-controls: $(BUILD)/save_controls.o
	python3 $(ROOT)/tools/amiga/test_save_controls.py
test: test-save-controls
tower-interactive-save: tower-probe test-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-interactive-save CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO -DV6_TOWER_UI_SAVE" $(ROOT)/build/amiga-tower-interactive-save/tower.adf
tower-interactive-save-run: tower-interactive-save
	python3 $(ROOT)/tools/amiga/run_interactive_save.py
tower-interactive-save-capture: tower-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-tower-ui-save CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_PLAY_REPLAY -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_AUDIO -DV6_TOWER_UI_SAVE -DV6_TOWER_UI_REPLAY" $(ROOT)/build/amiga-tower-ui-save/tower.adf
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-tower-ui-save --capture
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --capture --physical

.PHONY: test-interactive-save
test-interactive-save: test-save-controls test-campaign-replace
	python3 $(ROOT)/tools/amiga/test_interactive_save.py
test: test-interactive-save

.PHONY: test-room-boundaries
test-room-boundaries:
	python3 $(ROOT)/tools/amiga/test_room_boundaries.py
test: test-room-boundaries

$(BUILD)/teleporter.o: teleporter.c teleporter.h checkpoints.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-teleporter
test-teleporter: $(BUILD)/teleporter.o
	python3 $(ROOT)/tools/amiga/test_teleporter.py
test: test-teleporter
-include $(BUILD)/teleporter.d

$(BUILD)/teleporter_draw.o: teleporter_draw.c teleporter_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_draw.d

.PHONY: test-teleporter-draw tower-teleporter-capture
test-teleporter-draw: tower-probe
	python3 $(ROOT)/tools/amiga/test_teleporter_draw.py
tower-teleporter-capture: test-teleporter-draw
	python3 $(ROOT)/tools/amiga/test_teleporter_capture.py
test: test-teleporter-draw

$(BUILD)/teleporter_animation.o: teleporter_animation.c teleporter_animation.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_animation.d

.PHONY: test-teleporter-animation tower-teleporter-live-capture
test-teleporter-animation: $(BUILD)/teleporter_animation.o
	python3 $(ROOT)/tools/amiga/test_teleporter_animation.py
test: test-teleporter-animation

$(BUILD)/teleporter_menu.o: teleporter_menu.c teleporter_menu.h teleporter.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_menu.d
.PHONY: test-teleporter-menu
test-teleporter-menu: $(BUILD)/teleporter_menu.o
	python3 $(ROOT)/tools/amiga/test_teleporter_menu.py
test: test-teleporter-menu
tower-teleporter-live-capture: tower-probe test-teleporter-animation test-teleporter
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-live CPPFLAGS="-DV6_TOWER_PAIRS -DV6_TOWER_HOLD=0 -DV6_TOWER_TELEPORTER_HOLD=1 -DV6_TELEPORTER_LIVE -DV6_TOWER_CONTROLLER" $(ROOT)/build/amiga-teleporter-live/tower.adf
	python3 $(ROOT)/tools/amiga/run_teleporter_live.py

.PHONY: test-building-route tower-building-route-capture
test-building-route:
	python3 $(ROOT)/tools/amiga/test_building_route.py
test: test-building-route
tower-building-route-capture: tower-probe test-building-route
	$(MAKE) BUILD=$(ROOT)/build/amiga-building-route CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_BUILDING_REPLAY" $(ROOT)/build/amiga-building-route/tower.adf
	python3 $(ROOT)/tools/amiga/run_building_route.py

.PHONY: tower-building-route tower-building-route-run
tower-building-route: tower-probe test-building-route
	$(MAKE) BUILD=$(ROOT)/build/amiga-building-play CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING" $(ROOT)/build/amiga-building-play/tower.adf
tower-building-route-run: tower-building-route
	python3 $(ROOT)/tools/amiga/run_building_route.py --build $(ROOT)/build/amiga-building-play --interactive

$(BUILD)/campaign_route.o: campaign_route.c campaign_route.h campaign_save.h tower_route.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/campaign_route.d

.PHONY: tower-building-save-capture
tower-building-save-capture: tower-probe test-campaign-save test-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-building-save CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_BUILDING_REPLAY -DV6_BUILDING_SAVE" $(ROOT)/build/amiga-building-save/tower.adf
	python3 $(ROOT)/tools/amiga/run_building_save.py

.PHONY: tower-building-interactive-save tower-building-interactive-save-run tower-building-interactive-save-capture
tower-building-interactive-save: tower-probe test-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-building-ui CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_UI_SAVE" $(ROOT)/build/amiga-building-ui/tower.adf
tower-building-interactive-save-run: tower-building-interactive-save
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-building-ui --building
tower-building-interactive-save-capture: tower-building-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-building-ui-capture CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_BUILDING_REPLAY -DV6_TOWER_UI_SAVE" $(ROOT)/build/amiga-building-ui-capture/tower.adf
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-building-ui-capture --building --capture --physical

.PHONY: tower-building-menu-capture
tower-building-menu-capture: tower-probe test-teleporter-menu test-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-building-menu CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_BUILDING_REPLAY -DV6_TOWER_UI_SAVE -DV6_TELE_MENU_CAPTURE" $(ROOT)/build/amiga-building-menu/tower.adf
	python3 $(ROOT)/tools/amiga/run_building_menu.py

.PHONY: test-teleporter-travel
test-teleporter-travel: $(BUILD)/tower_route.o
	python3 $(ROOT)/tools/amiga/test_teleporter_travel.py
test: test-teleporter-travel

.PHONY: tower-energize-capture
tower-energize-capture: tower-probe test-teleporter-travel
	python3 $(ROOT)/tools/amiga/test_energize_graphics.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-energize CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE" $(ROOT)/build/amiga-energize/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py

.PHONY: test-energize-graphics
test-energize-graphics: tower-assets
	python3 $(ROOT)/tools/amiga/test_energize_graphics.py
test: test-energize-graphics

$(BUILD)/teleporter_arrival.o: teleporter_arrival.c teleporter_arrival.h teleporter.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_arrival.d
.PHONY: test-teleporter-arrival
test-teleporter-arrival: $(BUILD)/teleporter_arrival.o
	python3 $(ROOT)/tools/amiga/test_teleporter_arrival.py
test: test-teleporter-arrival

.PHONY: tower-energize-arrival-capture
tower-energize-arrival-capture: tower-probe test-teleporter-arrival test-arrival-route
	$(MAKE) BUILD=$(ROOT)/build/amiga-energize-arrival CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL" $(ROOT)/build/amiga-energize-arrival/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --arrival

	$(MAKE) BUILD=$(ROOT)/build/amiga-energize-arrival-flash CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_ENERGIZE_CAPTURE_TICKS=1" $(ROOT)/build/amiga-energize-arrival-flash/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --flash

.PHONY: test-arrival-route
test-arrival-route: $(BUILD)/tower_route.o $(BUILD)/teleporter_arrival.o
	python3 $(ROOT)/tools/amiga/test_arrival_route.py
test: test-arrival-route

$(BUILD)/teleporter_departure.o: teleporter_departure.c teleporter_departure.h teleporter.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_departure.d
.PHONY: test-teleporter-departure
test-teleporter-departure: $(BUILD)/teleporter_departure.o
	python3 $(ROOT)/tools/amiga/test_teleporter_departure.py
test: test-teleporter-departure

.PHONY: test-departure-route
test-departure-route: $(BUILD)/teleporter_departure.o $(BUILD)/teleporter_arrival.o $(BUILD)/tower_route.o
	python3 $(ROOT)/tools/amiga/test_departure_route.py
test: test-departure-route

.PHONY: tower-teleporter-roundtrip-capture
tower-teleporter-roundtrip-capture: tower-probe test-departure-route test-teleporter-colour
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-roundtrip CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP" $(ROOT)/build/amiga-teleporter-roundtrip/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-outbound CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_ENERGIZE_CAPTURE_TICKS=64" $(ROOT)/build/amiga-teleporter-outbound/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --outbound

$(BUILD)/teleporter_colour.o: teleporter_colour.c teleporter_colour.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_colour.d
.PHONY: test-teleporter-colour
test-teleporter-colour: $(BUILD)/teleporter_colour.o
	python3 $(ROOT)/tools/amiga/test_teleporter_colour.py
test: test-teleporter-colour

.PHONY: tower-teleporter-colour-capture
tower-teleporter-colour-capture: tower-probe test-teleporter-colour
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-colour CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_ENERGIZE_CAPTURE_TICKS=6" $(ROOT)/build/amiga-teleporter-colour/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --colour

$(BUILD)/sfx_mixer.o: sfx_mixer.c sfx_mixer.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/sfx_mixer.d
.PHONY: test-sfx-mixer
test-sfx-mixer: $(BUILD)/sfx_mixer.o
	python3 $(ROOT)/tools/amiga/test_sfx_mixer.py
test: test-sfx-mixer

$(BUILD)/paula_voice.o: paula_voice.c paula_voice.h audio.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/paula_voice.d
.PHONY: tower-teleporter-audio-capture
tower-teleporter-audio-capture: tower-probe test-audio test-paula-voice
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-paula CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_TRAVEL_AUDIO" $(ROOT)/build/amiga-teleporter-paula/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --audio

.PHONY: test-paula-voice
test-paula-voice: $(BUILD)/paula_voice.o
	python3 $(ROOT)/tools/amiga/test_paula_voice.py
test: test-paula-voice

$(BUILD)/audio_policy.o: audio_policy.c audio_policy.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/audio_policy.d
.PHONY: test-audio-policy
test-audio-policy: $(BUILD)/audio_policy.o
	python3 $(ROOT)/tools/amiga/test_audio_policy.py
test: test-audio-policy

.PHONY: tower-teleporter-reserved-audio-capture
tower-teleporter-reserved-audio-capture: tower-probe test-audio-policy test-paula-voice
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-reserved CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_TRAVEL_AUDIO -DV6_TRAVEL_SFX_MASK=3" $(ROOT)/build/amiga-teleporter-reserved/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --audio --reserved-audio
