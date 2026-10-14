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
OBJECTS := $(BUILD)/prototype.o $(BUILD)/room_codec.o $(BUILD)/player.o $(BUILD)/slice.o $(BUILD)/enemy.o $(BUILD)/pixel_collision.o $(BUILD)/animation.o $(BUILD)/sprites.o $(BUILD)/terrain.o $(BUILD)/blocks.o $(BUILD)/platform.o $(BUILD)/checkpoints.o $(BUILD)/disappearing.o $(BUILD)/platform_gate.o $(BUILD)/trinkets.o $(BUILD)/prize.o $(BUILD)/tower_stream.o $(BUILD)/tower_draw.o $(BUILD)/tower_copper.o

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
	$(CC) $(CPPFLAGS) $(if $(filter enemy traffic,$(SCENE)),-DV6_ENEMY_SCENE,) $(if $(filter platform pick beneath shenanigan,$(SCENE)),-DV6_PLATFORM_SCENE,) $(if $(filter beneath,$(SCENE)),-DV6_DISAPPEAR_SCENE,) $(CFLAGS) -Wno-volatile-register-var -fno-delete-null-pointer-checks -c $< -o $@

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

$(BUILD)/prize.o: prize.c prize.h platform_gate.h trinkets.h checkpoints.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

$(BUILD)/trinkets.o: trinkets.c trinkets.h player.h | $(BUILD)
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
test-trinkets: $(BUILD)/trinkets.o
	cc -std=c99 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -ffunction-sections -fdata-sections -Wl,-dead_strip -I. trinkets.c player.c $(ROOT)/tools/amiga/test_trinkets.c -o $(BUILD)/test_trinkets
	$(BUILD)/test_trinkets

.PHONY: test-trinkets
test: test-trinkets test-sprites test-terrain test-tile-edit test-tower-copper $(BUILD)/prototype_room.h
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

# Route ABI follows the native bank configuration. Stamp changes rebuild both
# users when a caller switches flags in an existing build directory.
ROUTE_MODE = $(if $(findstring -DV6_NORTH_ROUTE,$(CPPFLAGS)),1,0)
$(BUILD)/route-mode.txt: FORCE | $(BUILD)
	python3 -c 'from pathlib import Path; p=Path("$(BUILD)/route-mode.txt"); value="$(ROUTE_MODE)\n"; p.write_text(value) if not p.exists() or p.read_text()!=value else None'

$(BUILD)/tower_probe.o: tower_probe.c $(BUILD)/route-mode.txt $(ROOT)/build/amiga-feasibility/tower_assets.h $(ROOT)/build/amiga-feasibility/tower_map.h FORCE | $(BUILD)
	$(CC) $(CPPFLAGS) -DV6_ROUTE_PREDECODED=$(ROUTE_MODE) $(CFLAGS) -O2 -Wno-volatile-register-var -I$(ROOT)/build/amiga-feasibility -fno-delete-null-pointer-checks -c $< -o $@

$(BUILD)/tower.elf: $(BUILD)/north_route.o $(BUILD)/sprite_mux.o $(BUILD)/menu_slide.o $(BUILD)/ui_menu.o $(BUILD)/campaign_menu.o $(BUILD)/campaign_menu_file.o $(BUILD)/save_summary.o $(BUILD)/save_page.o $(BUILD)/map_slide.o $(BUILD)/map_transition.o $(BUILD)/map_draw.o $(BUILD)/keyboard.o $(BUILD)/map_menu.o $(BUILD)/vstitch_hint_draw.o $(BUILD)/vstitch_hint_copper.o $(BUILD)/vstitch_trigger.o $(BUILD)/prize_return.o $(BUILD)/prize_return_sprite.o $(BUILD)/prize_return_draw.o $(BUILD)/pixel_collision.o $(BUILD)/pickup_fade.o $(BUILD)/pickup_draw.o $(BUILD)/pickup_copper.o $(BUILD)/trinket_screen.o $(BUILD)/prize.o $(BUILD)/platform_gate.o $(BUILD)/disappearing.o $(BUILD)/trinkets.o $(BUILD)/platform.o $(BUILD)/enemy.o $(BUILD)/station_trigger.o $(BUILD)/teleporter_admission.o $(BUILD)/screen_shake.o $(BUILD)/screen_shake_dma.o $(BUILD)/screen_shake_display.o $(BUILD)/music_gain.o $(BUILD)/music_registers.o $(BUILD)/music_area.o $(BUILD)/music_control.o $(BUILD)/audio_policy.o $(BUILD)/paula_voice.o $(BUILD)/teleporter_colour.o $(BUILD)/teleporter_departure.o $(BUILD)/teleporter_arrival.o $(BUILD)/teleporter_menu.o $(BUILD)/campaign_route.o $(BUILD)/teleporter.o $(BUILD)/teleporter_animation.o $(BUILD)/teleporter_draw.o $(BUILD)/save_controls.o $(BUILD)/campaign_save.o $(BUILD)/campaign_file.o $(BUILD)/campaign_dos.o $(BUILD)/audio.o $(BUILD)/terrain.o $(BUILD)/companion.o $(BUILD)/dialogue.o $(BUILD)/rescue_script.o $(BUILD)/hallway_trigger.o $(BUILD)/hallway_crew.o $(BUILD)/tower_route.o $(BUILD)/checkpoints.o $(BUILD)/tower_gameplay.o $(BUILD)/blocks.o $(BUILD)/sprites.o $(BUILD)/animation.o $(BUILD)/tower_session.o $(BUILD)/player.o $(BUILD)/tower_camera.o $(BUILD)/tower_probe.o $(BUILD)/tower_draw.o $(BUILD)/tower_stream.o $(BUILD)/tower_copper.o $(BUILD)/room_codec.o
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

$(BUILD)/tower_route.o: tower_route.c tower_route.h tower_session.h $(BUILD)/route-mode.txt | $(BUILD)
	$(CC) -DV6_ROUTE_PREDECODED=$(ROUTE_MODE) $(CFLAGS) -O2 -c $< -o $@

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

$(BUILD)/rescue_script.o: rescue_script.c rescue_script.h hallway_crew.h station_trigger.h | $(BUILD)
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

$(BUILD)/campaign_save.o: campaign_save.c campaign_save.h teleporter_admission.h teleporter_menu.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-campaign-save
test-campaign-save: $(BUILD)/campaign_save.o
	python3 $(ROOT)/tools/amiga/test_campaign_save.py
test: test-campaign-save

.PHONY: test-campaign-state
test-campaign-state: $(BUILD)/campaign_save.o
	python3 $(ROOT)/tools/amiga/test_campaign_state.py
test: test-campaign-state

.PHONY: test-campaign-state-file
test-campaign-state-file: test-campaign-state $(BUILD)/campaign_file.o
	python3 $(ROOT)/tools/amiga/test_campaign_state_file.py
test: test-campaign-state-file

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

$(BUILD)/map_menu.o: map_menu.c map_menu.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-map-menu
test-map-menu: $(BUILD)/map_menu.o
	python3 $(ROOT)/tools/amiga/test_map_menu.py
test: test-map-menu

$(BUILD)/map_transition.o: map_transition.c map_transition.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-map-transition
test-map-transition: $(BUILD)/map_transition.o
	python3 $(ROOT)/tools/amiga/test_map_transition.py
test: test-map-transition

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

.PHONY: music-intake test-music-intake
music-intake:
	python3 $(ROOT)/tools/amiga/audit_music.py
test-music-intake:
	python3 $(ROOT)/tools/amiga/test_music_intake.py
test: test-music-intake

$(BUILD)/music_control.o: music_control.c music_control.h music_area.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/music_control.d
.PHONY: test-music-control
test-music-control: $(BUILD)/music_control.o
	python3 $(ROOT)/tools/amiga/test_music_control.py
test: test-music-control

$(BUILD)/music_area_map.h: $(ROOT)/tools/amiga/export_music_area.py $(ROOT)/tools/amiga/audit_music.py $(addprefix $(ROOT)/desktop_version/src/,Music.cpp Music.h BinaryBlob.h) | $(BUILD)
	python3 $(ROOT)/tools/amiga/export_music_area.py --out $(BUILD)
$(BUILD)/music_area.o: music_area.c music_area.h $(BUILD)/music_area_map.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/music_area.d
.PHONY: test-music-area
test-music-area: $(BUILD)/music_area.o $(BUILD)/music_control.o
	python3 $(ROOT)/tools/amiga/test_music_area.py
test: test-music-area

.PHONY: test-music-entry
test-music-entry: $(BUILD)/music_area.o $(BUILD)/music_control.o
	python3 $(ROOT)/tools/amiga/test_music_entry.py
test: test-music-entry

.PHONY: tower-teleporter-music-capture
tower-teleporter-music-capture: tower-probe test-music-entry
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-music CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_MUSIC_TRACE" $(ROOT)/build/amiga-teleporter-music/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --music

$(BUILD)/music_gain.o: music_gain.c music_gain.h audio.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/music_gain.d
.PHONY: test-music-gain
test-music-gain: $(BUILD)/music_gain.o
	$(CC) -nostdlib -m68000 -Wl,-e,v6_music_gain_plan $< -o $(BUILD)/music_gain-check.elf
	python3 $(ROOT)/tools/amiga/test_music_gain.py
test: test-music-gain

$(BUILD)/music_registers.o: music_registers.c music_registers.h audio.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/music_registers.d
.PHONY: test-music-registers
test-music-registers: $(BUILD)/music_registers.o
	$(CC) -nostdlib -m68000 -Wl,-e,v6_music_register_plan $< -o $(BUILD)/music-registers-check.elf
	python3 $(ROOT)/tools/amiga/test_music_registers.py
test: test-music-registers

.PHONY: tower-coexist-audio-capture
tower-coexist-audio-capture: tower-probe test-music-registers test-music-gain
	$(MAKE) BUILD=$(ROOT)/build/amiga-coexist-audio CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_TRAVEL_AUDIO -DV6_TRAVEL_SFX_MASK=3 -DV6_TOWER_COEXIST_AUDIO" $(ROOT)/build/amiga-coexist-audio/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --audio --reserved-audio --coexist-audio

$(BUILD)/screen_shake.o: screen_shake.c screen_shake.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
-include $(BUILD)/screen_shake.d
.PHONY: test-screen-shake
test-screen-shake: $(BUILD)/screen_shake.o
	python3 $(ROOT)/tools/amiga/test_screen_shake.py
test: test-screen-shake

$(BUILD)/screen_shake_dma.o: screen_shake_dma.c screen_shake_dma.h screen_shake.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
$(BUILD)/screen_shake_display.o: screen_shake_display.c screen_shake_display.h screen_shake.h tower_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-screen-shake-dma tower-teleporter-shake-capture
test-screen-shake-dma: $(BUILD)/screen_shake_dma.o $(BUILD)/screen_shake_display.o
	python3 $(ROOT)/tools/amiga/test_screen_shake_dma.py
test: test-screen-shake-dma
tower-teleporter-shake-capture: tower-probe test-screen-shake test-screen-shake-dma
	$(MAKE) BUILD=$(ROOT)/build/amiga-teleporter-shake CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_SHAKE" $(ROOT)/build/amiga-teleporter-shake/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --shake
	python3 $(ROOT)/tools/amiga/run_shake.py
-include $(BUILD)/screen_shake_dma.d $(BUILD)/screen_shake_display.d

.PHONY: tower-shake-audio-capture
tower-shake-audio-capture: tower-probe test-screen-shake test-screen-shake-dma test-audio-policy test-paula-voice
	$(MAKE) BUILD=$(ROOT)/build/amiga-shake-audio CPPFLAGS="-DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_ENERGIZE_CAPTURE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_SHAKE -DV6_TOWER_TRAVEL_AUDIO -DV6_TRAVEL_SFX_MASK=3" $(ROOT)/build/amiga-shake-audio/tower.adf
	python3 $(ROOT)/tools/amiga/run_energize.py --roundtrip --shake --audio --reserved-audio --build-dir $(ROOT)/build/amiga-shake-audio

.PHONY: tower-arrival-save-capture
tower-arrival-save-capture: tower-probe test-campaign-save test-campaign-replace test-departure-route test-screen-shake-dma
	python3 $(ROOT)/tools/amiga/run_arrival_save.py

$(BUILD)/teleporter_admission.o: teleporter_admission.c teleporter_admission.h teleporter_menu.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
-include $(BUILD)/teleporter_admission.d
.PHONY: test-teleporter-admission
test-teleporter-admission: $(BUILD)/teleporter_admission.o
	python3 $(ROOT)/tools/amiga/test_teleporter_admission.py
test: test-teleporter-admission

MENU_TRAVEL_FLAGS = -DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_UI_SAVE -DV6_TOWER_ENERGIZE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_MENU_TRAVEL
.PHONY: tower-menu-travel tower-menu-travel-run tower-menu-travel-capture
tower-menu-travel: tower-probe test-teleporter-admission
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-live CPPFLAGS="$(MENU_TRAVEL_FLAGS)" $(ROOT)/build/amiga-menu-live/tower.adf
tower-menu-travel-run: tower-menu-travel
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-menu-live --building
tower-menu-travel-capture: tower-probe test-teleporter-admission test-teleporter-menu test-departure-route test-interactive-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-travel CPPFLAGS="$(MENU_TRAVEL_FLAGS) -DV6_TOWER_BUILDING_REPLAY -DV6_TELE_MENU_CAPTURE -DV6_MENU_EXPLORED_CAPTURE" $(ROOT)/build/amiga-menu-travel/tower.adf
	python3 $(ROOT)/tools/amiga/run_menu_travel.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-unexplored CPPFLAGS="$(MENU_TRAVEL_FLAGS) -DV6_TOWER_BUILDING_REPLAY -DV6_TELE_MENU_CAPTURE" $(ROOT)/build/amiga-menu-unexplored/tower.adf
	python3 $(ROOT)/tools/amiga/run_menu_travel.py --build $(ROOT)/build/amiga-menu-unexplored --unexplored
	python3 $(ROOT)/tools/amiga/run_menu_travel.py --build $(ROOT)/build/amiga-menu-unexplored --load-return $(ROOT)/build/amiga-menu-travel/capture-menu-disk.adf

.PHONY: test-shake-caption tower-menu-effects tower-menu-effects-run tower-menu-effects-capture
test-shake-caption: $(BUILD)/screen_shake_display.o
	python3 $(ROOT)/tools/amiga/test_shake_caption.py
test: test-shake-caption
MENU_EFFECT_FLAGS = $(MENU_TRAVEL_FLAGS) -DV6_TOWER_SHAKE -DV6_TOWER_TRAVEL_AUDIO -DV6_TRAVEL_SFX_MASK=3
tower-menu-effects: tower-probe test-shake-caption
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-effects-live CPPFLAGS="$(MENU_EFFECT_FLAGS)" $(ROOT)/build/amiga-menu-effects-live/tower.adf
tower-menu-effects-run: tower-menu-effects
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-menu-effects-live --building
tower-menu-effects-capture: tower-probe test-campaign-state-file test-shake-caption test-screen-shake test-screen-shake-dma test-audio-policy test-paula-voice
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-effects CPPFLAGS="$(MENU_EFFECT_FLAGS) -DV6_TOWER_BUILDING_REPLAY -DV6_TELE_MENU_CAPTURE -DV6_MENU_EXPLORED_CAPTURE" $(ROOT)/build/amiga-menu-effects/tower.adf
	python3 $(ROOT)/tools/amiga/run_menu_travel.py --build $(ROOT)/build/amiga-menu-effects --effects
	python3 $(ROOT)/tools/amiga/run_menu_travel.py --build $(ROOT)/build/amiga-menu-effects --effects --exit-pending
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-effects-return CPPFLAGS="$(MENU_EFFECT_FLAGS) -DV6_TOWER_BUILDING_REPLAY -DV6_TELE_MENU_CAPTURE" $(ROOT)/build/amiga-menu-effects-return/tower.adf
	python3 $(ROOT)/tools/amiga/run_menu_travel.py --build $(ROOT)/build/amiga-menu-effects-return --load-return $(ROOT)/build/amiga-menu-effects/capture-menu-disk.adf --effects
	python3 $(ROOT)/tools/amiga/run_menu_travel.py --build $(ROOT)/build/amiga-menu-effects-return --load-return $(ROOT)/build/amiga-menu-effects/capture-menu-disk.adf --legacy-load --effects
	python3 $(ROOT)/tools/amiga/run_menu_effect_pixels.py

$(BUILD)/station_trigger.o: station_trigger.c station_trigger.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
.PHONY: test-station-trigger test-station-route
test-station-trigger: $(BUILD)/station_trigger.o
	python3 $(ROOT)/tools/amiga/test_station_trigger.py
test-station-route:
	python3 $(ROOT)/tools/amiga/test_station_route.py
	python3 $(ROOT)/tools/amiga/test_shenanigan_route.py
test: test-station-trigger test-station-route

.PHONY: test-station-rescue
test-station-rescue: $(BUILD)/rescue_script.o $(BUILD)/dialogue.o
	python3 $(ROOT)/tools/amiga/test_station_rescue.py
	$(CC) $(CFLAGS) -I$(ROOT)/build/amiga-station-rescue -c $(ROOT)/build/amiga-station-rescue/programs.c -o $(ROOT)/build/amiga-station-rescue/programs.o
test: test-station-rescue

STATION_FLAGS = -DV6_TOWER_SHENANIGAN -DV6_TOWER_CONTROLLER -DV6_TOWER_RECOVERY -DV6_TOWER_PLAY -DV6_TOWER_WORLD -DV6_TOWER_ROUTE -DV6_TOWER_BUILDING -DV6_TOWER_ENERGIZE -DV6_TOWER_TRIGGER_REPLAY -DV6_TOWER_RESCUE -DV6_TOWER_STATION -DV6_TOWER_AUDIO
.PHONY: tower-station tower-station-run
tower-station: tower-probe test-station-rescue test-station-trigger test-station-route test-station-graphics test-station-companion
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-live CPPFLAGS="$(STATION_FLAGS)" $(ROOT)/build/amiga-station-live/tower.adf
tower-station-run: tower-station
	python3 $(ROOT)/tools/amiga/run_tower_probe.py --build $(ROOT)/build/amiga-station-live --interactive

.PHONY: tower-station-capture
tower-station-capture: tower-station
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-capture CPPFLAGS="$(STATION_FLAGS) -DV6_STATION_CAPTURE" $(ROOT)/build/amiga-station-capture/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_game.py --build $(ROOT)/build/amiga-station-capture
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-skip CPPFLAGS="$(STATION_FLAGS) -DV6_STATION_CAPTURE -DV6_TOWER_RESCUE_SKIP" $(ROOT)/build/amiga-station-skip/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_game.py --build $(ROOT)/build/amiga-station-skip --skip

.PHONY: test-station-graphics
test-station-graphics: tower-assets
	python3 $(ROOT)/tools/amiga/test_station_graphics.py

.PHONY: test-campaign-progress tower-station-save tower-station-save-run tower-station-save-capture
test-campaign-collection: $(BUILD)/campaign_save.o $(BUILD)/campaign_file.o
	python3 $(ROOT)/tools/amiga/test_campaign_collection.py
.PHONY: test-campaign-collection
test: test-campaign-collection
test-campaign-progress: $(BUILD)/campaign_save.o $(BUILD)/campaign_file.o
	python3 $(ROOT)/tools/amiga/test_campaign_progress.py
test: test-campaign-progress
tower-station-save: tower-station test-campaign-progress
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-save-live CPPFLAGS="$(STATION_FLAGS) -DV6_STATION_SAVE" $(ROOT)/build/amiga-station-save-live/tower.adf
tower-station-save-run: tower-station-save
	python3 $(ROOT)/tools/amiga/run_station_save.py --build $(ROOT)/build/amiga-station-save-live --interactive
tower-station-save-capture: tower-station-save
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-save CPPFLAGS="$(STATION_FLAGS) -DV6_STATION_SAVE -DV6_STATION_CAPTURE" $(ROOT)/build/amiga-station-save/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_save.py --build $(ROOT)/build/amiga-station-save

.PHONY: test-station-companion tower-station-companion-capture
test-station-companion: $(BUILD)/companion.o
	python3 $(ROOT)/tools/amiga/test_station_companion.py
test: test-station-companion
tower-station-companion-capture: tower-station
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-companion CPPFLAGS="$(STATION_FLAGS) -DV6_STATION_CAPTURE -DV6_STATION_COMPANION_CAPTURE" $(ROOT)/build/amiga-station-companion/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_companion.py

STATION_MENU_FLAGS = $(STATION_FLAGS) -DV6_STATION_MENU -DV6_TOWER_UI_SAVE -DV6_TOWER_ARRIVAL -DV6_TOWER_ROUNDTRIP -DV6_TOWER_MENU_TRAVEL
.PHONY: tower-station-menu tower-station-menu-run tower-station-menu-capture
tower-station-menu: tower-station test-campaign-progress
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-menu-live CPPFLAGS="$(STATION_MENU_FLAGS)" $(ROOT)/build/amiga-station-menu-live/tower.adf
tower-station-menu-run: tower-station-menu
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-station-menu-live
tower-station-menu-capture: tower-station-menu
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-menu CPPFLAGS="$(STATION_MENU_FLAGS) -DV6_STATION_CAPTURE -DV6_TOWER_UI_REPLAY" $(ROOT)/build/amiga-station-menu/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_menu.py --build $(ROOT)/build/amiga-station-menu --live $(ROOT)/build/amiga-station-menu-live

.PHONY: tower-station-travel-capture
tower-station-travel-capture: tower-station-menu
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-travel CPPFLAGS="$(STATION_MENU_FLAGS) -DV6_TELE_MENU_CAPTURE -DV6_STATION_TRAVEL_CAPTURE" $(ROOT)/build/amiga-station-travel/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_travel.py --build $(ROOT)/build/amiga-station-travel --live $(ROOT)/build/amiga-station-menu-live

STATION_EFFECT_FLAGS = $(STATION_MENU_FLAGS) -DV6_TOWER_SHAKE -DV6_TOWER_TRAVEL_AUDIO -DV6_TRAVEL_SFX_MASK=12
.PHONY: tower-station-effects tower-station-effects-run tower-station-effects-capture
tower-station-effects: tower-station-menu test-shake-caption test-audio-policy test-paula-voice
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-effects-live CPPFLAGS="$(STATION_EFFECT_FLAGS)" $(ROOT)/build/amiga-station-effects-live/tower.adf
tower-station-effects-run: tower-station-effects
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-station-effects-live
tower-station-effects-capture: tower-station-effects
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-effects CPPFLAGS="$(STATION_EFFECT_FLAGS) -DV6_TELE_MENU_CAPTURE -DV6_STATION_TRAVEL_CAPTURE" $(ROOT)/build/amiga-station-effects/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_travel.py --build $(ROOT)/build/amiga-station-effects --live $(ROOT)/build/amiga-station-effects-live --effects
	$(MAKE) BUILD=$(ROOT)/build/amiga-station-effects-rescue CPPFLAGS="$(STATION_EFFECT_FLAGS) -DV6_STATION_CAPTURE" $(ROOT)/build/amiga-station-effects-rescue/tower.adf
	python3 $(ROOT)/tools/amiga/run_station_game.py --build $(ROOT)/build/amiga-station-effects-rescue --menu-effects

.PHONY: shenanigan-run
shenanigan-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-shenanigan SCENE=shenanigan all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-shenanigan

.PHONY: shenanigan-capture
shenanigan-capture:
	$(MAKE) BUILD=$(ROOT)/build/amiga-shenanigan SCENE=shenanigan all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-shenanigan --capture --shenanigan

.PHONY: tower-shenanigan-capture
tower-shenanigan-capture: tower-station-effects
	$(MAKE) BUILD=$(ROOT)/build/amiga-shenanigan-effects CPPFLAGS="$(STATION_EFFECT_FLAGS) -DV6_SHENANIGAN_CAPTURE" $(ROOT)/build/amiga-shenanigan-effects/tower.adf
	python3 $(ROOT)/tools/amiga/run_shenanigan_route.py --build $(ROOT)/build/amiga-shenanigan-effects

.PHONY: prize-run prize-capture
test-prize: $(BUILD)/prize.o
	cc -std=c99 -O2 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -I. $(ROOT)/tools/amiga/test_prize.c audio_policy.c prize.c platform_gate.c disappearing.c trinkets.c checkpoints.c platform.c enemy.c player.c terrain.c blocks.c -o $(BUILD)/test_prize
	$(BUILD)/test_prize
.PHONY: test-prize
test: test-prize
.PHONY: test-trinket-screen
test-trinket-screen: $(BUILD)/trinket_screen.o
	python3 $(ROOT)/tools/amiga/test_trinket_screen.py
test: test-trinket-screen
$(BUILD)/trinket_screen.o: trinket_screen.c trinket_screen.h trinkets.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
$(BUILD)/pickup_draw.o: pickup_draw.c pickup_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
$(BUILD)/pickup_copper.o: pickup_copper.c pickup_copper.h pickup_draw.h tower_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-pickup-presentation
test-pickup-presentation: $(BUILD)/pickup_draw.o $(BUILD)/pickup_copper.o
	python3 $(ROOT)/tools/amiga/test_pickup_presentation.py
test: test-pickup-presentation
prize-run:
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize SCENE=prize all
	python3 $(ROOT)/tools/amiga/run_copperline.py --rom "$(ROM)" --emulator "$(COPPERLINE)" --build $(ROOT)/build/amiga-prize
prize-capture: test-prize test-tile-edit
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-replay SCENE=prize CPPFLAGS="-DV6_PRIZE_REPLAY" all
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize SCENE=prize all
	python3 $(ROOT)/tools/amiga/test_prize_export.py --build $(ROOT)/build/amiga-prize-replay
	python3 $(ROOT)/tools/amiga/run_prize.py --build $(ROOT)/build/amiga-prize-replay --live $(ROOT)/build/amiga-prize

# Prize remains a candidate until its pickup UI and room sound cues are wired.
PRIZE_ROUTE_FLAGS = $(STATION_EFFECT_FLAGS) -DV6_TOWER_PRIZE -DV6_TOWER_COLLECTION_SAVE -DV6_TOWER_PICKUP_SCREEN
.PHONY: tower-prize-route tower-prize-route-run tower-prize-route-capture
tower-prize-route: tower-assets
	python3 -c 'from pathlib import Path; p=Path("$(ROOT)/build/amiga-feasibility"); b=(p/"loadmap.v6tr").read_bytes(); (p/"tower_map.h").write_text("static const unsigned char tower_map[]={"+",".join(map(str,b))+"};\n")'
	python3 $(ROOT)/tools/amiga/test_prize_graphics.py
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-route CPPFLAGS="$(PRIZE_ROUTE_FLAGS)" $(ROOT)/build/amiga-prize-route/tower.adf
tower-prize-route-run: tower-prize-route
	python3 $(ROOT)/tools/amiga/run_interactive_save.py --build $(ROOT)/build/amiga-prize-route
tower-prize-route-capture: tower-prize-route
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-route-replay CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_ROUTE_CAPTURE" $(ROOT)/build/amiga-prize-route-replay/tower.adf
	python3 $(ROOT)/tools/amiga/run_prize_route.py --build $(ROOT)/build/amiga-prize-route-replay --v4
.PHONY: tower-prize-pickup-capture
tower-prize-pickup-capture: tower-prize-route
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-pickup CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_ROUTE_CAPTURE -DV6_PICKUP_CAPTURE_HOLD" $(ROOT)/build/amiga-prize-pickup/tower.adf
	python3 $(ROOT)/tools/amiga/run_prize_pickup.py --build $(ROOT)/build/amiga-prize-pickup
.PHONY: test-prize-route
test-prize-route:
	python3 $(ROOT)/tools/amiga/test_prize_route.py
test: test-prize-route

.PHONY: test-prize-audio
test-prize-audio:
	python3 $(ROOT)/tools/amiga/test_prize_audio.py
test: test-prize-audio

$(BUILD)/pickup_fade.o: pickup_fade.c pickup_fade.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-pickup-fade
test-pickup-fade: $(BUILD)/pickup_fade.o
	python3 $(ROOT)/tools/amiga/test_pickup_fade.py
test: test-pickup-fade

.PHONY: test-prize-input tower-prize-input-capture
test-prize-input:
	python3 $(ROOT)/tools/amiga/test_prize_input.py
test: test-prize-input
tower-prize-input-capture: tower-prize-route test-prize-input
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-input CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE" $(ROOT)/build/amiga-prize-input/tower.adf
	python3 $(ROOT)/tools/amiga/run_prize_input.py --build $(ROOT)/build/amiga-prize-input

.PHONY: test-prize-death-platform
test-prize-death-platform:
	python3 $(ROOT)/tools/amiga/test_prize_death_platform.py
test: test-prize-death-platform

.PHONY: test-prize-checkpoint test-vstitch-graphics tower-prize-checkpoint-capture
test-prize-checkpoint:
	python3 $(ROOT)/tools/amiga/test_prize_checkpoint.py
test: test-prize-checkpoint
test-vstitch-graphics: tower-assets
	python3 $(ROOT)/tools/amiga/test_vstitch_graphics.py
tower-prize-checkpoint-capture: test-vstitch-graphics test-prize-checkpoint
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-checkpoint CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE" $(ROOT)/build/amiga-prize-checkpoint/tower.adf
	python3 $(ROOT)/tools/amiga/run_prize_checkpoint.py --build $(ROOT)/build/amiga-prize-checkpoint

.PHONY: test-prize-collection-input tower-prize-collection-input-capture
test-prize-collection-input:
	python3 $(ROOT)/tools/amiga/test_prize_collection_input.py
test: test-prize-collection-input
tower-prize-collection-input-capture: test-player-crop test-prize-collection-input
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-collection-input CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_PRIZE_COLLECTION_INPUT_CAPTURE" $(ROOT)/build/amiga-prize-collection-input/tower.adf
	python3 $(ROOT)/tools/amiga/run_prize_collection_input.py --build $(ROOT)/build/amiga-prize-collection-input

.PHONY: test-floor-retry
test-floor-retry:
	python3 $(ROOT)/tools/amiga/test_floor_retry.py
test: test-floor-retry

.PHONY: test-player-crop
test-player-crop: tower-assets
	python3 $(ROOT)/tools/amiga/test_player_crop.py

.PHONY: test-prize-return-data
test-prize-return-data: tower-assets
	python3 $(ROOT)/tools/amiga/test_prize_return_data.py

$(BUILD)/prize_return.o: prize_return.c prize_return.h platform.h enemy.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

.PHONY: test-prize-return-actors
test-prize-return-actors:
	python3 $(ROOT)/tools/amiga/test_prize_return_actors.py
test: test-prize-return-actors

$(BUILD)/prize_return_sprite.o: prize_return_sprite.c prize_return_sprite.h pixel_collision.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
.PHONY: test-prize-return-sprite
test-prize-return-sprite: tower-assets
	python3 $(ROOT)/tools/amiga/test_prize_return_sprite.py

.PHONY: test-prize-return-route
test-prize-return-route: tower-assets
	python3 $(ROOT)/tools/amiga/test_prize_return_route.py

$(BUILD)/prize_return_draw.o: prize_return_draw.c prize_return_draw.h tower_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-prize-return-draw tower-prize-return-input-capture
test: test-prize-return-draw
test-prize-return-draw: tower-assets
	python3 $(ROOT)/tools/amiga/test_prize_return_draw.py
tower-prize-return-input-capture: test-prize-return-draw test-prize-return-route test-prize-return-actors
	$(MAKE) BUILD=$(ROOT)/build/amiga-prize-return-input CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_PRIZE_RETURN_INPUT_CAPTURE" $(ROOT)/build/amiga-prize-return-input/tower.adf
	python3 $(ROOT)/tools/amiga/run_prize_return_input.py --build $(ROOT)/build/amiga-prize-return-input

# The west actor bank adds two moving enemies and six conveyors.
ifneq ($(findstring -DV6_PRIZE_RETURN_INPUT_CAPTURE,$(CPPFLAGS)),)
$(addprefix $(BUILD)/,enemy.o platform.o blocks.o sprites.o prize_return.o prize_return_sprite.o pixel_collision.o): CFLAGS += -O2
endif

$(BUILD)/vstitch_trigger.o: vstitch_trigger.c vstitch_trigger.h player.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-vstitch-trigger tower-vstitch-hint-capture
test-vstitch-trigger: $(BUILD)/vstitch_trigger.o
	python3 $(ROOT)/tools/amiga/test_vstitch_trigger.py
test: test-vstitch-trigger
tower-vstitch-hint-capture: tower-assets test-vstitch-trigger test-vstitch-hint-draw
	$(MAKE) BUILD=$(ROOT)/build/amiga-vstitch-hint CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE" $(ROOT)/build/amiga-vstitch-hint/tower.adf
	python3 $(ROOT)/tools/amiga/run_vstitch_hint.py --build $(ROOT)/build/amiga-vstitch-hint

$(BUILD)/vstitch_hint_draw.o: vstitch_hint_draw.c vstitch_hint_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
$(BUILD)/vstitch_hint_copper.o: vstitch_hint_copper.c vstitch_hint_draw.h tower_draw.h pickup_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-vstitch-hint-draw
test-vstitch-hint-draw: $(BUILD)/vstitch_hint_draw.o $(BUILD)/vstitch_hint_copper.o
	python3 $(ROOT)/tools/amiga/test_vstitch_hint_draw.py
test: test-vstitch-hint-draw

.PHONY: test-campaign-hint
test-campaign-hint: $(BUILD)/campaign_save.o $(BUILD)/campaign_file.o
	python3 $(ROOT)/tools/amiga/test_campaign_hint.py
test: test-campaign-hint

.PHONY: tower-vstitch-hint-save-capture
tower-vstitch-hint-save-capture: tower-assets test-campaign-hint test-vstitch-trigger test-vstitch-hint-draw
	$(MAKE) BUILD=$(ROOT)/build/amiga-vstitch-hint CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE" $(ROOT)/build/amiga-vstitch-hint/tower.adf
	$(MAKE) BUILD=$(ROOT)/build/amiga-vstitch-hint-load CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_VSTITCH_HINT_LOAD" $(ROOT)/build/amiga-vstitch-hint-load/tower.adf
	python3 $(ROOT)/tools/amiga/run_vstitch_hint_save.py --build $(ROOT)/build/amiga-vstitch-hint --load-build $(ROOT)/build/amiga-vstitch-hint-load

$(BUILD)/keyboard.o: keyboard.c keyboard.h map_menu.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-keyboard tower-map-input tower-map-input-capture tower-map-input-run
test-keyboard: $(BUILD)/keyboard.o
	python3 $(ROOT)/tools/amiga/test_keyboard.py
test: test-keyboard
tower-map-input: tower-assets test-keyboard test-map-menu
	$(MAKE) BUILD=$(ROOT)/build/amiga-map-input CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE" $(ROOT)/build/amiga-map-input/tower.adf
tower-map-input-capture: tower-map-input
	$(MAKE) BUILD=$(ROOT)/build/amiga-vstitch-hint-load CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_VSTITCH_HINT_LOAD" $(ROOT)/build/amiga-vstitch-hint-load/tower.adf
	python3 $(ROOT)/tools/amiga/run_map_input.py --build $(ROOT)/build/amiga-map-input --load-build $(ROOT)/build/amiga-vstitch-hint-load
tower-map-input-run: tower-map-input
	python3 $(ROOT)/tools/amiga/run_map_input.py --build $(ROOT)/build/amiga-map-input --run

$(BUILD)/map_draw.o: map_draw.c map_draw.h save_page.h sprites.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-map-draw tower-map-display tower-map-display-capture tower-map-display-run tower-map-display-dirty-capture
test-map-draw: $(BUILD)/map_draw.o
	python3 $(ROOT)/tools/amiga/test_map_draw.py
test: test-map-draw
tower-map-display: tower-assets test-map-draw test-map-menu test-map-transition test-map-slide test-keyboard
	python3 $(ROOT)/tools/amiga/convert_map_assets.py --data "$(DATA)" --out $(ROOT)/build/amiga-feasibility
	$(MAKE) BUILD=$(ROOT)/build/amiga-map-display CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE" $(ROOT)/build/amiga-map-display/tower.adf
tower-map-display-capture: tower-map-display
	python3 $(ROOT)/tools/amiga/run_map_display.py --build $(ROOT)/build/amiga-map-display
tower-map-display-run: tower-map-display
	python3 $(ROOT)/tools/amiga/run_map_input.py --build $(ROOT)/build/amiga-map-display --run
tower-map-display-dirty-capture: tower-map-display
	$(MAKE) BUILD=$(ROOT)/build/amiga-map-display-dirty CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_MAP_DIRTY_CAPTURE" $(ROOT)/build/amiga-map-display-dirty/tower.adf
	python3 $(ROOT)/tools/amiga/run_map_display.py --build $(ROOT)/build/amiga-map-display-dirty --dirty

$(BUILD)/map_slide.o: map_slide.c map_slide.h map_draw.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-map-slide
test-map-slide: $(BUILD)/map_slide.o
	python3 $(ROOT)/tools/amiga/test_map_slide.py
test: test-map-slide

$(BUILD)/save_page.o: save_page.c save_page.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-save-page
test-save-page: $(BUILD)/save_page.o
	python3 $(ROOT)/tools/amiga/test_save_page.py
test: test-save-page

.PHONY: test-save-draw
test-save-draw: $(BUILD)/map_draw.o test-save-page
	python3 $(ROOT)/tools/amiga/test_save_draw.py
test: test-save-draw

.PHONY: tower-save-display tower-save-display-capture tower-save-display-run
tower-save-display: tower-map-display test-save-dma
	python3 $(ROOT)/tools/amiga/convert_save_assets.py --out $(ROOT)/build/amiga-feasibility
	$(MAKE) BUILD=$(ROOT)/build/amiga-save-display CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_SAVE_DISPLAY_CAPTURE" $(ROOT)/build/amiga-save-display/tower.adf
tower-save-display-capture: tower-save-display
	python3 $(ROOT)/tools/amiga/run_map_display.py --build $(ROOT)/build/amiga-save-display --save-pages
	python3 $(ROOT)/tools/amiga/run_save_display.py --build $(ROOT)/build/amiga-save-display
tower-save-display-run: tower-save-display
	python3 $(ROOT)/tools/amiga/run_map_input.py --build $(ROOT)/build/amiga-save-display --run

.PHONY: test-save-dma
test-save-dma: test-save-draw
	python3 $(ROOT)/tools/amiga/test_save_dma.py
test: test-save-dma

$(BUILD)/save_summary.o: save_summary.c save_summary.h trinkets.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-save-summary
test-save-summary: $(BUILD)/save_summary.o
	python3 $(ROOT)/tools/amiga/test_save_summary.py
test: test-save-summary

$(BUILD)/campaign_menu.o: campaign_menu.c campaign_menu.h save_summary.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
$(BUILD)/campaign_menu_file.o: campaign_menu_file.c campaign_menu.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-campaign-menu
test-campaign-menu: $(BUILD)/campaign_menu.o $(BUILD)/campaign_menu_file.o
	python3 $(ROOT)/tools/amiga/test_campaign_menu.py
test: test-campaign-menu

$(BUILD)/ui_menu.o: ui_menu.c ui_menu.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@

.PHONY: test-ui-menu tower-menu
test-ui-menu: $(BUILD)/ui_menu.o test-save-summary
	python3 $(ROOT)/tools/amiga/test_ui_menu.py
test: test-ui-menu
tower-menu: tower-save-display test-campaign-menu
	python3 $(ROOT)/tools/amiga/convert_ui_assets.py --out $(ROOT)/build/amiga-feasibility
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_SAVE_DISPLAY_CAPTURE -DV6_MENU_COMPLETE" $(ROOT)/build/amiga-menu/tower.adf

.PHONY: tower-menu-load tower-menu-capture
tower-menu-load: tower-menu
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-load CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_VSTITCH_HINT_LOAD -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_SAVE_DISPLAY_CAPTURE -DV6_MENU_COMPLETE" $(ROOT)/build/amiga-menu-load/tower.adf
tower-menu-capture: tower-menu
	python3 $(ROOT)/tools/amiga/run_map_display.py --build $(ROOT)/build/amiga-menu --complete-menu
	python3 $(ROOT)/tools/amiga/run_ui_menu.py --build $(ROOT)/build/amiga-menu

.PHONY: tower-menu-reload-capture
tower-menu-reload-capture: tower-menu-load
	python3 $(ROOT)/tools/amiga/run_map_display.py --build $(ROOT)/build/amiga-menu --complete-menu
	python3 $(ROOT)/tools/amiga/run_ui_menu_reload.py --build $(ROOT)/build/amiga-menu --load-build $(ROOT)/build/amiga-menu-load

$(BUILD)/menu_slide.o: menu_slide.c menu_slide.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-menu-slide tower-menu-slide
test-menu-slide: $(BUILD)/menu_slide.o
	python3 $(ROOT)/tools/amiga/test_menu_slide.py
tower-menu-slide: tower-menu test-menu-slide
	$(MAKE) BUILD=$(ROOT)/build/amiga-menu-slide-native CPPFLAGS="$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_SAVE_DISPLAY_CAPTURE -DV6_MENU_COMPLETE -DV6_MENU_SLIDE" $(ROOT)/build/amiga-menu-slide-native/tower.adf

$(BUILD)/north_route.o: north_route.c north_route.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
.PHONY: test-north-route test-menu-portal-cache tower-menu-slide-capture
.PHONY: test-map-tower-cursor
.PHONY: test-sprite-mux
$(BUILD)/sprite_mux.o: sprite_mux.c sprite_mux.h | $(BUILD)
	$(CC) $(CFLAGS) -O2 -c $< -o $@
test-sprite-mux: $(BUILD)/sprite_mux.o test-north-route
	python3 $(ROOT)/tools/amiga/test_sprite_mux.py
.PHONY: tower-menu-scenes-capture
tower-menu-scenes-capture: tower-menu-slide
	python3 $(ROOT)/tools/amiga/run_menu_scenes.py --cppflags "$(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_SAVE_DISPLAY_CAPTURE -DV6_MENU_COMPLETE -DV6_MENU_SLIDE"
.PHONY: test-north-graphics
test-north-graphics: tower-assets
	python3 $(ROOT)/tools/amiga/test_north_graphics.py
test-map-tower-cursor: $(BUILD)/map_draw.o
	python3 $(ROOT)/tools/amiga/test_map_tower_cursor.py
test-north-route: $(BUILD)/north_route.o
	python3 $(ROOT)/tools/amiga/test_north_route.py
test-menu-portal-cache:
	python3 $(ROOT)/tools/amiga/test_menu_portal_cache.py
tower-menu-slide-capture: tower-menu-slide
	python3 $(ROOT)/tools/amiga/run_ui_slide.py --build $(ROOT)/build/amiga-menu-slide-native --page 0
	python3 $(ROOT)/tools/amiga/run_ui_slide.py --build $(ROOT)/build/amiga-menu-slide-native --page 1
	python3 $(ROOT)/tools/amiga/run_ui_slide.py --build $(ROOT)/build/amiga-menu-slide-native --page 2
	python3 $(ROOT)/tools/amiga/run_ui_slide.py --build $(ROOT)/build/amiga-menu-slide-native --page 3

NORTH_FLAGS = $(PRIZE_ROUTE_FLAGS) -DV6_PRIZE_INPUT_CAPTURE -DV6_VSTITCH_INPUT_CAPTURE -DV6_VSTITCH_HINT_CAPTURE -DV6_MAP_INPUT_CAPTURE -DV6_MAP_DISPLAY_CAPTURE -DV6_SAVE_DISPLAY_CAPTURE -DV6_MENU_COMPLETE -DV6_MENU_SLIDE -DV6_NORTH_ROUTE
.PHONY: tower-north tower-north-capture tower-north-scenes-capture tower-north-bob-capture test-sprite-overlay
# Private original-game assets are generated into ignored build output.
tower-north: tower-menu-slide
	$(MAKE) BUILD=$(ROOT)/build/amiga-north CPPFLAGS="$(NORTH_FLAGS)" $(ROOT)/build/amiga-north/tower.adf
tower-north-capture: tower-north
	python3 $(ROOT)/tools/amiga/run_north_capture.py --cppflags "$(NORTH_FLAGS)"
tower-north-scenes-capture: tower-north
	python3 $(ROOT)/tools/amiga/run_menu_scenes.py --cppflags "$(NORTH_FLAGS)" --north
tower-north-bob-capture: tower-north
	python3 $(ROOT)/tools/amiga/run_north_capture.py --cppflags "$(NORTH_FLAGS)" --case bob
.PHONY: tower-north-boot-capture
tower-north-boot-capture: tower-north
	python3 $(ROOT)/tools/amiga/test_north_boot.py --rom "$(ROM)"
test-sprite-overlay:
	python3 $(ROOT)/tools/amiga/test_sprite_overlay.py

.PHONY: test-predecoded-route
test-predecoded-route:
	python3 $(ROOT)/tools/amiga/test_predecoded_route.py
